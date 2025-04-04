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
import shutil
import stat
import time

from xdevice import ParamError
from xdevice import get_device_log_file
from xdevice import check_result_report
from xdevice import get_kit_instances
from xdevice import do_module_kit_setup
from xdevice import do_module_kit_teardown
from xdevice import get_config_value
from xdevice import Plugin
from xdevice import DeviceTestType
from xdevice import IDriver
from xdevice import get_plugin
from xdevice import CommonParserType
from xdevice import ShellHandler
from xdevice import ConfigConst
from xdevice import JsonParser
from xdevice import TestDescription
from xdevice import platform_logger

from ohos.constants import CKit
from ohos.executor.listener import CollectingPassListener
from core.driver.drivers import update_xml
from core.driver.drivers import get_result_savepath

__all__ = ["OHJSUnitTestDriver", "oh_jsunit_para_parse"]

LOG = platform_logger("Drivers")
TIME_OUT = 300 * 1000


def oh_jsunit_para_parse(runner, junit_paras):
    junit_paras = dict(junit_paras)
    test_type_list = ["function", "performance", "reliability", "security"]
    size_list = ["small", "medium", "large"]
    level_list = ["0", "1", "2", "3"]
    for para_name in junit_paras.keys():
        para_name = para_name.strip()
        para_values = junit_paras.get(para_name, [])
        if para_name == "class":
            runner.add_arg(para_name, ",".join(para_values))
        elif para_name == "notClass":
            runner.add_arg(para_name, ",".join(para_values))
        elif para_name == "testType":
            if para_values[0] not in test_type_list:
                continue
            # function/performance/reliability/security
            runner.add_arg(para_name, para_values[0])
        elif para_name == "size":
            if para_values[0] not in size_list:
                continue
            # size small/medium/large
            runner.add_arg(para_name, para_values[0])
        elif para_name == "level":
            if para_values[0] not in level_list:
                continue
            # 0/1/2/3/4
            runner.add_arg(para_name, para_values[0])
        elif para_name == "stress":
            runner.add_arg(para_name, para_values[0])


class OHJSUnitTestRunner:
    MAX_RETRY_TIMES = 3

    def __init__(self, config):
        self.arg_list = {}
        self.suites_name = None
        self.config = config
        self.rerun_attemp = 3
        self.suite_recorder = {}
        self.finished = False
        self.expect_tests_dict = dict()
        self.finished_observer = None
        self.retry_times = 1
        self.compile_mode = ""

    def dry_run(self):
        parsers = get_plugin(Plugin.PARSER, CommonParserType.oh_jsunit_list)
        if parsers:
            parsers = parsers[:1]
        parser_instances = []
        for parser in parsers:
            parser_instance = parser.__class__()
            parser_instances.append(parser_instance)
        handler = ShellHandler(parser_instances)
        command = self._get_dry_run_command()
        self.config.device.execute_shell_command(
            command, timeout=self.config.timeout, receiver=handler, retry=0)
        self.expect_tests_dict = parser_instances[0].tests_dict
        return parser_instances[0].tests

    def run(self, listener):
        handler = self._get_shell_handler(listener)
        command = self._get_run_command()
        self.config.device.execute_shell_command(
            command, timeout=self.config.timeout, receiver=handler, retry=0)

    def notify_finished(self):
        if self.finished_observer:
            self.finished_observer.notify_task_finished()
        self.retry_times -= 1

    def get_oh_test_runner_path(self):
        if self.compile_mode == "esmodule":
            return "/ets/testrunner/OpenHarmonyTestRunner"
        else:
            return "OpenHarmonyTestRunner"

    def add_arg(self, name, value):
        if not name or not value:
            return
        self.arg_list[name] = value

    def remove_arg(self, name):
        if not name:
            return
        if name in self.arg_list:
            del self.arg_list[name]

    def get_args_command(self):
        args_commands = ""
        for key, value in self.arg_list.items():
            if "wait_time" == key:
                args_commands = "%s -w %s " % (args_commands, value)
            else:
                args_commands = "%s -s %s %s " % (args_commands, key, value)
        return args_commands
    
    def _get_shell_handler(self, listener):
        parsers = get_plugin(Plugin.PARSER, CommonParserType.oh_jsunit)
        if parsers:
            parsers = parsers[:1]
        parser_instances = []
        for parser in parsers:
            parser_instance = parser.__class__()
            parser_instance.suites_name = self.suites_name
            parser_instance.listeners = listener
            parser_instance.runner = self
            parser_instances.append(parser_instance)
            self.finished_observer = parser_instance
        handler = ShellHandler(parser_instances)
        return handler

    def _get_run_command(self):
        command = ""
        if self.config.package_name:
            # aa test -p ${packageName} -b ${bundleName}-s
            # unittest OpenHarmonyTestRunner
            command = "aa test -p {} -b {} -s unittest OpenHarmonyTestRunner" \
                      " {}".format(self.config.package_name,
                                   self.config.bundle_name,
                                   self.get_args_command())
        elif self.config.module_name:
            #  aa test -m ${moduleName}  -b ${bundleName}
            #  -s unittest OpenHarmonyTestRunner
            command = "aa test -m {} -b {} -s unittest {} {}".format(
                self.config.module_name, self.config.bundle_name,
                self.get_oh_test_runner_path(), self.get_args_command())
        return command

    def _get_dry_run_command(self):
        command = ""
        if self.config.package_name:
            command = "aa test -p {} -b {} -s unittest OpenHarmonyTestRunner" \
                      " {} -s dryRun true".format(self.config.package_name,
                                                  self.config.bundle_name,
                                                  self.get_args_command())
        elif self.config.module_name:
            command = "aa test -m {} -b {} -s unittest {}" \
                      " {} -s dryRun true".format(self.config.module_name,
                                                  self.config.bundle_name,
                                                  self.get_oh_test_runner_path(),
                                                  self.get_args_command())

        return command


@Plugin(type=Plugin.DRIVER, id=DeviceTestType.oh_jsunit_test)
class OHJSUnitTestDriver(IDriver):
    """
    OHJSUnitTestDriver is a Test that runs a native test package on
    given device.
    """

    def __init__(self):
        self.timeout = 80 * 1000
        self.start_time = None
        self.result = ""
        self.error_message = ""
        self.kits = []
        self.config = None
        self.runner = None
        self.rerun = True
        self.rerun_all = True
        # log
        self.device_log = None
        self.hilog = None
        self.log_proc = None
        self.hilog_proc = None

    def __check_environment__(self, device_options):
        pass

    def __check_config__(self, config):
        pass

    def __execute__(self, request):
        try:
            LOG.debug("Developer_test Start execute OpenHarmony JSUnitTest")
            self.config = request.config
            self.config.device = request.config.environment.devices[0]

            config_file = request.root.source.config_file
            suite_file = request.root.source.source_file
            result_save_path = get_result_savepath(suite_file, self.config.report_path)
            self.result = os.path.join(result_save_path, "%s.xml" % request.get_module_name())
            if not suite_file:
                raise ParamError(
                    "test source '%s' not exists" %
                    request.root.source.source_string, error_no="00110")
            LOG.debug("Test case file path: %s" % suite_file)
            self.config.device.set_device_report_path(request.config.report_path)
            self.hilog = get_device_log_file(request.config.report_path,
                                        request.config.device.__get_serial__() + "_" + request.
                                        get_module_name(),
                                        "device_hilog")

            hilog_open = os.open(self.hilog, os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                                 0o755)
            self.config.device.device_log_collector.add_log_address(self.device_log, self.hilog)
            self.config.device.execute_shell_command(command="hilog -r")
            with os.fdopen(hilog_open, "a") as hilog_file_pipe:
                if hasattr(self.config, ConfigConst.device_log) \
                        and self.config.device_log.get(ConfigConst.tag_enable) == ConfigConst.device_log_on \
                        and hasattr(self.config.device, "clear_crash_log"):
                    self.config.device.device_log_collector.clear_crash_log()
                self.log_proc, self.hilog_proc = self.config.device.device_log_collector.\
                    start_catch_device_log(hilog_file_pipe=hilog_file_pipe)
                self._run_oh_jsunit(config_file, request)
        except Exception as exception:
            self.error_message = exception
            if not getattr(exception, "error_no", ""):
                setattr(exception, "error_no", "03409")
            LOG.exception(self.error_message, exc_info=True, error_no="03409")
            raise exception
        finally:
            try:
                self._handle_logs(request)
            finally:
                xml_path = os.path.join(
                    request.config.report_path, "result",
                    '.'.join((request.get_module_name(), "xml")))
                shutil.move(xml_path, self.result)
                self.result = check_result_report(
                    request.config.report_path, self.result, self.error_message)
                update_xml(request.root.source.source_file, self.result)

    def __result__(self):
        return self.result if os.path.exists(self.result) else ""

    def _run_oh_jsunit(self, config_file, request):
        try:
            if not os.path.exists(config_file):
                LOG.error("Error: Test cases don't exist %s." % config_file)
                raise ParamError(
                    "Error: Test cases don't exist %s." % config_file,
                    error_no="00102")
            json_config = JsonParser(config_file)
            self.kits = get_kit_instances(json_config,
                                          self.config.resource_path,
                                          self.config.testcases_path)

            self._get_driver_config(json_config)
            self.config.device.connector_command("target mount")
            self._start_smart_perf()
            do_module_kit_setup(request, self.kits)
            self.runner = OHJSUnitTestRunner(self.config)
            self.runner.suites_name = request.get_module_name()
            self._get_runner_config(json_config)
            if hasattr(self.config, "history_report_path") and \
                    self.config.testargs.get("test"):
                self._do_test_retry(request.listeners, self.config.testargs)
            else:
                if self.rerun:
                    self.runner.retry_times = self.runner.MAX_RETRY_TIMES
                    # execute test case
                self._do_tf_suite()
                self._make_exclude_list_file(request)
                oh_jsunit_para_parse(self.runner, self.config.testargs)
                self._do_test_run(listener=request.listeners)

        finally:
            do_module_kit_teardown(request)

    def _get_driver_config(self, json_config):
        package = get_config_value('package-name',
                                   json_config.get_driver(), False)
        module = get_config_value('module-name',
                                  json_config.get_driver(), False)
        bundle = get_config_value('bundle-name',
                                  json_config. get_driver(), False)
        is_rerun = get_config_value('rerun', json_config.get_driver(), False)

        self.config.package_name = package
        self.config.module_name = module
        self.config.bundle_name = bundle
        self.rerun = True if is_rerun == 'true' else False

        if not package and not module:
            raise ParamError("Neither package nor module is found"
                             " in config file.", error_no="03201")
        timeout_config = get_config_value("shell-timeout",
                                          json_config.get_driver(), False)
        if timeout_config:
            self.config.timeout = int(timeout_config)
        else:
            self.config.timeout = TIME_OUT

    def _get_runner_config(self, json_config):
        test_timeout = get_config_value('test-timeout',
                                        json_config.get_driver(), False)
        if test_timeout:
            self.runner.add_arg("wait_time", int(test_timeout))

        testcase_timeout = get_config_value('testcase-timeout',
                                            json_config.get_driver(), False)
        if testcase_timeout:
            self.runner.add_arg("timeout", int(testcase_timeout))
        self.runner.compile_mode = get_config_value(
            'compile-mode', json_config.get_driver(), False)

    def _do_test_run(self, listener):
        test_to_run = self._collect_test_to_run()
        LOG.info("Collected suite count is: {}, test count is: {}".
                 format(len(self.runner.expect_tests_dict.keys()),
                        len(test_to_run) if test_to_run else 0))
        if not test_to_run or not self.rerun:
            self.runner.run(listener)
            self.runner.notify_finished()
        else:
            self._run_with_rerun(listener, test_to_run)

    def _collect_test_to_run(self):
        run_results = self.runner.dry_run()
        return run_results

    def _run_tests(self, listener):
        test_tracker = CollectingPassListener()
        listener_copy = listener.copy()
        listener_copy.append(test_tracker)
        self.runner.run(listener_copy)
        test_run = test_tracker.get_current_run_results()
        return test_run

    def _run_with_rerun(self, listener, expected_tests):
        LOG.debug("Developer_test Ready to run with rerun, expect run: %s"
                  % len(expected_tests))
        test_run = self._run_tests(listener)
        self.runner.retry_times -= 1
        LOG.debug("Run with rerun, has run: %s" % len(test_run)
                  if test_run else 0)
        if len(test_run) < len(expected_tests):
            expected_tests = TestDescription.remove_test(expected_tests,
                                                         test_run)
            if not expected_tests:
                LOG.debug("No tests to re-run twice,please check")
                self.runner.notify_finished()
            else:
                self._rerun_twice(expected_tests, listener)
        else:
            LOG.debug("Rerun once success")
            self.runner.notify_finished()

    def _rerun_twice(self, expected_tests, listener):
        tests = []
        for test in expected_tests:
            tests.append("%s#%s" % (test.class_name, test.test_name))
        self.runner.add_arg("class", ",".join(tests))
        LOG.debug("Ready to rerun twice, expect run: %s" % len(expected_tests))
        test_run = self._run_tests(listener)
        self.runner.retry_times -= 1
        LOG.debug("Rerun twice, has run: %s" % len(test_run))
        if len(test_run) < len(expected_tests):
            expected_tests = TestDescription.remove_test(expected_tests,
                                                         test_run)
            if not expected_tests:
                LOG.debug("No tests to re-run third,please check")
                self.runner.notify_finished()
            else:
                self._rerun_third(expected_tests, listener)
        else:
            LOG.debug("Rerun twice success")
            self.runner.notify_finished()

    def _rerun_third(self, expected_tests, listener):
        tests = []
        for test in expected_tests:
            tests.append("%s#%s" % (test.class_name, test.test_name))
        self.runner.add_arg("class", ",".join(tests))
        LOG.debug("Rerun to rerun third, expect run: %s" % len(expected_tests))
        self._run_tests(listener)
        LOG.debug("Rerun third success")
        self.runner.notify_finished()

    def _make_exclude_list_file(self, request):
        if "all-test-file-exclude-filter" in self.config.testargs:
            json_file_list = self.config.testargs.get(
                "all-test-file-exclude-filter")
            self.config.testargs.pop("all-test-file-exclude-filter")
            if not json_file_list:
                LOG.warning("all-test-file-exclude-filter value is empty!")
            else:
                if not os.path.isfile(json_file_list[0]):
                    LOG.warning(
                        "[{}] is not a valid file".format(json_file_list[0]))
                    return
                file_open = os.open(json_file_list[0], os.O_RDONLY,
                                    stat.S_IWUSR | stat.S_IRUSR)
                with os.fdopen(file_open, "r") as file_handler:
                    json_data = json.load(file_handler)
                exclude_list = json_data.get(
                    DeviceTestType.oh_jsunit_test, [])
                filter_list = []
                for exclude in exclude_list:
                    if request.get_module_name() not in exclude:
                        continue
                    filter_list.extend(exclude.get(request.get_module_name()))
                if not isinstance(self.config.testargs, dict):
                    return
                if 'notClass' in self.config.testargs.keys():
                    filter_list.extend(self.config.testargs.get('notClass', []))
                self.config.testargs.update({"notClass": filter_list})

    def _do_test_retry(self, listener, testargs):
        tests_dict = dict()
        case_list = list()
        for test in testargs.get("test"):
            test_item = test.split("#")
            if len(test_item) != 2:
                continue
            case_list.append(test)
            if test_item[0] not in tests_dict:
                tests_dict.update({test_item[0] : []})
            tests_dict.get(test_item[0]).append(
                TestDescription(test_item[0], test_item[1]))
        self.runner.add_arg("class", ",".join(case_list))
        self.runner.expect_tests_dict = tests_dict
        self.config.testargs.pop("test")
        self.runner.run(listener)
        self.runner.notify_finished()

    def _do_tf_suite(self):
        if hasattr(self.config, "tf_suite") and \
                self.config.tf_suite.get("cases", []):
            case_list = self.config["tf_suite"]["cases"]
            self.config.testargs.update({"class": case_list})

    def _start_smart_perf(self):
        if not hasattr(self.config, ConfigConst.kits_in_module):
            return
        if CKit.smartperf not in self.config.get(ConfigConst.kits_in_module):
            return
        sp_kits = get_plugin(Plugin.TEST_KIT, CKit.smartperf)[0]
        sp_kits.target_name = self.config.bundle_name
        param_config = self.config.get(ConfigConst.kits_params).get(
            CKit.smartperf, "")
        sp_kits.__check_config__(param_config)
        self.kits.insert(0, sp_kits)

    def _handle_logs(self, request):
        serial = "{}_{}".format(str(self.config.device.__get_serial__()), time.time_ns())
        log_tar_file_name = "{}".format(str(serial).replace(":", "_"))
        if hasattr(self.config, ConfigConst.device_log) and \
                self.config.device_log.get(ConfigConst.tag_enable) == ConfigConst.device_log_on \
                and hasattr(self.config.device, "start_get_crash_log"):
            self.config.device.device_log_collector.\
                start_get_crash_log(log_tar_file_name, module_name=request.get_module_name())
        self.config.device.device_log_collector.\
            remove_log_address(self.device_log, self.hilog)
        self.config.device.device_log_collector.\
            stop_catch_device_log(self.log_proc)
        self.config.device.device_log_collector.\
            stop_catch_device_log(self.hilog_proc)
