#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2021 Huawei Device Co., Ltd.
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
import platform
import subprocess
import tempfile
from abc import ABCMeta
from abc import abstractmethod

from core.config.resource_manager import ResourceManager


##############################################################################
##############################################################################

DEVICE_TEST_PATH = "/%s/%s/" % ("data", "test")


def get_level_para_string(level_string):
    level_list = list(set(level_string.split(",")))
    level_para_string = ""
    for item in level_list:
        if not item.isdigit():
            continue
        item = item.strip(" ")
        level_para_string = (f"{level_para_string}Level{item},")
    level_para_string = level_para_string.strip(",")
    return level_para_string


def make_long_command_file(command, longcommand_path, filename):
    sh_file_name = '%s.sh' % filename
    file_path = os.path.join(longcommand_path, sh_file_name)
    try:
        with open(file_path, "a") as file_desc:
            file_desc.write(command)
    except(IOError, ValueError) as err_msg:
        print("Error for make long command file: ", err_msg)
    return sh_file_name, file_path


def is_exist_target_in_device(device, path, target):
    command = "ls -l %s | grep %s" % (path, target)
    check_result = False
    stdout_info = device.shell_with_output(command)
    if stdout_info != "" and stdout_info.find(target) != -1:
        check_result = True
    return check_result


def receive_coverage_data(device, result_path, suite_file, file_name):
    file_dir = suite_file.split("distributedtest\\")[1].split("\\")[0]
    target_name = "obj"
    cxx_cov_path = os.path.abspath(os.path.join(
        result_path,
        "..",
        "coverage",
        "data",
        "cxx",
        file_name + '_' + file_dir + '_' + device.device_sn))

    if is_exist_target_in_device(device, DEVICE_TEST_PATH, "obj"):
        if not os.path.exists(cxx_cov_path):
            os.makedirs(cxx_cov_path)
        device.shell(
            "cd %s; tar -czf %s.tar.gz %s" % (DEVICE_TEST_PATH, target_name, target_name))
        src_file_tar = os.path.join(DEVICE_TEST_PATH, "%s.tar.gz" % target_name)
        device.pull_file(src_file_tar, cxx_cov_path)
        tar_path = os.path.join(cxx_cov_path, "%s.tar.gz" % target_name)
        if platform.system() == "Windows":
            process = subprocess.Popen("tar -zxf %s -C %s" % (tar_path, cxx_cov_path), shell=True)
            process.communicate()
            os.remove(tar_path)
        else:
            subprocess.Popen("tar -zxf %s -C %s > /dev/null 2>&1" %
                             (tar_path, cxx_cov_path), shell=True)
            subprocess.Popen("rm -rf %s" % tar_path, shell=True)


##############################################################################
##############################################################################


class ITestDriver:
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self, suite_file, result_path, options, push_flag=False):
        pass


##############################################################################
##############################################################################


class CppTestDriver(ITestDriver):
    def __init__(self, device, hdc_tools):
        self.device = device
        self.hdc_tools = hdc_tools

    def execute(self, suite_file, result_path, options, background=False):
        case_dir, file_name = os.path.split(suite_file)
        dst_dir = case_dir.split("distributedtest\\")[1]
        os.makedirs(os.path.join(result_path, "temp", dst_dir), exist_ok=True)

        long_command_path = tempfile.mkdtemp(
            prefix="long_command_",
            dir=os.path.join(result_path, "temp", dst_dir))
        if not options.coverage:
            command = "cd %s; rm -rf %s.xml; chmod +x *; ./%s" % (
                DEVICE_TEST_PATH,
                file_name,
                file_name)
        else:
            coverage_outpath = options.coverage_outpath
            strip_num = len(coverage_outpath.split("/")) - 1
            command = "cd %s; rm -rf %s.xml; chmod +x *; GCOV_PREFIX=. " \
                      "GCOV_PREFIX_STRIP=%s ./%s" % \
                      (DEVICE_TEST_PATH,
                       file_name,
                       str(strip_num),
                       file_name,
                       )

        print("command: %s" % command)
        sh_file_name, file_path = make_long_command_file(command, 
                                                         long_command_path, 
                                                         file_name)
        self.device.push_file(file_path, DEVICE_TEST_PATH)

        # push resource files
        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = \
            resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dic, resource_dir,
                                               self.device)
        if background:
            sh_command = "nohup sh %s >%s 2>&1 &" % (
                os.path.join(DEVICE_TEST_PATH, sh_file_name),
                os.path.join(DEVICE_TEST_PATH, "agent.log"))
        else:
            sh_command = "sh %s" % (
                os.path.join(DEVICE_TEST_PATH, sh_file_name))
        self.device.shell(sh_command)

        if options.coverage:
            receive_coverage_data(self.device, result_path, suite_file, file_name)


##############################################################################
##############################################################################

