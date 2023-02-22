# coding=utf-8

#
# Copyright (c) 2020-2023 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import subprocess
import json
import sys
import time

from public_method import get_server_dict, get_config_ip, get_sn_list


def modify_init_file(developer_path, device_sn, device_ip):
    """
    /etc/init.cfg文件添加cmds
    """
    hdc_str = "hdc -s %s:8710 -t %s " % (device_ip, device_sn)
    recv_path = os.path.join(developer_path, "localCoverage/resident_service/resources")
    print(hdc_str + "file recv /etc/init.cfg %s" % recv_path)
    subprocess.Popen(hdc_str + "file recv /etc/init.cfg %s" % recv_path,
                     shell=True).communicate()
    recv_restores_path = os.path.join(recv_path, "restores_environment")
    if not os.path.exists(recv_restores_path):
        os.mkdir(recv_restores_path)
    recv_restores_name = os.path.join(recv_restores_path, "init.cfg")
    if not os.path.exists(recv_restores_name):
        subprocess.Popen(hdc_str + "file recv /etc/init.cfg %s" % recv_restores_path,
                         shell=True).communicate()
    else:
        print("INFO: file exit", recv_restores_name)

    cfg_file_path = os.path.join(recv_path, "init.cfg")
    if os.path.exists(cfg_file_path):
        with open(cfg_file_path, "r") as fp:
            json_data = json.load(fp)

        for jobs_list in json_data["jobs"]:
            if jobs_list["name"] == "init":
                if jobs_list["cmds"][-1] != "export GCOV_FETCH_METHOD FM_SIGNA":
                    jobs_list["cmds"].append("mkdir /data/gcov 0777 system system")
                    jobs_list["cmds"].append("export GCOV_PREFIX /data/gcov")
                    jobs_list["cmds"].append("export GCOV_FETCH_METHOD FM_SIGNA")
                else:
                    return
        json_str = json.dumps(json_data, indent=2)
        with open(cfg_file_path, "w") as json_file:
            json_file.write(json_str)
    else:
        print("init.cfg file not exists")
        return
    print(hdc_str + "shell mount -o rw,remount / > /dev/null 2>&1")
    subprocess.Popen(hdc_str + "shell mount -o rw,remount / > /dev/null 2>&1",
                     shell=True).communicate()
    print(hdc_str + "file send %s %s" % (cfg_file_path, "/etc/"))
    subprocess.Popen(hdc_str + "file send %s %s" % (cfg_file_path, "/etc/"),
                     shell=True).communicate()
    subprocess.Popen(hdc_str + "shell param set persist.appspawn.client.timeout 120 > /dev/null 2>&1",
                     shell=True).communicate()
    print(hdc_str + "shell reboot")
    subprocess.Popen(hdc_str + "shell reboot > /dev/null 2>&1", shell=True).communicate()
    return


def modify_faultloggerd_file(developer_path, device_sn, device_ip):
    hdc_str = "hdc -s %s:8710 -t %s " % (device_ip, device_sn)
    so_path = os.path.join(
        developer_path, "localCoverage/resident_service/resources/libgcov_dump_sign.z.so")
    _, system_lib = subprocess.getstatusoutput(
        hdc_str + "shell find /system/lib -name libgcov_dump_sign.z.so")
    _, system_lib64 = subprocess.getstatusoutput(
        hdc_str + "shell find /system/lib64 -name libgcov_dump_sign.z.so")
    _, enforce = subprocess.getstatusoutput(hdc_str + "shell getenforce")
    if_reboot = False
    if not system_lib or not system_lib64 or enforce != "Permissive":
        if_reboot = True
        print(hdc_str + "shell mount -o rw,remount /")
        subprocess.Popen(hdc_str + "shell mount -o rw,remount /",
                         shell=True).communicate()
        print(hdc_str + "file send %s %s" % (so_path, "/system/lib/"))
        subprocess.Popen(hdc_str + "file send %s %s" % (so_path, "/system/lib/"),
                         shell=True).communicate()
        subprocess.Popen(hdc_str + "file send %s %s" % (so_path, "/system/lib64/"),
                         shell=True).communicate()
        subprocess.Popen(hdc_str + "shell sed -i 's/enforcing/permissive/g' /system/etc/selinux/config",
                         shell=True).communicate()

    recv_path = os.path.join(developer_path, "localCoverage/resident_service/resources")
    print(hdc_str + "file recv /system/etc/init/faultloggerd.cfg %s" % recv_path)
    subprocess.Popen(hdc_str + "file recv /system/etc/init/faultloggerd.cfg %s" % recv_path,
                     shell=True).communicate()

    cfg_file_path = os.path.join(recv_path, "faultloggerd.cfg")
    if os.path.exists(cfg_file_path):
        with open(cfg_file_path, "r") as fp:
            json_data = json.load(fp)
        if len(json_data["jobs"]) == 1 and json_data["jobs"][0]["name"] != "pre-init":
            if_reboot = True
            json_data["jobs"].insert(0, {
                "name": "pre-init",
                "cmds": [
                    "export LD_PRELOAD libgcov_dump_sign.z.so"
                ]
            })
            json_str = json.dumps(json_data, indent=4)
            with open(cfg_file_path, "w") as json_file:
                json_file.write(json_str)
            print(hdc_str + "file send %s %s" % (cfg_file_path, "/system/etc/init/"))
            subprocess.Popen(hdc_str + "file send %s %s" % (cfg_file_path, "/system/etc/init/"),
                             shell=True).communicate()
    else:
        print("faultloggerd.cfg file not exists.")
    if if_reboot:
        print(hdc_str + "shell reboot")
        subprocess.Popen(hdc_str + "shell reboot", shell=True).communicate()


def split_foundation_services(developer_path, device_sn, device_ip,
                              system_info_dict, home_path):
    """
    foundation.xml、XXX.xml文件推送到 /system/profile
    XXX.cfg文件推送到/etc/init/
    reboot设备，可以将服务从foundation中拆分出来，成为一个独立服务进程
    """
    resident_service_path = os.path.join(
        developer_path, "localCoverage/resident_service")
    config_path = os.path.join(resident_service_path, "config")
    restores_path = os.path.join(
        resident_service_path, "resources", "restores_environment")
    xml_restores_path = os.path.join(restores_path, "foundation.xml")

    hdc_str = "hdc -s %s:8710 -t %s " % (device_ip, device_sn)
    if not os.path.exists(xml_restores_path):
        print(hdc_str + "file recv /system/profile/foundation.xml %s" % restores_path)
        subprocess.Popen(hdc_str + "file recv /system/profile/foundation.xml %s" % restores_path,
                         shell=True).communicate()

    # 推送xml数据
    flag = False
    for key, value_list in system_info_dict.items():
        for process_str in value_list:
            foundation_xml_path = os.path.join(config_path, process_str, "foundation.xml")
            print(hdc_str + "shell mount -o rw,remount /")
            subprocess.Popen(hdc_str + "shell mount -o rw,remount /",
                             shell=True).communicate()
            if os.path.exists(foundation_xml_path):
                flag = True
                subprocess.Popen(hdc_str + "shell rm -rf /lost+found", shell=True).communicate()
                subprocess.Popen(hdc_str + "shell rm -rf /log", shell=True).communicate()
                subprocess.Popen(hdc_str + "shell rm -rf %s" % home_path, shell=True).communicate()
                print(hdc_str + "file send %s %s" % (foundation_xml_path, "/system/profile/"))
                subprocess.Popen(hdc_str + "file send %s %s" % (
                    foundation_xml_path, "/system/profile/"), shell=True).communicate()

                process_xml_path = os.path.join(config_path, process_str, process_str + ".xml")
                print(hdc_str + "file send %s %s" % (process_xml_path, "/system/profile/"))
                subprocess.Popen(hdc_str + "file send %s %s" % (
                    process_xml_path, "/system/profile/"), shell=True).communicate()

                process_cfg_path = os.path.join(config_path, process_str, process_str + ".cfg")
                print(hdc_str + "file send %s %s" % (process_cfg_path, "/etc/init/"))
                subprocess.Popen(hdc_str + "file send %s %s" % (
                    process_cfg_path, "/etc/init/"), shell=True).communicate()
    if flag:
        print(hdc_str + "shell reboot")
        subprocess.Popen(hdc_str + "shell reboot", shell=True).communicate()
        while True:
            after_sn_list = get_sn_list("hdc -s %s:8710 list targets" % device_ip)
            time.sleep(10)
            if device_sn in after_sn_list:
                break

    subprocess.Popen(hdc_str + "shell mount -o rw,remount /",
                     shell=True).communicate()
    subprocess.Popen(hdc_str + 'shell "rm -fr %s"' % ("/data/gcov" + home_path),
                     shell=True).communicate()
    subprocess.Popen(hdc_str + 'shell "chmod 777 /data/gcov - R"', shell=True).communicate()
    subprocess.Popen(hdc_str + "shell getenforce", shell=True).communicate()
    return


def modify_init_cfg(developer_path, device_ip, device_sn_list):
    if device_ip and len(device_sn_list) >= 1:
        before_sn_list = device_sn_list
        for device_sn_str in device_sn_list:
            modify_init_file(developer_path, device_sn_str, device_ip)

        while True:
            after_sn_list = get_sn_list("hdc -s %s:8710 list targets" % device_ip)
            time.sleep(10)
            if after_sn_list == before_sn_list:
                break
    else:
        print("user_config.xml device ip not config")


def modify_faultloggerd_cfg(developer_path, device_ip, device_sn_list):
    if device_ip and len(device_sn_list) >= 1:
        before_sn_list = device_sn_list
        for device_sn_str in device_sn_list:
            modify_faultloggerd_file(developer_path, device_sn_str, device_ip)

        while True:
            after_sn_list = get_sn_list("hdc -s %s:8710 list targets" % device_ip)
            time.sleep(10)
            if after_sn_list == before_sn_list:
                break
    else:
        print("user_config.xml device ip not config")


if __name__ == '__main__':
    command_args = sys.argv[1]
    command_str = command_args.split("command_str=")[1].replace(",", " ")
    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_path = os.path.join(
        current_path.split("/developer_test/src")[0], "developer_test")
    home_path = '/'.join(root_path.split("/")[:3])

    # 获取user_config中的device ip
    device_ip = get_config_ip(os.path.join(developer_path, "config/user_config.xml"))
    device_sn_list = get_sn_list("hdc -s %s" % device_ip + ":8710 list targets")

    # 修改设备init.cfg文件
    modify_init_cfg(developer_path, device_ip, device_sn_list)
    # 修改faultloggerd.cfg文件
    modify_faultloggerd_cfg(developer_path, device_ip, device_sn_list)

    # 获取子系统部件与服务的关系
    system_info_dict, services_component_dict, component_gcda_dict = get_server_dict(command_str)

    # 推送服务对应的xml文件
    if device_ip and len(system_info_dict.keys()) >= 1:
        for device_sn_str in device_sn_list:
            split_foundation_services(developer_path, device_sn_str,
                                      device_ip, system_info_dict, home_path)
