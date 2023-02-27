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


if __name__ == '__main__':
    try:
        current_path = os.getcwd()
        root_path = current_path.split("/test/testfwk/developer_test")[0]
        subsystem_config_path = os.path.join(
            root_path, "test/testfwk/developer_test/localCoverage/restore_comment/part_config.json")
        if os.path.exists(subsystem_config_path):
            with open(subsystem_config_path, "r", encoding="utf-8", errors="ignore") as fp:
                data_dict = json.load(fp)
            for key, value in data_dict.items():
                if "path" in value.keys():
                    for path_str in value["path"]:
                        file_path = os.path.join(root_path, path_str)
                        if os.path.exists(file_path):
                            if os.path.exists(file_path + "_primal"):
                                subprocess.Popen("rm -rf %s" % file_path, shell=True).communicate()
                                subprocess.Popen("mv %s %s" % (
                                    file_path + "_primal", file_path), shell=True).communicate()
                        else:
                            print("The directory does not exist.", file_path)
    except:
        print(traceback.format_exc())
