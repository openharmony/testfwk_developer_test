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
import json
import os
import subprocess
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
            if suffix in [".c", ".cpp", ".html"]:
                file_path_list_append(file_path)
    return file_path_list


def recover_source_file(source_path_list, keys):
    if not source_path_list:
        print("no any source file here")
        return

    for path in source_path_list:
        source_dir, suffix_name = os.path.splitext(path)
        if not os.path.exists(path):
            continue
        if suffix_name != ".html" and "test" in path:
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as read_fp:
            code_lines = read_fp.readlines()
        if os.path.exists(f"{source_dir}_bk{suffix_name}"):
            os.remove(f"{source_dir}_bk{suffix_name}")
        with os.fdopen(os.open(f"{source_dir}_bk{suffix_name}", FLAGS, MODES), 'w') as write_fp:
            for line in code_lines:
                for key in keys:
                    if key in line:
                        write_fp.write(line.replace(key, ""))
                    else:
                        write_fp.write(line)

            os.remove(path)
            subprocess.Popen("mv %s %s" % (f"{source_dir}_bk{suffix_name}", path),
                             shell=True).communicate()


def recover_cpp_file(part_name_path):
    try:
        if os.path.exists(part_name_path):
            with open(part_name_path, "r", encoding="utf-8", errors="ignore") as fp:
                data_dict = json.load(fp)
            for key, value in data_dict.items():
                if "path" in value.keys():
                    for path_str in value["path"]:
                        file_path = os.path.join(root_path, path_str)
                        if os.path.exists(file_path):
                            cpp_list = get_source_file_list(file_path)
                            recover_source_file(cpp_list, keys=[" //LCOV_EXCL_BR_LINE"])
                        else:
                            print("The directory does not exist.", file_path)
            os.remove(path)
    except(FileNotFoundError, AttributeError, ValueError, KeyError):
            print("recover LCOV_EXCL_BR_LINE Error")


if __name__ == '__main__':
    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    html_path = os.path.join(
        root_path,
        "test/testfwk/developer_test/localCoverage/codeCoverage/results/coverage/reports/cxx/html")
    html_arr_list = get_source_file_list(html_path)

    print("[*************   start Recover Source File *************]")
    recover_source_file(html_arr_list, keys=[" //LCOV_EXCL_BR_LINE"])
    
    part_info_path = os.path.join(
        root_path,
        "test/testfwk/developer_test/localCoverage/restore_comment/part_config.json")
    recover_cpp_file(part_info_path)

    print("[**************   End Recover Source File **************]")
