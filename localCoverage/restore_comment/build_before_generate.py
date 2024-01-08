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
import stat

FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL
MODES = stat.S_IWUSR | stat.S_IRUSR


def get_source_file_list(path):
    """
    获取path路径下源文件路径列表
    """
    file_path_list = []
    file_path_list_append = file_path_list.append
    for root, dirs, files in os.walk(path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            _, suffix = os.path.splitext(file_name)
            if suffix in [".c", ".cpp"]:
                file_path_list_append(file_path)
    return file_path_list


def rewrite_source_file(source_path_list: list):
    """
    源文件加“//LCOV_EXCL_BR_LINE”
    """
    keys = ["if", "while", "switch", "case", "for", "try", "catch"]
    if not source_path_list:
        print("no any source file here")
        return

    print("[**********  Start Rewrite Source File **********]")
    for path in source_path_list:
        if not os.path.exists(path) or "test" in path:
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as read_fp:
            code_lines = read_fp.readlines()
        source_dir, suffix_name = os.path.splitext(path)
        # with open(f"{source_dir}_bk.{suffix_name}", "w",
        #           encoding="utf-8", errors="ignore") as write_fp:
        if os.path.exists(f"{source_dir}_bk.{suffix_name}"):
            os.remove(f"{source_dir}_bk.{suffix_name}")
        with os.fdopen(os.open(f"{source_dir}_bk.{suffix_name}", FLAGS, MODES), 'w') as write_fp:
            for line in code_lines:
                sign_number = 0
                for key in keys:
                    sign_number += 1
                    if key in line and line.strip().startswith(key):
                        write_fp.write(line)
                        break
                    elif " //LCOV_EXCL_BR_LINE" not in line and not line.strip().endswith("\\") \
                            and sign_number == len(keys):
                        write_fp.write(line.strip("\n").strip("\n\r") + " //LCOV_EXCL_BR_LINE")
                        write_fp.write("\n")
                        break
                    elif sign_number == len(keys):
                        write_fp.write(line)
                        break

            os.remove(path)
            subprocess.Popen("mv %s %s" % (f"{source_dir}_bk.{suffix_name}", path),
                             shell=True).communicate()
    print("[**********  End Rewrite Source File **********]")


def add_lcov(subsystem_config_path):
    try:
        with open(subsystem_config_path, "r", encoding="utf-8", errors="ignore") as fp:
            data_dict = json.load(fp)
        for key, value in data_dict.items():
            if "path" in value.keys():
                for path_str in value["path"]:
                    file_path = os.path.join(root_path, path_str)
                    primal_path = f"{file_path}_primal"
                    if os.path.exists(file_path):
                        if not os.path.exists(primal_path):
                            subprocess.Popen("cp -r %s %s" % (
                                file_path, primal_path), shell=True).communicate()
                        source_file_path = get_source_file_list(file_path)
                        rewrite_source_file(source_file_path)
                    else:
                        print("The directory does not exist.", file_path)
    except(FileNotFoundError, AttributeError, ValueError, KeyError):
        print("add LCOV_EXCL_BR_LINE Error")


def get_part_config_json(part_list, system_info_path, part_path):
    if os.path.exists(system_info_path):
        new_json_text = {}
        for part in part_list:
            with open(system_info_path, "r") as system_text:
                system_text_json = json.load(system_text)
                if part in system_text_json:
                    new_json_text[part] = system_text_json[part]
                else:
                    print("Error: part not in all_subsystem_config.json")
        new_json = json.dumps(new_json_text, indent=4)
        # with open(part_path, "w") as out_file:
        if os.path.exists(part_path):
            os.remove(part_path)
        with os.fdopen(os.open(part_path, FLAGS, MODES), 'w') as out_file:
            out_file.write(new_json)
    else:
        print("%s not exists.", system_info_path)


if __name__ == '__main__':
    part_name_list = []
    while True:
        print("For example: run -tp partname\n"
              "             run -tp partname1 partname2")

        # 获取用户输入命令
        part_name = input("Please enter your command: ")
        if part_name == "":
            continue
        if " -tp " in part_name:
            part_name_list = part_name.strip().split(" -tp ")[1].split()
            break
        else:
            continue

    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    all_system_info_path = os.path.join(
        root_path,
        "test/testfwk/developer_test/localCoverage/all_subsystem_config.json")
    part_info_path = os.path.join(
        root_path,
        "test/testfwk/developer_test/localCoverage/restore_comment/part_config.json")

    # 获取要修改的源代码的部件信息
    get_part_config_json(part_name_list, all_system_info_path, part_info_path)

    # 执行修改
    add_lcov(part_info_path)
