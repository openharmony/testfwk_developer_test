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
import json
import shutil
import shlex
import subprocess
import sys
import stat

FLAGS = os.O_WRONLY | os.O_APPEND | os.O_CREAT
MODES = stat.S_IWUSR | stat.S_IRUSR

# 子系统json目录
SYSTEM_JSON = "build/subsystem_config.json"
# 覆盖率gcda
COVERAGE_GCDA_RESULTS = "test/local_coverage/code_coverage/results/coverage/data/cxx"
# 报告路径
REPORT_PATH = "test/local_coverage/code_coverage/results/coverage/reports/cxx"
# llvm-gcov.sh
LLVM_GCOV = "test/local_coverage/code_coverage/llvm-gcov.sh"


def _init_sys_config():
    sys.localcoverage_path = os.path.join(current_path, "..")
    sys.path.insert(0, sys.localcoverage_path)


def call(cmd_list, is_show_cmd=False, out=None, err=None):
    return_flag = False
    try:
        if is_show_cmd:
            print("execute command: {}".format(" ".join(cmd_list)))
        if 0 == subprocess.call(cmd_list, shell=False, stdout=out, stderr=err):
            return_flag = True
    except Exception:
        print("Error : command {} execute faild!".format(cmd_list))
        return_flag = False
    return return_flag


def execute_command(command, printflag=False):
    try:
        cmd_list = shlex.split(command)
        coverage_log_path = os.path.join(
            CODEPATH, "test/testfwk/developer_test/local_coverage", "coverage.log")
        with os.fdopen(os.open(coverage_log_path, FLAGS, MODES), 'a') as fd:
            call(cmd_list, printflag, fd, fd)
    except IOError:
        print("Error: Exception occur in open err")


def get_subsystem_config_info():
    subsystem_info_dic = {}
    subsystem_config_filepath = os.path.join(CODEPATH, SYSTEM_JSON)
    if os.path.exists(subsystem_config_filepath):
        data = None
        with open(subsystem_config_filepath, 'r') as f:
            data = json.load(f)
        if not data:
            print("subsystem config file error.")
        for value in data.values():
            subsystem_name = value.get('name')
            subsystem_dir = value.get('dir')
            subsystem_path = value.get('path')
            subsystem_project = value.get('project')
            subsystem_rootpath = os.path.join(CODEPATH, subsystem_path)
            subsystem_info_dic[subsystem_name] = [
                subsystem_project, subsystem_dir,
                subsystem_path, subsystem_rootpath
            ]
    return subsystem_info_dic


def get_subsystem_name_list():
    subsystem_name_list = []
    subsystem_info_dic = get_subsystem_config_info()
    for key in subsystem_info_dic.keys():
        subsystem_rootpath = subsystem_info_dic[key][3]
        if os.path.exists(subsystem_rootpath):
            subsystem_name_list.append(key)
    return subsystem_name_list


def get_subsystem_rootpath(subsystem_name):
    subsystem_path = ""
    subsystem_rootpath = ""
    subsystem_info_dic = get_subsystem_config_info()
    for key in subsystem_info_dic.keys():
        if key == subsystem_name:
            subsystem_path = subsystem_info_dic[key][2]
            subsystem_rootpath = subsystem_info_dic[key][3]
            break
    return subsystem_path, subsystem_rootpath


def is_filterout_dir(ignore_prefix, check_path):
    # 屏蔽列表
    filter_out_list = ["unittest", "third_party", "test"]
    for item in filter_out_list:
        check_list = check_path[len(ignore_prefix):].split("/")
        if item in check_list:
            return True
    return False


def rm_unnecessary_dir(cov_path):
    topdir = os.path.join(cov_path, "obj")
    for root, dirs, files in os.walk(topdir):
        if is_filterout_dir(topdir, root):
            shutil.rmtree(root)


def get_files_from_dir(find_path, postfix=None):
    names = os.listdir(find_path)
    file_list = []
    for fn in names:
        if not os.path.isfile(os.path.join(find_path, fn)):
            continue
        if postfix is not None:
            if fn.endswith(postfix):
                file_list.append(fn)
        else:
            file_list.append(fn)
    return file_list


def get_gcno_files(cov_path, dir_name):
    gcda_strip_path = dir_name[len(cov_path) + 1:]
    gcda_list = get_files_from_dir(dir_name, ".gcda")
    for file_name in gcda_list:
        gcno_name = f"{os.path.splitext(file_name)[0]}.gcno"
        gcno_path = os.path.join(
            os.path.join(CODEPATH, OUTPUT), gcda_strip_path, gcno_name)
        if os.path.exists(gcno_path):
            if os.path.exists(gcno_path):
                shutil.copy(gcno_path, dir_name)
        else:
            print("%s not exists!", gcno_path)


def get_module_gcno_files(cov_path, dir_name):
    for root, dirs, files in os.walk(dir_name):
        get_gcno_files(cov_path, root)


def gen_subsystem_trace_info(subsystem, data_dir, test_dir):
    src_dir = os.path.join(CODEPATH, OUTPUT)
    single_info_path = os.path.join(
        CODEPATH, REPORT_PATH, "single_test", test_dir)
    if not os.path.exists(single_info_path):
        os.makedirs(single_info_path)
    output_name = os.path.join(
        CODEPATH, single_info_path, f"{subsystem}_output.info")
    if not os.path.exists(src_dir):
        print("Sours path %s not exist!", src_dir)
        return
    cmd = "lcov -c -b {} -d  {} --gcov-tool {} -o {} --ignore-errors source,gcov".format(
        src_dir, data_dir, os.path.join(CODEPATH, LLVM_GCOV), output_name)
    print(f"single_test**{cmd}")
    execute_command(cmd)


def cut_info(subsystem, test_dir):
    trace_file = os.path.join(
        CODEPATH, REPORT_PATH, "single_test",
        test_dir, f"{subsystem}_output.info")
    output_name = os.path.join(
        CODEPATH, REPORT_PATH, "single_test",
        test_dir, f"{subsystem}_strip.info")
    remove = r"'*/unittest/*' '*/third_party/*' 'sdk/android-arm64/*'"
    if not os.path.exists(trace_file):
        print("Error: trace file %s not exisit!", trace_file)
        return
    cmd = "lcov --remove {} {} -o {}".format(trace_file, remove, output_name)
    execute_command(cmd)


def gen_info(cov_path, test_dir, subsystem_list):
    if len(subsystem_list) == 0:
        return
    for subsystem in subsystem_list:
        (subsystem_path, subsystem_rootpath) = get_subsystem_rootpath(subsystem)
        subsystem_data_abspath = os.path.join(cov_path, "obj", subsystem_path)
        if not os.path.exists(subsystem_data_abspath):
            continue
        get_module_gcno_files(cov_path, subsystem_data_abspath)
        gen_subsystem_trace_info(subsystem, subsystem_data_abspath, test_dir)
        cut_info(subsystem, test_dir)


def gen_all_test_info(subsystem_list):
    cov_path = os.path.join(CODEPATH, COVERAGE_GCDA_RESULTS)
    single_test_dir_list = []
    for root, dirs, files in os.walk(cov_path):
        single_test_dir_list = dirs
        break
    for index, cur_test_dir in enumerate(single_test_dir_list):
        cur_test_abs_dir = os.path.join(cov_path, cur_test_dir)
        rm_unnecessary_dir(cur_test_abs_dir)
        gen_info(cur_test_abs_dir, cur_test_dir, subsystem_list)


def merge_subsystem_info_from_all_test(subsystem):
    single_test_info_path = os.path.join(CODEPATH, REPORT_PATH, "single_test")
    subsystem_info_list = []
    subsystem_info_name = f"{subsystem}_strip.info"
    for root, dirs, files in os.walk(single_test_info_path):
        if subsystem_info_name in files:
            subsystem_info_path_tmp = os.path.join(
                single_test_info_path, root, subsystem_info_name)
            subsystem_info_list.append(subsystem_info_path_tmp)
    if len(subsystem_info_list) == 0:
        return
    info_output_name = os.path.join(
        CODEPATH, REPORT_PATH, subsystem_info_name)
    cmd = "lcov -a {} -o {}".format(
        " -a ".join(subsystem_info_list), info_output_name)
    execute_command(cmd)


def merge_all_test_subsystem_info(subsystem_list):
    single_test_info_path = os.path.join(
        CODEPATH, REPORT_PATH, "single_test")
    if not os.path.exists(single_test_info_path):
        print("Error: the single test info path %s not exist",
              single_test_info_path)
        return
    for subsystem in subsystem_list:
        print("Merging all %s info from test data......", subsystem)
        merge_subsystem_info_from_all_test(subsystem)


def merge_info(report_dir):
    if not os.path.exists(report_dir):
        print("Error: report dir %s not exist", report_dir)
        return
    subsystem_name_list = get_files_from_dir(report_dir, "_strip.info")
    if len(subsystem_name_list) == 0:
        print("Error: get subsytem trace files in \report directory failed.")
        return
    trace_file_list = []
    for subsystem in subsystem_name_list:
        trace_file_name = os.path.join(report_dir, subsystem)
        trace_file_list.append(trace_file_name)
    cmd = "lcov -a {} -o {}".format(
        " -a ".join(trace_file_list), os.path.join(report_dir, "ohos_codeCoverage.info"))
    execute_command(cmd)


def merge_all_subsystem_info():
    print("Merging all the sysbsystem trace files......")
    merge_info(os.path.join(CODEPATH, REPORT_PATH))


def gen_html(cov_path):
    tracefile = os.path.join(CODEPATH, REPORT_PATH, "ohos_codeCoverage.info")
    if not os.path.exists(tracefile):
        print("Error: the trace file %s not exist", tracefile)
        return
    cmd = "genhtml --branch-coverage --demangle-cpp -o {} -p {} --ignore-errors source {}".format(
        os.path.join(CODEPATH, REPORT_PATH, "html"), CODEPATH, tracefile)
    execute_command(cmd)


def gen_final_report(cov_path):
    print("Generating the html report......")
    gen_html(cov_path)


if __name__ == "__main__":
    current_path = os.path.abspath(os.path.dirname(__name__))
    CODEPATH = current_path.split("/test/testfwk/developer_test")[0]
    _init_sys_config()
    from local_coverage.utils import get_product_name
    # 编译生成的out路径
    OUTPUT = "out/{}".format(get_product_name(CODEPATH))

    gen_all_test_info(subsystem_list=get_subsystem_name_list())
    merge_all_test_subsystem_info(subsystem_list=get_subsystem_name_list())
    merge_all_subsystem_info()
    gen_final_report(os.path.join(CODEPATH, COVERAGE_GCDA_RESULTS))
