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

import json
import os
import subprocess
import sys


def get_subsystem_config(part_str, developer_path):
    all_system_info_path = os.path.join(
        developer_path, "localCoverage/all_subsystem_config.json"
    )
    if os.path.exists(all_system_info_path):
        new_json_text = {}
        with open(all_system_info_path, "r", encoding="utf-8") as system_text:
            system_text_json = json.load(system_text)
            if part_str in system_text_json:
                new_json_text[part_str] = system_text_json[part_str]
            else:
                print(f"Error: {part_str} not in all_subsystem_config.json")
        return new_json_text
    else:
        print(f"{all_system_info_path} not exists!")
        return {}


def get_system_or_vendor(code_path):
    repo_config_path = os.path.join(code_path, ".repo/manifests.git/.repo_config.json")
    if os.path.exists(repo_config_path):
        with open(repo_config_path, "r", encoding="utf-8") as fp:
            text_json = json.load(fp)
            if "manifest.filename" in text_json:
                text = text_json["manifest.filename"][0]
                if text.startswith("system"):
                    return "system"
                if text.startswith("vendor"):
                    return "vendor"
            else:
                return "blue"
    else:
        print(f"Error: {repo_config_path} not exist!")
        return "Error"


def get_bundle_json(part_str, developer_path, code_path):
    part_json = get_subsystem_config(part_str, developer_path)
    system_or_vendor = get_system_or_vendor(code_path)
    if system_or_vendor == "system":
        command = ["./build_system.sh", "--abi-type", "generic_generic_arm_64only", "--device-type",
                   "hisi_all_phone_standard", "--ccache", "--build-variant", "root"]
    elif system_or_vendor == "system":
        command = ["./build_vendor.sh", "--abi-type", "generic_generic_arm_64only", "--device-type",
                   "general_8425L_phone_standard", "--ccache", "--build-variant", "root",
                   "--gn-args", "uefi_enable=true"]
    else:
        command = ["./build.sh", "--product-name", "rk3568", "--ccache"]

    if part_json.get(part_str):
        bundle_json_path = os.path.join(code_path, part_json[part_str]["path"][0], "bundle.json")
        if os.path.exists(bundle_json_path):
            with open(bundle_json_path, "r", encoding="utf-8") as bundle_json_text:
                bundle_json = json.load(bundle_json_text)
            os.chdir(code_path)
            part_name = bundle_json["component"]["name"]
            command.append("--build-target")
            command.append(part_name)

            if bundle_json["component"]["build"].get("test"):
                test_path = bundle_json["component"]["build"]["test"]
                test_str = " ".join([i.strip("//") for i in test_path])
                command.append("--build-target")
                command.append(test_str)

            command.append("--gn-args")
            command.append("use_clang_coverage=true")
            print(command)
            if subprocess.call(command) == 0:
                build_result = True
            else:
                build_result = False
            os.chdir(developer_path)
            return build_result

        else:
            print(f"{bundle_json_path}不存在，不能获取编译参数，请检查该部件的bundle.json文件！")
            return False


def execute_case(developer_test, part_name):
    start_path = os.path.join(developer_test, "start.sh")
    run_cmd = f"run -t UT -tp {part_name} -cov coverage \n"
    print(run_cmd)
    with os.popen(start_path, "w") as finput:
        finput.write("1\n")
        finput.write(run_cmd)
        finput.write("quit\n")
        finput.write("exit(0)\n")


if __name__ == '__main__':
    test_part_str = sys.argv[1]
    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_test_path = os.path.join(root_path, "test/testfwk/developer_test")
    build_before_path = os.path.join(
        developer_test_path,
        "localCoverage/restore_comment/build_before_generate.py"
    )
    subprocess.run("python3 %s %s" % (build_before_path, test_part_str), shell=True)
    build_success = get_bundle_json(test_part_str, developer_test_path, root_path)
    if build_success:
        execute_case(developer_test_path, test_part_str)
