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
import sys
import json
import shutil
import subprocess
import platform

from xdevice import platform_logger
from core.utils import get_build_output_path
from core.utils import get_output_path
from core.utils import scan_support_product
from core.common import is_open_source_product
from core.config.config_manager import UserConfigManager

BUILD_FILE_PATH = "./build_system.sh"
BUILD_FILEPATH = "./build.sh"
BUILD_LITE = "build/lite/build.py"
BUILD_TARGET_PLATFORM = "build_platform=\"%s\""
BUILD_PRODUCT_NAME = "product_name=%s"
BUILD_TARGET_SUBSYSTEM = "target_subsystem=%s"
BUILD_TARGET_SUITE = "suite=%s"
LOG = platform_logger("BuildTestcases")


##############################################################################
##############################################################################

class BuildTestcases(object):
    def __init__(self, project_rootpath):
        self.project_rootpath = project_rootpath
        user_manager = UserConfigManager()
        self.part_deps_path = os.path.join(sys.source_code_root_path,
                                           "build",
                                           "tools",
                                           "module_dependence",
                                           "part_deps.py")
        self.is_build_example = user_manager.get_user_config_flag(
            "build", "example")
        self.build_parameter_dic = user_manager.get_user_config(
            "build", "parameter")

    @classmethod
    def _copy_folder(cls, source_dir, target_dir):
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        if platform.system() == 'Windows':
            command = ["xcopy", "/f", "/s", "/e", "/y",
                       "/b", "/q", source_dir, target_dir]
        else:
            command = ["cp", "-rf", source_dir, target_dir]

        LOG.info("command: %s" % str(command))
        return subprocess.call(command) == 0

    @classmethod
    def _get_testcase_outname_by_productform(cls, productform):
        if productform == "phone" or is_open_source_product(productform):
            return ""

        testcase_outpath = ""

        # 路径注释 get_build_output_path = OpenHarmony/out/rk3568/build_configs/platforms_info/toolchain_to_variant.json
        toolchain_filepath = os.path.join(
            get_build_output_path(productform),
            "build_configs",
            "platforms_info",
            "toolchain_to_variant.json")
        if os.path.exists(toolchain_filepath):
            data_dic = []
            with open(toolchain_filepath, 'r') as toolchain_file:
                data_dic = json.load(toolchain_file)
                if not data_dic:
                    LOG.warning("The %s file load error." %
                                toolchain_filepath)
                    data_dic = []
            paltform_toolchain_dic = data_dic.get("platform_toolchain")
            testcase_outpath = paltform_toolchain_dic.get(productform, "")
            pos = testcase_outpath.rfind(':') + 1
            testcase_outpath = testcase_outpath[pos:len(testcase_outpath)]
        return testcase_outpath

    @classmethod
    def _delete_xts_testcase_dir(cls, para):
        xts_testcase_out_dir = os.path.join(
            get_build_output_path(para.productform),
            "suites",
            para.testtype[0],
            "testcases")
        LOG.info("xts_testcase_out_dir=%s" % xts_testcase_out_dir)
        # 删除~/OpenHarmony/out/rk3568/suites/xts/testcases目录内容
        if os.path.exists(xts_testcase_out_dir):
            shutil.rmtree(xts_testcase_out_dir)

    def _delete_testcase_dir(self, productform):
        if is_open_source_product(productform):
            package_out_dir = os.path.join(
                get_build_output_path(productform),
                "packages",
                "phone",
                "tests")
        else:
            package_out_dir = os.path.join(
                get_build_output_path(productform),
                "packages",
                productform,
                "tests")

        LOG.info("package_out_dir=%s" % package_out_dir)
        # 删除~/OpenHarmony/out/rk3568/packages/phone/tests目录内容
        if os.path.exists(package_out_dir):
            shutil.rmtree(package_out_dir)

        phone_out_dir = os.path.join(
            self.project_rootpath, "out", "release", "tests")
        LOG.info("phone_out_dir=%s" % phone_out_dir)
        # 删除~/OpenHarmony/out/release/tests目录内容
        if os.path.exists(phone_out_dir):
            shutil.rmtree(phone_out_dir)

        curr_productform_outname = self._get_testcase_outname_by_productform(
            productform)
        if curr_productform_outname == "":
            return

        curr_productform_outdir = os.path.join(
            get_build_output_path(productform),
            curr_productform_outname,
            "tests")
        LOG.info("curr_productform_outdir=%s" % curr_productform_outdir)
        if os.path.exists(curr_productform_outdir):
            shutil.rmtree(curr_productform_outdir)

    def _merge_testcase_dir(self, productform):
        if is_open_source_product(productform):
            package_out_dir = os.path.join(
                get_build_output_path(productform),
                "packages",
                "phone")
        else:
            package_out_dir = os.path.join(
                get_build_output_path(productform),
                "packages",
                productform)
        if platform.system() == 'Windows':
            package_out_dir = os.path.join(package_out_dir, "tests")

        phone_out_dir = os.path.join(get_build_output_path(productform),
                                     "tests")
        if os.path.exists(phone_out_dir):
            self._copy_folder(phone_out_dir, package_out_dir)

        curr_productform_outname = self._get_testcase_outname_by_productform(
            productform)
        if curr_productform_outname == "":
            return

        curr_productform_outdir = os.path.join(
            get_build_output_path(productform),
            curr_productform_outname,
            "tests")
        LOG.info("curr_productform_outdir=%s" % curr_productform_outdir)
        if os.path.exists(curr_productform_outdir):
            self._copy_folder(curr_productform_outdir, package_out_dir)

    def _execute_build_command(self, productform, command):
        build_result = False
        current_path = os.getcwd()
        os.chdir(self.project_rootpath)

        if productform == "rk3568":
            command.append("--product-name")
            command.append(productform)
        else:
            global BUILD_FILEPATH
            BUILD_FILEPATH = BUILD_FILE_PATH

        if os.path.exists(BUILD_FILEPATH):
            build_command = [BUILD_FILEPATH]
            build_command.extend(command)
            LOG.info("build_command: %s" % str(build_command))
            if subprocess.call(build_command) == 0:
                build_result = True
            else:
                build_result = False
        else:
            LOG.warning("Error: The %s is not exist" % BUILD_FILEPATH)

        os.chdir(current_path)
        return build_result

    def _execute_build_deps_files_command(self, productform, command):
        build_deps_files_result = False
        current_path = os.getcwd()
        os.chdir(self.project_rootpath)

        if productform == "rk3568":
            command.append("--product-name")
            command.append(productform)
        else:
            global BUILD_FILEPATH
            BUILD_FILEPATH = BUILD_FILE_PATH

        if os.path.exists(BUILD_FILEPATH):
            build_deps_files_command = [BUILD_FILEPATH]
            build_deps_files_command.extend(command)
            LOG.info("build_deps_files_command: %s" % str(build_deps_files_command))
            if subprocess.call(build_deps_files_command) == 0:
                build_deps_files_result = True
            else:
                build_deps_files_result = False
        else:
            LOG.warning("Build Deps Files Error: The %s is not exist" % BUILD_FILEPATH)

        os.chdir(current_path)
        return build_deps_files_result

    def _execute_build_part_deps_command(self, para):
        build_part_deps_result = False
        build_part_deps_command = []
        current_path = os.getcwd()
        #路径 deps_files_path = ~/OpenHarmony/out/baltimore/deps_files
        os.chdir(self.project_rootpath)
        if para.productform == "rk3568":
            deps_files_path = os.path.abspath(os.path.join(
                get_build_output_path(para.productform), "deps_files"))
        else:
            deps_files_path = os.path.abspath(os.path.join(
                get_output_path(),"deps_files"))
        LOG.info("deps_files_path: %s" % deps_files_path)
        build_part_deps_command.append(self.part_deps_path)
        build_part_deps_command.append("--deps-files-path")

        if os.path.exists(deps_files_path):
            build_part_deps_command.append(deps_files_path)
            LOG.info("build_part_deps_command: %s" % str(build_part_deps_command))
            if subprocess.call(build_part_deps_command) == 0:
                build_part_deps_result = True
            else:
                build_part_deps_result = False
        else:
            LOG.warning("Build Part Deps Info Error: The %s is not exist" % deps_files_path)

        os.chdir(current_path)
        return build_part_deps_result

    def _execute_build_xts_command(self, para):
        build_result = False
        xts_build_command = []
        current_path = os.getcwd()
        # eg.路径 acts_rootpath = ~/OpenHarmony/test/xts/acts
        xts_project_rootpath = os.path.join(sys.source_code_root_path,
                                                 "test",
                                                 "xts",
                                                 para.testtype[0])
        os.chdir(xts_project_rootpath)
        xts_build_command.append(BUILD_PRODUCT_NAME % para.productform)
        xts_build_command.append("system_size=standard")
        if len(para.subsystem) > 0:
            input_subsystem = ",".join(para.subsystem)
            xts_build_command.append(BUILD_TARGET_SUBSYSTEM % input_subsystem)
        if para.testsuit != "" and len(para.subsystem) == 0:
            LOG.error("Please specify subsystem.")
            return
        target_cpu = self.build_parameter_dic.get("target_cpu")
        if target_cpu == "arm64":
            xts_build_command.append("target_arch=" + target_cpu)
            xts_build_command.append("use_musl=true")
        if os.path.exists(BUILD_FILEPATH):
            build_command = [BUILD_FILEPATH]
            build_command.extend(xts_build_command)
            LOG.info("build_xts_command: %s" % str(build_command))
            if subprocess.call(build_command) == 0:
                build_result = True
            else:
                build_result = False
        else:
            LOG.warning("Build XTS Testcase Error: The %s is not exist" % BUILD_FILEPATH)

        os.chdir(current_path)
        return build_result

    def build_fuzz_testcases(self, para):
        self._delete_testcase_dir(para.productform)
        helper_path = os.path.join("..", "libs", "fuzzlib", "fuzzer_helper.py")
        command = [sys.executable, helper_path, 'make',
                   'make_temp_test', para.productform]
        if subprocess.call(command, shell=False) == 0:
            build_result = True
        else:
            build_result = False
        self._merge_testcase_dir(para.productform)
        return build_result

    # 编译测试用例（编译命令拼接）
    def build_testcases(self, productform, target):
        command = []
        if self.is_build_example:
            command.append("--gn-args")
            command.append("build_example=true")
        if isinstance(target, list):
            for test in target:
                command.append("--build-target")
                command.append(test + "_test")
        elif isinstance(target, str):
            for test in target.split(','):
                command.append("--build-target")
                command.append(test)

        if productform == "rk3568":
            pass
        else:
            command.append("--abi-type")
            command.append("generic_generic_arm_64only")
            command.append("--device-type")
            command.append("hisi_newbaltimore_newphone_standard")
            command.append("--build-variant")
            command.append("root")
        command.append("--ccache")
        self._delete_testcase_dir(productform)
        build_result = self._execute_build_command(productform, command)
        self._merge_testcase_dir(productform)
        return build_result

    # 编译XTS测试用例
    def build_xts_testcases(self, para):
        self._delete_xts_testcase_dir(para)
        build_result = self._execute_build_xts_command(para)
        return build_result

    def build_deps_files(self, productform):
        command = ["--ccache", "--gn-args", "pycache_enable=true", "--gn-args",
                   "check_deps=true", "--build-only-gn"]
        if productform == "rk3568":
            pass
        else:
            command.append("--abi-type")
            command.append("generic_generic_arm_64only")
            command.append("--device-type")
            command.append("hisi_newbaltimore_newphone_standard")
            command.append("--build-variant")
            command.append("root")
        return self._execute_build_deps_files_command(productform, command)

    #部件间依赖关系预处理，生成part_deps_info.json
    def build_part_deps(self, para):
        build_part_deps_result = self._execute_build_part_deps_command(para)
        return build_part_deps_result
        
    def build_gn_file(self, productform):
        command = []
        if self.is_build_example:
            command.append("--gn-args")
            command.append("build_example=true")
        command.append("--build-only-gn")
        command.append("--gn-args")
        command.append(BUILD_TARGET_PLATFORM % productform)
        return self._execute_build_command(productform, command)

    def build_version(self, productform):
        command = []
        command.append("--build-target")
        command.append("make_all")
        command.append("--gn-args")
        command.append(BUILD_TARGET_PLATFORM % productform)
        return self._execute_build_command(productform, command)

##############################################################################
##############################################################################
