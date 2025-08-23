#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2025 Huawei Device Co., Ltd.
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
import datetime
import xml.etree.ElementTree as ET
from xdevice import platform_logger

LOG = platform_logger("arkts_tdd_report_generator")


class ResultConstruction(object):
    def __init__(self):
        self.testsuite_summary = {}
        self.start_time = None
        self.end_time = None
        self.suite_file_name = None

    def format_xml(self, elem_node, level=0):
        if len(elem_node):
            if not elem_node.text or not elem_node.text.strip():
                elem_node.text = "\n" + level * "    "
            if not elem_node.tail or not elem_node.tail.strip():
                elem_node.tail = "\n" + level * "  "
            for elem in elem_node:
                self.format_xml(elem, level + 1)
            if not elem_node.tail or not elem_node.tail.strip():
                elem_node.tail = "\n" + level * "  "
        else:
            if level and (not elem_node.tail or not elem_node.tail.strip()):
                elem_node.tail = "\n" + level * "  "

    def node_construction(self, suite_result_file):
        # 创建根元素
        testsuites = ET.Element("testsuites")
        testsuites.set("name", self.suite_file_name)
        testsuites.set("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        testsuites.set("time", str(float(self.testsuite_summary['taskconsuming']) / 1000))
        testsuites.set("errors", self.testsuite_summary['Error'])
        testsuites.set("disabled", '0')  # ?
        testsuites.set("failures", self.testsuite_summary['Failure'])
        testsuites.set("tests", self.testsuite_summary['Tests run'])
        testsuites.set("ignored", self.testsuite_summary['Ignore'])
        testsuites.set("unavailable", "0")  # ?
        testsuites.set("starttime", self.start_time)
        testsuites.set("endtime", self.end_time)
        testsuites.set("repeat", "1")  # ?
        testsuites.set("round", "1")  # ?
        testsuites.set("test_type", "OHJSUnitTest")

        for key, value in self.testsuite_summary.items():
            if not isinstance(value, dict):
                continue
            testsuite = ET.SubElement(testsuites, "testsuite")
            case_detail = value['case_detail']
            fail_count = 0
            for detail in case_detail:
                if detail['testcaseResult'] == 'fail':
                    fail_count += 1

            testsuite.set("name", key)
            testsuite.set("time", str(float(value['testsuite_consuming']) / 1000))
            testsuite.set("errors", "0")
            testsuite.set("disabled", "0")
            testsuite.set("failures", str(fail_count))
            testsuite.set("ignored", "0")
            testsuite.set("tests", value['testsuiteCaseNum'])
            testsuite.set("report", "")

            case_detail = value['case_detail']
            for detail in case_detail:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", detail['case_name'])
                testcase.set("status", "run")
                testcase.set("time", str(float(detail['testcaseConsuming']) / 1000))
                testcase.set("classname", key)

                if detail['testcaseResult'] is not None:
                    testcase.set("result", "completed")

                testcase.set("level", "1")

                if detail['testcaseResult'] == 'fail':
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", detail['testcaseFailDetail'])
                    failure.set("type", "")
                    failure.text = detail['testcaseFailDetail']
        self.format_xml(testsuites)

        # 将 ElementTree 写入 XML 文件
        tree = ET.ElementTree(testsuites)
        tree.write(suite_result_file, encoding="UTF-8", xml_declaration=True, short_empty_elements=True)
        LOG.info(f"XML 文件已生成: {suite_result_file}")