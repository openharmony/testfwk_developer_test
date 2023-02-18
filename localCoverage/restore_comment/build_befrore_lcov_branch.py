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
import traceback
import json


def get_file_list(find_path, postfix=""):
    file_names = os.listdir(find_path)
    file_list = []
    if len(file_names) > 0:
        for fn in file_names:
            if postfix != "":
                if fn.find(postfix) != -1 and fn[-len(postfix):] == postfix:
                    file_list.append(fn)
            else:
                file_list.append(fn)
    return


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


def get_source_file_list(path):
    """
    获取path路径下源文件路径列表
    """
    file_path_list = []
    file_path_list_append = file_path_list.append
    for root, dirs, files in os.walk(path):
        if files:
            for file_name in files:
                file_path = os.path.join(root, file_name)
                _, suffix = os.path.splitext(file_name)
                if suffix in [".c", ".h", ".cpp"]:
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
        with open(source_dir + f"_bk.{suffix_name}", "w",
                  encoding="utf-8", errors="ignore") as write_fp:

            for line in code_lines:
                for key in keys:
                    if key in line and line.strip().startswith(key):
                        write_fp.write(line)
                    elif " //LCOV_EXCL_BR_LINE" not in line and not line.strip().endswith("\\"):
                        write_fp.write(line.strip("\n").strip("\n\r") + " //LCOV_EXCL_BR_LINE")
                        write_fp.write("\n")
                    else:
                        write_fp.write(line)
                    break

            os.remove(path)
            subprocess.Popen("mv %s %s" % (source_dir + f"_bk.{suffix_name}", path),
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
                    if os.path.exists(file_path):
                        subprocess.Popen("cp -r %s %s" % (
                            file_path, file_path + "_primal"), shell=True).communicate()
                        source_file_path = get_source_file_list(file_path)
                        rewrite_source_file(source_file_path)
                    else:
                        print("The directory does not exist.", file_path)
    except:
        print(traceback.format_exc())


def get_part_config_json(part_name_list, all_system_info_path, part_info_path):
    if os.path.exists(all_system_info_path):
        new_json_text = {}
        for part in part_name_list:
            with open(all_system_info_path, "r") as system_text:
                system_text_json = json.load(system_text)
                if part in system_text_json:
                    new_json_text[part] = system_text_json[part]
                else:
                    print("part not in all_subsystem_config.json")
        new_json = json.dumps(new_json_text, indent=4)
        with open(part_info_path, "w") as out_file:
            out_file.write(new_json)
    else:
        print("%s not exists.", all_system_info_path)


if __name__ == '__main__':
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
        root_path, "test/testfwk/developer_test/localCoverage/all_subsystem_config.json")
    part_info_path = os.path.join(
        root_path, "test/testfwk/developer_test/localCoverage/restore_comment/part_config.json")

    # 获取要修改的源代码的部件信息
    get_part_config_json(part_name_list, all_system_info_path, part_info_path)

    # 执行修改
    add_lcov(part_info_path)
