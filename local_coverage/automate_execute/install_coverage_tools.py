#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2024 Huawei Device Co., Ltd.
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


def sub_command(command):
    proc = subprocess.Popen(command, shell=True)
    try:
        proc.communicate()
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.terminate()


def install_tool(home_path):
    coverage_sh = os.path.join(
        home_path, "test/testfwk/developer_test/local_coverage/automate_execute/coverage.sh")
    sub_command("chmod +x %s" % coverage_sh)
    sub_command(coverage_sh)


def update_lcovrc():
    print("修改/etc/lcovrc文件中：lcov_branch_coverage=0为lcov_branch_coverage=1")
    subprocess.call(["sudo", "echo", ""])
    file_path = "/etc/lcovrc"
    os.chmod(file_path, 0o777)
    with open(file_path, "r", encoding="utf-8") as f:
        txt = f.read()
    txt = txt.replace("lcov_branch_coverage = 0", "lcov_branch_coverage = 1")
    with open(file_path, "w", encoding="utf-8") as f1:
        f1.write(txt)


if __name__ == '__main__':
    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    if os.geteuid() == 0:
        install_tool(root_path)
        update_lcovrc()
    else:
        print("当前用户不是root用户，请在root用户下执行该脚本，因为lcov只能在root下安装，"
              "且需要修改/etc/lcovrc文件，其他用户没有权限修改，会导致分支覆盖率无法生成！")





