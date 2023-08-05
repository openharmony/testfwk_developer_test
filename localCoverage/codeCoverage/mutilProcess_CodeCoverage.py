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
import multiprocessing
import sys
from multiprocessing import Process

# 子系统json目录
SYSTEM_JSON = "test/testfwk/developer_test/localCoverage/codeCoverage/subsystem_config.json"
# 覆盖率gcda
COVERAGE_GCDA_RESULTS = "test/testfwk/developer_test/localCoverage/codeCoverage/results/coverage/data/cxx"
# 报告路径
REPORT_PATH = "test/testfwk/developer_test/localCoverage/codeCoverage/results/coverage/reports/cxx"
# llvm-gcov.sh
LLVM_GCOV = "test/testfwk/developer_test/localCoverage/codeCoverage/llvm-gcov.sh"
# 测试套划分步长
STEP_SIZE = 10


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
    except IOError:
        print("Error : command {} execute faild!".format(cmd_list))
        return_flag = False

    return return_flag


def execute_command(command, printflag=False):
    try:
        cmd_list = shlex.split(command)
        coverage_log_path = os.path.join(
            CODEPATH, "test/testfwk/developer_test/localCoverage", "coverage.log")
        with open(coverage_log_path, 'a') as fd:
            call(cmd_list, printflag, fd, fd)
    except IOError:
        print("Error: Exception occur in open error")


def get_subsystem_config_info():
    filter_subsystem_name_list = [
        "subsystem_examples",
    ]
    subsystem_info_dic = {}
    subsystem_config_filepath = os.path.join(CODEPATH, SYSTEM_JSON)
    if os.path.exists(subsystem_config_filepath):
        data = None
        with open(subsystem_config_filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            print("subsystem config file error.")
        for value in data.values():
            subsystem_name = value.get("name")
            if subsystem_name in filter_subsystem_name_list:
                continue
            subsystem_dir = value.get('dir')
            subsystem_path = value.get('path')
            subsystem_project = value.get('project')
            subsystem_rootpath = []
            for path in subsystem_path:
                subsystem_rootpath.append(os.path.join(CODEPATH, path))
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
        for subsystem_rootpath_item in subsystem_rootpath:
            if os.path.exists(subsystem_rootpath_item):
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
            os.path.join(CODEPATH, OUTPUT), gcda_strip_path, gcno_name
        )
        if os.path.exists(gcno_path):
            shutil.copy(gcno_path, dir_name)
        else:
            print(f"{gcno_path} not exists!")


def get_module_gcno_files(cov_path, dir_name):
    for root, dirs, files in os.walk(dir_name):
        get_gcno_files(cov_path, root)


def gen_subsystem_trace_info(subsystem, data_dir, test_dir, lcovrc_path):
    src_dir = os.path.join(CODEPATH, OUTPUT)
    single_info_path = os.path.join(
        CODEPATH, REPORT_PATH, "single_test", test_dir
    )
    if not os.path.exists(single_info_path):
        os.makedirs(single_info_path)
    output_name = os.path.join(
        CODEPATH, single_info_path, f"{subsystem}_output.info"
    )
    if not os.path.exists(src_dir):
        print(f"Sours path {src_dir} not exists!")
        return

    cmd = "lcov -c -b {} -d {} --gcov-tool {} --config-file {} -o {} --ignore-errors source,gcov".format(
        src_dir, data_dir, os.path.join(CODEPATH, LLVM_GCOV), lcovrc_path, output_name)
    print("single_test**##father_pid:%s##child_pid:%s cmd:%s config file:%s" % (
        os.getpid(), os.getppid(), cmd, lcovrc_path
    ))
    execute_command(cmd)


def cut_info(subsystem, test_dir):
    trace_file = os.path.join(
        CODEPATH, REPORT_PATH, "single_test",
        test_dir,  f"{subsystem}_output.info"
    )
    output_name = os.path.join(
        CODEPATH, REPORT_PATH, "single_test",
        test_dir, f"{subsystem}_strip.info"
    )

    remove = r"'*/third_party/*' 'sdk/android-arm64/*'"
    if not os.path.exists(trace_file):
        print(f"Error: trace file {trace_file} not exists!")
        return

    cmd = "lcov --remove {} {} -o {}".format(trace_file, remove, output_name)
    execute_command(cmd)


def gen_info(cov_path, test_dir, subsystem_list, lcovrc_path):
    if len(subsystem_list) == 0:
        print("Error: get subsystem list failed, can not generate trace info")
        return

    loop = 0
    for subsystem in list(set(subsystem_list)):
        subsystem_path, subsystem_rootpath = get_subsystem_rootpath(subsystem)
        for subsys_path in subsystem_path:
            subsystem_data_abspath = os.path.join(cov_path, "obj", subsys_path)
            # check  id subsystem data is exists
            if not os.path.exists(subsystem_data_abspath):
                continue

            # copy gcno to the gcda same directory
            get_module_gcno_files(cov_path, subsystem_data_abspath)

            # generate coverage info for each subsystem
            gen_subsystem_trace_info(
                f"{subsystem}#{subsys_path.replace('/', '_')}#{ str(loop)}",
                subsystem_data_abspath, test_dir, lcovrc_path
            )

            # remove some type which useless
            cut_info(f"{subsystem}#{subsys_path.replace('/', '_')}#{str(loop)}", test_dir)

        loop += 1


def generate_coverage_info(single_test_dir_list, lcovrc_path, subsystem_list):
    cov_path = os.path.join(CODEPATH, COVERAGE_GCDA_RESULTS)
    for index, cur_test_dir in enumerate(single_test_dir_list):
        cur_test_abs_dir = os.path.join(cov_path, cur_test_dir)
        gen_info(cur_test_abs_dir, cur_test_dir, subsystem_list, lcovrc_path)


def gen_all_test_info(subsystem_list):
    cov_path = os.path.join(CODEPATH, COVERAGE_GCDA_RESULTS)
    print(os.getpid(), os.getppid())
    single_test_dir_list = []
    for root, dirs, files in os.walk(cov_path):
        single_test_dir_list = dirs
        break

    return single_test_dir_list


def merge_subsystem_info_from_all_test(subsystem):
    single_test_info_path = os.path.join(
        CODEPATH, REPORT_PATH, "single_test"
    )
    subsystem_info_list = []
    subsystem_info_name = f"{subsystem}_strip.info"
    for root, dirs, files in os.walk(single_test_info_path):
        for file in files:
            if file.startswith(subsystem) and file.endswith("_strip.info"):
                subsystem_info_path_tmp = os.path.join(
                    single_test_info_path, root, file
                )
                print(f"##{subsystem_info_path_tmp}")
                subsystem_info_list.append(subsystem_info_path_tmp)

    if len(subsystem_info_list) == 0:
        return

    info_output_name = os.path.join(
        CODEPATH, REPORT_PATH, subsystem_info_name
    )
    cmd = "lcov -a {} -o {}".format(
        " -a ".join(subsystem_info_list), info_output_name
    )
    execute_command(cmd)


def merge_all_test_subsystem_info(subsystem_list):
    single_test_info_path = os.path.join(
        CODEPATH, REPORT_PATH, "single_test"
    )
    if not os.path.exists(single_test_info_path):
        print(f"Error: the single test info path "
              f"{single_test_info_path} not exist")
        return

    for subsystem in subsystem_list:
        print(f"Merging all {subsystem} info from test data")
        merge_subsystem_info_from_all_test(subsystem)


def merge_info(report_dir):
    if not os.path.exists(report_dir):
        print(f"Error: report dir {report_dir} not exists!")
        return

    subsystem_name_list = get_files_from_dir(report_dir, "_strip.info")
    if len(subsystem_name_list) == 0:
        print("Error: get subsystem trace files in report directory failed.")
        return

    trace_file_list = []
    for subsystem in subsystem_name_list:
        trace_file_name = os.path.join(report_dir, subsystem)
        trace_file_list.append(trace_file_name)

    cmd = "lcov -a {} -o {}".format(
        " -a ".join(trace_file_list), os.path.join(report_dir, "ohos_codeCoverage.info")
    )
    execute_command(cmd)


def merge_all_subsystem_info():
    print("Merging all the subsystem trace files")
    merge_info(os.path.join(CODEPATH, REPORT_PATH))


def gen_html(cov_path):
    tracefile = os.path.join(CODEPATH, REPORT_PATH, "ohos_codeCoverage.info")
    if not os.path.exists(tracefile):
        print(f"Error: the trace file {tracefile} not exists!")
        return

    cmd = "genhtml --branch-coverage --demangle-cpp -o {} -p {} --ignore-errors source {}".format(
        os.path.join(CODEPATH, REPORT_PATH, "html"), CODEPATH, tracefile)
    execute_command(cmd)


def gen_final_report(cov_path):
    print("Generating the html report")
    gen_html(cov_path)


if __name__ == '__main__':
    current_path = os.path.abspath(os.path.dirname(__name__))
    CODEPATH = current_path.split("/test/testfwk/developer_test")[0]
    # lcovrc配置文件集合
    LCOVRC_SET = f"{CODEPATH}/test/testfwk/developer_test/localCoverage/codeCoverage/coverage_rc"
    _init_sys_config()
    from localCoverage.utils import get_product_name
    # 编译生成的out路径
    OUTPUT = "out/{}".format(get_product_name(CODEPATH))

    case_list = gen_all_test_info(subsystem_list=get_subsystem_name_list())
    multiprocessing.set_start_method("fork")  # fork spawn forkserver
    start = end = 0
    Tag = False
    process_list = []
    for i in range(len(case_list)):
        lcov_path = f"{LCOVRC_SET}/lcovrc_cov_{str(i)}"
        print(lcov_path)
        if os.path.exists(lcov_path):
            print(f"{lcov_path}{'@' * 20}yes")
        else:
            raise Exception("mutilProcess have error -rc path not existed. "
                            "please fix add run")

        start = end
        end += STEP_SIZE
        if end >= len(case_list):
            end = len(case_list)
            Tag = True

        p = Process(target=generate_coverage_info,
                    args=(case_list[start:end], lcov_path,
                          get_subsystem_name_list()))
        p.daemon = True
        p.start()
        process_list.append(p)
        if Tag:
            break

    for i in process_list:
        i.join()

    merge_all_test_subsystem_info(subsystem_list=get_subsystem_name_list())
    merge_all_subsystem_info()
    gen_final_report(os.path.join(CODEPATH, COVERAGE_GCDA_RESULTS))
