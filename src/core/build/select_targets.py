#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020-2022 Huawei Device Co., Ltd.
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
from xdevice import platform_logger
from core.utils import get_file_list_by_postfix
from core.utils import get_build_output_path
from core.config.parse_parts_config import ParsePartsConfig

LOG = platform_logger("SelectTargets")


##############################################################################
##############################################################################

class SelectTargets(object):
    def __init__(self, project_rootpath):
        self.project_rootpath = project_rootpath

    @classmethod
    def _get_mlf_data_from_file(cls, filepath):
        data_list = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as mlf_file:
                data_list = json.load(mlf_file)
                if not data_list:
                    LOG.warning("The %s file load error." % filepath)
                    data_list = []
        return data_list

    @classmethod
    def _get_part_path_data(cls, productform):
        part_path_dic = {}
        parser = ParsePartsConfig(productform)
        # 获取infos_for_testfwk.json配置文件中“phone”节点下“part_infos”节点数据
        part_infos = parser.get_part_infos()
        if part_infos is None:
            LOG.error("part_infos is None.")
            return part_path_dic

        for part_name in part_infos:
            part_info = part_infos.get(part_name, None)
            if part_info is None:
                continue

            origin_part_name = part_info.get("origin_part_name")
            build_out_dir = part_info.get("build_out_dir")

            part_path_list = []
            # default_part_path：~/OpenHarmony/out/rk3568/module_list_files/部件名（以rk3568举例）
            default_part_path = os.path.join(
                get_build_output_path(productform),
                "module_list_files",
                origin_part_name)
            if os.path.exists(default_part_path):
                part_path_list.append(default_part_path)
            # 如果build_out_dir不是当前目录，将新目录加到part_path_list中
            if build_out_dir != ".":
                product_part_path = os.path.join(
                    get_build_output_path(productform),
                    build_out_dir,
                    "module_list_files",
                    origin_part_name)
                if os.path.exists(product_part_path):
                    part_path_list.append(product_part_path)
            part_path_dic[part_name] = part_path_list
        return part_path_dic

    def _get_target_list_from_path(self, typelist, check_path):
        target_list = []
        if os.path.exists(check_path):
            # 获取部件编译输出目录（~/OpenHarmony/out/rk3568/module_list_files/部件名1）中.mlf文件列表
            mlf_file_list = get_file_list_by_postfix(
                check_path, ".mlf")
            # 遍历mlf_file_list中所有目录下面mlf文件中的label列表
            for filepath in mlf_file_list:
                # 获取mlf文件中的JSON数据信息列表
                mlf_info_list = self._get_mlf_data_from_file(filepath)
                for data in mlf_info_list:
                    # 举例："test_type": "moduletest"
                    test_type = data.get("test_type")
                    # 举例："label": "//base/accessibility/services/test:aams_accessibility_keyevent_filter_test
                    # (//build/toolchain/ohos:ohos_clang_arm)"
                    target_path = data.get("label")
                    if "ALL" in typelist:
                        target_list.append(target_path)
                        continue
                    if test_type in typelist:
                        target_list.append(target_path)
        return target_list

    def _get_target_list_by_type(self, productform, typelist):
        target_list = []
        # 获取所有部件编译输出信息列表：[{“部件名1”：[~/OpenHarmony/out/rk3568/module_list_files/部件名1]}]
        # 或者{“部件名1”：[~/OpenHarmony/out/rk3568/module_list_files/部件名1，
        # ~/OpenHarmony/out/rk3568/编译目录build_out_dir/module_list_files/部件名1]}
        part_path_dic = self._get_part_path_data(productform)
        for item in part_path_dic:
            part_path_list = part_path_dic.get(item)
            for part_path in part_path_list:
                print("part_path = %s" % part_path)
                temp_list = self._get_target_list_from_path(typelist,
                    part_path)
                target_list.extend(temp_list)
        return target_list

    def _get_target_list_by_part(self, productform, typelist, partlist):
        target_list = []
        part_path_dic = self._get_part_path_data(productform)
        for partname in partlist:
            part_path_list = part_path_dic.get(partname, [])
            for part_path in part_path_list:
                temp_list = self._get_target_list_from_path(typelist,
                    part_path)
                target_list.extend(temp_list)
        return target_list

    def _get_target_list_by_module(self, productform, typelist, partlist,
                                   testmodule):
        target_list = []
        part_path_dic = self._get_part_path_data(productform)
        for partname in partlist:
            part_path_list = part_path_dic.get(partname, [])
            for part_path in part_path_list:
                module_path = os.path.join(part_path, testmodule)
                LOG.info("module_path = %s." % module_path)
                if os.path.exists(module_path):
                    temp_list = self._get_target_list_from_path(typelist,
                        module_path)
                    target_list.extend(temp_list)
        return target_list

    def get_build_targets(self, productform, typelist, partlist, testmodule):
        target_list = []

        if productform == "" or len(typelist) == 0:
            LOG.warning("Error: productform or typelist is empty.")
            return []

        if len(partlist) == 0 and testmodule != "":
            LOG.warning(
                "The part cannot be empty When the module is not empty.")
            return []
        # productform不为空，typelist（test type[UT,MST,ST,PERF,ALL]）不为空
        # partlist和testmodule为空，通过testtype获取部件列表
        if len(partlist) == 0 and testmodule == "":
            target_list = self._get_target_list_by_type(productform, typelist)
            return target_list
        # productform不为空，typelist（test type[UT,MST,ST,PERF,ALL]）不为空
        # partlist不为空，testmodule为空，通过testtype、partlist一起获取部件列表
        if len(partlist) != 0 and testmodule == "":
            target_list = self._get_target_list_by_part(productform, typelist,
                                                        partlist)
            return target_list
        # productform不为空，typelist（test type[UT,MST,ST,PERF,ALL]）不为空
        # partlist不为空，testmodule不为空，通过testtype、partlist、testmodule一起获取部件列表
        if len(partlist) != 0 and testmodule != "":
            target_list = self._get_target_list_by_module(productform,
                                                          typelist,
                                                          partlist,
                                                          testmodule)

        return target_list

    # 通过infos_for_testfwk.json文件获取所有子部件信息编译目录信息：
    # [{“部件名1”：[~/OpenHarmony/out/rk3568/module_list_files/部件名1]}]
    # 然后遍历这些目录中的mlf文件，获取其中定义的label，返回label集合
    # 遍历时通过testmodule控制遍历的部件指定模块目录，如果不定义，则遍历子部件下面所有模块目录
    # 遍历时通过partlist控制遍历指定部件目录，如果不定义，则遍历infos_for_testfwk.json文件中定义的所有子部件目录
    def filter_build_targets(self, para):
        productform = para.productform
        typelist = para.testtype
        partlist = para.partname_list
        testmodule = para.testmodule

        print("partlist = %s" % str(partlist))
        target_list = self.get_build_targets(productform, typelist,
                                             partlist, testmodule)
        return target_list


##############################################################################
##############################################################################
