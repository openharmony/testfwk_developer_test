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
import sys

from public_method import get_server_dict, get_config_ip, get_sn_list


def _init_sys_config():
    sys.localcoverage_path = os.path.join(current_path, "..")
    sys.path.insert(0, sys.localcoverage_path)


def attach_pid(device_ip, device_sn, process_str, component_gcda_dict, developer_path,
               resident_service_path, services_str, root_path, device_port):
    """
    1. 在设备里ps -ef | grep SERVICE 获取进程号
    2. kill - '信号' pid
    """
    hdc_str = "hdc -s %s:%s -t %s" % (device_ip, device_port, device_sn)
    print("%s shell chmod 777 /data/gcov -R" % hdc_str)
    coverage_command("%s shell chmod 777 /data/gcov -R" % hdc_str)
    coverage_command("%s shell mount -o rw,remount /" % hdc_str)
    local_sh_path = os.path.join(resident_service_path, "resources", "gcov_flush.sh")
    coverage_command("dos2unix %s" % local_sh_path)
    print("%s file send %s %s" % (hdc_str, local_sh_path, "/data/"))
    coverage_command("%s file send %s %s" % (hdc_str, local_sh_path, "/data/"))
    coverage_command("%s shell chmod 777 /data/gcov_flush.sh" % hdc_str)
    print("%s shell sh /data/gcov_flush.sh %s" % (hdc_str, services_str))
    coverage_command("%s shell sh /data/gcov_flush.sh %s" % (hdc_str, services_str))

    # 拉取gcda文件
    get_gcda_file(device_ip, device_sn, process_str, component_gcda_dict,
                  developer_path, services_str, root_path, device_port)


def get_gcda_file(device_ip, device_sn, process_str, component_gcda_dict,
                  developertest_path, services_str, roots_path, device_port):
    hdc_str = "hdc -s %s:%s -t %s" % (device_ip, device_port, device_sn)
    home_path = '/'.join(roots_path.split("/")[:3])
    gcda_path = f"/data/gcov{roots_path}"

    for component_gcda_path in component_gcda_dict[process_str]:
        gcov_root = os.path.join(gcda_path, 'out', product_name, component_gcda_path)
        gcda_file_name = os.path.basename(gcov_root)
        gcda_file_path = os.path.dirname(gcov_root)
        print("%s shell 'cd %s; tar -czf %s.tar.gz %s'" % (
            hdc_str, gcda_file_path, gcda_file_name, gcda_file_name))
        coverage_command("%s shell 'cd %s; tar -czf %s.tar.gz %s'" % (
            hdc_str, gcda_file_path, gcda_file_name, gcda_file_name
        ))

        local_gcda_path = os.path.dirname(
            os.path.join(developertest_path, "reports/coverage/data/cxx",
                         f"{services_str}_service", component_gcda_path))

        if not os.path.exists(local_gcda_path):
            os.makedirs(local_gcda_path)
        tar_path = os.path.join(gcda_file_path, "%s.tar.gz" % gcda_file_name)
        print("%s file recv %s %s" % (hdc_str, tar_path, local_gcda_path))
        coverage_command("%s file recv %s %s" % (
            hdc_str, tar_path, local_gcda_path))

        local_tar = os.path.join(local_gcda_path, "%s.tar.gz" % gcda_file_name)
        print("tar -zxf %s -C %s > /dev/null 2>&1" % (local_tar, local_gcda_path))
        coverage_command("tar -zxf %s -C %s > /dev/null 2>&1" % (
            local_tar, local_gcda_path))
        coverage_command("rm -rf %s" % local_tar)
        print("%s shell rm -fr %s" % (hdc_str, f"/data/gcov{home_path}"))
        coverage_command("%s shell rm -fr %s" % (hdc_str, f"/data/gcov{home_path}"))


def get_service_list(device_ip, device_sn, system_info_dict, services_component_dict,
                     component_gcda_dict, developer_path, resident_service_path, root_path, port):

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
                           developer_path, resident_service_path, services_str, root_path, port)
    return


if __name__ == '__main__':
    command_args = sys.argv[1]
    command_str = command_args.split("command_str=")[1].replace(",", " ")
    current_path = os.getcwd()
    _init_sys_config()
    from localCoverage.utils import get_product_name, coverage_command

    root_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_test_path = os.path.join(root_path, "test/testfwk/developer_test")
    service_path = os.path.join(
        developer_test_path, "localCoverage/resident_service")
    config_path = os.path.join(service_path, "config")
    product_name = get_product_name(root_path)

    # 获取子系统部件与服务的关系
    system_dict, services_dict, component_dict = get_server_dict(command_str)

    ip, port, sn = get_config_ip(os.path.join(developer_test_path, "config/user_config.xml"))
    if not port:
        port = "8710"
    device_sn_list = []
    if sn:
        device_sn_list.extend(sn.replace(" ", "").split(";"))
    else:
        device_sn_list = get_sn_list("hdc -s %s:%s list targets" % (ip, port))

    if ip and len(device_sn_list) >= 1 and len(system_dict.keys()) >= 1:
        for sn_str in device_sn_list:
            get_service_list(ip, sn_str, system_dict, services_dict, component_dict,
                             developer_test_path, service_path, root_path, port)
