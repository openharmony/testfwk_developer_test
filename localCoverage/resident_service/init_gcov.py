#!/usr/bin/env python3
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
import xml.etree.ElementTree as ET
from public_method import get_server_dict, get_config_ip, get_sn_list


def _init_sys_config():
    sys.localcoverage_path = os.path.join(current_path, "..")
    sys.path.insert(0, sys.localcoverage_path)


def modify_init_file(developer_path, hdc_str):
    """
    /etc/init.cfg文件添加cmds
    """
    recv_path = os.path.join(developer_path, "localCoverage/resident_service/resources")
    print("%s file recv /etc/init.cfg %s" % (hdc_str, recv_path))
    coverage_command("%s file recv /etc/init.cfg %s" % (hdc_str, recv_path))
    recv_restores_path = os.path.join(recv_path, "restores_environment")
    if not os.path.exists(recv_restores_path):
        os.mkdir(recv_restores_path)
    recv_restores_name = os.path.join(recv_restores_path, "init.cfg")
    if not os.path.exists(recv_restores_name):
        coverage_command("%s file recv /etc/init.cfg %s" % (hdc_str, recv_restores_path))
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
    print("%s shell mount -o rw,remount / > /dev/null 2>&1" % hdc_str)
    coverage_command("%s shell mount -o rw,remount / > /dev/null 2>&1" % hdc_str)
    print("%s file send %s %s" % (hdc_str, cfg_file_path, "/etc/"))
    coverage_command("%s file send %s %s" % (hdc_str, cfg_file_path, "/etc/"))
    coverage_command("%s shell param set persist.appspawn.client.timeout 120 > /dev/null 2>&1" % hdc_str)
    return


def modify_faultloggerd_file(developer_path, hdc_str):
    _, enforce = subprocess.getstatusoutput("%s shell getenforce" % hdc_str)
    coverage_command("%s shell mount -o rw,remount /" % hdc_str)
    print("%s shell mount -o rw,remount /" % hdc_str)
    if enforce != "Permissive":
        coverage_command("%s shell sed -i 's/enforcing/permissive/g' /system/etc/selinux/config" % hdc_str)

    recv_path = os.path.join(developer_path, "localCoverage/resident_service/resources")
    print("%s file recv /system/etc/init/faultloggerd.cfg %s" % (hdc_str, recv_path))
    coverage_command("%s file recv /system/etc/init/faultloggerd.cfg %s" % (hdc_str, recv_path))

    cfg_file_path = os.path.join(recv_path, "faultloggerd.cfg")
    if os.path.exists(cfg_file_path):
        with open(cfg_file_path, "r") as fp:
            json_data = json.load(fp)
        if len(json_data["jobs"]) == 1 and json_data["jobs"][0]["name"] != "pre-init":
            json_data["jobs"].insert(0, {
                "name": "pre-init",
                "cmds": [
                    "export LD_PRELOAD libcoverage_signal_handler.z.so"
                ]
            })
            json_str = json.dumps(json_data, indent=4)
            with open(cfg_file_path, "w") as json_file:
                json_file.write(json_str)
            print("%s file send %s %s" % (hdc_str, cfg_file_path, "/system/etc/init/"))
            coverage_command("%s file send %s %s" % (hdc_str, cfg_file_path, "/system/etc/init/"))
    else:
        print("faultloggerd.cfg file not exists.")

    return


def modify_foundation_xml(serv, config_path, origin_xml) -> str:
    """
    修改foundation.xml文件，删去拆分的进程相关
    :param serv: 拆分进程
    :param config_path: 配置文件路径
    :param origin_xml: 原foundation.xml
    :return: 修改后foundation.xml路径
    """
    lib_list = FoundationServer.lib_dict

    tree = ET.parse(origin_xml)
    root = tree.getroot()
    loadlibs = root.find("loadlibs")

    for lib in lib_list:
        for sa in root.findall('systemability'):
            if lib in sa.find('libpath').text:
                root.remove(sa)
        for ll in loadlibs.findall('libpath'):
            if lib in ll.text:
                loadlibs.remove(ll)

    tree.write(os.path.join(config_path, 'foundation.xml'), encoding='utf-8', xml_declaration=True)
    return os.path.join(config_path, 'foundation.xml')


def create_service_xml(serv, config_path, origin_xml) -> str:
    """
    创建进程xml
    :param serv: 进程名
    :param config_path:配置文件所在目录
    :param origin_xml: 原foundation.xml
    :return: xml文件路径
    """
    lib_list = FoundationServer.lib_dict

    tree = ET.parse(origin_xml)
    root = tree.getroot()
    loadlibs = root.find("loadlibs")

    for lib in lib_list:
        for sa in root.findall('systemability'):
            if lib not in sa.find('libpath').text:
                root.remove(sa)
        for lp in loadlibs.findall('libpath'):
            if lib not in lp.text:
                loadlibs.remove(lp)

    tree.write(os.path.join(config_path, '{}.xml'.format(serv)), encoding='utf-8', xml_declaration=True)
    return os.path.join(config_path, '{}.xml'.format(serv))


def create_service_cfg(serv, config_path, origin_cfg) -> str:
    """
    创建进程cfg文件
    :param serv: 进程名
    :param config_path:配置文件所在目录
    :param origin_cfg: 原foundation.cfg
    :return: cfg文件路径
    """
    with open(origin_cfg, "r") as jf:
        json_obj = json.load(jf)
        json_obj["jobs"][0]["name"] = "services:{}".format("wms")

        json_obj["services"][0]["name"] = "services:{}".format("wms")

        path_list = json_obj["services"][0]["path"]
        path_list.remove("/system/profile/foundation.xml")
        path_list.append("/system/profile/{}.xml".format(serv))
        json_obj["services"][0]["path"] = path_list

        json_obj["services"][0]["jobs"]["on-start"] = "services:{}".format("wms")

    cfg_path = os.path.join(config_path, "{}.cfg".format(serv))
    with open(cfg_path, 'w') as r:
        json.dump(json_obj, r, indent=4)
    return cfg_path


def remove_configs(config_path):
    """
    清理配置文件目录下的xml和cfg文件
    :param config_path: 配置文件目录
    :return:
    """
    logger("Clear xml and cfg...", "INFO")

    file_list = os.listdir(config_path)
    for file in file_list:
        if file.endswith(".xml"):
            os.remove(os.path.join(config_path, file))
            logger("remove {}".format(os.path.join(config_path, file)), "INFO")
        if file.endswith(".cfg"):
            os.remove(os.path.join(config_path, file))
            logger("remove {}".format(os.path.join(config_path, file)), "INFO")


def split_foundation_services(developer_path, system_info_dict, home_path, hdc_dict):
    """
    foundation.xml、XXX.xml文件推送到 /system/profile
    XXX.cfg文件推送到/etc/init/
    reboot设备，可以将服务从foundation中拆分出来，成为一个独立服务进程
    """
    config_path = os.path.join(developer_path, "localCoverage", "resident_service")
    remove_configs(config_path)

    device_ip = hdc_dict["device_ip"]
    hdc_port = hdc_dict["device_port"]
    device_sn = hdc_dict["device_sn_str"]

    hdc_command(device_ip, hdc_port, device_sn, "file recv /system/profile/foundation.xml {}".format(config_path))
    hdc_command(device_ip, hdc_port, device_sn, "file recv /etc/init/foundation.cfg {}".format(config_path))

    if os.path.exists(os.path.join(config_path, "foundation.xml")):
        origin_xml = os.path.join(config_path, "foundation_origin.xml")
        os.rename(os.path.join(config_path, "foundation.xml"), origin_xml)
    else:
        logger("{} not exist, Cannot modify.".format(os.path.join(config_path, "foundation.xml")), "ERROR")
        return

    if os.path.exists(os.path.join(config_path, "foundation.cfg")):
        origin_cfg = os.path.join(config_path, "foundation_origin.cfg")
        os.rename(os.path.join(config_path, "foundation.cfg"), origin_cfg)
    else:
        logger("{} not exist, Cannot modify.".format(os.path.join(config_path, "foundation.cfg")), "ERROR")
        return

    foundation_process_list = FoundationServer.lib_dict.keys()

    # 推送配置文件
    for _, value_list in system_info_dict.items():
        for process_str in value_list:
            if process_str in foundation_process_list:
                foundation_xml = modify_foundation_xml(process_str, config_path, origin_xml)
                service_xml = create_service_xml(process_str, config_path, origin_xml)
                service_cfg = create_service_cfg(process_str, config_path, origin_cfg)

                hdc_command(device_ip, hdc_port, device_sn, "shell rm -rf {}".format(home_path))
                hdc_command(device_ip, hdc_port, device_sn, "file send {} /system/profile/".format(foundation_xml))
                hdc_command(device_ip, hdc_port, device_sn, "file send {} /system/profile/".format(service_xml))
                hdc_command(device_ip, hdc_port, device_sn, "file send {} /etc/init/".format(service_cfg))

    return


def modify_cfg_xml_file(developer_path, device_ip, device_sn_list,
                        system_info_dict, home_path, device_port):
    if device_ip and len(device_sn_list) >= 1:
        for device_sn_str in device_sn_list:
            hdc_str = "hdc -s %s:%s -t %s" % (device_ip, device_port, device_sn_str)
            hdc_dict = {"device_ip": device_ip, "device_port": device_port, "device_sn_str": device_sn_str}
            modify_init_file(developer_path, hdc_str)
            modify_faultloggerd_file(
                developer_path, hdc_str)
            # 推送服务对应的xml文件
            split_foundation_services(developer_path, system_info_dict, home_path, hdc_dict)
            logger("{} shell reboot".format(hdc_str), "INFO")
            coverage_command("%s shell reboot > /dev/null 2>&1" % hdc_str)
            while True:
                after_sn_list = get_sn_list("hdc -s %s:%s list targets" % (device_ip, device_port))
                time.sleep(10)
                if device_sn_str in after_sn_list:
                    break
            coverage_command("%s shell getenforce" % hdc_str)
    else:
        logger("user_config.xml device ip not config", "ERROR")


if __name__ == '__main__':
    command_args = sys.argv[1]
    command_str = command_args.split("command_str=")[1].replace(",", " ")
    current_path = os.getcwd()
    _init_sys_config()
    from localCoverage.utils import coverage_command, \
        logger, hdc_command, FoundationServer

    root_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_test_path = os.path.join(root_path, "test/testfwk/developer_test")
    home_paths = '/'.join(root_path.split("/")[:3])

    # 获取user_config中的device ip
    ip, port, sn = get_config_ip(os.path.join(developer_test_path, "config/user_config.xml"))
    if not port:
        port = "8710"
    sn_list = []
    if sn:
        sn_list.extend(sn.replace(" ", "").split(";"))
    else:
        sn_list = get_sn_list("hdc -s %s:%s list targets" % (ip, port))

    # 获取子系统部件与服务的关系
    system_dict, _, _ = get_server_dict(command_str)

    # 修改设备init.cfg, faultloggerd.cfg等文件
    modify_cfg_xml_file(developer_test_path, ip, sn_list,
                        system_dict, home_paths, port)
