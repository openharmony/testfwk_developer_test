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


def genPartsInfoJSON(folder_list, output_json_path):
    """
    根据部件信息,生成字典至json文件中
    """
    if len(folder_list) != 0:
        data_dict = {}
        for folder_str in folder_list:
            data_dict[folder_str] = "innerkits/ohos-arm64/" + folder_str
        output_json_path = os.path.join(output_json_path, "kits_modules_info.json")
        json_str = json.dumps(data_dict, indent=2)
        with open(output_json_path, "w") as json_file:
            json_file.write(json_str)
    else:
        print("Failed to obtain component information")


def getPartsJson(path):
    """
    #获取out/ohos-arm-release/innerkits/ohos-arm内部接口文件夹名称列表
    """
    if os.path.exists(path):
        folder_list = os.listdir(path)
    else:
        print("The folder does not exist")
        folder_list = []
    return folder_list


if __name__ == "__main__":
    current_path = os.getcwd()
    root_path = current_path.split("/test/testfwk/developer_test")[0]
    part_info_path = os.path.join(
        root_path, "out/baltimore/innerkits/ohos-arm64"
    )
    output_json_path = os.path.join(
        root_path, "out/baltimore/packages/phone/innerkits/ohos-arm64"
    )
    subprocess.Popen("mkdir -p " + output_json_path, shell=True)
    folder_list = getPartsJson(part_info_path)
    genPartsInfoJSON(folder_list, output_json_path)

