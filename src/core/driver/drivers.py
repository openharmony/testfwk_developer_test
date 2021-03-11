#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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
import time
import platform
import json
import shutil
import zipfile
import tempfile
from dataclasses import dataclass


from xdevice import DeviceTestType
from xdevice import DeviceLabelType
from xdevice import ExecuteTerminate
from xdevice import DeviceError

from xdevice import IDriver
from xdevice import platform_logger
from xdevice import Plugin
from core.utils import get_decode
from core.config.resource_manager import ResourceManager


__all__ = [
    "CppTestDriver",
    "DexTestDriver",
    "HapTestDriver",
    "disable_keyguard",
    "GTestConst"]

LOG = platform_logger("Drivers")
DEFAULT_TEST_PATH = "/%s/%s/" % ("data", "test")

TIME_OUT = 900 * 1000


##############################################################################
##############################################################################


class DisplayOutputReceiver:
    def __init__(self):
        self.output = ""
        self.unfinished_line = ""

    def _process_output(self, output, end_mark="\n"):
        content = output
        if self.unfinished_line:
            content = "".join((self.unfinished_line, content))
            self.unfinished_line = ""
        lines = content.split(end_mark)
        if content.endswith(end_mark):
            return lines[:-1]
        else:
            self.unfinished_line = lines[-1]
            return lines[:-1]

    def __read__(self, output):
        self.output = "%s%s" % (self.output, output)
        lines = self._process_output(output)
        for line in lines:
            line = line.strip()
            if line:
                LOG.info(get_decode(line))

    def __error__(self, message):
        pass

    def __done__(self, result_code="", message=""):
        pass


@dataclass
class GTestConst(object):
    exec_para_filter = "--gtest_filter"
    exec_para_level = "--gtest_testsize"


@dataclass
class ZunitConst(object):
    z_unit_app = "ohos.unittest.App"
    output_dir = "OUTPUT_DIR="
    output_file = "OUTPUT_FILE="
    test_class = "TEST_CLASS="
    exec_class = "EXEC_CLASS="
    exec_method = "EXEC_METHOD="
    exec_level = "EXEC_LEVEL="
    coverage_flag = "COVERAGE_FLAG=1"
    jtest_status_filename = "jtest_status.txt"
    remote_command_dir = "commandtmp"


def get_device_log_file(report_path, serial=None, log_name="device_log"):
    from xdevice import Variables
    log_path = os.path.join(report_path, Variables.report_vars.log_dir)
    os.makedirs(log_path, exist_ok=True)

    serial = serial or time.time_ns()
    device_file_name = "{}_{}.log".format(log_name, serial)
    device_log_file = os.path.join(log_path, device_file_name)
    return device_log_file


def get_level_para_string(level_string):
    level_list = list(set(level_string.split(",")))
    level_para_string = ""
    for item in level_list:
        if not item.isdigit():
            continue
        item = item.strip(" ")
        level_para_string += ("Level%s," % item)
    level_para_string = level_para_string.strip(",")
    return level_para_string


def get_execute_java_test_files(suite_file):
    java_test_file = ""
    test_info_file = suite_file[:suite_file.rfind(".")] + ".info"
    if not os.path.exists(test_info_file):
        return java_test_file
    try:
        with open(test_info_file, "r") as file_desc:
            lines = file_desc.readlines()
            for line in lines:
                class_name, _ = line.split(',', 1)
                class_name = class_name.strip()
                if not class_name.endswith("Test"):
                    continue
                java_test_file += class_name + ","
    except(IOError, ValueError) as err_msg:
        LOG.exception("Error to read info file: ", err_msg)
    if java_test_file != "":
        java_test_file = java_test_file[:-1]
    return java_test_file


def get_java_test_para(testcase, testlevel):
    exec_class = "*"
    exec_method = "*"
    exec_level = ""

    if "" != testcase and "" == testlevel:
        pos = testcase.rfind(".")
        if pos != -1:
            exec_class = testcase[0:pos]
            exec_method = testcase[pos + 1:]
            exec_level = ""
        else:
            exec_class = "*"
            exec_method = testcase
            exec_level = ""
    elif "" == testcase and "" != testlevel:
        exec_class = "*"
        exec_method = "*"
        exec_level = get_level_para_string(testlevel)

    return exec_class, exec_method, exec_level


def get_result_savepath(testsuit_path, result_rootpath):
    findkey = os.sep + "tests" + os.sep
    filedir, _ = os.path.split(testsuit_path)
    pos = filedir.find(findkey)
    if -1 != pos:
        subpath = filedir[pos + len(findkey):]
        pos1 = subpath.find(os.sep)
        if -1 != pos1:
            subpath = subpath[pos1 + len(os.sep):]
            result_path = os.path.join(result_rootpath, "result", subpath)
        else:
            result_path = os.path.join(result_rootpath, "result")
    else:
        result_path = os.path.join(result_rootpath, "result")

    if not os.path.exists(result_path):
        os.makedirs(result_path)

    LOG.info("result_savepath = " + result_path)
    return result_path


# all testsuit common Unavailable test result xml
def _create_empty_result_file(filepath, filename, error_message):
    error_message = str(error_message)
    error_message = error_message.replace("\"", "")
    error_message = error_message.replace("<", "")
    error_message = error_message.replace(">", "")
    error_message = error_message.replace("&", "")
    if filename.endswith(".hap"):
        filename = filename.split(".")[0]
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding='utf-8') as file_desc:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime())
            file_desc.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file_desc.write(
                '<testsuites tests="0" failures="0" '
                'disabled="0" errors="0" timestamp="%s" '
                'time="0" name="AllTests">\n' % time_stamp)
            file_desc.write(
                '  <testsuite name="%s" tests="0" failures="0" '
                'disabled="0" errors="0" time="0.0" '
                'unavailable="1" message="%s">\n' %
                (filename, error_message))
            file_desc.write('  </testsuite>\n')
            file_desc.write('</testsuites>\n')
    return


def _unlock_screen(device):
    device.execute_shell_command("svc power stayon true")
    time.sleep(1)


def _unlock_device(device):
    device.execute_shell_command("input keyevent 82")
    time.sleep(1)
    device.execute_shell_command("wm dismiss-keyguard")
    time.sleep(1)


def _lock_screen(device):
    device.execute_shell_command("svc power stayon false")
    time.sleep(1)


def disable_keyguard(device):
    _unlock_screen(device)
    _unlock_device(device)


def _sleep_according_to_result(result):
    if result:
        time.sleep(1)


##############################################################################
##############################################################################

class ResultManager(object):
    def __init__(self, testsuit_path, config):
        self.testsuite_path = testsuit_path
        self.config = config
        self.result_rootpath = self.config.report_path
        self.device = self.config.device
        if testsuit_path.endswith(".hap"):
            self.device_testpath = self.config.test_hap_out_path
        else:
            self.device_testpath = self.config.target_test_path
        self.testsuite_name = os.path.basename(self.testsuite_path)
        self.is_coverage = False

    def set_is_coverage(self, is_coverage):
        self.is_coverage = is_coverage

    def get_test_results(self, error_message=""):
        # Get test result files
        filepath = self.obtain_test_result_file()
        if not os.path.exists(filepath):
            _create_empty_result_file(filepath, self.testsuite_name,
                                      error_message)
        if "benchmark" == self.config.testtype[0]:
            if self.device.is_directory(
                    os.path.join(self.device_testpath, "benchmark")):
                self._obtain_benchmark_result()
        # Get coverage data files
        if self.is_coverage:
            self.obtain_coverage_data()

        return filepath

    def _obtain_benchmark_result(self):
        benchmark_root_dir = os.path.abspath(
            os.path.join(self.result_rootpath, "benchmark"))
        benchmark_dir = os.path.abspath(
            os.path.join(benchmark_root_dir,
                         self.get_result_sub_save_path(),
                         self.testsuite_name))

        if not os.path.exists(benchmark_dir):
            os.makedirs(benchmark_dir)

        print("benchmark_dir =%s", benchmark_dir)
        if not self.device.pull_file(
                os.path.join(self.device_testpath, "benchmark"),
                benchmark_dir):
            os.rmdir(benchmark_dir)
        return benchmark_dir

    def get_result_sub_save_path(self):
        find_key = os.sep + "tests" + os.sep
        file_dir, _ = os.path.split(self.testsuite_path)
        pos = file_dir.find(find_key)
        subpath = ""
        if -1 != pos:
            subpath = file_dir[pos + len(find_key):]
            pos1 = subpath.find(os.sep)
            if -1 != pos1:
                subpath = subpath[pos1 + len(os.sep):]
        print("subpath = " + subpath)
        return subpath

    def obtain_test_result_file(self):
        result_save_path = get_result_savepath(self.testsuite_path,
            self.result_rootpath)
        result_file_path = os.path.join(result_save_path,
            "%s.xml" % self.testsuite_name)

        result_josn_file_path = os.path.join(result_save_path,
            "%s.json" % self.testsuite_name)

        if self.testsuite_path.endswith('.hap'):
            remote_result_file = os.path.join(self.device_testpath,
                "testcase_result.xml")
            remote_json_result_file = os.path.join(self.device_testpath,
                "%s.json" % self.testsuite_name)
        else:
            remote_result_file = os.path.join(self.device_testpath,
                "%s.xml" % self.testsuite_name)
            remote_json_result_file = os.path.join(self.device_testpath,
                "%s.json" % self.testsuite_name)

        if self.device.is_file_exist(remote_result_file):
            self.device.pull_file(remote_result_file, result_file_path)
        elif self.device.is_file_exist(remote_json_result_file):
            self.device.pull_file(remote_json_result_file,
                                  result_josn_file_path)
            result_file_path = result_josn_file_path
        else:
            LOG.error("%s not exist", remote_result_file)

        return result_file_path

    def make_empty_result_file(self, error_message=""):
        result_savepath = get_result_savepath(self.testsuite_path,
            self.result_rootpath)
        result_filepath = os.path.join(result_savepath, "%s.xml" %
            self.testsuite_name)
        if not os.path.exists(result_filepath):
            _create_empty_result_file(result_filepath,
                self.testsuite_name, error_message)

    def is_exist_target_in_device(self, path, target):
        if platform.system() == "Windows":
            command = '\"ls -l %s | grep %s\"' % (path, target)
        else:
            command = "ls -l %s | grep %s" % (path, target)

        check_result = False
        stdout_info = self.device.execute_shell_command(command)
        if stdout_info != "" and stdout_info.find(target) != -1:
            check_result = True
        return check_result

    def obtain_coverage_data(self):
        cov_root_dir = os.path.abspath(os.path.join(
            self.result_rootpath,
            "..",
            "coverage",
            "data",
            "exec"))
        java_cov_path = get_result_savepath(
            self.testsuite_path,
            cov_root_dir)

        dst_target_name = "%s.exec" % self.testsuite_name
        src_target_name = "jacoco.exec"
        if self.is_exist_target_in_device(self.device_testpath,
                                          src_target_name):
            if not os.path.exists(java_cov_path):
                os.makedirs(java_cov_path)
            self.device.pull_file(
                os.path.join(self.device_testpath, src_target_name),
                os.path.join(java_cov_path, dst_target_name))

        target_name = "obj"
        cxx_cov_path = os.path.abspath(os.path.join(
            self.result_rootpath,
            "..",
            "coverage",
            "data",
            "cxx",
            self.testsuite_name))

        if self.is_exist_target_in_device(DEFAULT_TEST_PATH, target_name):
            if not os.path.exists(cxx_cov_path):
                os.makedirs(cxx_cov_path)
            src_file = os.path.join(DEFAULT_TEST_PATH, target_name)
            self.device.pull_file(src_file, cxx_cov_path, is_create=True)


##############################################################################
##############################################################################

@Plugin(type=Plugin.DRIVER, id=DeviceTestType.cpp_test)
class CppTestDriver(IDriver):
    """
    CppTest is a Test that runs a native test package on given device.
    """
    # test driver config
    config = None
    result = ""

    def __check_environment__(self, device_options):
        if len(device_options) == 1 and device_options[0].label is None:
            return True
        if len(device_options) != 1 or \
                device_options[0].label != DeviceLabelType.phone:
            return False
        return True

    def __check_config__(self, config):
        pass

    def __result__(self):
        return self.result if os.path.exists(self.result) else ""

    def __execute__(self, request):
        try:
            self.config = request.config
            self.config.target_test_path = DEFAULT_TEST_PATH
            self.config.device = request.config.environment.devices[0]

            suite_file = request.root.source.source_file
            LOG.debug("Testsuite FilePath: %s" % suite_file)

            if not suite_file:
                LOG.error("test source '%s' not exists" %
                          request.root.source.source_string)
                return

            if not self.config.device:
                result = ResultManager(suite_file, self.config)
                result.set_is_coverage(False)
                result.make_empty_result_file(
                    "No test device is found. ")
                return

            serial = request.config.device.__get_serial__()
            device_log_file = get_device_log_file(
                request.config.report_path,
                serial)

            with open(device_log_file, "a", encoding="UTF-8") as file_pipe:
                self.config.device.start_catch_device_log(file_pipe)
                self._init_gtest()
                self._run_gtest(suite_file)
        finally:
            self.config.device.stop_catch_device_log()

    def _init_gtest(self):
        self.config.device.hdc_command("remount")
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.target_test_path)

    def _run_gtest(self, suite_file):
        from xdevice import Variables
        filename = os.path.basename(suite_file)
        test_para = self._get_test_para(self.config.testcase,
                                        self.config.testlevel,
                                        self.config.testtype,
                                        self.config.target_test_path,
                                        filename)
        is_coverage_test = True if self.config.coverage else False

        # push testsuite file
        self.config.device.push_file(suite_file, self.config.target_test_path)

        # push resource files
        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = \
            resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dic, resource_dir,
                                               self.config.device)

        # execute testcase
        if not self.config.coverage:
            command = "cd %s; rm -rf %s.xml; chmod +x *; ./%s %s" % (
                self.config.target_test_path,
                filename,
                filename,
                test_para)
        else:
            coverage_outpath = self.config.coverage_outpath
            strip_num = len(coverage_outpath.split(os.sep)) - 1
            command = "cd %s; rm -rf %s.xml; chmod +x *; GCOV_PREFIX=. " \
                "GCOV_PREFIX_STRIP=%s ./%s %s" % \
                (self.config.target_test_path,
                 filename,
                 str(strip_num),
                 filename,
                 test_para)

        result = ResultManager(suite_file, self.config)
        result.set_is_coverage(is_coverage_test)

        try:
            # get result
            display_receiver = DisplayOutputReceiver()
            self.config.device.execute_shell_command(
                command,
                receiver=display_receiver,
                timeout=TIME_OUT,
                retry=0)
            return_message = display_receiver.output
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = str(exception.args)

        self.result = result.get_test_results(return_message)
        resource_manager.process_cleaner_data(resource_data_dic,
            resource_dir,
            self.config.device)

    @staticmethod
    def _get_test_para(testcase,
                       testlevel,
                       testtype,
                       target_test_path,
                       filename):
        if "benchmark" == testtype[0]:
            test_para = (" --benchmark_out_format=json"
                         " --benchmark_out=%s%s.json") % (
                            target_test_path, filename)
            return test_para

        if "" != testcase and "" == testlevel:
            test_para = "%s=%s" % (GTestConst.exec_para_filter, testcase)
        elif "" == testcase and "" != testlevel:
            level_para = get_level_para_string(testlevel)
            test_para = "%s=%s" % (GTestConst.exec_para_level, level_para)
        else:
            test_para = ""
        return test_para


##############################################################################
##############################################################################

@Plugin(type=Plugin.DRIVER, id=DeviceTestType.dex_test)
class DexTestDriver(IDriver):
    """
    DexTest is a Test that runs a native test package on given device.
    """
    # test driver config
    config = None
    result = ""

    def __check_environment__(self, device_options):
        pass

    def __check_config__(self, config):
        pass

    def __result__(self):
        return self.result if os.path.exists(self.result) else ""

    def __execute__(self, request):
        try:
            self.config = request.config
            self.config.target_test_path = DEFAULT_TEST_PATH
            self.config.device = request.config.environment.devices[0]

            suite_file = request.root.source.source_file
            LOG.debug("Testsuite FilePath: %s" % suite_file)

            if not suite_file:
                LOG.error("test source '%s' not exists" %
                          request.root.source.source_string)
                return

            if not self.config.device:
                result = ResultManager(suite_file, self.config)
                result.set_is_coverage(False)
                result.make_empty_result_file(
                    "No test device is found. ")
                return

            serial = request.config.device.__get_serial__()
            device_log_file = get_device_log_file(
                request.config.report_path,
                serial)

            with open(device_log_file, "a", encoding="UTF-8") as file_pipe:
                self.config.device.start_catch_device_log(file_pipe)
                self._init_junit_test()
                self._run_junit_test(suite_file)
        finally:
            self.config.device.stop_catch_device_log()

    def _init_junit_test(self):
        self.config.device.hdc_command("remount")
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mount -o rw,remount,rw /%s" % "system")

    def _run_junit_test(self, suite_file):
        filename = os.path.basename(suite_file)
        suitefile_target_test_path = self.config.target_test_path
        junit_test_para = self._get_junit_test_para(filename, suite_file)
        is_coverage_test = True if self.config.coverage else False

        # push testsuite file
        self.config.device.push_file(suite_file, self.config.target_test_path)

        # push resource files
        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = \
            resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dic, resource_dir,
                                               self.config.device)

        # execute testcase
        return_message = self._execute_suitefile_junittest(
            filename, junit_test_para, suitefile_target_test_path)

        result = ResultManager(suite_file, self.config)
        result.set_is_coverage(is_coverage_test)
        self.result = result.get_test_results(return_message)

        resource_manager.process_cleaner_data(resource_data_dic, resource_dir,
                                              self.config.device)

    def _get_junit_test_para(self, filename, suite_file):
        exec_info = get_java_test_para(self.config.testcase,
                                       self.config.testlevel)
        java_test_file = get_execute_java_test_files(suite_file)
        junit_test_para = self._get_dex_test_para(filename, java_test_file,
                                                  exec_info)
        return junit_test_para

    def _get_dex_test_para(self, filename, java_test_file, exec_info):
        if "benchmark" == self.config.testtype[0]:
            main_class = "ohos.hmh.Executor"
        else:
            main_class = ZunitConst.z_unit_app
        exec_class, exec_method, exec_level = exec_info
        dex_test_para = "%s  %s%s  %s%s  %s%s  %s%s  %s%s  %s%s" % (
            main_class, ZunitConst.output_dir,
            self.config.target_test_path,
            ZunitConst.output_file, filename,
            ZunitConst.test_class, java_test_file,
            ZunitConst.exec_class, exec_class,
            ZunitConst.exec_method, exec_method,
            ZunitConst.exec_level, exec_level)
        if self.config.coverage:
            dex_test_para += " %s" % ZunitConst.coverage_flag
        return dex_test_para

    def _execute_suitefile_junittest(self, filename, testpara,
                                     target_test_path):
        return_message = self._execute_dexfile_junittest(filename, testpara,
                                                         target_test_path)
        return return_message

    def _execute_dexfile_junittest(self, filename, testpara, target_test_path):
        from xdevice import Variables
        long_command_path = tempfile.mkdtemp(prefix="long_command_",
                                             dir=self.config.report_path)
        if self.config.coverage:
            coverage_outpath = self.config.coverage_outpath
            strip_num = len(coverage_outpath.split(os.sep)) - 1

            command = "cd %s; rm -rf %s.xml; chmod +x *;" \
                      " export BOOTCLASSPATH=%s%s:$BOOTCLASSPATH;" \
                      " export GCOV_PREFIX=%s; export GCOV_PREFIX_STRIP=%d;" \
                      " app_process %s%s %s" % \
                      (target_test_path,
                       filename,
                       target_test_path,
                       filename,
                       target_test_path,
                       strip_num,
                       target_test_path,
                       filename,
                       testpara)
        else:
            command = "cd %s; rm -rf %s.xml; chmod +x *;" \
                      " export BOOTCLASSPATH=%s%s:$BOOTCLASSPATH;" \
                      " app_process %s%s %s" % \
                      (target_test_path,
                       filename,
                       target_test_path,
                       filename,
                       target_test_path,
                       filename,
                       testpara)

        LOG.info("command: %s" % command)
        sh_file_name, file_path = \
            self._make_long_command_file(command, long_command_path, filename)
        remote_command_dir = os.path.join(target_test_path,
                                          ZunitConst.remote_command_dir)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % remote_command_dir)
        self.config.device.push_file(file_path, remote_command_dir)
        try:
            display_receiver = DisplayOutputReceiver()
            self.config.device.execute_shell_command(
                "sh %s/%s" % (remote_command_dir, sh_file_name),
                receiver=display_receiver,
                timeout=TIME_OUT,
                retry=0)
            return_message = display_receiver.output
            if display_receiver.output:
                time.sleep(1)
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = str(exception.args)
        shutil.rmtree(long_command_path)
        return return_message

    @staticmethod
    def _make_long_command_file(command, longcommand_path, filename):
        sh_file_name = '%s.sh' % filename
        file_path = os.path.join(longcommand_path, sh_file_name)
        try:
            with open(file_path, "a") as file_desc:
                file_desc.write(command)
        except(IOError, ValueError) as err_msg:
            LOG.exception("Error for make long command file: ", err_msg)
        return sh_file_name, file_path


##############################################################################
##############################################################################

@Plugin(type=Plugin.DRIVER, id=DeviceTestType.hap_test)
class HapTestDriver(IDriver):
    """
    HapTest is a Test that runs a native test package on given device.
    """
    # test driver config
    config = None
    instrument_hap_file_suffix = '_ad.hap'
    result = ""

    def __init__(self):
        self.ability_name = ""
        self.package_name = ""
        self.activity_name = ""

    def __check_environment__(self, device_options):
        pass

    def __result__(self):
        return self.result if os.path.exists(self.result) else ""

    def __check_config__(self, config):
        pass

    def __execute__(self, request):
        try:
            self.config = request.config
            self.config.target_test_path = DEFAULT_TEST_PATH
            self.config.device = request.config.environment.devices[0]

            suite_file = request.root.source.source_file
            LOG.debug("Testsuite FilePath: %s" % suite_file)

            if not suite_file:
                LOG.error("test source '%s' not exists" %
                          request.root.source.source_string)
                return

            if not self.config.device:
                result = ResultManager(suite_file, self.config)
                result.set_is_coverage(False)
                result.make_empty_result_file(
                    "No test device is found. ")
                return

            package_name, ability_name = self._get_package_and_ability_name(
                suite_file)
            self.package_name = package_name
            self.ability_name = ability_name
            self.activity_name = "%s.MainAbilityShellActivity" % \
                                 self.package_name
            self.config.test_hap_out_path = \
                "/data/data/%s/files/test/result/" % self.package_name
            self.config.test_suite_timeout = TIME_OUT

            serial = request.config.device.__get_serial__()
            device_log_file = get_device_log_file(
                request.config.report_path,
                serial)

            with open(device_log_file, "a", encoding="UTF-8") as file_pipe:
                self.config.device.start_catch_device_log(file_pipe)
                self._init_junit_test()
                self._run_junit_test(suite_file)
        finally:
            self.config.device.stop_catch_device_log()

    def _init_junit_test(self):
        self.config.device.hdc_command("remount")
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mount -o rw,remount,rw /%s" % "system")

    def _run_junit_test(self, suite_file):
        filename = os.path.basename(suite_file)
        suitefile_target_test_path = self.config.test_hap_out_path
        junit_test_para = self._get_junit_test_para(filename, suite_file)
        is_coverage_test = True if self.config.coverage else False

        # push testsuite file
        self.config.device.push_file(suite_file, self.config.target_test_path)

        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = \
            resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dic, resource_dir,
                                               self.config.device)

        # execute testcase, especially self.config.test_hap_out_path
        install_result = self._install_hap(filename)
        result = ResultManager(suite_file, self.config)
        result.set_is_coverage(is_coverage_test)

        if install_result:
            return_message = self._execute_suitefile_junittest(
                filename,
                junit_test_para,
                suitefile_target_test_path)
            try:
                self.result = result.get_test_results(return_message)
            finally:
                self._unistall_hap(self.package_name)
        else:
            self.result = result.get_test_results("Error: install hap failed.")
            LOG.error("Error: install hap failed.")

        resource_manager.process_cleaner_data(resource_data_dic, resource_dir,
                                              self.config.device)

    def _get_junit_test_para(self, filename, suite_file):
        if not filename.endswith(self.instrument_hap_file_suffix):
            exec_class, exec_method, exec_level = get_java_test_para(
                self.config.testcase, self.config.testlevel)
            java_test_file = get_execute_java_test_files(suite_file)
            junit_test_para = self._get_hap_test_para(java_test_file,
                                                      exec_class,
                                                      exec_method,
                                                      exec_level)
        else:
            junit_test_para = get_execute_java_test_files(suite_file)
        return junit_test_para

    def _get_hap_test_para(self, java_test_file, exec_class, exec_method,
                           exec_level):
        hap_test_para = "%s%s#%s%s#%s%s#%s%s" % (
            ZunitConst.test_class, java_test_file,
            ZunitConst.exec_class, exec_class,
            ZunitConst.exec_method, exec_method,
            ZunitConst.exec_level, exec_level)

        if self.config.coverage:
            hap_test_para += "#%s" % ZunitConst.coverage_flag
        return hap_test_para

    def _execute_suitefile_junittest(self, filename, testpara,
                                     target_test_path):
        return_message = self._execute_hapfile_junittest(filename, testpara,
                                                         target_test_path)
        return return_message

    def _execute_hapfile_junittest(self, filename, testpara, target_test_path):
        _unlock_screen(self.config.device)
        _unlock_device(self.config.device)

        try:
            if not filename.endswith(self.instrument_hap_file_suffix):
                return_message = self.start_hap_activity(testpara)
                LOG.info("HAP Testcase is executing, please wait a moment...")
                if "Error" not in return_message:
                    self._check_hap_finished(target_test_path)
            else:
                return_message = self.start_instrument_hap_activity(testpara)
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = str(exception.args)

        _lock_screen(self.config.device)
        return return_message

    def _init_hap_device(self):
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.test_hap_out_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.test_hap_out_path)

    def _install_hap(self, filename):
        message = self.config.device.execute_shell_command(
            "bm install -p %s" % os.path.join(self.config.target_test_path,
                                              filename))
        message = str(message).rstrip()
        if message == "" or "Success" in message:
            return_code = True
            if message != "":
                LOG.info(message)
        else:
            return_code = False
            if message != "":
                LOG.warning(message)

        _sleep_according_to_result(return_code)
        return return_code

    def start_hap_activity(self, testpara):
        try:
            if not self.config.coverage:
                display_receiver = DisplayOutputReceiver()
                self.config.device.execute_shell_command(
                    "am start -S -n %s/%s --es param '%s'" %
                    (self.package_name,
                     self.activity_name,
                     testpara),
                    receiver=display_receiver,
                    timeout=self.config.test_suite_timeout,
                    retry=0)
            else:
                coverage_outpath = self.config.coverage_outpath
                strip_num = len(coverage_outpath.split(os.sep)) - 1
                display_receiver = DisplayOutputReceiver()
                self.config.device.execute_shell_command(
                    "cd %s; export GCOV_PREFIX=%s;" \
                    " export GCOV_PREFIX_STRIP=%d;" \
                    " am start -S -n %s/%s --es param %s" %
                    (self.config.target_test_path,
                     self.config.target_test_path,
                     strip_num,
                     self.package_name,
                     self.activity_name,
                     testpara),
                    receiver=display_receiver,
                    timeout=self.config.test_suite_timeout,
                    retry=0)

            _sleep_according_to_result(display_receiver.output)
            return_message = display_receiver.output
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = exception.args
        return return_message

    def start_instrument_hap_activity(self, testpara):
        from xdevice import Variables
        try:
            display_receiver = DisplayOutputReceiver()
            if not self.config.coverage:
                self.config.device.execute_shell_command(
                    "aa start -p %s -n %s -s AbilityTestCase %s -w %s" %
                    (self.package_name,
                     self.ability_name,
                     testpara,
                     str(self.config.test_suite_timeout)),
                    receiver=display_receiver,
                    timeout=self.config.test_suite_timeout,
                    retry=0)
            else:
                coverage_outpath = self.config.coverage_outpath
                strip_num = len(coverage_outpath.split(os.sep)) - 1
                self.config.device.execute_shell_command(
                    "cd %s; export GCOV_PREFIX=%s;"
                    " export GCOV_PREFIX_STRIP=%d;"
                    " aa start -p %s -n %s -s AbilityTestCase %s -w %s" %
                    (self.config.target_test_path,
                     self.config.target_test_path,
                     strip_num,
                     self.package_name,
                     self.ability_name,
                     testpara,
                     str(self.config.test_suite_timeout)),
                    receiver=display_receiver,
                    timeout=self.config.test_suite_timeout,
                    retry=0)
            _sleep_according_to_result(display_receiver.output)
            return_message = display_receiver.output
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = exception.args
        return return_message

    def _check_hap_finished(self, target_test_path):
        run_timeout = True
        sleep_duration = 3
        target_file = os.path.join(target_test_path,
                                   ZunitConst.jtest_status_filename)
        for _ in range(
                int(self.config.test_suite_timeout / (1000 * sleep_duration))):
            check_value = self.config.device.is_file_exist(target_file)
            LOG.info("%s state: %s", self.config.device.device_sn,
                     self.config.device.test_device_state.value)
            if not check_value:
                time.sleep(sleep_duration)
                continue
            run_timeout = False
            break
        if run_timeout:
            return_code = False
            error_message = "HAP Testcase executed timeout or exception, " \
                            "please check detail information from system log"
            LOG.error(error_message)
        else:
            return_code = True
            LOG.info("HAP Testcase executed finished")
        return return_code

    def _unistall_hap(self, package_name):
        return_message = self.config.device.execute_shell_command(
            "pm uninstall %s" % package_name)
        _sleep_according_to_result(return_message)
        return return_message

    @staticmethod
    def _get_package_and_ability_name(hap_filepath):
        package_name = ""
        ability_name = ""

        if os.path.exists(hap_filepath):
            filename = os.path.basename(hap_filepath)

            # unzip the hap file
            hap_bak_path = os.path.abspath(os.path.join(
                os.path.dirname(hap_filepath),
                "%s.bak" % filename))
            zf_desc = zipfile.ZipFile(hap_filepath)
            try:
                zf_desc.extractall(path=hap_bak_path)
            except RuntimeError as error:
                print(error)
            zf_desc.close()

            # verify config.json file
            app_profile_path = os.path.join(hap_bak_path, "config.json")
            if not os.path.exists(app_profile_path):
                print("file %s not exists" % app_profile_path)
                return package_name, ability_name

            if os.path.isdir(app_profile_path):
                print("%s is a folder, and not a file" % app_profile_path)
                return package_name, ability_name

            # get package_name and ability_name value.
            load_dict = {}
            with open(app_profile_path, 'r') as load_f:
                load_dict = json.load(load_f)
            profile_list = load_dict.values()
            for profile in profile_list:
                package_name = profile.get("package")
                if not package_name:
                    continue

                abilities = profile.get("abilities")
                for abilitie in abilities:
                    abilities_name = abilitie.get("name")
                    if abilities_name.startswith("."):
                        ability_name = package_name + abilities_name[
                            abilities_name.find("."):]
                    else:
                        ability_name = abilities_name
                    break
                break

            # delete hap_bak_path
            if os.path.exists(hap_bak_path):
                shutil.rmtree(hap_bak_path)
        else:
            print("file %s not exists" % hap_filepath)

        return package_name, ability_name


##############################################################################
##############################################################################
