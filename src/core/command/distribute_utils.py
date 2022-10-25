#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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
import re
from xdevice import platform_logger
from xdevice import EnvironmentManager
from xdevice import ResultReporter
from xdevice import ExecInfo

LOG = platform_logger("distribute_utils")


def make_device_info_file(tmp_path):
    env_manager = EnvironmentManager()
    device_info_file_path = os.path.join(tmp_path,
                                         "device_info_file.txt")
    with open(device_info_file_path, "w") as file_handle:
        if not env_manager.managers:
            return
        if list(env_manager.managers.values())[0].devices_list:
            for device in list(env_manager.managers.values())[0].devices_list:
                get_device_info(device, file_handle)
        else:
            for device in list(env_manager.managers.values())[1].devices_list:
                get_device_info(device, file_handle)


def get_device_info(device, file_handle):
    """
    
    :param device: 
    :param file_handle: 
    :return: 
    """
    if device.test_device_state.value == "ONLINE":
        status = device.label if device.label else 'None'
        LOG.info("%s,%s" % (device.device_sn, status))
        file_handle.write("%s,%s,%s,%s\n" % (
            device.device_sn,
            device.label if device.label else 'None',
            device.host,
            device.port))


def make_reports(result_rootpath, start_time):
    exec_info = ExecInfo()
    exec_info.test_type = "systemtest"
    exec_info.device_name = "ALL"
    exec_info.host_info = ""
    exec_info.test_time = start_time
    exec_info.log_path = os.path.join(result_rootpath, "log")
    exec_info.platform = "ALL"
    exec_info.execute_time = ""

    result_report = ResultReporter()
    result_report.__generate_reports__(report_path=result_rootpath,
                                       task_info=exec_info)
    return True


def check_ditributetest_environment():
    env_manager = EnvironmentManager()
    devices_list = list(env_manager.managers.values())[0].devices_list
    if not devices_list:
        devices_list = list(env_manager.managers.values())[1].devices_list
    evn_status = True
    if len(devices_list) == 0:
        LOG.error("no devices online")
        return False
    device_zero = devices_list[0]
    for device in devices_list:
        if device != device_zero:
            device_ip = query_device_ip(device)
            if device_ip == "":
                evn_status = False
                continue
            if not check_zdn_network(device, device_ip):
                LOG.error("device_%s ping devices_%s failed" % (
                    device_zero.device_sn, device.device_sn))
                evn_status = False
    if not evn_status:
        LOG.error("Environment status = False, test end")
        return False
    LOG.info("Environment status == True")
    return True


def check_zdn_network(device, device_ip=""):
    command = "ping -c 3 " + device_ip
    output = device.execute_shell_command(command)
    if "" == output:
        return False
    packet_lose = re.findall(r"\d+%", output)
    LOG.info("packet lose=%s " % packet_lose[0])
    if "0%" == packet_lose[0]:
        return True
    return False


def query_device_ip(device):
    output = device.execute_shell_command("getprop ohos.boot.hardware")
    if output == "":
        return ""

    isemulator = re.findall(r"read only", output)
    output = device.execute_shell_command("ifconfig")
    if output == "":
        return ""

    if 0 != len(isemulator):
        ipaddress = re.findall(r"\b10\.0\.2\.[0-9]{1,3}\b", output)
    else:
        ip_template = r"\b192\.168\.(?:[0-9]{1,3}\.)[0-9]{1,3}\b"
        ipaddress = re.findall(ip_template, output)
    if len(ipaddress) == 0:
        LOG.error("get device_%s ip fail,please check the net"
                  % device.device_sn)
        return ""
    return ipaddress[0]


def get_test_case(test_case):
    result = {}
    for test in test_case:
        case_dir, file_name = os.path.split(test)
        if case_dir not in result:
            sub_data = {"suits_dir": case_dir}
            result[case_dir] = sub_data
        else:
            sub_data = result.get(case_dir)
        if file_name.endswith("Test"):
            sub_data["major_target_name"] = file_name
        else:
            sub_data["agent_target_name"] = file_name
    return list(result.values())

