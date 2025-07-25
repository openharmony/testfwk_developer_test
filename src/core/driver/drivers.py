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

import json
import os
import re
import shutil
import subprocess
import sys
import time
import platform
import zipfile
import stat
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from json import JSONDecodeError

from xdevice import DeviceTestType, check_result_report
from xdevice import DeviceLabelType
from xdevice import CommonParserType
from xdevice import ExecuteTerminate
from xdevice import DeviceError
from xdevice import ShellHandler

from xdevice import IDriver
from xdevice import platform_logger
from xdevice import Plugin
from xdevice import get_plugin
from ohos.environment.dmlib import process_command_ret
from core.utils import get_decode
from core.utils import get_fuzzer_path
from core.config.resource_manager import ResourceManager
from core.config.config_manager import FuzzerConfigManager

__all__ = [
    "CppTestDriver",
    "JSUnitTestDriver",
    "disable_keyguard",
    "GTestConst"]

LOG = platform_logger("Drivers")
DEFAULT_TEST_PATH = "/%s/%s/" % ("data", "test")
OBJ = "obj"
_ACE_LOG_MARKER = " a0c0d0"
TIME_OUT = 900 * 1000
JS_TIMEOUT = 10
CYCLE_TIMES = 50

FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL
MODES = stat.S_IWUSR | stat.S_IRUSR


class CollectingOutputReceiver:
    def __init__(self):
        self.output = ""

    def __read__(self, output):
        self.output = "%s%s" % (self.output, output)

    def __error__(self, message):
        pass

    def __done__(self, result_code="", message=""):
        pass


class DisplayOutputReceiver:
    def __init__(self):
        self.output = ""
        self.unfinished_line = ""

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


@dataclass
class GTestConst(object):
    exec_para_filter = "--gtest_filter"
    exec_para_level = "--gtest_testsize"
    exec_acts_para_filter = "--jstest_filter"
    exec_acts_para_level = "--jstest_testsize"


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
        level_para_string = f"{level_para_string}Level{item},"
    level_para_string = level_para_string.strip(",")
    return level_para_string


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


def get_test_log_savepath(result_rootpath, result_suit_path):
    suit_path = result_suit_path.split("result")[-1].strip(os.sep).split(os.sep)[0]
    test_log_path = os.path.join(result_rootpath, "log", "test_log", suit_path)

    if not os.path.exists(test_log_path):
        os.makedirs(test_log_path)

    LOG.info("test_log_savepath = {}".format(test_log_path))
    return test_log_path


def update_xml(suite_file, result_xml):
    suite_path_txt = suite_file.split(".")[0] + "_path.txt"
    if os.path.exists(suite_path_txt) and os.path.exists(result_xml):
        with open(suite_path_txt, "r") as path_text:
            line = path_text.readline().replace("//", "").strip()
        tree = ET.parse(result_xml)
        tree.getroot().attrib["path"] = line
        tree.getroot().attrib["name"] = os.path.basename(suite_file.split(".")[0])

        test_suit = os.path.basename(result_xml).split(".")[0]
        log_path = os.path.abspath(result_xml).split("result")[0]
        crash_path = os.path.join(log_path, "log", test_suit)
        all_items = os.listdir(crash_path)

        # 筛选以crash开头的目录
        matching_dirs = [os.path.join(crash_path, item) for item in all_items if
                         os.path.isdir(os.path.join(crash_path, item))
                         and item.startswith(f"crash_log_{test_suit}")]
        if len(matching_dirs) >= 1:
            tree.getroot().attrib["is_crash"] = "1"
        tree.write(result_xml)


def remove_color_codes(text):
    """
    color ascii to utf-8
    Args:
         text:
        
    Returns:

    """
    return text.encode('unicode_escape').decode('utf-8')


# all testsuit common Unavailable test result xml
def _create_empty_result_file(filepath, filename, error_message):
    error_message = remove_color_codes(error_message)
    error_message = error_message.replace("\"", "")
    error_message = error_message.replace("<", "")
    error_message = error_message.replace(">", "")
    error_message = error_message.replace("&", "")
    if filename.endswith(".hap"):
        filename = filename.split(".")[0]
    if not os.path.exists(filepath):
        with os.fdopen(os.open(filepath, FLAGS, MODES), 'w') as file_desc:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime())
            file_desc.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file_desc.write(
                '<testsuites tests="0" failures="0" '
                'disabled="0" errors="0" timestamp="%s" '
                'time="0" name="%s" unavailable="1">\n' % (time_stamp, filename))
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


def _create_fuzz_crash_file(filepath, filename):
    if not os.path.exists(filepath):
        with os.fdopen(os.open(filepath, FLAGS, MODES), 'w') as file_desc:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime())
            file_desc.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file_desc.write(
                '<testsuites disabled="0" name="%s" '
                'time="300" timestamp="%s" errors="0" '
                'failures="1" tests="1">\n' % (filename, time_stamp))
            file_desc.write(
                '  <testsuite disabled="0" name="%s" time="300" '
                'errors="0" failures="1" tests="1">\n' % filename)
            file_desc.write(
                '    <testcase name="%s" time="300" classname="%s" '
                'status="run">\n' % (filename, filename))
            file_desc.write(
                '      <failure type="" '
                'message="Fuzzer crash. See ERROR in log file">\n')
            file_desc.write('      </failure>\n')
            file_desc.write('    </testcase>\n')
            file_desc.write('  </testsuite>\n')
            file_desc.write('</testsuites>\n')
    return


def _create_fuzz_pass_file(filepath, filename):
    if not os.path.exists(filepath):
        with os.fdopen(os.open(filepath, FLAGS, MODES), 'w') as file_desc:
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime())
            file_desc.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file_desc.write(
                '<testsuites disabled="0" name="%s" '
                'time="300" timestamp="%s" errors="0" '
                'failures="0" tests="1">\n' % (filename, time_stamp))
            file_desc.write(
                '  <testsuite disabled="0" name="%s" time="300" '
                'errors="0" failures="0" tests="1">\n' % filename)
            file_desc.write(
                '    <testcase name="%s" time="300" classname="%s" '
                'status="run"/>\n' % (filename, filename))
            file_desc.write('  </testsuite>\n')
            file_desc.write('</testsuites>\n')
    return


def _create_fuzz_result_file(filepath, filename, error_message):
    error_message = str(error_message)
    error_message = error_message.replace("\"", "")
    error_message = error_message.replace("<", "")
    error_message = error_message.replace(">", "")
    error_message = error_message.replace("&", "")
    if "AddressSanitizer" in error_message:
        LOG.error("FUZZ TEST CRASH")
        _create_fuzz_crash_file(filepath, filename)
    elif re.search(r'Done (\b\d+\b) runs in (\b\d+\b) second',
                   error_message, re.M) is not None:
        LOG.info("FUZZ TEST PASS")
        _create_fuzz_pass_file(filepath, filename)
    else:
        LOG.error("FUZZ TEST UNAVAILABLE")
        _create_empty_result_file(filepath, filename, error_message)
    return


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
        filepath, _ = self.obtain_test_result_file()
        if "fuzztest" == self.config.testtype[0]:
            LOG.info("create fuzz test report")
            _create_fuzz_result_file(filepath, self.testsuite_name,
                                     error_message)
            if not self.is_coverage:
                self._obtain_fuzz_corpus()

        if not os.path.exists(filepath):
            _create_empty_result_file(filepath, self.testsuite_name,
                                      error_message)
        if "benchmark" == self.config.testtype[0]:
            self._obtain_benchmark_result()
        # Get coverage data files
        if self.is_coverage:
            self.obtain_coverage_data()

        return filepath

    def get_test_results_hidelog(self, error_message=""):
        # Get test result files
        result_file_path, test_log_path = self.obtain_test_result_file()
        log_content = ""
        if not error_message:
            if os.path.exists(test_log_path):
                with open(test_log_path, "r") as log:
                    log_content = log.readlines()
            else:
                LOG.error("{}: Test log not exist.".format(test_log_path))
        else:
            log_content = error_message

        if "fuzztest" == self.config.testtype[0]:
            LOG.info("create fuzz test report")
            _create_fuzz_result_file(result_file_path, self.testsuite_name,
                                     log_content)
            if not self.is_coverage:
                self._obtain_fuzz_corpus()

        if not os.path.exists(result_file_path):
            _create_empty_result_file(result_file_path, self.testsuite_name,
                                      log_content)
        if "benchmark" == self.config.testtype[0]:
            self._obtain_benchmark_result()
        # Get coverage data files
        if self.is_coverage:
            self.obtain_coverage_data()

        return result_file_path

    def get_result_sub_save_path(self):
        find_key = os.sep + "benchmark" + os.sep
        file_dir, _ = os.path.split(self.testsuite_path)
        pos = file_dir.find(find_key)
        subpath = ""
        if -1 != pos:
            subpath = file_dir[pos + len(find_key):]
        LOG.info("subpath = " + subpath)
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

        if self.config.testtype[0] != "fuzztest":
            if self.device.is_file_exist(remote_result_file):
                self.device.pull_file(remote_result_file, result_file_path)
            elif self.device.is_file_exist(remote_json_result_file):
                self.device.pull_file(remote_json_result_file,
                                      result_josn_file_path)
                result_file_path = result_josn_file_path
            else:
                LOG.info("%s not exist", remote_result_file)

        if self.config.hidelog:
            remote_log_result_file = os.path.join(self.device_testpath,
                                                  "%s.log" % self.testsuite_name)
            test_log_save_path = get_test_log_savepath(self.result_rootpath, result_save_path)
            test_log_file_path = os.path.join(test_log_save_path,
                                              "%s.log" % self.testsuite_name)
            self.device.pull_file(remote_log_result_file, test_log_file_path)
            return result_file_path, test_log_file_path

        return result_file_path, ""

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


        tests_path = self.config.testcases_path
        test_type = self.testsuite_path.split(tests_path)[1].strip(os.sep).split(os.sep)[0]
        cxx_cov_path = os.path.abspath(os.path.join(
            self.result_rootpath,
            "..",
            "coverage",
            "data",
            "cxx",
            self.testsuite_name + '_' + test_type))

        if os.path.basename(self.testsuite_name).startswith("rust_"):
            target_name = "lib.unstripped"
        else:
            target_name = OBJ
        if self.is_exist_target_in_device(DEFAULT_TEST_PATH, target_name):
            if not os.path.exists(cxx_cov_path):
                os.makedirs(cxx_cov_path)
            else:
                cxx_cov_path = cxx_cov_path + f"_{str(int(time.time()))}"
            self.config.device.execute_shell_command(
                "cd %s; tar -czf %s.tar.gz %s" % (DEFAULT_TEST_PATH, target_name, target_name))
            src_file_tar = os.path.join(DEFAULT_TEST_PATH, "%s.tar.gz" % target_name)
            self.device.pull_file(src_file_tar, cxx_cov_path, is_create=True, timeout=TIME_OUT)
            tar_path = os.path.join(cxx_cov_path, "%s.tar.gz" % target_name)
            if platform.system() == "Windows":
                process = subprocess.Popen("tar -zxf %s -C %s" % (tar_path, cxx_cov_path), shell=True)
                process.communicate()
                os.remove(tar_path)
                os.rename(os.path.join(cxx_cov_path, target_name), os.path.join(cxx_cov_path, OBJ))
            else:
                subprocess.Popen("tar -zxf %s -C %s > /dev/null 2>&1" %
                                 (tar_path, cxx_cov_path), shell=True).communicate()
                subprocess.Popen("rm -rf %s" % tar_path, shell=True).communicate()
                if target_name != OBJ:
                    subprocess.Popen("mv %s %s" % (os.path.join(cxx_cov_path, target_name),
                                                   os.path.join(cxx_cov_path, OBJ)), shell=True).communicate()
    
    def _obtain_fuzz_corpus(self):
        command = f"cd {DEFAULT_TEST_PATH}; tar czf {self.testsuite_name}_corpus.tar.gz corpus;"
        self.config.device.execute_shell_command(command)
        result_save_path = get_result_savepath(self.testsuite_path, self.result_rootpath)
        LOG.info(f"fuzz_dir = {result_save_path}")
        self.device.pull_file(f"{DEFAULT_TEST_PATH}/{self.testsuite_name}_corpus.tar.gz", result_save_path)

    def _obtain_benchmark_result(self):
        benchmark_root_dir = os.path.abspath(
            os.path.join(self.result_rootpath, "benchmark"))
        benchmark_dir = os.path.abspath(
            os.path.join(benchmark_root_dir,
                         self.get_result_sub_save_path(),
                         self.testsuite_name))

        if not os.path.exists(benchmark_dir):
            os.makedirs(benchmark_dir)

        LOG.info("benchmark_dir = %s" % benchmark_dir)
        self.device.pull_file(os.path.join(self.device_testpath,
                                           "%s.json" % self.testsuite_name), benchmark_dir)
        if not os.path.exists(os.path.join(benchmark_dir,
                                           "%s.json" % self.testsuite_name)):
            os.rmdir(benchmark_dir)
        return benchmark_dir


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
                
            self.config.device.set_device_report_path(request.config.report_path)
            if request.config.hilogswitch != "0":
                self.config.device.device_log_collector.start_hilog_task()
            self._init_gtest()
            self._run_gtest(suite_file)

        finally:
            log_path = get_result_savepath(request.root.source.source_file, request.config.report_path)
            suit_name = os.path.basename(request.root.source.source_file)
            xml_path = os.path.join(log_path, f"{suit_name}.xml")
            if not os.path.exists(xml_path):
                _create_empty_result_file(xml_path, suit_name, "ERROR")
            serial = "{}_{}".format(str(request.config.device.__get_serial__()), time.time_ns())
            log_tar_file_name = "{}_{}".format(request.get_module_name(), str(serial).replace(
                ":", "_"))
            try:
                if request.config.hilogswitch != "0":
                    self.config.device.device_log_collector.stop_hilog_task(
                        log_tar_file_name, module_name=request.get_module_name())
            finally:
                update_xml(request.root.source.source_file, xml_path)

    @staticmethod
    def _alter_init(name):
        with open(name, "rb") as f:
            lines = f.read()
        str_content = lines.decode("utf-8")

        pattern_sharp = '^\s*#.*$(\n|\r\n)'
        pattern_star = '/\*.*?\*/(\n|\r\n)+'
        pattern_xml = '<!--[\s\S]*?-->(\n|\r\n)+'

        if re.match(pattern_sharp, str_content, flags=re.M):
            striped_content = re.sub(pattern_sharp, '', str_content, flags=re.M)
        elif re.findall(pattern_star, str_content, flags=re.S):
            striped_content = re.sub(pattern_star, '', str_content, flags=re.S)
        elif re.findall(pattern_xml, str_content, flags=re.S):
            striped_content = re.sub(pattern_xml, '', str_content, flags=re.S)
        else:
            striped_content = str_content

        striped_bt = striped_content.encode("utf-8")
        if os.path.exists(name):
            os.remove(name)
        with os.fdopen(os.open(name, FLAGS, MODES), 'wb') as f:
            f.write(striped_bt)

    def _init_gtest(self):
        self.config.device.connector_command("target mount")
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mount -o rw,remount,rw /")
        if "fuzztest" == self.config.testtype[0]:
            self.config.device.execute_shell_command(
                "mkdir -p %s" % os.path.join(self.config.target_test_path,
                                             "corpus"))

    def _gtest_command(self, suite_file):
        filename = os.path.basename(suite_file)
        test_para = self._get_test_para(self.config.testcase,
                                        self.config.testlevel,
                                        self.config.testtype,
                                        self.config.target_test_path,
                                        suite_file,
                                        filename,
                                        self.config.iteration)

        # execute testcase
        if not self.config.coverage:
            if self.config.random == "random":
                seed = random.randint(1, 100)
                command = "cd %s; rm -rf %s.xml; chmod +x *; ./%s %s --gtest_shuffle --gtest_random_seed=%d" % (
                    self.config.target_test_path,
                    filename,
                    filename,
                    test_para,
                    seed)
            else:
                command = "cd %s; rm -rf %s.xml; chmod +x *; ./%s %s" % (
                    self.config.target_test_path,
                    filename,
                    filename,
                    test_para)
        else:
            coverage_outpath = self.config.coverage_outpath
            if coverage_outpath:
                strip_num = len(coverage_outpath.strip("/").split("/"))
            else:
                ohos_config_path = os.path.join(sys.source_code_root_path, "out", "ohos_config.json")
                with open(ohos_config_path, 'r') as json_file:
                    json_info = json.load(json_file)
                    out_path = json_info.get("out_path")
                strip_num = len(out_path.strip("/").split("/"))
            if "fuzztest" == self.config.testtype[0]:
                self._push_corpus_cov_if_exist(suite_file)
                command = f"cd {self.config.target_test_path}; tar zxf {filename}_corpus.tar.gz; \
                                        rm -rf {filename}.xml; chmod +x *; GCOV_PREFIX={DEFAULT_TEST_PATH}; \
                                        GCOV_PREFIX_STRIP={strip_num} ./{filename} {test_para}"
            else:
                command = "cd %s; rm -rf %s.xml; chmod +x *; GCOV_PREFIX=%s " \
                          "GCOV_PREFIX_STRIP=%s ./%s %s" % \
                          (self.config.target_test_path,
                           filename,
                           DEFAULT_TEST_PATH,
                           str(strip_num),
                           filename,
                           test_para)

        if self.config.hidelog:
            command += " > {}.log 2>&1".format(filename)

        return command

    def _run_gtest(self, suite_file):
        from xdevice import Variables
        is_coverage_test = True if self.config.coverage else False

        # push testsuite file
        self.config.device.push_file(suite_file, self.config.target_test_path)
        self.config.device.execute_shell_command(
            "hilog -d %s" % (os.path.join(self.config.target_test_path,
                                          os.path.basename(suite_file)))
        )
        self._push_corpus_if_exist(suite_file)

        # push resource files
        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dic, resource_dir,
                                               self.config.device)

        command = self._gtest_command(suite_file)

        result = ResultManager(suite_file, self.config)
        result.set_is_coverage(is_coverage_test)

        try:
            # get result
            if self.config.hidelog:
                return_message = ""
                display_receiver = CollectingOutputReceiver()
                self.config.device.execute_shell_command(
                    command,
                    receiver=display_receiver,
                    timeout=TIME_OUT,
                    retry=0)
            else:
                display_receiver = DisplayOutputReceiver()
                self.config.device.execute_shell_command(
                    command,
                    receiver=display_receiver,
                    timeout=TIME_OUT,
                    retry=0)
                return_message = display_receiver.output
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = str(exception.args)

        if self.config.hidelog:
            self.result = result.get_test_results_hidelog(return_message)
        else:
            self.result = result.get_test_results(return_message)

        resource_manager.process_cleaner_data(resource_data_dic,
                                              resource_dir,
                                              self.config.device)

    def _push_corpus_cov_if_exist(self, suite_file):
        corpus_path = suite_file.split("fuzztest")[-1].strip(os.sep)
        cov_file = os.path.join(
            sys.framework_root_dir, "reports", "latest_corpus", corpus_path + "_corpus.tar.gz")
        LOG.info("corpus_cov file :%s" % str(cov_file))
        self.config.device.push_file(cov_file, os.path.join(self.config.target_test_path))

    def _push_corpus_if_exist(self, suite_file):
        if "fuzztest" == self.config.testtype[0]:
            corpus_path = os.path.join(get_fuzzer_path(suite_file), "corpus")
            if not os.path.isdir(corpus_path):
                return

            corpus_dirs = []
            corpus_file_list = []

            for root, _, files in os.walk(corpus_path):
                if not files:
                    continue

                corpus_dir = root.split("corpus")[-1]
                if corpus_dir != "":
                    corpus_dirs.append(corpus_dir)

                for file in files:
                    cp_file = os.path.normcase(os.path.join(root, file))
                    corpus_file_list.append(cp_file)
                    if file == "init":
                        self._alter_init(cp_file)

            # mkdir corpus files dir
            if corpus_dirs:
                for corpus in corpus_dirs:
                    mkdir_corpus_command = f"shell; mkdir -p {corpus}"
                    self.config.device.connector_command(mkdir_corpus_command)

            # push corpus file
            if corpus_file_list:
                for corpus_file in corpus_file_list:
                    self.config.device.push_file(corpus_file,
                                                 os.path.join(self.config.target_test_path, "corpus"))

    def _get_test_para(self,
                       testcase,
                       testlevel,
                       testtype,
                       target_test_path,
                       suite_file,
                       filename,
                       iteration):
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

        if iteration:
            test_para += f" --gtest_repeat={iteration}"

        if "fuzztest" == testtype[0]:
            cfg_list = FuzzerConfigManager(os.path.join(get_fuzzer_path(
                suite_file), "project.xml")).get_fuzzer_config("fuzztest")
            LOG.info("config list :%s" % str(cfg_list))
            if self.config.coverage:
                test_para += "corpus -runs=0" + \
                             " -max_len=" + cfg_list[0] + \
                             " -max_total_time=" + cfg_list[1] + \
                             " -rss_limit_mb=" + cfg_list[2]
            else:
                test_para += "corpus -max_len=" + cfg_list[0] + \
                             " -max_total_time=" + cfg_list[1] + \
                             " -rss_limit_mb=" + cfg_list[2]

        return test_para


@Plugin(type=Plugin.DRIVER, id=DeviceTestType.jsunit_test)
class JSUnitTestDriver(IDriver):
    """
    JSUnitTestDriver is a Test that runs a native test package on given device.
    """

    def __init__(self):
        self.config = None
        self.result = ""
        self.start_time = None
        self.ability_name = ""
        self.package_name = ""
        # log
        self.hilog = None
        self.hilog_proc = None
    
    def __check_environment__(self, device_options):
        pass

    def __check_config__(self, config):
        pass

    def __result__(self):
        return self.result if os.path.exists(self.result) else ""

    def __execute__(self, request):
        try:
            LOG.info("developer_test driver")
            self.config = request.config
            self.config.target_test_path = DEFAULT_TEST_PATH
            self.config.device = request.config.environment.devices[0]

            suite_file = request.root.source.source_file
            result_save_path = get_result_savepath(suite_file, self.config.report_path)
            self.result = os.path.join(result_save_path, "%s.xml" % request.get_module_name())
            if not suite_file:
                LOG.error("test source '%s' not exists" %
                          request.root.source.source_string)
                return

            if not self.config.device:
                result = ResultManager(suite_file, self.config)
                result.set_is_coverage(False)
                result.make_empty_result_file(
                    "No test device is found")
                return

            package_name, ability_name = self._get_package_and_ability_name(
                suite_file)
            self.package_name = package_name
            self.ability_name = ability_name
            self.config.test_hap_out_path = \
                "/data/data/%s/files/" % self.package_name
            self.config.device.connector_command("shell hilog -r")

            self.hilog = get_device_log_file(
                request.config.report_path,
                request.config.device.__get_serial__() + "_" + request.
                get_module_name(),
                "device_hilog")

            hilog_open = os.open(self.hilog, os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                                 0o755)

            with os.fdopen(hilog_open, "a") as hilog_file_pipe:
                self.config.device.device_log_collector.add_log_address(None, self.hilog)
                _, self.hilog_proc = self.config.device.device_log_collector.\
                    start_catch_device_log(hilog_file_pipe=hilog_file_pipe)
                self._init_jsunit_test()
                self._run_jsunit(suite_file, self.hilog)
                hilog_file_pipe.flush()
                self.generate_console_output(self.hilog, request)
                xml_path = os.path.join(
                    request.config.report_path, "result",
                    '.'.join((request.get_module_name(), "xml")))
                shutil.move(xml_path, self.result)
        finally:
            self.config.device.device_log_collector.remove_log_address(None, self.hilog)
            self.config.device.device_log_collector.stop_catch_device_log(self.hilog_proc)
            update_xml(request.root.source.source_file, self.result)

    @staticmethod
    def _get_acts_test_para(testcase,
                            testlevel,
                            testtype,
                            target_test_path,
                            suite_file,
                            filename):
        if "actstest" == testtype[0]:
            test_para = (" --actstest_out_format=json"
                         " --actstest_out=%s%s.json") % (
                            target_test_path, filename)
            return test_para

        if "" != testcase and "" == testlevel:
            test_para = "%s=%s" % (GTestConst.exec_acts_para_filter, testcase)
        elif "" == testcase and "" != testlevel:
            level_para = get_level_para_string(testlevel)
            test_para = "%s=%s" % (GTestConst.exec_acts_para_level, level_para)
        else:
            test_para = ""
        return test_para

    @staticmethod
    def _get_hats_test_para(testcase,
                            testlevel,
                            testtype,
                            target_test_path,
                            suite_file,
                            filename):
        if "hatstest" == testtype[0]:
            test_hats_para = (" --hatstest_out_format=json"
                         " --hatstest_out=%s%s.json") % (
                            target_test_path, filename)
            return test_hats_para

        if "" != testcase and "" == testlevel:
            test_hats_para = "%s=%s" % (GTestConst.exec_para_filter, testcase)
        elif "" == testcase and "" != testlevel:
            level_para = get_level_para_string(testlevel)
            test_hats_para = "%s=%s" % (GTestConst.exec_para_level, level_para)
        else:
            test_hats_para = ""
        return test_hats_para

    @classmethod
    def _get_json_shell_timeout(cls, json_filepath):
        test_timeout = 0
        try:
            with open(json_filepath, 'r') as json_file:
                data_dic = json.load(json_file)
                if not data_dic:
                    return test_timeout
                else:
                    if "driver" in data_dic.keys():
                        driver_dict = data_dic.get("driver")
                        if driver_dict and "test-timeout" in driver_dict.keys():
                            test_timeout = int(driver_dict["shell-timeout"]) / 1000
                    return test_timeout
        except JSONDecodeError:
            return test_timeout
        finally:
            print(" get json shell timeout finally")

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
                print("Unzip error: ", hap_bak_path)
            zf_desc.close()

            # verify config.json file
            app_profile_path = os.path.join(hap_bak_path, "config.json")
            if not os.path.exists(app_profile_path):
                print("file %s not exist" % app_profile_path)
                return package_name, ability_name

            if os.path.isdir(app_profile_path):
                print("%s is a folder, and not a file" % app_profile_path)
                return package_name, ability_name

            # get package_name and ability_name value
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
            print("file %s not exist" % hap_filepath)
        return package_name, ability_name

    def generate_console_output(self, device_log_file, request):
        result_message = self.read_device_log(device_log_file)

        report_name = request.get_module_name()
        parsers = get_plugin(
            Plugin.PARSER, CommonParserType.jsunit)
        if parsers:
            parsers = parsers[:1]
        for listener in request.listeners:
            listener.device_sn = self.config.device.device_sn
        parser_instances = []

        for parser in parsers:
            parser_instance = parser.__class__()
            parser_instance.suites_name = report_name
            parser_instance.suite_name = report_name
            parser_instance.listeners = request.listeners
            parser_instances.append(parser_instance)
        handler = ShellHandler(parser_instances)
        process_command_ret(result_message, handler)

    def read_device_log(self, device_log_file):
        result_message = ""
        with open(device_log_file, "r", encoding='utf-8',
                  errors='ignore') as file_read_pipe:
            while True:
                data = file_read_pipe.readline()
                if not data:
                    break
                # only filter JSApp log
                if data.lower().find(_ACE_LOG_MARKER) != -1:
                    result_message += data
                    if data.find("[end] run suites end") != -1:
                        break
        return result_message

    def start_hap_execute(self):
        try:
            command = "aa start -d 123 -a %s.MainAbility -b %s" \
                      % (self.package_name, self.package_name)
            self.start_time = time.time()
            result_value = self.config.device.execute_shell_command(
                command, timeout=TIME_OUT)

            if "success" in str(result_value).lower():
                LOG.info("execute %s's testcase success. result value=%s"
                         % (self.package_name, result_value))
            else:
                LOG.info("execute %s's testcase failed. result value=%s"
                         % (self.package_name, result_value))

            _sleep_according_to_result(result_value)
            return_message = result_value
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = exception.args

        return return_message

    def _init_jsunit_test(self):
        self.config.device.connector_command("target mount")
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mount -o rw,remount,rw /")

    def _run_jsunit(self, suite_file, device_log_file):
        filename = os.path.basename(suite_file)
        _, suffix_name = os.path.splitext(filename)

        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = resource_manager.get_resource_data_dic(suite_file)
        if suffix_name == ".hap":
            json_file_path = suite_file.replace(".hap", ".json")
            if os.path.exists(json_file_path):
                timeout = self._get_json_shell_timeout(json_file_path)
            else:
                timeout = ResourceManager.get_nodeattrib_data(resource_data_dic)
        else:
            timeout = ResourceManager.get_nodeattrib_data(resource_data_dic)
        resource_manager.process_preparer_data(resource_data_dic, resource_dir, self.config.device)
        main_result = self._install_hap(suite_file)
        result = ResultManager(suite_file, self.config)
        if main_result:
            self._execute_hapfile_jsunittest()
            try:
                status = False
                actiontime = JS_TIMEOUT
                times = CYCLE_TIMES
                if timeout:
                    actiontime = timeout
                    times = 1
                with open(device_log_file, "r", encoding='utf-8',
                          errors='ignore') as file_read_pipe:
                    for i in range(0, times):
                        if status:
                            break
                        else:
                            time.sleep(float(actiontime))
                        start_time = int(time.time())
                        while True:
                            data = file_read_pipe.readline()
                            if data.lower().find(_ACE_LOG_MARKER) != -1 and data.find("[end] run suites end") != -1:
                                LOG.info("execute testcase successfully.")
                                status = True
                                break
                            if int(time.time()) - start_time > 5:
                                break
            finally:
                _lock_screen(self.config.device)
                self._uninstall_hap(self.package_name)
        else:
            self.result = result.get_test_results("Error: install hap failed")
            LOG.error("Error: install hap failed")

        resource_manager.process_cleaner_data(resource_data_dic, resource_dir, self.config.device)

    def _execute_hapfile_jsunittest(self):
        _unlock_screen(self.config.device)
        _unlock_device(self.config.device)

        try:
            return_message = self.start_hap_execute()
        except (ExecuteTerminate, DeviceError) as exception:
            return_message = str(exception.args)

        return return_message

    def _install_hap(self, suite_file):
        message = self.config.device.connector_command("install %s" % suite_file)
        message = str(message).rstrip()
        if message == "" or "success" in message:
            return_code = True
            if message != "":
                LOG.info(message)
        else:
            return_code = False
            if message != "":
                LOG.warning(message)

        _sleep_according_to_result(return_code)
        return return_code

    def _uninstall_hap(self, package_name):
        return_message = self.config.device.execute_shell_command(
            "bm uninstall -n %s" % package_name)
        _sleep_according_to_result(return_message)
        return return_message


@Plugin(type=Plugin.DRIVER, id=DeviceTestType.oh_rust_test)
class OHRustTestDriver(IDriver):
    def __init__(self):
        self.result = ""
        self.error_message = ""
        self.config = None

    def __check_environment__(self, device_options):
        pass

    def __check_config__(self, config):
        pass

    def __execute__(self, request):
        try:
            LOG.debug("Start to execute open harmony rust test")
            self.config = request.config
            self.config.device = request.config.environment.devices[0]
            self.config.target_test_path = DEFAULT_TEST_PATH
            suite_file = request.root.source.source_file
            LOG.debug("Testsuite filepath:{}".format(suite_file))

            if not suite_file:
                LOG.error("test source '{}' not exists".format(
                    request.root.source.source_string))
                return

            result_save_path = get_result_savepath(suite_file, self.config.report_path)
            self.result = os.path.join(result_save_path, "%s.xml" % request.get_module_name())
            self.config.device.set_device_report_path(request.config.report_path)
            self.config.device.device_log_collector.start_hilog_task()
            self._init_oh_rust()
            self._run_oh_rust(suite_file, request)
        except Exception as exception:
            self.error_message = exception
            if not getattr(exception, "error_no", ""):
                setattr(exception, "error_no", "03409")
            LOG.exception(self.error_message, exc_info=False, error_no="03409")
        finally:
            serial = "{}_{}".format(str(request.config.device.__get_serial__()),
                                    time.time_ns())
            log_tar_file_name = "{}_{}".format(
                request.get_module_name(), str(serial).replace(":", "_"))
            try:
                self.config.device.device_log_collector.stop_hilog_task(
                    log_tar_file_name, module_name=request.get_module_name())
            finally:
                xml_path = os.path.join(
                    request.config.report_path, "result",
                    '.'.join((request.get_module_name(), "xml")))
                shutil.move(xml_path, self.result)
                update_xml(request.root.source.source_file, self.result)
                self.result = check_result_report(
                    request.config.report_path, self.result, self.error_message)
    
    def __result__(self):
        return self.result if os.path.exists(self.result) else ""

    def _init_oh_rust(self):
        self.config.device.connector_command("target mount")
        self.config.device.execute_shell_command(
            "rm -rf %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mkdir -p %s" % self.config.target_test_path)
        self.config.device.execute_shell_command(
            "mount -o rw,remount,rw /")

    def _run_oh_rust(self, suite_file, request=None):
        self.config.device.push_file(suite_file, self.config.target_test_path)
        self.config.device.execute_shell_command(
            "hilog -d %s" % (os.path.join(self.config.target_test_path,
                                          os.path.basename(suite_file)))
        )
        resource_manager = ResourceManager()
        resource_data_dict, resource_dir = \
            resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dict,
                                               resource_dir,
                                               self.config.device)
        for listener in request.listeners:
            listener.device_sn = self.config.device.device_sn

        parsers = get_plugin(Plugin.PARSER, CommonParserType.oh_rust)
        if parsers:
            parsers = parsers[:1]
        parser_instances = []
        for parser in parsers:
            parser_instance = parser.__class__()
            parser_instance.suite_name = request.get_module_name()
            parser_instance.listeners = request.listeners
            parser_instances.append(parser_instance)
        handler = ShellHandler(parser_instances)
        if self.config.coverage:
            command = "cd {}; chmod +x *; GCOV_PREFIX=. ./{}".format(
                self.config.target_test_path, os.path.basename(suite_file))
        else:
            command = "cd {}; chmod +x *; ./{}".format(
                self.config.target_test_path, os.path.basename(suite_file))
        self.config.device.execute_shell_command(
            command, timeout=TIME_OUT, receiver=handler, retry=0)
        if self.config.coverage:
            result = ResultManager(suite_file, self.config)
            result.obtain_coverage_data()
        resource_manager.process_cleaner_data(resource_data_dict, resource_dir,
                                              self.config.device)
