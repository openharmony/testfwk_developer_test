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
import subprocess
import time
from subprocess import Popen, PIPE, STDOUT


def logger(content, level):
    """
    日志打印
    :param content:日志内容
    :param level: 日志等级
    :return:
    """
    create_time = "{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print("[{}] [{}] [{}]".format(create_time, level, content))


def json_parse(json_file):
    """
    json文件解析为json对象
    :param json_file:json文件
    :return:json对象
    """
    if os.path.exists(json_file):
        with open(json_file, "r") as jf:
            return json.load(jf)

    logger("{} not exist.".format(json_file), "ERROR")
    return {}


def get_product_name(root_path):
    """
    从ohos_config.json中获取编译产物路径
    :param root_path: ohos_config.json所在的目录
    :return: 编译产量生成的路径
    """
    ohos_config = os.path.join(root_path, "ohos_config.json")
    json_obj = json_parse(ohos_config)
    if json_obj:
        product_name = json_obj["out_path"].split("out")[1].strip("/")
        return product_name

    logger("{} not exist.".format(ohos_config), "ERROR")
    return ""


def shell_command(command_list: list):
    """
    命令行执行命令
    :param command_list:命令参数列表
    :return:
    """
    process = Popen(command_list, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        for line in iter(process.stdout.readline, b""):
            logger(line.decode().strip(), "INFO")
    exitcode = process.wait()
    return process, exitcode


def hdc_command(device_ip, device_port, device_sn, command):
    """
    hdc对远程映射的设备执行命令
    :param device_ip:远程映射的ip
    :param device_port:hdc端口
    :param device_sn:设备sn号
    :param command:
    :return:
    """
    connect_cmd = "hdc -s {}:{} -t {} ".format(device_ip, device_port, device_sn)
    cmd = connect_cmd + command
    cmd_list = cmd.split(" ")
    logger(cmd_list, "INFO")
    _, exitcode = shell_command(cmd_list)
    return exitcode


def coverage_command(command):
    """
    coverage_command
    :param command:
    :return:
    """
    proc = subprocess.Popen(command, shell=True)
    try:
        proc.communicate()
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.terminate()


def tree_find_file_endswith(path, suffix, file_list=None):
    """
    获取目录下所有以指定字符串结尾的文件
    :param path: 需要遍历的目录
    :param suffix: 后缀
    :param file_list:
    :return:
    """
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path) and full_path.endswith(suffix):
            file_list.append(full_path)
        if os.path.isdir(full_path):
            tree_find_file_endswith(full_path, suffix, file_list)
    return file_list
