#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

import sys
import os
import json

from core.utils import get_build_output_path
from core.common import is_open_source_product
from core.config.config_manager import UserConfigManager


##############################################################################
##############################################################################

class ParsePartsConfig(object):
    def __init__(self, productform):
        self.productform = productform
        self.subsystem_infos, self.part_infos = self.get_infos_data()

    # 获取配置文件地址：~/OpenHarmony/out/rk3568/build_configs/infos_for_testfwk.json（以rk3568举例）
    def get_config_file_path(self):
        manager = UserConfigManager()
        # 获取user_config.xml文件中的配置的<test_cases>（编译好的测试用例地址）
        testcase_dir = manager.get_test_cases_dir()

        # 如果没有在developtertest/config/user_config里配置test_cases路径，
        # 就到OpenHarmony/out/rk3568/build_configs/infos_for_testfwk.json里查找
        if testcase_dir == "":
            if sys.source_code_root_path != "":
                config_filepath = os.path.join(
                    get_build_output_path(self.productform),
                    "build_configs",
                    "infos_for_testfwk.json")
            else:
                config_filepath = ""

        # 如果在developtertest/config/user_config里配置了test_cases路径，就在这个路径下的infos_for_testfwk.json里查找
        else:
            config_filepath = os.path.join(
                testcase_dir,
                "infos_for_testfwk.json")
        return config_filepath

    def get_infos_data(self):
        config_filepath = self.get_config_file_path()

        # 检验给出的路径是否真地存在
        if not os.path.exists(config_filepath):
            print("Error: %s is not exist." % config_filepath)
            return None, None

        data_dic = None
        with open(config_filepath, 'r') as file_handle:
            data_dic = json.load(file_handle)
            if not data_dic:
                print("Error: json file load error.")
                return None, None

        # open source branch, the part form of all product is "phone"
        if is_open_source_product(self.productform):
            product_data_dic = data_dic.get("phone", None)
        else:
            product_data_dic = data_dic.get(self.productform, None)
        # product_data_dic：infos_for_testfwk.json配置文件中“phone”节点数据
        if product_data_dic is None:
            print("Error: product_data_dic is None.")
            return None, None
        # subsystem_infos（系统中定义的子系统列表）：infos_for_testfwk.json配置文件中“phone”节点下“subsystem_infos”节点数据
        subsystem_infos = product_data_dic.get("subsystem_infos", None)
        # subsystem_infos（系统中定义的部件信息列表）：infos_for_testfwk.json配置文件中“phone”节点下“part_infos”节点数据
        part_infos = product_data_dic.get("part_infos", None)
        return subsystem_infos, part_infos

    def get_subsystem_infos(self):
        return self.subsystem_infos

    def get_part_infos(self):
        return self.part_infos

    def get_subsystem_name_list(self):
        subsystem_name_list = []
        if self.subsystem_infos:
            for item in self.subsystem_infos:
                subsystem_name_list.append(item)
        return subsystem_name_list

    # 获取部件列表
    def get_part_list(self, subsystemlist, partlist):
        # 如果options参数中的partlist不为空，直接返回partlist
        if len(partlist) != 0:
            return partlist
        # 如果infos_for_testfwk.json配置文件的subsystem_infos为None，返回options参数中的subsystemlist
        if self.subsystem_infos is None:
            return subsystemlist

        part_name_list = []
        # 遍历options参数中的子系统列表，并且将infos_for_testfwk.json配置文件的subsystem_infos中的对应子系统的部件列表加入到part_name_list中
        if len(subsystemlist) != 0:
            for item in subsystemlist:
                parts = self.subsystem_infos.get(item, [])
                part_name_list.extend(parts)
        return part_name_list


##############################################################################
##############################################################################
