#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
import datetime
from importlib import reload
reload(sys)
import os
import stat

FLAGS_WRITE = os.O_WRONLY | os.O_CREAT | os.O_EXCL
FLAGS_ADD = os.O_WRONLY | os.O_APPEND | os.O_CREAT
MODES = stat.S_IWUSR | stat.S_IRUSR


html_head = """
<!DOCTYPE html>
<html lang="en" xmlns:th="http://www.thymeleaf.org">
<head>
    <meta charset="UTF-8"/>
    <title>接口覆盖率邮件模板</title>
    <style type="text/css">
        table.reference, table.tecspec {
            border-collapse: collapse;
            width: 95%;
            margin-bottom: 4px;
            margin-top: 4px;
            text-align: center;
        }
        table.reference tr:nth-child(even) {
            background-color: #fff;
        }
        table.reference tr:nth-child(odd) {
            background-color: #f6f4f0;
        }
        table.reference th {
            color: #fff;
            background-color: #14b8c7;
            border: 1px solid #555;
            font-size: 18px;
            padding: 3px;
            vertical-align: top;
        }
        table.reference td {
            line-height: 1.5em;
            min-width: 24px;
            border: 1px solid #d4d4d4;
            padding: 5px;
            padding-top: 1px;
            padding-bottom: 1px;
            vertical-align: top;
        }
        .article-body h3 {
            font-size: 1.8em;
            margin: 2px 0;
            line-height: 1.8em;
        }

    </style>
</head>
"""
html_body_start = """
<body>"""

html_body_ended = """
</body>"""
html_ended = """
</html>"""


def sort_by_field_element(elem):
    return int(float(elem[3][:-1]))   # @######value是浮点数，如1.0，那么需要先转float再转int


def sort_by_field_element_data(elem):
    return elem[2]


def create_html_start(reportpath):
    try:
        if os.path.exists(reportpath):
            os.remove(reportpath)
        with os.fdopen(os.open(reportpath, FLAGS_WRITE, MODES), 'w') as report:
            report.write(html_head)
            report.write(html_body_start)
    except(IOError, ValueError):
        print("Error for create html start ",)


def create_title(reportpath, title_name, summary_list):
    currdatetime = datetime.date.today().strftime("%Y-%m-%d")
    report_title = """
    <h2 style="text-align: center;font-family: 微软雅黑">%s coverage report (%s)</h2>
    """
    content = report_title % (title_name, currdatetime)
    report_title = content + """
    <div><table align="center"><tbody>
      <tr>
          <th align='left'>
          <h4 style="font-family: 微软雅黑;">Summary Report</h4>
          <h4 style="font-family: 微软雅黑;">接口总数%s, 已覆盖%s, 未覆盖%s</h4>
      </tr>
   </tbody>
   </table>
   </div>
    """
    subsystems = ""
    count = 0
    for item in summary_list:
        subsystem = item[0]
        if count < 3:
            subsystems = subsystems + "、" + subsystem
            count = count + 1
        if subsystem == "Summary":
            nocoverd = item[1] - item[2]
            report_title = report_title % (item[1], item[2], nocoverd)
    try:
        with os.fdopen(os.open(reportpath, FLAGS_ADD, MODES), 'a') as report:
            report.write(report_title)
    except(IOError, ValueError):
        print("Error for create html title")


def create_summary(reportpath, summary_list):
    table_title = """
        <h4 style="text-align: left;font-family: 微软雅黑;margin-left: 3%;">Summary</h4>
        """

    table_start = """<div><table class="reference" align="center"><tbody>"""

    table_head = """
            <tr>
                <th style="width:20%;">PartName</th>
                <th style="width:20%;">TotalCount</th>
                <th style="width:20%;">CoveredCount</th>
                <th style="width:20%;">Coverage</th>
            </tr>"""

    table_line = """
            <tr class=normal>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>
        """

    table_ended = """</tbody></table></div>
        """
    try:
        if len(summary_list) == 0:
            return

        with os.fdopen(os.open(reportpath, FLAGS_ADD, MODES), 'a') as report:
            report.write(table_title)
            report.write(table_start)
            report.write(table_head)
            for item in summary_list:
                content = table_line % (item[0], str(item[1]), str(item[2]), item[3])
                report.write(content)
            report.write(table_ended)
    except(IOError, ValueError):
        print("Error for create html summary")


def create_table_test(reportpath, subsystem_name, datalist, total_count, covered_count):
    table_title = """
    %s details:</h4>
    """
    table_start = """<div><table class="reference" align="center"><tbody>"""
    table_head = """
        <tr>
            <th>PartName</th>
            <th>ClassName</th>
            <th>InterfaceName</th>
            <th>IsCovered</th>
        </tr>"""
    table_line = """
        <tr class=normal>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
        </tr>
    """
    table_summary = """
                <tr class='normal' align="center">
                    <td colspan="4" >TotalCount: %s, CoveredCount:%s, Coverage: %s</td>
                </tr>
            """
    table_ended = """</tbody></table></div>
    """
    try:
        with os.fdopen(os.open(reportpath, FLAGS_ADD, MODES), 'a') as report:
            print("part_name==" + subsystem_name)
            tabletitle = table_title % (subsystem_name)
            print("tabletitle==" + tabletitle)
            tabletitle = "<h4 style=\"text-align: left;font-family: 微软雅黑;margin-left: 3%;\">" + tabletitle + "</h4>"
            report.write(tabletitle)
            report.write(table_start)
            report.write(table_head)
            datalist.sort(key=sort_by_field_element_data, reverse=False)

            for line in datalist:
                if str(line[2]) == "N":
                    content = table_line % (
                        "<font=>" + subsystem_name + "</font>", "<font>" + line[0] + "</font>",
                        "<font>" + line[1] + "</font>",
                        "<font color=\"red\">" + str(line[2]) + "</font>")
                    report.write(content)
                else:
                    content = table_line % (
                        "<font>" + subsystem_name + "</font>", "<font>" + line[0] + "</font>",
                        "<font>" + line[1] + "</font>",
                        "<font color=\"green\">" + str(line[2]) + "</font>")
                    report.write(content)
            if 0 != total_count:
                coverage = str("%.2f" % (covered_count * 100 / total_count)) + "%"
            else:
                coverage = "0%"
            coverage = table_summary % (total_count, covered_count, coverage)
            report.write(coverage)
            report.write(table_ended)
    except(IOError, ValueError):
        print("Error for create html table test")


def create_html_ended(reportpath):
    try:
        with os.fdopen(os.open(reportpath, FLAGS_ADD, MODES), 'a') as report:
            report.write(html_body_ended)
            report.write(html_ended)
    except(IOError, ValueError):
        print("Error for create html end")
