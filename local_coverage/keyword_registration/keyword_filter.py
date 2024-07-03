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

import os
import re
import time
import json
import stat
import fcntl
import platform
import linecache
import traceback
from multiprocessing import Pool

from lxml import html
from selectolax.parser import HTMLParser

FLAGS_WRITE = os.O_WRONLY | os.O_CREAT | os.O_EXCL
FLAGS_ADD = os.O_WRONLY | os.O_APPEND | os.O_CREAT
MODES = stat.S_IWUSR | stat.S_IRUSR


class CoverageReportPath:
    def __init__(self, report_path):
        self.report_path = report_path

    def gcov_file_generator(self):
        """
        gcov文件生成器
        """
        for root_path, _, files in os.walk(self.report_path):
            for file in files:
                if not file.endswith(".gcov.html"):
                    continue
                file_path = os.path.join(root_path, file)
                yield file_path

    def modify_report_style(self):
        """
        修改覆盖率报告css样式
        """
        css_file_path = ""
        for root_path, _, files in os.walk(self.report_path):
            for file in files:
                if file == "gcov.css":
                    css_file_path = os.path.join(root_path, file)
        text = """
/* update */
span.linenumupdate, span.branchexecupdate, span.branchnoexecupdate,
span.linecovupdate, span.linenocovupdate, span.branchcovupdate,
span.branchnocovupdate
{
  background-color:#BBBBBB;
}"""
        if os.path.exists(css_file_path):
            with os.fdopen(os.open(css_file_path, FLAGS_ADD, MODES), 'a+') as file:
                file.write(text)

    def get_statistic_path(self, gcov_file_path: str):
        """
        根据gcov.html路径和统计等级获取统计报告路径
        """
        file_name_list = ["index.html", "index-sort-b.html",
                          "index-sort-f.html", "index-sort-l.html"]
        index_path_list = [
            os.path.normcase(os.path.join(os.path.dirname(gcov_file_path), file_name))
            for file_name in file_name_list
        ]
        out_path_list = [
            os.path.normcase(os.path.join(self.report_path, file_name))
            for file_name in file_name_list
        ]
        index_path_list.extend(out_path_list)
        return index_path_list


class KeywordRegistration:
    def __init__(self, report_path):
        self.report_path = report_path
        self.keyword_file_path = os.path.normcase(
            os.path.join(os.path.dirname(__file__), "keyword.json"))

    @staticmethod
    def get_coverage_content(file_path):
        """
        获取覆盖率文件内容
        """
        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    @staticmethod
    def get_tag(content, line):
        start_index = content.find(f'<a name="{line}"')
        end_index = content.find(f'<a name="{int(line) + 1}"')
        tag = content[start_index:end_index - 1]
        return tag

    @staticmethod
    def get_source_code(html_tag):
        """
        获取源码
        """
        source_code1 = re.findall(r'Cov.*">(.*?)</span></a>', html_tag)
        source_code2 = re.findall(r'covupdate.*">(.*?)</span></a>', html_tag)
        if source_code1:
            source_code = source_code1[0][13:].strip()
        elif source_code2:
            source_code = source_code2[0][13:].strip()
        else:
            source_code = HTMLParser(html_tag).text()[39:].strip()
        
        return source_code

    @staticmethod
    def update_tag(tag: str):
        replace_item_list = ["lineNum", "branchNoCov", "branchCov", "lineCov",
                             "branchNoExec", "lineNoCov", "branchExec"]

        for item in replace_item_list:
            if item in tag:
                replace_item = (item + "Update").lower()
                tag = tag.replace(item, replace_item)
        return tag

    @staticmethod
    def get_branch_line_list(keyword_line: int, branch_line_list: list):
        """
        获取大于关键字行号的所有分支行号
        """
        if keyword_line in branch_line_list:
            index = branch_line_list.index(keyword_line)
            branch_line_list = branch_line_list[index:]
        else:
            for line in branch_line_list:
                if line > keyword_line:
                    index = branch_line_list.index(line)
                    branch_line_list = branch_line_list[index:]
                    break
        return branch_line_list

    @staticmethod
    def get_keyword_judge_char(keyword, keyword_source_code):
        """
        获取关键字替代字符
        """
        if "&" in keyword:
            keyword = keyword.replace("&", "<")

        keyword_index = keyword_source_code.find(keyword)
        if keyword_index == -1:
            return ""

        try:
            keyword_code = keyword_source_code[:keyword_index + len(keyword)]
            if " = " in keyword_code:
                judge_key = keyword_code.split(" = ")[0].split()[-1]
            else:
                bracket_index = keyword_code.find("(")
                bracket_code = keyword_code[:bracket_index]
                judge_key = bracket_code.split()[-1]
            return judge_key
        except (IndexError, ValueError):
            return ""

    @staticmethod
    def get_branch_data_by_tag(tag_html: str, symbol_status=None):
        """
        根据前端标签获取分支数据
        """
        if symbol_status:
            key = r"#+\-*"
        else:
            key = r"#+\-"
        branch_line_list = re.findall(rf"> ([{key}]) </span>", tag_html)

        return branch_line_list

    @staticmethod
    def get_judge_condition_index(judge_key: str, source_code: str):
        """
        获取判断条件索引
        """
        keyword_index_list = []
        keyword_index_list_append = keyword_index_list.append

        condition_str_list = re.split(rf"\|\||&&", source_code)
        for index, code_str in enumerate(condition_str_list):
            if judge_key in code_str:
                keyword_index_list_append(index)
        return keyword_index_list, condition_str_list

    @staticmethod
    def update_source_code_tag(html_tag: str):
        replace_item_list = ["lineNum", "lineCov", "lineNoCov"]

        for item in replace_item_list:
            if item in html_tag:
                replace_item = (item + "Update").lower()
                html_tag = html_tag.replace(item, replace_item)

        return html_tag

    @staticmethod
    def modify_tag_style(tag, rate):
        """
        修改标签样式
        """
        if 75 <= rate < 90:
            tag = tag.replace("headerCovTableEntryLo", "headerCovTableEntryMed")
            tag = tag.replace("coverPerLo", "coverPerMed")
            tag = tag.replace("coverNumLo", "coverNumMed")
        elif rate >= 90:
            tag = tag.replace("headerCovTableEntryLo", "headerCovTableEntryHi")
            tag = tag.replace("headerCovTableEntryMed", "headerCovTableEntryHi")
            tag = tag.replace("coverPerLo", "coverPerHi")
            tag = tag.replace("coverNumLo", "coverNumHi")
            tag = tag.replace("coverPerMed", "coverPerHi")
            tag = tag.replace("coverNumMed", "coverNumHi")
        return tag

    @staticmethod
    def _branch_replace(branch):
        """
        分支符号替换
        """
        if branch == "#":
            branch = "> # <"
        elif branch == "+":
            branch = "> + <"
        elif branch == "*":
            branch = "> * <"
        else:
            branch = "> - <"
        return branch

    @staticmethod
    def _single_condition_modify_html(branch_html, branch_list):
        """
        单条件修改代码块html
        """
        line_item = '<span class="lineNum">         </span>'
        line_feed_index = branch_html.find(line_item)
        if line_feed_index == -1:
            if "+" in branch_list:
                update_branch_tag = branch_html.replace("> - <", ">   <")
                update_branch_tag = update_branch_tag.replace("> # <", ">   <")
            else:
                try:
                    first_branch = branch_list[0]
                    first_branch = "> " + first_branch + " <"
                    first_branch_index = branch_html.find(first_branch)
                    branch_tag = branch_html[:first_branch_index + 5]
                    update_branch_tag = branch_html[first_branch_index + 5:]
                    update_branch_tag = update_branch_tag.replace("> - <", ">   <")
                    update_branch_tag = update_branch_tag.replace("> # <", ">   <")
                    update_branch_tag = branch_tag + update_branch_tag
                except ValueError:
                    return ""
        else:
            line_feed_index = branch_html.find(line_item)
            update_branch_tag = branch_html[:line_feed_index + len(line_item) + 1]
            if "-" not in branch_list and "+" not in branch_list:
                del_count = update_branch_tag.count("> # <")
                update_branch_tag = update_branch_tag.replace("> # <", ">   <", del_count - 1)
            else:
                update_branch_tag = update_branch_tag.replace("> - <", ">   <")
                update_branch_tag = update_branch_tag.replace("> # <", ">   <")
            branch_tag = branch_html[line_feed_index + len(line_item) + 1:]
            line_feed_index = branch_tag.find(line_item)
            if line_feed_index == -1:
                branch_tag = branch_tag.replace("> - <", ">   <")
                branch_tag = branch_tag.replace("> # <", ">   <")
                update_branch_tag += branch_tag
            else:
                loop_count = 0
                while line_feed_index + 1:
                    loop_count += 1
                    if loop_count > 200:
                        continue
                    try:
                        update_branch_tag += branch_tag[:line_feed_index + len(line_item) + 1]
                        update_branch_tag = update_branch_tag.replace("> - <", ">   <")
                        update_branch_tag = update_branch_tag.replace("> # <", ">   <")
                        branch_tag = branch_tag[line_feed_index + len(line_item) + 1:]
                        line_feed_index = branch_tag.find(line_item)
                    except ValueError:
                        return ""

                branch_tag = branch_tag.replace("> - <", ">   <")
                update_branch_tag = update_branch_tag.replace("> # <", ">   <")
                update_branch_tag += branch_tag
        return update_branch_tag

    def get_break_line_tag(self, content, origin_branch_html, branch_line):
        """
        获取分支换行的判断条件源码tag
        """
        get_tag = self.get_tag
        left_brace_exist = False
        line_break = loop_count = 0
        while not left_brace_exist:
            if loop_count > 10:
                break
            line_break += 1
            origin_branch_html = os.path.join(origin_branch_html, "\n")
            next_line_tag = get_tag(content, branch_line + line_break)
            if "{" in next_line_tag:
                left_brace_exist = True
            origin_branch_html += next_line_tag
            loop_count += 1
        return origin_branch_html

    def get_keyword_info(self):
        """
        获取报备关键字信息
        """
        try:
            with open(self.keyword_file_path, "r") as file:
                keyword_dict = json.load(file)
            keyword_list = keyword_dict.get("KEYWORD")
            return keyword_list
        except (FileNotFoundError, AttributeError, FileExistsError):
            return []
            
    def get_coverage_lines_by_branch(self, file_path, content=None):
        """
        获取覆盖率报告中的所有的if分支行号
        """
        if not content:
            content = self.get_coverage_content(file_path)
        if not content:
            return []
        _, file_name = os.path.split(file_path)
        branch_line_list = re.findall(
            r'''<a name="(\d+).*?Branch.*? if \(|
            <a name="(\d+).*?Branch.*? if\(''', content)

        if branch_line_list:
            branch_line_list = [int(line_tuple[0]) if line_tuple[0] else
                                int(line_tuple[1]) for line_tuple in branch_line_list]
            return branch_line_list
        else:
            return []

    def get_coverage_lines_by_keyword(self, keyword, content):
        """
        获取关键字在覆盖率报告中的行号
        """
        if "&" in keyword:
            keyword = keyword.replace("&", "")
        origin_keyword = keyword
        if keyword.endswith("("):
            keyword = keyword.replace("(", "")
            keyword_line_list = re.findall(
                rf'<a name="(\d+).*?[ .;!:()]{keyword}[ .;!:()&]', content)
        else:
            keyword_line_list = re.findall(
                rf'<a name="(\d+).*?[ .;!:()]{keyword}[ .;!:)&]', content)

        if keyword_line_list:
            keyword_line_list = [int(line) for line in keyword_line_list]
            keyword_branch_list = []
            get_tag = self.get_tag
            keyword_branch_list_append = keyword_branch_list.append
            keyword_line_list_remove = keyword_line_list.remove
            for line in keyword_line_list:
                tag_html = get_tag(content, line)
                if origin_keyword not in tag_html:
                    keyword_branch_list_append(line)
                if 'title="Branch' not in tag_html:
                    continue
                if "switch (" in tag_html or "switch(" in tag_html:
                    keyword_branch_list_append(line)
                elif "while (" in tag_html or "while(" in tag_html:
                    keyword_branch_list_append(line)
                elif "for (" in tag_html or "for(" in tag_html:
                    keyword_branch_list_append(line)
                elif "do {" in tag_html or "do{" in tag_html:
                    keyword_branch_list_append(line)
            for key in keyword_branch_list:
                keyword_line_list_remove(key)
        return keyword_line_list

    def code_body_judge(self, line, content):
        """
        全量报备按行获取覆盖率报告源码
        """
        func_body_tag_list = []
        update_func_body_tag_list = []
        func_body_tag_list_append = func_body_tag_list.append
        update_func_body_tag_list_append = update_func_body_tag_list.append
        get_tag = self.get_tag
        update_tag = self.update_tag
        tag = get_tag(content, line)
        if "{" not in tag:
            return func_body_tag_list, update_func_body_tag_list

        braces_sub = 1
        if "{" not in tag:
            braces_sub = 0
        next_line = int(line) + 1
        branch_braces_sub = count = 0
        sub_brace_start_status = sub_brace_end_status = False
        while braces_sub:
            count += 1
            if count > 200:
                return [], []
            next_tag = get_tag(content, str(next_line))
            func_body_tag_list_append(next_tag)
            if "{" in next_tag:
                if branch_braces_sub:
                    branch_braces_sub += 1
                braces_sub += 1
            if "}" in next_tag:
                if branch_braces_sub:
                    branch_braces_sub -= 1
                braces_sub -= 1
            if 'title="Branch' in next_tag:
                branch_braces_sub += 1
                sub_brace_start_status = True
            if not branch_braces_sub and \
                    (sub_brace_start_status == sub_brace_end_status):
                next_tag = update_tag(next_tag)
            if not branch_braces_sub and sub_brace_start_status:
                sub_brace_end_status = True
            update_func_body_tag_list_append(next_tag)
            next_line += 1
        return func_body_tag_list, update_func_body_tag_list

    def get_line_funcname(self, branch_line, content):
        """
        获取行号源码所在函数的函数名
        """
        function_name = ""
        previous_line = int(branch_line)
        loop_count = 0
        get_tag = self.get_tag
        while not function_name:
            loop_count += 1
            if loop_count > 500:
                return function_name

            previous_line -= 1
            tag = get_tag(content, previous_line)
            tag_text = self.get_source_code(tag)
            if "LOG" in tag_text or tag_text.startswith("//"):
                continue
            if tag_text.strip().startswith("{"):
                child_count = left_parentheses_count = right_parentheses_count = 0
                while previous_line:
                    child_count += 1
                    if child_count > 100:
                        return function_name

                    previous_line -= 1
                    html_text = get_tag(content, previous_line)
                    source_code = self.get_source_code(html_text)
                    if "LOG" in source_code or "}" in source_code or source_code.endswith(";"):
                        break
                    if source_code.startswith("//"):
                        continue
                    if "{" in source_code:
                        previous_line += 1
                        break
                    left_parentheses_count += source_code.count("(")
                    right_parentheses_count += source_code.count(")")
                    if not left_parentheses_count == right_parentheses_count:
                        continue
                    if " operator" in source_code:
                        class_name_list = re.findall(r'\((.*?)\)', source_code)
                        if class_name_list:
                            function_name = class_name_list[0].strip()
                            return function_name

                    function_name_list = re.findall(r' (.*?)\(', source_code)
                    if function_name_list:
                        function_name = function_name_list[0].strip()
                        return function_name
        return function_name 

    def update_coverage_ratio_tag(self, file_path):
        """
        修改覆盖率比率数据
        """
        with open(file_path, "r", encoding="utf-8") as coverage_file:
            content = coverage_file.read()

        covered_nums = len(re.findall(r"> ([+]) </span>", content))
        branch_total = len(re.findall(r"> ([+\-#]) </span>", content))

        line = 0
        start_line = 1
        content_list = content.splitlines()
        for line_text in content_list:
            if '<td class="headerItem">Branches:</td>' in line_text:
                line = start_line
                break
            start_line += 1
        linecache.clearcache()
        coverage_tag = linecache.getline(file_path, line)
        covered_tag = linecache.getline(file_path, line + 1)
        coverage_total_tag = linecache.getline(file_path, line + 2)
        try:
            origin_hit = int(re.findall(r"(\d+)", covered_tag)[0])
            origin_total = int(re.findall(r"(\d+)", coverage_total_tag)[0])
            coverage_rate_tag = linecache.getline(file_path, line + 3)
            replace_tag = coverage_tag + covered_tag + coverage_total_tag + \
                          coverage_rate_tag
            if origin_total - branch_total == 0 and origin_hit - covered_nums == 0:
                return
            if int(branch_total) == 0:
                coverage = 0.0
            else:
                coverage = round(int(covered_nums) / int(branch_total) * 100, 1)

            origin_rate = re.findall(r"(\d+.\d+)", coverage_rate_tag)[0]
            update_tag = coverage_tag + covered_tag.replace(
                str(origin_hit), str(covered_nums)) + \
                         coverage_total_tag.replace(str(origin_total),
                                                    str(branch_total)) + \
                         coverage_rate_tag.replace(origin_rate, str(coverage))

            update_tag = self.modify_tag_style(update_tag, coverage)
            if replace_tag in content:
                content = content.replace(replace_tag, update_tag)

            os.remove(file_path)
            with os.fdopen(os.open(file_path, FLAGS_WRITE, MODES), 'w') as file:
                file.write(content)

            # 修改数据统计页面
            hit_shield_num = origin_hit - covered_nums
            total_shield_num = origin_total - branch_total
            self.update_statistic(file_path, hit_shield_num, total_shield_num)
        except (IndexError, TypeError, FileNotFoundError):
            pass

    def update_statistic(self, file_path, hit_shield_num, total_shield_num):
        """
        修改覆盖率分支数据
        """
        index_path_list = CoverageReportPath(self.report_path).get_statistic_path(file_path)
        for index_path in index_path_list:
            if not os.path.exists(index_path):
                continue

            with open(index_path, "r", encoding="utf-8") as coverage_file:
                fcntl.flock(coverage_file.fileno(), fcntl.LOCK_EX)
                content = coverage_file.read()

            file_dir, file_name = os.path.split(file_path)
            if os.path.normcase(file_dir) not in os.path.normcase(index_path):
                if platform.system() == "Windows":
                    judge_item = file_dir.replace(self.report_path + "\\", "")
                    judge_item = ">" + judge_item.replace("\\", "/") + "</a>"
                else:
                    judge_item = file_dir.replace(self.report_path + "/", "")
                    judge_item = ">" + judge_item + "</a>"
            else:
                judge_item = ">" + file_name.replace(".gcov.html", "")

            start_line = 1
            line = tag_line = 0
            content_list = content.splitlines()
            tmp = '<td class="headerItem">Branches:</td>'
            for line_text in content_list:
                if not line and tmp in line_text:
                    line = start_line
                if judge_item in line_text:
                    tag_line = start_line
                    break
                start_line += 1
            try:
                # total statistic modify
                linecache.clearcache()
                coverage_head_tag = linecache.getline(index_path, line)
                origin_hit_tag = linecache.getline(index_path, line + 1)
                origin_hit_num = int(re.findall(r"(\d+)", origin_hit_tag)[0])
                origin_total_tag = linecache.getline(index_path, line + 2)
                origin_total_num = int(re.findall(r"(\d+)", origin_total_tag)[0])
                origin_rate_tag = linecache.getline(index_path, line + 3)
                origin_rate = re.findall(r"(\d+.\d+)", origin_rate_tag)[0]
                replace_tag = coverage_head_tag + origin_hit_tag + \
                              origin_total_tag + origin_rate_tag

                # file branch modify
                no_change_file_tag = ""
                for i in range(8):
                    no_change_file_tag += linecache.getline(index_path, tag_line + i)
                file_rate_tag = linecache.getline(index_path, tag_line + 8)
                file_covered_tag = linecache.getline(index_path, tag_line + 9)
                file_tag = no_change_file_tag + file_rate_tag + file_covered_tag
                origin_file_covered_num, origin_file_total_num = map(
                    int, re.findall(r"(\d+)", file_covered_tag))
                if origin_file_total_num:
                    origin_file_rate = re.findall(r"(\d+.\d+)", file_rate_tag)[0]
                else:
                    # 不存在覆盖率
                    origin_file_rate = "-"
                head_hit_num = origin_hit_num - hit_shield_num
                head_total_num = origin_total_num - total_shield_num
                if head_total_num == 0:
                    rate = 0.0
                else:
                    rate = round(head_hit_num / head_total_num * 100, 1)
                file_hit_num = origin_file_covered_num - hit_shield_num
                file_total_num = origin_file_total_num - total_shield_num
                if file_total_num == 0:
                    file_rate = 0.0
                else:
                    file_rate = round(file_hit_num / file_total_num * 100, 1)
                update_tag = coverage_head_tag + origin_hit_tag.replace(
                    str(origin_hit_num), str(head_hit_num)) + \
                             origin_total_tag.replace(str(origin_total_num),
                                                      str(head_total_num)) + \
                             origin_rate_tag.replace(origin_rate, str(rate))

                update_tag = self.modify_tag_style(update_tag, rate)

                update_branch_tag = file_rate_tag.replace(
                    origin_file_rate, str(file_rate)) + \
                                    file_covered_tag.replace(
                                        str(origin_file_covered_num) + " / " +
                                        str(origin_file_total_num), str(file_hit_num) + " / " +
                                        str(file_total_num))

                update_branch_tag = self.modify_tag_style(update_branch_tag, file_rate)
                update_branch_tag = no_change_file_tag + update_branch_tag
                if replace_tag in content:
                    content = content.replace(replace_tag, update_tag)
                if file_tag in content:
                    content = content.replace(file_tag, update_branch_tag)
                os.remove(index_path)
                with os.fdopen(os.open(index_path, FLAGS_WRITE, MODES), 'w') as file:
                    file.write(content)
                    fcntl.flock(file.fileno(), fcntl.LOCK_UN)
                time.sleep(1)
            except (IndexError, TypeError, FileNotFoundError):
                pass

    def judge_branch_exists(self, file_path):
        """
        判断报告是否存在分支
        """
        content = self.get_coverage_content(file_path)
        branch_total = len(re.findall(r"> ([+\-#]) </span>", content))
        if branch_total:
            return True
        else:
            return False

    def modify_branch(self, file_path, keyword_list):
        """
        html报告分支屏蔽修改
        """
        branch_line_list = self.get_coverage_lines_by_branch(file_path)
        if not branch_line_list:
            return

        branch_line_list.sort()
        no_change_content = self.get_coverage_content(file_path)
        for keyword in keyword_list:
            content = self.get_coverage_content(file_path)
            keyword_line_list = self.get_coverage_lines_by_keyword(keyword, content)
            if not keyword_line_list:
                continue
            for key_line in keyword_line_list:
                key_html = self.get_tag(content, key_line)
                if not key_html or "LOG" in key_html:
                    continue

                function_name = self.get_line_funcname(key_line, content)
                sub_branch_line_list = self.get_branch_line_list(
                    key_line, branch_line_list)
                keyword_source_code = self.get_source_code(key_html)
                if not all([function_name, keyword_source_code,
                            sub_branch_line_list]):
                    continue

                judge_key = keyword
                if 'title="Branch' not in key_html:
                    judge_key = self.get_keyword_judge_char(
                        keyword, keyword_source_code)
                if "*" in judge_key:
                    judge_key = judge_key.replace("*", "")
                if "&" in judge_key:
                    judge_key = judge_key.replace("&", "")
                if_branch_line = self._check_if_branch_line(
                    judge_key, sub_branch_line_list, key_line,
                    content, function_name)

                if not if_branch_line:
                    continue

                origin_branch_html = self.get_tag(content, if_branch_line)
                branch_html = origin_branch_html
                if "{" not in origin_branch_html:
                    origin_branch_html = self.get_break_line_tag(
                        content, origin_branch_html, if_branch_line)
                    branch_html = origin_branch_html
                top_source_code = self.get_source_code(branch_html)
                no_change_branch_html = self.get_tag(
                    no_change_content, if_branch_line)
                branch_list = self.get_branch_data_by_tag(no_change_branch_html)
                if not branch_list:
                    continue
                if "#" not in branch_list and "-" not in branch_list:
                    continue
                branch_tag_data = self.get_branch_data_by_tag(branch_html, True)
                if len(branch_tag_data) <= 1:
                    continue
                if len(branch_list) == 2:
                    if "-" in branch_list:
                        update_branch_tag = branch_html.replace("> - <", ">   <")
                    else:
                        update_branch_tag = branch_html.replace("> # <", ">   <", 1)
                else:
                    branch_length = len(branch_list)
                    judge_index_list, condition_str_list = self.\
                        get_judge_condition_index(judge_key, top_source_code)
                    if not len(judge_index_list):
                        continue
                    if len(condition_str_list) == 1:
                        update_branch_tag = self._single_condition_modify_html(
                            branch_html, branch_list)
                    else:
                        update_branch_tag = self._multi_condition_modify_html(
                            branch_html, branch_length, condition_str_list,
                            judge_index_list)
                    if not update_branch_tag:
                        return

                update_branch_tag = self.update_source_code_tag(
                    update_branch_tag)
                content = content.replace(origin_branch_html, update_branch_tag)
                source_code_tag_list, update_source_code_tag_list = self.\
                    code_body_judge(int(if_branch_line), content)
                if source_code_tag_list:
                    source_code_tag_html = "\n".join(source_code_tag_list)
                    update_source_code_tag_html = "\n".join(
                        update_source_code_tag_list)
                    content = content.replace(
                        source_code_tag_html, update_source_code_tag_html)

            os.remove(file_path)
            with os.fdopen(os.open(file_path, FLAGS_WRITE, MODES), 'w') as new_html:
                new_html.write(content)

        content = self.get_coverage_content(file_path)
        content = content.replace('> * </span>', '>   </span>')
        os.remove(file_path)

        with os.fdopen(os.open(file_path, FLAGS_WRITE, MODES), 'w') as new_html:
            new_html.write(content)

    def keyword_registration(self, file_path, keyword_list):
        """
        报备
        """
        self.modify_branch(file_path, keyword_list)

        # 修改覆盖率数据
        self.update_coverage_ratio_tag(file_path)
        return True

    def multiprocessing_registration(self):
        """
        多进程关键字报备
        """
        keyword_list = self.get_keyword_info()
        if not keyword_list:
            return

        # 创建报告路径生成器
        report_instance = CoverageReportPath(self.report_path)
        # 修改css文件
        report_instance.modify_report_style()
        # 创建报告路径生成器
        report_generator = report_instance.gcov_file_generator()
        # 获取关键字
        keyword_registration = self.keyword_registration

        pool = Pool(10)
        apply_async = pool.apply_async
        while True:
            file_path = next(report_generator, None)
            if not file_path:
                break

            # 关键字报备
            apply_async(keyword_registration, args=(file_path, keyword_list))

        pool.close()
        pool.join()
    
    def _check_if_branch_line(self, judge_key, sub_branch_line_list,
                              key_line, content, function_name):
        """
        确定if分支行号
        """
        if_branch_line = None
        for branch_line in sub_branch_line_list:
            if branch_line == key_line:
                if_branch_line = key_line
                break
            # 获取分支行所在函数名
            branch_function_name = self.get_line_funcname(
                branch_line, content)
            # 关键字范围只在关键字所在函数之内
            branch_line_tag = self.get_tag(content, branch_line)
            try:
                if "{" not in branch_line_tag:
                    branch_line_tag = self.get_break_line_tag(
                        content, branch_line_tag, branch_line)
                branch_line_source_code = self.get_source_code(
                    branch_line_tag)
                if function_name == branch_function_name:
                    if judge_key in branch_line_source_code:
                        if_branch_line = branch_line
                        break
                else:
                    break
            except (ValueError, KeyError):
                pass

        return if_branch_line

    def _multi_condition_modify_html(self, branch_html, branch_length,
                                     condition_str_list, judge_index_list):
        """
        多条件修改代码块html
        """
        line_item = '<span class="lineNum">         </span>'
        if branch_length % len(condition_str_list):
            line_feed_index = branch_html.find(line_item)
            update_branch_tag = branch_html[:line_feed_index]
            update_branch_tag = update_branch_tag.replace("> - <", ">   <")
            branch_html = branch_html[line_feed_index:]
            loop_count = 0
            while line_feed_index + 1:
                loop_count += 1
                if loop_count > 200:
                    continue
                line_feed_index = branch_html.count(line_item)
                if line_feed_index > 1:
                    try:
                        line_feed_length = len(line_item)
                        branch_tag_before = branch_html[:line_feed_length]
                        branch_html = branch_html[line_feed_length:]
                        line_feed_index = branch_html.find(line_item)
                        branch_tag_after = branch_html[:line_feed_index]
                        branch_tag_after = branch_tag_after.replace("> - <", ">   <")
                        branch_tag = branch_tag_before + branch_tag_after
                    except ValueError:
                        return ""
                else:
                    branch_tag = branch_html
                    branch_tag = branch_tag.replace("> - <", ">   <")
                    # 不再换行，索引为-1
                    line_feed_index = -1

                update_branch_tag += branch_tag
                if line_feed_index == -1:
                    branch_html = ""
                else:
                    branch_html = branch_html[line_feed_index:]
            if branch_html != "":
                branch_html = branch_html.replace("> - <", ">   <")
                update_branch_tag += branch_html
        else:
            branch_list = self.get_branch_data_by_tag(branch_html, True)
            update_branch_tag = ""
            end_count = -1
            try:
                for index in judge_index_list:
                    branch_data = branch_list[:(index + 1) * 2]
                    # 要修改的分支数据列表长度
                    branch_data_length = len(branch_data)
                    change_status = False
                    for count, branch in enumerate(branch_data, 1):
                        if count <= end_count:
                            continue

                        end_count = count
                        branch = self._branch_replace(branch)
                        end_index = branch_html.find(branch)
                        branch_tag = branch_html[:end_index + 5]
                        if branch_data_length - count in [0, 1]:
                            if change_status:
                                continue
                            if branch == "> # <":
                                change_status = True
                                branch_tag = branch_tag.replace("> # <", "> * <")
                            elif branch == "> - <":
                                change_status = True
                                branch_tag = branch_tag.replace("> - <", "> * <")
                        update_branch_tag += branch_tag
                        branch_html = branch_html[end_index + 5:]
            except (ValueError, TypeError):
                return ""
            update_branch_tag += branch_html
        return update_branch_tag


def main(report_path):
    manager = KeywordRegistration(report_path)
    start_time = time.time()
    manager.multiprocessing_registration()
    end_time = time.time()
    times = round(end_time - start_time, 3)
    print("*" * 50, "关键字分支屏蔽结束", "*" * 50, "耗时：", times)


if __name__ == '__main__':
    current_path = os.getcwd()
    home_path = current_path.split("/test/testfwk/developer_test")[0]
    developer_path = os.path.join(home_path, "test/testfwk/developer_test")
    html_path = os.path.join(developer_path, "local_coverage/code_coverage/results/coverage/reports/cxx/html")
    main(html_path)
