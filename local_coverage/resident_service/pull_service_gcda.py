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

from public_method import get_server_dict, get_config_ip_info, get_sn_list


def _init_sys_config():
    sys.localcoverage_path = os.path.join(current_path, "..")
    sys.path.insert(0, sys.localcoverage_path)


def restore_config(device_ip, device_port, device_sn, cfg_path):
    """
    恢复设备内配置文件
    :param device_ip:
    :param device_sn:
    :param cfg_path:
    :param device_port:
    :return:
    """
    remount_cmd = "shell mount -o rw,remount /"
    hdc_command(device_ip, device_port, device_sn, remount_cmd)
    remount_cmd_mount = "target mount"
    hdc_command(device_ip, device_port, device_sn, remount_cmd_mount)
    origin_foundation = os.path.join(cfg_path, "foundation_origin.json")
    restore_foundation_cmd = "file send {} /system/profile/foundation.json".format(origin_foundation)
    hdc_command(device_ip, device_port, device_sn, restore_foundation_cmd)
    serv_list = FoundationServer.lib_dict
    for serv in serv_list:
        rm_xml_cmd = "shell rm /system/profile/{}.json".format(serv)
        hdc_command(device_ip, device_port, device_sn, rm_xml_cmd)
        rm_cfg_cmd = "shell rm /etc/init/{}.cfg".format(serv)
        hdc_command(device_ip, device_port, device_sn, rm_cfg_cmd)


def attach_pid(device_ip, device_sn, process_str, component_gcda_dict, developer_path,
               resident_service_path, services_str, root, device_port):
    """
    1. 在设备里ps -ef | grep SERVICE 获取进程号
    2. kill - '信号' pid
    """
    hdc_str = "hdc -s %s:%s -t %s" % (device_ip, device_port, device_sn)
    print("%s shell chmod 777 /data/gcov -R" % hdc_str)
    coverage_command("%s shell chmod 777 /data/gcov -R" % hdc_str)
    coverage_command("%s shell mount -o rw,remount /" % hdc_str)
    coverage_command("%s target mount" % hdc_str)
    local_sh_path = os.path.join(resident_service_path, "resources", "gcov_flush.sh")
    coverage_command("dos2unix %s" % local_sh_path)
    print("%s file send %s %s" % (hdc_str, local_sh_path, "/data/"))
    coverage_command("%s file send %s %s" % (hdc_str, local_sh_path, "/data/"))
    coverage_command("%s shell chmod 777 /data/gcov_flush.sh" % hdc_str)
    print("%s shell sh /data/gcov_flush.sh %s" % (hdc_str, services_str))
    coverage_command("%s shell sh /data/gcov_flush.sh %s" % (hdc_str, services_str))

    # 拉取gcda文件
    get_gcda_file(device_ip, device_sn, process_str, component_gcda_dict,
                  developer_path, services_str, root, device_port)


def get_gcda_file(device_ip, device_sn, process_str, component_gcda_dict,
                  developertest_path, services_str, roots_path, device_port):
    hdc_str = "hdc -s %s:%s -t %s" % (device_ip, device_port, device_sn)
    home_path = '/'.join(roots_path.split("/")[:3])
    gcda_path = f"/data/gcov{roots_path}"

    component_gcda_paths = component_gcda_dict.get(process_str) if component_gcda_dict.get(process_str) else []
    for component_gcda_path in component_gcda_paths:
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
                     component_gcda_dict, developer_path, resident_service_path, root, port_nu):

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
                           developer_path, resident_service_path, services_str, root, port_nu)
    return


if __name__ == '__main__':
    command_args = sys.argv[1]
    command_str = command_args.split("command_str=")[1].replace(",", " ")
    current_path = os.getcwd()
    _init_sys_config()
    from local_coverage.utils import get_product_name, coverage_command, hdc_command, FoundationServer

    root_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_test_path = os.path.join(root_path, "test/testfwk/developer_test")
    service_path = os.path.join(
        developer_test_path, "local_coverage/resident_service")
    config_path = os.path.join(service_path, "config")
    product_name = get_product_name(root_path)

    # 获取子系统部件与服务的关系
    system_dict, services_dict, component_dict = get_server_dict(command_str)

    ip_list, port_list, sn_list = get_config_ip_info(os.path.join(developer_test_path, "config/user_config.xml"))
    if not port_list:
        port_list = ["8710"] * len(ip_list)
    # sn_list = []
    # if sn:
    #     sn_list.extend(sn.replace(" ", "").split(";"))
    # else:
    #     sn_list = get_sn_list("hdc -s %s:%s list targets" % (ip, port))
    if not sn_list:
        for i in range(list(ip_list)):
            ip = ip_list[i]
            port = port_list[i]
            sn_list.extend(get_sn_list("hdc -s %s:%s list targets" % (ip, port)))

    if ip and len(sn_list) >= 1 and len(system_dict.keys()) >= 1:
        for sn_str in sn_list:
            get_service_list(ip, sn_str, system_dict, services_dict, component_dict,
                             developer_test_path, service_path, root_path, port)
            restore_config(ip, port, sn_str, config_path)
