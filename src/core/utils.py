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

import sys
import os
import platform
import time
import json
from core.config.config_manager import UserConfigManager, FrameworkConfigManager


def get_filename_extension(file):
    _, fullname = os.path.split(file)
    filename, ext = os.path.splitext(fullname)
    return filename, ext


def create_dir(path):
    full_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)


def get_file_list(find_path, postfix=""):
    file_names = os.listdir(find_path)
    file_list = []
    if len(file_names) > 0:
        for file_name in file_names:
            if postfix != "":
                if file_name.find(postfix) != -1 \
                        and file_name[-len(postfix):] == postfix:
                    file_list.append(file_name)
            else:
                file_list.append(file_name)
    return file_list


# 获取目录下每一个文件，并放到一个列表里
def get_file_list_by_postfix(path, postfix=""):
    file_list = []
    for dirs in os.walk(path):
        files = get_file_list(find_path=dirs[0], postfix=postfix)
        for file_name in files:
            if "" != file_name and -1 == file_name.find(__file__):
                file_name = os.path.join(dirs[0], file_name)
                if os.path.isfile(file_name):
                    file_list.append(file_name)
    return file_list


def get_device_log_file(report_path, serial=None, log_name="device_log"):
    log_path = os.path.join(report_path, "log")
    os.makedirs(log_path, exist_ok=True)

    serial = serial or time.time_ns()
    device_file_name = "{}_{}.log".format(log_name, serial)
    device_log_file = os.path.join(log_path, device_file_name)
    return device_log_file


def get_build_output_path(product_form):
    if sys.source_code_root_path == "":
        return ""

    standard_large_system_list = scan_support_product()
    product_list = FrameworkConfigManager().get_framework_config("productform")
    if product_form in standard_large_system_list:
        device_name = parse_device_name(product_form)
        if device_name is not None:
            build_output_name = device_name
        else:
            return ""
    elif product_form in product_list and (product_form not in standard_large_system_list):
        build_output_name = product_form
    else:
        board_info_list = product_form.split("_")
        if len(board_info_list) < 3:
            return ""

        first_build_output = board_info_list[1] + "_" + board_info_list[2]
        second_build_output = product_form
        build_output_name = os.path.join(first_build_output,
                                         second_build_output)

    build_output_path = os.path.join(sys.source_code_root_path,
                                     "out",
                                     build_output_name)
    # 返回编译结果输出目录：~/OpenHarmony/out/rk3568（以rk3568举例）
    return build_output_path


def scan_support_product():
    # scan standard and large system info
    # 路径注释 product_form_dir = OpenHarmony/productdefine/common/products/
    product_form_dir = os.path.join(sys.source_code_root_path,
                                    "productdefine",
                                    "common",
                                    "products")
    productform_list = []
    if os.path.exists(product_form_dir):
        for product_form_file in os.listdir(product_form_dir):
            if os.path.isdir(os.path.join(product_form_dir,
                                          product_form_file)):
                continue
            product_file = os.path.basename(product_form_file)
            if product_file.endswith(".build") or "parts" in product_file or \
                    "x86_64" in product_file or "32" in product_file:
                continue
            product_name, _ = os.path.splitext(product_file)
            productform_list.append(product_name)
    return productform_list


def get_output_path():
    # 获取输出路径
    ohos_config_path = os.path.join(sys.source_code_root_path, "out", "ohos_config.json")
    with open(ohos_config_path, 'r') as json_file:
        json_info = json.load(json_file)
        out_name = json_info.get("out_path").split("out")[1].strip("/")
    return out_name


def parse_device_name(product_form):
    device_json_file = os.path.join(sys.source_code_root_path,
                                    "productdefine", "common", "products",
                                    "{}.json".format(product_form))
    device_name = ""
    if not os.path.exists(device_json_file):
        return device_name

    with open(device_json_file, 'r') as json_file:
        json_info = json.load(json_file)
    if not json_info:
        return device_name
    device_name = json_info.get('product_device')
    if not device_name:
        device_name = get_output_path()
    return device_name


def parse_product_info(product_form):
    build_prop = os.path.join(sys.source_code_root_path,
                              "out",
                              "preloader",
                              product_form,
                              "build.prop")
    if not os.path.exists(build_prop):
        return {}

    with open(build_prop, 'r') as pro_file:
        properties = {}
        for line in pro_file:
            if line.find('=') > 0:
                strs = line.replace('\n', '').split('=')
                properties[strs[0]] = strs[1]
    return properties


def is_32_bit_test():
    manager = UserConfigManager()
    para_dic = manager.get_user_config("build", "parameter")
    target_cpu = para_dic.get("target_cpu", "")
    if target_cpu == "arm":
        return True
    return False


def get_decode(stream):
    if not isinstance(stream, str) and not isinstance(stream, bytes):
        ret = str(stream)
    else:
        try:
            ret = stream.decode("utf-8", errors="ignore")
        except (ValueError, AttributeError, TypeError):
            ret = str(stream)
    return ret


def get_fuzzer_path(suite_file):
    filename = os.path.basename(suite_file)
    suitename = filename.split("FuzzTest")[0]
    current_dir = os.path.dirname(suite_file)
    while True:
        if os.path.exists(os.path.join(current_dir, "tests")):
            res_path = os.path.join(os.path.join(current_dir, "tests"), "res")
            break
        current_dir = os.path.dirname(current_dir)
    fuzzer_path = os.path.join(res_path, "%s_fuzzer" % suitename.lower())
    return fuzzer_path


def is_lite_product(product_form, code_root_path):
    if code_root_path is None or code_root_path == "":
        return True if len(product_form.split("_")) >= 3 else False
    else:
        product_list = FrameworkConfigManager().get_framework_config("productform")
        if (product_form in scan_support_product() or product_form in product_list) \
                and product_form.find("wifiiot") == -1:
            return False
        else:
            return True
