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
import xml.etree.ElementTree as ET


def get_config_ip(filepath):
    ip_config = ""
    try:
        data_dic = {}
        if os.path.exists(filepath):
            tree = ET.parse(filepath)
            root = tree.getroot()
            for node in root.findall("environment/device"):
                if node.attrib["type"] != "usb-hdc":
                    continue
                for sub in node:
                    data_dic[sub.tag] = sub.text if sub.text else ""
                ip_config = data_dic.get("ip", "")
    except ET.ParseError as xml_exception:
        print("occurs exception:{}".format(xml_exception.agrs))

    return ip_config


def get_sn_list(command):
    device_sn_list = []
    # 执行查询设备sn号命令并获取执行结果
    proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    strout = proc.stdout.read()
    if isinstance(strout, bytes):
        strout = strout.decode("utf-8", "ignore")
    for line in strout.split("\n"):
        line = line.strip().replace('\t', ' ')
        if line != "":
            device_sn_list.append(line)

    return device_sn_list


def get_all_part_service():
    current_path = os.getcwd()
    developer_path = current_path.split("/test/testfwk/developer_test")[0]
    system_part_service_path = os.path.join(
        developer_path, "developer_test/localCoverage/resident_service/system_part_service.json")
    if os.path.exists(system_part_service_path):
        with open(system_part_service_path, "r") as system_text:
            system_text_json = json.load(system_text)
            system_info_dict = system_text_json["system_info_dict"]
            services_component_dict = system_text_json["service_component_dict"]
            component_gcda_dict = system_text_json["component_gcda_dict"]
            return system_info_dict, services_component_dict, component_gcda_dict
    else:
        print("%s not exists.", system_part_service_path)


def get_system_dict_to_server_name(server_name: str, system_info_dict):
    for system, server_list in system_info_dict.ites():
        if server_name in server_list:
            system_info_dict_after = {
                system: [server_name]
            }
            return system_info_dict_after


def get_server_dict(command):
    system_info_dict, services_component_dict, component_gcda_dict = get_all_part_service()
    system_info_dict_after = {}
    services_component_dict_after = {}
    component_gcda_dict_after = {}
    server_name = None
    if " -ts " in command:
        _, testsuite = command.split(" -ts ")
        if testsuite in services_component_dict.get("dinput"):
            services_component_dict_after = {
                "dinput": [testsuite]
            }
            server_name = "dinput"
        elif testsuite in services_component_dict.get("softbus_server"):
            services_component_dict_after = {
                "softbus_server": [testsuite]
            }
            server_name = "softbus_server"
        if server_name:
            system_info_dict_after = get_system_dict_to_server_name(server_name, system_info_dict)
            component_gcda_dict_after = {
                server_name: component_gcda_dict.get(server_name)
            }
    elif " -tp " in command:
        component_name = command.split(" -tp ")[-1].split(" ")[0]
        for server, component_list in services_component_dict.items():
            if component_name in component_list:
                if server in ["dinput", "softbus_server"]:
                    break
                services_component_dict_after = {
                    server: [component_name]
                }
                server_name = server
                break
            if server_name:
                system_info_dict_after = get_system_dict_to_server_name(server_name, system_info_dict)
                component_gcda_dict_after = {
                    server_name: component_gcda_dict.get(server_name)
                }
    elif " ss " in command:
        system_name = command.split(" -ss ")[-1].split(" ")[0]
        server_list = system_info_dict.get(system_name)
        system_info_dict_after = {
            system_name: server_list
        }
        for server_name in server_list:
            services_component_dict_after.update({
                server_name: services_component_dict.get(server_name)
            })
            component_gcda_dict_after.update({
                server_name: component_gcda_dict.get(server_name)
            })
    return system_info_dict_after, services_component_dict_after, component_gcda_dict_after
