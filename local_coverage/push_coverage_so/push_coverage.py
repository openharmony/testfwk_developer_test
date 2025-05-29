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


def get_subsystem_name(partname: str) -> str:
    """
    获取部件所属的子系统名
    :param partname:
    :return: 子系统名
    """
    parts_info_json = os.path.join(out_path, "build_configs", "parts_info", "part_subsystem.json")
    if not os.path.exists(parts_info_json):
        logger("{} not exists.".format(parts_info_json), "ERROR")
        return ""
    json_obj = json_parse(parts_info_json)
    if json_obj:
        if partname not in json_obj:
            logger("{} part not exist in {}".format(partname, parts_info_json), "ERROR")
            return ""
        return json_obj[partname]
    return ""


def find_part_so_dest_path(test_part: str) -> str:
    """
    获取指定部件的obj目录
    :param test_part:部件名称
    :return:部件obj目录
    """
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
    """
    获取指定子系统的obj目录
    :param sub_system:子系统名
    :return: 子系统下所有部件obj目录的列表
    """
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


def find_so_source_dest(path: str, subsystem_name: str) -> dict:
    """
    获取so和设备里所在目录的对应关系
    :param path: 子系统obj目录
    :return: so和设备里所在目录的对应关系dict
    """
    so_dict = dict()
    json_list = list()
    if not path:
        return {}

    json_list = tree_find_file_endswith(path, "_module_info.json", json_list)

    for j in json_list:
        json_obj = json_parse(j)
        if "subsystem_name" not in json_obj:
            continue
        if json_obj["subsystem_name"] != subsystem_name:
            continue
        if "source" not in json_obj or "dest" not in json_obj:
            logger("{} json file error.".format(j), "ERROR")
            return {}

        source_path = os.path.join(out_path, json_obj["source"])
        if source_path.endswith(".so"):
            so_dict[source_path] = [tmp for tmp in json_obj["dest"] if (
                    tmp.startswith("system/") or tmp.startswith("vendor/"))]

    return so_dict


def push_coverage_so(so_dict: dict):
    """
    推送so到设备
    :param so_dict: so和设备里目录对应dict
    :return:
    """
    if not so_dict:
        logger("No coverage so to push.", "INFO")
        return
    for device in device_sn_list:
        cmd = "shell mount -o rw,remount /"
        hdc_command(device_ip, device_port, device, cmd)
        cmd_mount = "target mount"
        hdc_command(device_ip, device_port, device, cmd_mount)
        for source_path, dest_paths in so_dict.items():
            if not os.path.exists(source_path):
                logger("{} not exist.".format(source_path), "ERROR")
                continue
            for dest_path in dest_paths:
                full_dest = os.path.join("/", dest_path)
                command = "file send {} {}".format(source_path, full_dest)
                hdc_command(device_ip, device_port, device, command)


if __name__ == "__main__":
    current_path = os.path.abspath(os.path.dirname(__name__))

    _init_sys_config()
    from local_coverage.resident_service.public_method import get_config_ip_info, get_sn_list
    from local_coverage.utils import get_product_name, hdc_command, tree_find_file_endswith,\
                                    json_parse, logger, is_elffile

    root_path = current_path.split("/test/testfwk/developer_test")[0]
    out_path = os.path.join(root_path, "out", get_product_name(root_path))
    developer_path = os.path.join(root_path, "test", "testfwk", "developer_test")

    # 获取远程映射相关hdc参数
    device_ip, device_port, device_sn_strs = get_config_ip_info(os.path.join(developer_path, "config", "user_config.xml"))
    if not device_port:
        device_port = "8710"
    if not device_sn_strs:
        device_sn_list = get_sn_list("hdc -s {}:{} list targets".format(device_ip, device_port))
    else:
        device_sn_list = device_sn_strs.split(";")

    subsystem_list, testpart_list = [], []
    testtype = sys.argv[1]
    param_list = sys.argv[2:]

    # 入参为ss子系统和tp部件分别处理
    if testtype == "testpart":
        for param in param_list:
            testpart_list.append(param.strip("[").strip("]").strip(","))
            for testpart in testpart_list:
                json_path_list = find_part_so_dest_path(testpart)
                subsystem = get_subsystem_name(testpart)
                source_dest_dict = find_so_source_dest(json_path_list, subsystem)
                push_coverage_so(source_dest_dict)
    else:
        for param in param_list:
            subsystem_list.append(param.strip("[").strip("]").strip(","))

            if len(subsystem_list) == 1:
                subsystem = subsystem_list[0]
                json_path_list = find_subsystem_so_dest_path(subsystem)
                for json_path in json_path_list:
                    source_dest_dict = find_so_source_dest(json_path, subsystem)
                    push_coverage_so(source_dest_dict)
