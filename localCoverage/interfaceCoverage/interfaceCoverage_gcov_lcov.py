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
import sys
import json
import shutil
import subprocess
import CppHeaderParser
import get_innerkits_json
import make_report

root_path = os.getcwd()
CODEPATH = root_path.split("/test/testfwk/developer_test")[0]
SUB_SYSTEM_INFO_PATH = os.path.join(
    CODEPATH, "test/testfwk/developer_test/localCoverage/codeCoverage/results/coverage/reports/cxx")
OUTPUT_REPORT_PATH = os.path.join(
    CODEPATH, "test/testfwk/developer_test/localCoverage/interfaceCoverage/results/coverage/interface_kits"
)
filter_file_name_list = [
    "appexecfwk/libjnikit/include/jni.h",
]
FILTER_CLASS_ATTRIBUTE_LIST = ["ACE_EXPORT", "OHOS_NWEB_EXPORT"]


def _init_sys_config():
    sys.localcoverage_path = os.path.join(current_path, "..")
    sys.path.insert(0, sys.localcoverage_path)


def create_coverage_result_outpath(filepath):
    if os.path.exists(filepath):
        shutil.rmtree(filepath)
    os.makedirs(filepath)


def get_subsystem_part_list(project_rootpath):
    subsystme_part_dict = {}
    subsystem_part_config_filepath = os.path.join(
        project_rootpath, "out", product_name, "build_configs/infos_for_testfwk.json")
    if os.path.exists(subsystem_part_config_filepath):
        try:
            with open(subsystem_part_config_filepath, 'r') as f:
                data = json.load(f)
        except IOError:
            print("Error for open subsystem config file. ")
        if not data:
            print("subsystem_part config file error.")
        else:
            subsystme_part_dict = data.get("phone", "").get("subsystem_infos", "")
        return subsystme_part_dict
    else:
        print("subsystem_part_config_filepath not exists.")
        return {}


def load_json_data():
    json_file_path = os.path.join(CODEPATH, KIT_MODULES_INFO)
    json_data_dic = {}
    if os.path.isfile(json_file_path):
        try:
            with open(json_file_path, 'r') as f:
                json_data_dic = json.load(f)
            if not json_data_dic:
                print("Loadind file \"%s\" error" % json_file_path)
                return {}
        except(IOError, ValueError):
            print("Error for load_json_data: \"%s\"" % json_file_path)
    else:
        print("Info: \"%s\" not exist." % json_file_path)
    return json_data_dic


def get_file_list(find_path, postfix):
    file_names = os.listdir(find_path)
    file_list = []
    if len(file_names) > 0:
        for fn in file_names:
            if fn.find(postfix) != -1 and fn[-len(postfix):] == postfix:
                file_list.append(fn)
    return file_list


def get_file_list_by_postfix(path, postfix, filter_jar=""):
    file_list = []
    for dirs in os.walk(path):
        files = get_file_list(find_path=dirs[0], postfix=postfix)
        for file_path in files:
            if "" != file_path and -1 == file_path.find(__file__):
                pos = file_path.rfind(os.sep)
                file_name = file_path[pos + 1:]
                file_path = os.path.join(dirs[0], file_path)
                if filter_jar != "" and file_name == filter_jar:
                    print("Skipped %s" % file_path)
                    continue
                file_list.append(file_path)
    return file_list


def is_need_to_be_parsed(filepath):
    for item in filter_file_name_list:
        if -1 != filepath.find(item):
            return False
    return True


def get_pubilc_func_list_from_headfile(cxx_header_filepath):
    pubilc_func_list = []
    try:
        cpp_header = CppHeaderParser.CppHeader(cxx_header_filepath)
        for classname in cpp_header.classes:
            class_name = classname
            curr_class = cpp_header.classes[classname]
            for func in curr_class["methods"]["public"]:
                func_returntype = func["rtnType"]
                func_name = func["name"]
                if class_name in FILTER_CLASS_ATTRIBUTE_LIST:
                    class_name = func_name
                if func_returntype.find("KVSTORE_API") != -1:
                    func_returntype = func_returntype.replace("KVSTORE_API", "").strip()
                if func_name.isupper():
                    continue
                if class_name == func_name:
                    destructor = func["destructor"]
                    if destructor:
                        func_name = f"~{func_name}"
                    func_returntype = ""
                debug = func["debug"].replace("KVSTORE_API", "")
                debug = debug.replace(" ", "")
                debug = debug.strip("{")
                if debug.endswith("=delete;"):
                    continue
                if debug.endswith("=default;"):
                    continue
                if debug.startswith("inline"):
                    continue
                if debug.startswith("constexpr"):
                    continue
                if debug.startswith("virtual"):
                    continue
                template = func["template"]
                if template:
                    continue
                param_type_list = [t["type"] for t in func["parameters"]]
                pubilc_func_list.append((cxx_header_filepath, class_name,
                                         func_name, param_type_list, func_returntype))
        for func in cpp_header.functions:
            func_returntype = func["rtnType"]
            func_name = func["name"]
            if func_returntype.find("KVSTORE_API") != -1:
                func_returntype = func_returntype.replace("KVSTORE_API", "").strip()
            if func_name.isupper():
                continue
            template = func["template"]
            if template:
                continue
            debug = func["debug"].replace("KVSTORE_API", "")
            debug = debug.replace(" ", "")
            debug = debug.strip("{")
            if debug.startswith("inline"):
                continue
            if debug.startswith("constexpr"):
                continue
            param_type_list = [t["type"] for t in func["parameters"]]
            pubilc_func_list.append(
                (cxx_header_filepath, "", func_name, param_type_list,
                 func_returntype)
            )
    except CppHeaderParser.CppParseError:
        print("")
    return pubilc_func_list


def get_sdk_interface_func_list(part_name):
    interface_func_list = []
    sub_path = load_json_data().get(part_name, "")
    if sub_path == "":
        return interface_func_list

    sdk_path = os.path.join(CODEPATH, "out", product_name, sub_path)
    if os.path.exists(sdk_path):
        file_list = get_file_list_by_postfix(sdk_path, ".h")
        for file in file_list:
            try:
                if is_need_to_be_parsed(file):
                    interface_func_list += get_pubilc_func_list_from_headfile(file)
            except Exception:
                print("get interface error ", sdk_path)
    else:
        print("Error: %s is not exist." % sdk_path)
    return interface_func_list


def get_function_info_string(func_string):
    function_info = ""
    cxxfilt_filepath = "/usr/bin/c++filt"
    if os.path.exists(cxxfilt_filepath):
        command = ["c++filt", func_string]
        function_info = subprocess.check_output(command, shell=False)
    else:
        print("/usr/bin/c++filt is not exist.")
    return function_info


def get_covered_function_list(subsystem_name):
    covered_function_list = []
    file_name = f"{subsystem_name}_strip.info"
    file_path = os.path.join(SUB_SYSTEM_INFO_PATH, file_name)
    if os.path.exists(file_path):
        with open(file_path, "r") as fd:
            for line in fd:
                if line.startswith("FNDA:"):
                    sub_line_string = line[len("FNDA:"):].replace("\n", "").strip()
                    temp_list = sub_line_string.split(",")
                    if len(temp_list) == 2 and int(temp_list[0]) != 0:
                        func_info = get_function_info_string(temp_list[1])
                        if "" == func_info:
                            continue
                        func_info = func_info.replace("\n", "")
                        if func_info == temp_list[1] and func_info.startswith("_"):
                            continue
                        covered_function_list.append(func_info)
    else:
        pass
    return covered_function_list


def get_para_sub_string(content):
    start_index = -1
    ended_index = -1
    parentheses_list_left = []
    parentheses_list_right = []

    for index in range(len(content)):
        char = content[index]
        if "<" == char:
            if 0 == len(parentheses_list_left):
                start_index = index
            parentheses_list_left.append(char)
            continue
        if ">" == char:
            parentheses_list_right.append(char)
            if len(parentheses_list_left) == len(parentheses_list_right):
                ended_index = index
                break
            continue

    if -1 == start_index:
        substring = content
    else:
        if -1 != ended_index:
            substring = content[start_index:ended_index + 1]
        else:
            substring = content[start_index:]

    return substring


def filter_para_sub_string(source):
    content = source
    if content != "":
        while True:
            pos = content.find("<")
            if -1 != pos:
                substring = get_para_sub_string(content[pos:])
                content = content.replace(substring, "")
            else:
                break
    return content


def get_function_para_count(func_info):
    pos_start = func_info.find("(")
    pos_end = func_info.rfind(")")
    content = func_info[pos_start + 1: pos_end]
    if "" == content:
        return 0
    content = filter_para_sub_string(content)
    para_list = content.split(",")
    return len(para_list)


def get_covered_result_data(public_interface_func_list, covered_func_list):
    coverage_result_list = []
    for item in public_interface_func_list:
        data_list = list(item)
        class_name = data_list[1]
        func_name = data_list[2]
        para_list = data_list[3]
        return_val = data_list[4]
        para_string = ""
        for index in range(len(para_list)):
            if para_list[index].strip() == "":
                continue
            curr_para = para_list[index]
            para_string += curr_para
            if index < len(para_list) - 1:
                para_string += ", "
        fun_string = f"{return_val}' '{func_name}({para_string.strip().strip(',')})"
        fun_string = fun_string.strip()
        fun_string = filter_para_sub_string(fun_string)

        if class_name != "":
            find_string = f"::{class_name}::{func_name}("
        else:
            find_string = func_name
        func_info_list = []
        for line in covered_func_list:
            if -1 != line.find(find_string):
                func_info_list.append(line)
        curr_list = [class_name, fun_string]
        if len(func_info_list) == 0:
            curr_list.append("N")
        elif len(func_info_list) == 1:
            curr_list.append("Y")
        else:
            interface_para_count = len(para_list)
            find_flag = False
            for funcinfo in func_info_list:
                if find_string == funcinfo:
                    curr_list.append("Y")
                    break
                para_count = get_function_para_count(funcinfo)
                if interface_para_count == para_count:
                    curr_list.append("Y")
                    find_flag = True
                    break
            if not find_flag:
                curr_list.append("N")
        coverage_result_list.append(curr_list)
    return coverage_result_list


def get_interface_coverage_result_list(subsystem_name, subsystem_part_dict):
    part_list = subsystem_part_dict.get(subsystem_name, [])
    public_interface_func_list = []
    for part_str in part_list:
        try:
            interface_func_list = get_sdk_interface_func_list(part_str)
            public_interface_func_list.extend(interface_func_list)
        except Exception:
            print("####")
    covered_func_list = get_covered_function_list(subsystem_name)
    interface_coverage_result_list = get_covered_result_data(
        public_interface_func_list, covered_func_list)
    return interface_coverage_result_list


def get_coverage_data(data_list):
    covered_count = 0
    total_count = len(data_list)
    if 0 != total_count:
        for item in data_list:
            if "Y" == item[2] or "Recorded" == item[2]:
                covered_count += 1
        coverage = str(covered_count * 100 / total_count) + "%"
    else:
        coverage = "0%"
    return covered_count, coverage


def get_summary_data(interface_data_list):
    summary_list = []
    total_count = 0
    covered_count = 0

    for item in interface_data_list:
        subsystem_name = item[0]
        data_list = item[1]
        if 0 != len(data_list):
            count, coverage = get_coverage_data(data_list)
            summary_list.append([subsystem_name, len(data_list), count, coverage])
            total_count += len(data_list)
            covered_count += count
    if 0 != total_count:
        total_coverage = str(covered_count * 100 / total_count) + "%"
        summary_list.append(["Summary", total_count, covered_count, total_coverage])
    return summary_list


def make_summary_file(summary_list, output_path):
    report_path = os.path.join(output_path, "coverage_summary_file.xml")
    try:
        with open(report_path, "w") as fd:
            fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            fd.write('<coverage>\n')
            for item in summary_list:
                fd.write("    <item subsystem_name=\"%s\" "
                         "function_count=\"%s\" coverage_value=\"%s\" />\n" % (
                    item[0], str(item[1]), item[3]))
            fd.write('</coverage>\n')
    except(IOError, ValueError):
        print("Error for make coverage result:",)


def make_result_file(interface_data_list, summary_list, output_path, title_name):
    report_path = os.path.join(output_path, "ohos_interfaceCoverage.html")
    make_report.create_html_start(report_path)
    make_report.create_title(report_path, title_name, summary_list)
    make_report.create_summary(report_path, summary_list)
    for item in interface_data_list:
        subsystem_name = item[0]
        data_list = item[1]
        if 0 == len(data_list):
            continue
        count, coverage = get_coverage_data(data_list)
        make_report.create_table_test(
            report_path, subsystem_name, data_list, len(data_list), count)
    make_report.create_html_ended(report_path)


def make_coverage_result_file(interface_data_list, output_path, title_name):
    summary_list = get_summary_data(interface_data_list)
    make_summary_file(summary_list, output_path)
    make_result_file(interface_data_list, summary_list, output_path, title_name)


def make_interface_coverage_result():
    subsystem_name_list = system_name_list
    interface_data_list = []
    subsystem_part_dict = get_subsystem_part_list(CODEPATH)
    for subsystem_name in subsystem_name_list:
        coverage_result_list = get_interface_coverage_result_list(
            subsystem_name, subsystem_part_dict)
        interface_data_list.append([subsystem_name, coverage_result_list])
    make_coverage_result_file(interface_data_list, OUTPUT_REPORT_PATH,
                              "Inner Interface")


if __name__ == "__main__":
    current_path = os.getcwd()
    _init_sys_config()
    from localCoverage.utils import get_product_name, get_target_cpu
    product_name = get_product_name(CODEPATH)
    cpu_type = get_target_cpu(CODEPATH)
    PATH_INFO_PATH = "out/{}/innerkits/ohos-{}".format(product_name, cpu_type)
    OUTPUT_JSON_PATH = "out/{}/packages/phone/innerkits/ohos-{}".format(
        product_name, cpu_type)
    KIT_MODULES_INFO = "out/{}/packages/phone/innerkits/ohos-{}/kits_modules_info.json".format(
        product_name, cpu_type)

    system_args = sys.argv[1]
    system_name_list = system_args.split(",")
    get_innerkits_json.gen_parts_info_json(
        get_innerkits_json.get_parts_list(os.path.join(CODEPATH, PATH_INFO_PATH)),
        os.path.join(CODEPATH, OUTPUT_JSON_PATH), cpu_type
    )
    if len(system_name_list) > 0:
        make_interface_coverage_result()
    else:
        print("subsystem_name not exists!")
