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


def _init_sys_config():
    sys.localcoverage_path = os.path.join(current_path, "..")
    sys.path.insert(0, sys.localcoverage_path)


def find_part_so_dest_path(test_part: str) -> str:
    parts_info_json = os.path.join(out_path, "build_configs", "parts_info", "parts_path_info.json")
    if not os.path.exists(parts_info_json):
        logger("{} not exists.".format(parts_info_json), "ERROR")
        return ""
    json_obj = json_parse(parts_info_json)
    if json_obj:
        if test_part not in json_obj:
            logger("{} part not exist in {}.".format(test_part, parts_info_json), "ERROR")
            return ""
        path = os.path.join(out_path, "obj", json_obj[test_part])
        return path

    return ""


def find_subsystem_so_dest_path(sub_system: str) -> list:
    subsystem_config_json = os.path.join(out_path, "build_configs", "subsystem_info", "subsystem_build_config.json")
    if not os.path.exists(subsystem_config_json):
        logger("{} not exists.".format(subsystem_config_json), "ERROR")
        return []

    json_obj = json_parse(subsystem_config_json)
    if json_obj:
        if sub_system not in json_obj["subsystem"]:
            logger("{} not exist in subsystem_build_config.json".format(sub_system), "ERROR")
            return []
        if "path" not in json_obj["subsystem"][sub_system]:
            logger("{} no path in subsystem_build_config.json".format(sub_system), "ERROR")
            return []

        path = list()
        for s in json_obj["subsystem"][sub_system]["path"]:
            path.append(os.path.join(out_path, "obj", s))
        return path

    return []


def find_so_source_dest(path: str) -> dict:
    so_dict = dict()
    json_list = list()
    if not path:
        return {}

    json_list = tree_find_file_endswith(path, "_module_info.json", json_list)

    for j in json_list:
        json_obj = json_parse(j)
        if "source" not in json_obj or "dest" not in json_obj:
            logger("{} json file error.".format(j), "ERROR")
            return {}

        if json_obj["source"].endswith(".so"):
            so_dict[json_obj["source"]] = json_obj["dest"]

    return so_dict


def push_coverage_so(so_dict: dict):
    if not so_dict:
        logger("No coverage so to push.", "INFO")
        return
    for device in device_sn_list:
        cmd = "shell mount -o rw,remount /"
        hdc_command(device_ip, device_port, device, cmd)
        for source_path, dest_paths in so_dict.items():
            full_source = os.path.join(out_path, source_path)
            if not os.path.exists(full_source):
                logger("{} not exist.".format(full_source), "ERROR")
                continue
            for dest_path in dest_paths:
                full_dest = os.path.join("/", dest_path)
                command = "file send {} {}".format(full_source, full_dest)
                hdc_command(device_ip, device_port, device, command)


if __name__ == "__main__":
    current_path = os.path.abspath(os.path.dirname(__name__))

    _init_sys_config()
    from localCoverage.resident_service.public_method import get_config_ip, get_sn_list
    from localCoverage.utils import get_product_name, hdc_command, tree_find_file_endswith, json_parse, logger

    root_path = current_path.split("/test/testfwk/developer_test")[0]
    out_path = os.path.join(root_path, "out", get_product_name(root_path))
    developer_path = os.path.join(root_path, "test", "testfwk", "developer_test")

    device_ip, device_port, device_sn_strs = get_config_ip(os.path.join(developer_path, "config", "user_config.xml"))
    if not device_port:
        device_port = "8710"
    if not device_sn_strs:
        device_sn_list = get_sn_list("hdc -s {}:{} list targets".format(device_ip, device_port))
    else:
        device_sn_list = device_sn_strs.split(";")

    subsystem_list, testpart_list = [], []
    param = sys.argv[1]
    if param.split("=")[0] == "testpart":
        testpart_list = param.split("=")[1].lstrip("[").rstrip("]").split(",")
    else:
        subsystem_list = param.split("=")[1].lstrip("[").rstrip("]").split(",")

    if testpart_list and subsystem_list:
        logger("Both parts and subsystem exist, not push coverage so.", "INFO")
        exit(0)
    if len(subsystem_list) == 1:
        subsystem = subsystem_list[0]
        json_path_list = find_subsystem_so_dest_path(subsystem)
        for json_path in json_path_list:
            source_dest_dict = find_so_source_dest(json_path)
            push_coverage_so(source_dest_dict)
    elif len(subsystem_list) == 0:
        for testpart in testpart_list:
            json_path_list = find_part_so_dest_path(testpart)
            source_dest_dict = find_so_source_dest(json_path_list)
            push_coverage_so(source_dest_dict)
    else:
        logger("More than one subsystem, no need to push coverage so.", "INFO")
        exit(0)
