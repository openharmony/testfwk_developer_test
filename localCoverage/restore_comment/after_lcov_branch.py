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
import stat

FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL
MODES = stat.S_IWUSR | stat.S_IRUSR


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
    return file_list


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


def recover_source_file(cpp_list, keys):
    if not cpp_list:
        print("no any .cpp file here")
        return

    for path in cpp_list:
        if not os.path.exists(path):
            return
        for key in keys:
            with open(path, "r") as read_fp:
                code_lines = read_fp.readlines()
            # with open(f"{path.split('.')[0]}_bk.html", "w") as write_fp:
            if os.path.exists(f"{path.split('.')[0]}_bk.html"):
                os.remove(f"{path.split('.')[0]}_bk.html")
            with os.fdopen(os.open(f"{path.split('.')[0]}_bk.html", FLAGS, MODES), 'w') as write_fp:
                for line in code_lines:
                    if key in line:
                        write_fp.write(line.strip("\n").strip("\n\r").replace(" //LCOV_EXCL_BR_LINE", ""))
                        write_fp.write("\n")
                    else:
                        write_fp.write(line)

            os.remove(path)
            subprocess.Popen("mv %s %s" % (f"{path.split('.')[0]}_bk.html", path),
                             shell=True).communicate()


if __name__ == '__main__':
    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    html_path = os.path.join(
        root_path,
        "test/testfwk/developer_test/localCoverage/codeCoverage/results/coverage/reports/cxx/html")
    cpp_arr_list = get_file_list_by_postfix(html_path, ".html")
    recover_source_file(cpp_arr_list, keys=[" //LCOV_EXCL_BR_LINE"])
