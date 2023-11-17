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
import sys
import json
import shutil
import subprocess
from shutil import copyfile

from utils import get_product_name, coverage_command


def get_subsystem_config(part_list, developer_path):
    all_system_info_path = os.path.join(
        developer_path, "localCoverage/all_subsystem_config.json"
    )
    system_info_path = os.path.join(
        developer_path, "localCoverage/codeCoverage/subsystem_config.json"
    )
    if os.path.exists(all_system_info_path):
        new_json_text = {}
        for part in part_list:
            with open(all_system_info_path, "r", encoding="utf-8") as system_text:
                system_text_json = json.load(system_text)
                if part in system_text_json:
                    new_json_text[part] = system_text_json[part]
                else:
                    print("Error: part not in all_subsystem_config.json")

        new_json = json.dumps(new_json_text, indent=4)
        with open(system_info_path, "w") as out_file:
            out_file.write(new_json)
    else:
        print("%s not exists.", all_system_info_path)


def copy_coverage(developer_path):
    print("*" * 40, "Start TO Get Code Coverage Report", "*" * 40)
    coverage_path = os.path.join(developer_path, "reports/coverage")
    code_path = os.path.join(
        developer_path, "localCoverage/codeCoverage/results/coverage"
    )
    if os.path.exists(code_path):
        shutil.rmtree(code_path)
    shutil.copytree(coverage_path, code_path)


def remove_thrd_gcda(developer_path):
    print("remove thirdparty gcda")
    gcda_dir_path = os.path.join(developer_path, "localCoverage/codeCoverage/results/coverage/data/cxx")
    if os.path.exists(gcda_dir_path):
        for i in os.listdir(gcda_dir_path):
            remove_out = os.path.join(gcda_dir_path, i, "obj/out")
            remove_thrd = os.path.join(gcda_dir_path, i, "obj/third_party")
            if os.path.exists(remove_out):
                print("remove {}".format(remove_out))
                shutil.rmtree(remove_out)
            if os.path.exists(remove_thrd):
                print("remove {}".format(remove_thrd))
                shutil.rmtree(remove_thrd)


def generate_coverage_rc(developer_path):
    coverage_rc_path = os.path.join(
        developer_path, "localCoverage/codeCoverage/coverage_rc"
    )
    lcovrc_cov_template_path = os.path.join(coverage_rc_path, "lcovrc_cov_template")
    for num in range(16):
        tmp_cov_path = os.path.join(coverage_rc_path, f"tmp_cov_{num}")
        lcovrc_cov_path = os.path.join(coverage_rc_path, f"lcovrc_cov_{num}")
        if not os.path.exists(tmp_cov_path):
            os.mkdir(tmp_cov_path)
            if not os.path.exists(os.path.join(tmp_cov_path, "ex.txt")):
                with open(os.path.join(tmp_cov_path, "ex.txt"), mode="w") as f:
                    f.write("")

            copyfile(lcovrc_cov_template_path, lcovrc_cov_path)
            with open(lcovrc_cov_path, mode="a") as f:
                f.write("\n\n")
                f.write("# Location for temporary directories\n")
                f.write(f"lcov_tmp_dir = {tmp_cov_path}")


def execute_code_cov_tools(developer_path):
    llvm_gcov_path = os.path.join(
        developer_path, "localCoverage/codeCoverage/llvm-gcov.sh"
    )
    coverage_command("dos2unix %s" % llvm_gcov_path)
    coverage_command("chmod 777 %s" % llvm_gcov_path)
    tools_path = os.path.join(
        developer_path, "localCoverage/codeCoverage/mutilProcess_CodeCoverage.py"
    )
    coverage_command("python3 %s" % tools_path)


def get_subsystem_name(part_list, product_name):
    if product_name:
        testfwk_json_path = os.path.join(
            root_path, "out", product_name, "build_configs/infos_for_testfwk.json"
        )
        if os.path.exists(testfwk_json_path):
            with open(testfwk_json_path, "r", encoding="utf-8") as json_text:
                system_json = json.load(json_text)
                subsystem_info = system_json.get("phone").get("subsystem_infos")
                subsystem_list = []
                for part in part_list:
                    for key in subsystem_info.keys():
                        if part in subsystem_info.get(key) and key not in subsystem_list:
                            subsystem_list.append(key)
                subsystem_str = ','.join(list(map(str, subsystem_list)))
                return subsystem_str
        else:
            print("%s not exists.", testfwk_json_path)
            return ""
    else:
        print("product_name is not null")
        return ""


def execute_interface_cov_tools(partname_str, developer_path):
    print("*" * 40, "Start TO Get Interface Coverage Report", "*" * 40)
    innerkits_json_path = os.path.join(
        developer_path,
        "localCoverage/interfaceCoverage/get_innerkits_json.py"
    )
    coverage_command("python3 %s" % innerkits_json_path)

    interface_path = os.path.join(
        developer_path,
        "localCoverage/interfaceCoverage/interfaceCoverage_gcov_lcov.py"
    )
    subprocess.run("python3 %s %s" % (interface_path, partname_str), shell=True)


if __name__ == '__main__':
    testpart_args = sys.argv[1]
    test_part_list = testpart_args.split("testpart=")[1].split(",")

    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_test_path = os.path.join(root_path, "test/testfwk/developer_test")

    # 获取产品形态
    product_names = get_product_name(root_path)

    # copy gcda数据到覆盖率工具指定位置
    copy_coverage(developer_test_path)
    generate_coverage_rc(developer_test_path)
    remove_thrd_gcda(developer_test_path)

    # 获取部件位置信息config
    if len(test_part_list) > 0:
        get_subsystem_config(test_part_list, developer_test_path)

    # 执行代码覆盖率
    execute_code_cov_tools(developer_test_path)
    # 报备
    keyword_path = os.path.join(
        developer_test_path, "localCoverage/keyword_registration/keyword_filter.py")
    subprocess.run("python3 %s" % keyword_path, shell=True)

    # 执行接口覆盖率
    if len(test_part_list) > 0:
        execute_interface_cov_tools(testpart_args, developer_test_path)
    else:
        print("subsystem or part without!")

    # 源代码还原
    after_lcov_branch_path = os.path.join(
        developer_test_path, "localCoverage/restore_comment/after_lcov_branch.py")
    if os.path.exists(after_lcov_branch_path):
        subprocess.run("python3 %s " % after_lcov_branch_path, shell=True)
    restore_source_code_path = os.path.join(
        developer_test_path, "localCoverage/restore_comment/restore_source_code.py")
    subprocess.run("python3 %s" % restore_source_code_path, shell=True)

    print(r"See the code coverage report in: "
          r"/test/testfwk/developer_test/localCoverage/codeCoverage/results/coverage/reports/cxx/html")
    print(r"See the interface coverage report in: "
          r"/test/testfwk/developer_test/localCoverage/interfaceCoverage/results/coverage/interface_kits")
