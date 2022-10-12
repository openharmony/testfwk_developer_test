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

from pydoc import classname
import time
import os
import sys
import datetime
import xml.etree.ElementTree as ElementTree

from core.constants import SchedulerType
from xdevice import Plugin
from xdevice import get_plugin
from xdevice import platform_logger
from xdevice import Scheduler
from xdevice import DeviceTestType
from core.utils import get_build_output_path
from core.utils import scan_support_product
from core.utils import is_lite_product
from core.common import is_open_source_product
from core.command.parameter import Parameter
from core.command.distribute_execute import DbinderTest
from core.testcase.testcase_manager import TestCaseManager
from core.config.config_manager import UserConfigManager
from core.config.parse_parts_config import ParsePartsConfig
from core.config.resource_manager import ResourceManager

LOG = platform_logger("Run")


class Run(object):

    history_cmd_list = []
    
    @classmethod
    def get_history(self):
        return self.history_cmd_list

    def process_command_run(self, command, options):
        para = Parameter()
        test_type_list = para.get_testtype_list(options.testtype)
        if len(test_type_list) == 0:
            LOG.error("The testtype parameter is incorrect.")
            return
        options.testtype = test_type_list

        parser = ParsePartsConfig(options.productform)
        partname_list = parser.get_part_list(
            options.subsystem,
            options.testpart)
        options.partname_list = partname_list
        options.coverage_outpath = self.get_coverage_outpath(options)

        LOG.info("")
        LOG.info("------------------------------------")
        LOG.info("Input parameter:")
        LOG.info("productform   = %s" % options.productform)
        LOG.info("testtype      = %s" % str(options.testtype))
        LOG.info("subsystem     = %s" % str(options.subsystem))
        LOG.info("testpart      = %s" % str(options.testpart))
        LOG.info("testmodule    = %s" % options.testmodule)
        LOG.info("testsuit      = %s" % options.testsuit)
        LOG.info("testcase      = %s" % options.testcase)
        LOG.info("testlevel     = %s" % options.testlevel)
        LOG.info("testargs     = %s" % options.testargs)
        LOG.info("repeat     = %s" % options.repeat)
        LOG.info("retry         = %s" % options.retry)
        LOG.info("historylist   = %s" % options.historylist)
        LOG.info("runhistory   = %s" % options.runhistory)
        LOG.info("partname_list = %s" % str(options.partname_list))
        LOG.info("------------------------------------")
        LOG.info("")

        if not para.check_run_parameter(options):
            LOG.error("Input parameter is incorrect.")
            return
      
        current_time = datetime.datetime.now()
        #记录命令运行历史
        need_record_history = False
        cmd_record = {
            "time" : str(current_time),
            "raw_cmd" : options.current_raw_cmd,
            "result" : "unknown",
            "command": command,
            "options": options
        }
        if not ("-hl" in options.current_raw_cmd or "-rh" in options.current_raw_cmd \
            or "--retry" in options.current_raw_cmd):
            need_record_history = True

        #打印历史记录
        if options.historylist:
            print("The latest command history is: %d" % len(self.history_cmd_list))
            for index in range(0, len(self.history_cmd_list)):
                cmd_record = self.history_cmd_list[index]
                print("%d. [%s] - [%s]::[%s]" % (index + 1, cmd_record["time"], 
                      cmd_record["raw_cmd"], cmd_record["result"]))
            return
        #重新运行历史里的一条命令
        if options.runhistory > 0:
            #如果记录大于10则认为非法
            if options.runhistory > 10 or options.runhistory > len(self.history_cmd_list):
                print("input history command[%d] out of range:", options.runhistory)
                return
            cmd_record = self.history_cmd_list[options.runhistory - 1]
            print("run history command:", cmd_record["raw_cmd"])
            need_record_history = False
            command = cmd_record["command"]
            options = cmd_record["options"]

        if options.retry:
            if len(self.history_cmd_list) <= 0:
                LOG.info("No history command exsit")
                return
            history_cmd = self.history_cmd_list[-1]
            command = history_cmd["command"]
            options = history_cmd["options"]
            latest_report_path = os.path.join(
                sys.framework_root_dir, "reports/latest/summary_report.xml")
            tree = ElementTree.parse(latest_report_path)
            root = tree.getroot()
            has_failed_case = 0
            test_targets = {}
            fail_list = []
            for child in root:
                print(child.tag, ":", child.attrib)
                for grand in child:
                    print(grand.tag, ":", grand.attrib)
                    if grand.attrib["result"] == 'false':
                        fail_case = grand.attrib["classname"] + "#" + grand.attrib["name"]
                        fail_list.append(fail_case)
                        has_failed_case += 1
            test_targets["class"] = fail_list
            setattr(options, "testargs", test_targets)
            print("retry option:", options)
            if has_failed_case > 0:
                if not self._build_test_cases(options):
                    LOG.error("Build test cases failed.")
                    return
                scheduler = get_plugin(plugin_type=Plugin.SCHEDULER,
                                    plugin_id=SchedulerType.SCHEDULER)[0]
                scheduler.exec_command(command, options)
            else:
                LOG.info("No testcase to retry")
            return

        if not self._build_test_cases(options):
            LOG.error("Build test cases failed.")
            return

        if "actstest" in options.testtype:
            test_dict = self.get_acts_test_dict(options)
            options.testcases_path = self.get_acts_tests_out_path(options.productform)
            options.resource_path = self.get_acts_tests_out_path(options.productform)
        else:
            test_dict = self.get_test_dict(options)

        if not self._check_test_dictionary(test_dict):
            LOG.error("The test file list is empty.")
            return

        if ("distributedtest" in options.testtype and
                len(options.testtype) == 1):
            from core.command.distribute_utils import get_test_case
            from core.command.distribute_utils \
                import check_ditributetest_environment
            from core.command.distribute_utils import make_device_info_file
            from core.command.distribute_utils import make_reports

            local_time = time.localtime()
            create_time = time.strftime('%Y-%m-%d-%H-%M-%S', local_time)
            start_time = time.strftime('%Y-%m-%d %H:%M:%S', local_time)

            if not check_ditributetest_environment():
                return

            output_test = get_test_case(test_dict["CXX"])
            if not output_test:
                return

            result_rootpath = os.path.join(sys.framework_root_dir,
                "reports",
                create_time)

            log_path = os.path.join(result_rootpath, "log")
            tmp_path = os.path.join(result_rootpath, "temp")
            os.makedirs(log_path, exist_ok=True)
            os.makedirs(tmp_path, exist_ok=True)

            Scheduler.start_task_log(log_path)
            make_device_info_file(tmp_path)

            for case in output_test:
                agent_target_name = case["agent_target_name"]
                major_target_name = case["major_target_name"]
                manager = DbinderTest(result_rootpath, case["suits_dir"])
                manager.setUp()
                manager.test_distribute(major_target_name, agent_target_name, options)
                manager.tearDown()

            make_reports(result_rootpath, start_time)
            Scheduler.stop_task_logcat()
        else:
            options.testdict = test_dict
            options.target_outpath = self.get_target_out_path(
                options.productform)

            scheduler = get_plugin(plugin_type=Plugin.SCHEDULER,
                                   plugin_id=SchedulerType.SCHEDULER)[0]
            if scheduler is None:
                LOG.error("Can not find the scheduler plugin.")
            else:
                if is_lite_product(options.productform,
                                   sys.source_code_root_path):
                    options.testcases_path = options.target_outpath
                    options.resource_path = os.path.abspath(os.path.join(
                        sys.framework_root_dir, "..", "resource"))
                    if options.productform.find("wifiiot") != -1:
                        scheduler.update_test_type_in_source(".bin",
                            DeviceTestType.ctest_lite)
                        scheduler.update_ext_type_in_source("BIN",
                            DeviceTestType.ctest_lite)
                    else:
                        print("productform is not wifiiot")
                scheduler.exec_command(command, options)
        if need_record_history:
            #读文件获取运行结果
            latest_report_path = os.path.join(sys.framework_root_dir, "reports/latest/summary_report.xml")
            with open(latest_report_path) as report_file:
                for report_line in report_file:
                    if "testsuites name=\"summary_report\"" in report_line:
                        result = report_line.replace("\n", "")
                        result = result.replace("<testsuites name=\"summary_report\" ", "")
                        result = result.replace(">", "")
                        cmd_record["result"] = result
                        break
            if len(self.history_cmd_list) >= 10:
                del self.history_cmd_list[0]
            self.history_cmd_list.append(cmd_record)
        print("-------------run end: ", self.history_cmd_list)
        return

    ##############################################################
    ##############################################################

    @classmethod
    def get_target_out_path(cls, product_form):
        target_out_path = UserConfigManager().get_test_cases_dir()
        if target_out_path == "":
            target_out_path = os.path.join(
                get_build_output_path(product_form),
                "packages",
                product_form)
        target_out_path = os.path.abspath(target_out_path)
        return target_out_path

    @classmethod
    def _build_test_cases(cls, options):
        if options.coverage:
            LOG.info("Coverage testing, no need to compile testcases")
            return True

        is_build_testcase = UserConfigManager().get_user_config_flag(
            "build", "testcase")
        project_root_path = sys.source_code_root_path
        if is_build_testcase and project_root_path != "":
            from core.build.build_manager import BuildManager
            build_manager = BuildManager()
            return build_manager.build_testcases(project_root_path, options)
        else:
            return True

    @classmethod
    def _check_test_dictionary(cls, test_dictionary):
        is_valid_status = False
        key_list = sorted(test_dictionary.keys())
        for key in key_list:
            file_list = test_dictionary[key]
            if len(file_list) > 0:
                is_valid_status = True
                break
        return is_valid_status

    @classmethod
    def get_tests_out_path(cls, product_form):
        testcase_path = UserConfigManager().get_test_cases_dir()
        if testcase_path == "":
            all_product_list = scan_support_product()
            if product_form in all_product_list:
                if is_open_source_product(product_form):
                    testcase_path = os.path.abspath(os.path.join(
                        get_build_output_path(product_form),
                        "packages",
                        "phone",
                        "tests"))
                else:
                    testcase_path = os.path.abspath(os.path.join(
                        get_build_output_path(product_form),
                        "packages",
                        product_form,
                        "tests"))
            else:
                testcase_path = os.path.join(
                    get_build_output_path(product_form), "tests")
        LOG.info("testcase_path=%s" % testcase_path)
        return testcase_path

    @classmethod
    def get_acts_tests_out_path(cls, product_form):
        acts_testcase_path = os.path.abspath(os.path.join(
            get_build_output_path(product_form),
            "suites",
            "acts",
            "testcases"))
        LOG.info("acts_testcase_path=%s" % acts_testcase_path)
        return acts_testcase_path

    @classmethod
    def get_coverage_outpath(cls, options):
        coverage_out_path = ""
        if options.coverage:
            coverage_out_path = get_build_output_path(options.productform)
            if coverage_out_path == "":
                coverage_out_path = UserConfigManager().get_user_config(
                    "coverage").get("outpath", "")
            if coverage_out_path == "":
                LOG.error("Coverage test: coverage_outpath is empty.")
        return coverage_out_path

    def get_acts_test_dict(self, options):
        # 获取测试用例编译结果路径
        acts_test_case_path = self.get_acts_tests_out_path(options.productform)
        acts_test_dict = TestCaseManager().get_acts_test_files(acts_test_case_path, options)
        return acts_test_dict

    def get_test_dict(self, options):
        # 获取测试用例编译结果路径
        test_case_path = self.get_tests_out_path(options.productform)
        if not os.path.exists(test_case_path):
            LOG.error("%s is not exist." % test_case_path)
            return

        test_dict = TestCaseManager().get_test_files(test_case_path, options)
        return test_dict


