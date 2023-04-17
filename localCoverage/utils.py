#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
import json
import time
from subprocess import Popen, PIPE, STDOUT


def logger(info, level):
    create_time = "{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print("[{}] [{}] [{}]".format(create_time, level, info))


def json_parse(json_file):
    if os.path.exists(json_file):
        with open(json_file, "r") as jf:
            return json.load(jf)

    logger("{} not exist.".format(json_file), "ERROR")
    return


def get_product_name(root_path):
    ohos_config = os.path.join(root_path, "ohos_config.json")
    json_obj = json_parse(ohos_config)
    if json_obj:
        product_name = json_obj["out_path"].split("out")[1].strip("/")
        return product_name

    logger("{} not exist.".format(ohos_config), "ERROR")
    return


def shell_command(command):
    process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    with process.stdout:
        for line in iter(process.stdout.readline, b""):
            logger(line.decode().strip(), "INFO")
    exitcode = process.wait()
    return process, exitcode


def hdc_command(device_ip, device_port, device_sn, command):
    connect_cmd = "hdc -s {}:{} -t {} ".format(device_ip, device_port, device_sn)
    cmd = connect_cmd + command
    logger(cmd, "INFO")
    _, exitcode = shell_command(cmd)
    return exitcode


def tree_find_file_endswith(path, suffix, file_list=[]):
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path) and full_path.endswith(suffix):
            file_list.append(full_path)
        if os.path.isdir(full_path):
            tree_find_file_endswith(full_path, suffix, file_list)
    return file_list
