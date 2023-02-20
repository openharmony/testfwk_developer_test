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
import sys


from public_method import get_server_dict, get_config_ip, get_sn_list


def attach_pid(device_ip, device_sn, process_str, component_gcda_dict,
               developer_path, resident_service_path, services_str):
    """
    1. 在设备里ps -ef | grep SERVICE 获取进程号
    2. kill - '信号' pid
    """
    hdc_str = "hdc -s %s:8710 -t %s" % (device_ip, device_sn)
    print(hdc_str + "shell chmod 777 /data/gcov -R")
    subprocess.Popen(hdc_str + "shell chmod 777 /data/gcov -R", shell=True).communicate()
    subprocess.Popen(hdc_str + "shell mount -o rw,remount /", shell=True).communicate()
    local_sh_path = os.path.join(resident_service_path, "resources", "gcov_flush.sh")
    print(hdc_str + "file send %s %s" % (local_sh_path, "/data/"))
    subprocess.Popen(hdc_str + "file send %s %s" % (local_sh_path, "/data/"),
                     shell=True).communicate()
    subprocess.Popen(hdc_str + "shell chmod 777 /data/gcov_flush.sh",
                     shell=True).communicate()
    print(hdc_str + "shell sh /data/gcov_flush.sh %s" % services_str)
    subprocess.Popen(hdc_str + "shell sh /data/gcov_flush.sh %s" % services_str,
                     shell=True).communicate()

    # 拉取gcda文件
    get_gcda_file(device_ip, device_sn, process_str, component_gcda_dict,
                  developer_path, services_str)


def get_gcda_file(device_ip, device_sn, process_str, component_gcda_dict,
                  developertest_path, services_str):
    hdc_str = "hdc -s %s:8710 -t %s" % (device_ip, device_sn)
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    home_path = '/'.join(root_path.split("/")[:3])
    gcda_path = "/data/gcov" + root_path

    for component_gcda_path in component_gcda_dict[process_str]:
        gcov_root = os.path.join(gcda_path, component_gcda_path)
        gcda_file_name = os.path.basename(gcov_root)
        gcda_file_path = os.path.dirname(gcov_root)
        print(hdc_str + "shell 'cd %s; tar -czf %s.tar.gz %s'" % (
            gcda_file_path, gcda_file_name, gcda_file_name))
        subprocess.Popen(hdc_str + "shell 'cd %s; tar -czf %s.tar.gz %s'" % (
            gcda_file_path, gcda_file_name, gcda_file_name), shell=True).communicate()

        obj_gcda_path = component_gcda_path.split("baltimore")[-1].strip("/")
        local_gcda_path = os.path.dirname(
            os.path.join(developertest_path, "reports/coverage/data/cxx",
                         services_str + "_service", obj_gcda_path))

        if not os.path.exists(local_gcda_path):
            os.makedirs(local_gcda_path)
        tar_path = os.path.join(gcda_file_path, "%s.tar.gz" % gcda_file_name)
        print(hdc_str + "file recv %s %s" % (tar_path, local_gcda_path))
        subprocess.Popen(hdc_str + "file recv %s %s" % (
            tar_path, local_gcda_path), shell=True).communicate()

        local_tar = os.path.join(local_gcda_path, "%s.tar.gz" % gcda_file_name)
        print("tar -zxf %s -C %s > /dev/null 2>&1" % (local_tar, local_gcda_path))
        subprocess.Popen("tar -zxf %s -C %s > /dev/null 2>&1" % (
            local_tar, local_gcda_path), shell=True).communicate()
        subprocess.Popen("rm -rf %s" % local_tar, shell=True).communicate()
        print(hdc_str + "shell rm -fr %s" % ("/data/gcov" + home_path))
        subprocess.Popen(hdc_str + "shell rm -fr %s" % ("/data/gcov" + home_path),
                         shell=True).communicate()


def get_service_list(device_ip, device_sn, system_info_dict, services_component_dict,
                     component_gcda_dict, developer_path, resident_service_path):

    service_list = []
    for key, value_list in system_info_dict.items():
        for process_str in value_list:
            if process_str in services_component_dict.keys():
                service_list.append(process_str)
            else:
                return
    if len(service_list) > 0:
        for process_str in service_list:
            services_list = process_str.split("|")
            for services_str in services_list:
                attach_pid(device_ip, device_sn, process_str, component_gcda_dict,
                           developer_path, resident_service_path, services_str)
    return


if __name__ == '__main__':
    command_args = sys.argv[1]
    command_str = command_args.split("command_str=")[1].replace(",", " ")
    current_path = os.getcwd()
    developer_path = os.path.join(
        current_path.split("/developer_test/src")[0], "developer_test")
    resident_service_path = os.path.join(
        developer_path, "localCoverage/resident_service")
    config_path = os.path.join(resident_service_path, "config")

    # 获取子系统部件与服务的关系
    system_info_dict, services_component_dict, component_gcda_dict = get_server_dict(command_str)

    device_ip = get_config_ip(os.path.join(developer_path, "config/user_config.xml"))
    device_sn_list = get_sn_list("hdc -s %s" % device_ip + ":8710 list targets")

    if device_ip and len(device_sn_list) >= 1 and len(system_info_dict.keys()) >= 1:
        for device_sn_str in device_sn_list:
            get_service_list(device_ip, device_sn_str, system_info_dict, services_component_dict,
                             component_gcda_dict, developer_path, resident_service_path)

