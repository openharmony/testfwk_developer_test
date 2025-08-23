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
import os
import subprocess
import threading
from datetime import timezone
from datetime import timedelta
from datetime import datetime

from core.arkts_tdd.artts_tdd_report.arkts_tdd_report_generator import ResultConstruction
from core.driver.drivers import _create_empty_result_file
from xdevice import ResultReporter
from xdevice import platform_logger, ExecInfo

ARKPATH = "arkcompiler/runtime_core/static_core/out/bin/ark"
ETSSTDLIBPATH = "arkcompiler/runtime_core/static_core/out/plugins/ets/etsstdlib.abc"

LOG = platform_logger("arkts_tdd_build")


def get_path_code_directory(after_dir):
    """
    拼接绝对路径工具类
    """
    current_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_path)

    root_path = current_dir.split("/test/testfwk/developer_test")[0]

    # 拼接用户传入路径
    full_path = os.path.join(root_path, after_dir)

    return full_path


def run_test(options):
    report_folder_path = options.result_rootpath
    log_path = options.log_path

    result_path = os.path.join(report_folder_path, "result")
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    test_file_dict = options.testdict
    suite_file_list = test_file_dict['ABC']

    testcases_path = options.testcases_path

    os.getcwd()
    result_construction = ResultConstruction()
    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for index, suite_file in enumerate(suite_file_list):
        run_abc_files(suite_file, log_path, testcases_path, result_path, index, suite_file_list, result_construction)

    exec_info = ExecInfo()
    exec_info.test_type = "ARKTS TDD"
    exec_info.device_name = "ALL"
    exec_info.host_info = ""
    exec_info.test_time = test_time
    exec_info.log_path = log_path
    exec_info.platform = "HarmonyOS"
    exec_info.execute_time = ""

    result_report = ResultReporter()
    result_report.__generate_reports__(report_path=report_folder_path,
                                       task_info=exec_info)


def write_output_to_log(result, log_file, testsuite_summary):
    class_name = ''
    case_name = ''
    testcase_result = ''
    testcase_map = {}
    testcase_list = []
    case_index = 0
    testsuite_case_num = 0
    while True:
        # 读取一行输出
        output = result.stdout.readline()
        if result.poll() is not None:
            # 子进程结束，退出循环
            break
        if not output:
            continue
        line = output.rstrip().replace("\n", "").replace("\r", "").replace("\t", " ")

        if line.startswith('[Hypium][suite start]'):
            class_name = line.replace('[Hypium][suite start]', '')
            testsuite_summary[class_name] = {}
            testcase_map = {}
            testcase_list = []
            testsuite_summary[class_name]['case_detail'] = []
            case_index = 0

        if line.startswith('OHOS_REPORT_SUM:'):
            testsuite_case_num = line.replace('OHOS_REPORT_SUM:', '').strip()
            testsuite_summary[class_name]['testsuiteCaseNum'] = testsuite_case_num

        if line.startswith('OHOS_REPORT_STATUS: test='):
            testcase_map = {}
            testsuite_summary[class_name]['case_detail'].append(testcase_map)
            testcase_list.append(testcase_map)
            case_name = line.replace('OHOS_REPORT_STATUS: test=', '')
            testcase_map['case_name'] = case_name
            case_index += 1

        if case_name + ' ; consuming ' in line:
            testcase_result = line[9:13]
            consuming_list = line.split(case_name + ' ; consuming ')
            testcase_consuming = '0'
            if len(consuming_list) > 1:
                testcase_consuming = consuming_list[1].replace('ms', '')
            testcase_map['testcaseResult'] = testcase_result
            testcase_map['testcaseConsuming'] = testcase_consuming
            LOG.info(f'[{case_index}/{testsuite_case_num.strip()}] {class_name}#{case_name} {testcase_result}')

        if testcase_result == 'fail' and line.startswith('[Hypium][failDetail]'):
            testcase_faildetail = line.replace('[Hypium][failDetail]', '')
            testcase_map['testcaseFailDetail'] = testcase_faildetail

        if line.startswith('OHOS_REPORT_STATUS: suiteconsuming='):
            testsuite_consuming = line.replace('OHOS_REPORT_STATUS: suiteconsuming=', '')
            testsuite_summary[class_name]['testsuite_consuming'] = testsuite_consuming

        if line.startswith('OHOS_REPORT_RESULT:'):
            testsuites_result = line.replace("OHOS_REPORT_RESULT: stream=", "")
            testsuites_detail = testsuites_result.split(",")
            for detail in testsuites_detail:
                detail_temp = detail.split(":")
                testsuite_summary[detail_temp[0].strip()] = detail_temp[1].strip()

        if line.startswith('OHOS_REPORT_STATUS: taskconsuming='):
            taskconsuming = line.replace("OHOS_REPORT_STATUS: taskconsuming=", "")
            testsuite_summary["taskconsuming"] = taskconsuming
        # 将输出写入文件
        log_file.write(output)
        log_file.flush()  # 确保内容立即写入文件


def run_abc_files(suite_file, log_path, testcases_path, result_path, index, suite_file_list, result_construction):
    file_name = os.path.basename(suite_file)
    prefix_name, suffix_name = os.path.splitext(file_name)
    suite_name = prefix_name
    suite_log_path = os.path.join(log_path, prefix_name)
    if not os.path.exists(suite_log_path):
        os.makedirs(suite_log_path)

    suite_file_path = os.path.dirname(suite_file)
    module_output_path = suite_file_path.replace(testcases_path, "")
    suite_result_path = os.path.join(result_path, module_output_path.lstrip("/").lstrip("\\"))
    if not os.path.exists(suite_result_path):
        os.makedirs(suite_result_path)

    suite_result_file = os.path.join(suite_result_path, prefix_name + '.xml')
    os.chdir(suite_file_path)
    """
    执行生成的abc文件并生成报告日志
    """
    abs_ark_path = get_path_code_directory(ARKPATH)
    abs_etsstdlib_path = get_path_code_directory(ETSSTDLIBPATH)
    log_file = os.path.join(suite_log_path, f"{suite_name}.log")
    command = [
        abs_ark_path, f"--boot-panda-files={abs_etsstdlib_path}", f"--load-runtimes=ets", f"{file_name}",
        f"OpenHarmonyTestRunner/ETSGLOBAL::main"]
    LOG.info(f"执行命令 {command}")

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    LOG.info(f'[{index + 1} / {len(suite_file_list)}] Executing: {suite_file}')
    testsuite_summary = {}
    return_message = ""
    try:
        result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        with open(log_file, "a") as log_file:
            # 启动线程，实时读取输出并写入文件
            thread = threading.Thread(target=write_output_to_log, args=(result, log_file, testsuite_summary))
            thread.start()

            # 等待子进程完成
            result.wait()
            thread.join()  # 等待线程完成
        stdout, stderr = result.communicate()
        if stderr:
            return_message = stderr
    except Exception as error:
        return_message = str(error)

    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if len(testsuite_summary) != 0:
        result_construction.testsuite_summary = testsuite_summary
        result_construction.start_time = start_time
        result_construction.end_time = end_time
        result_construction.suite_file_name = suite_name
        result_construction.node_construction(suite_result_file)

    if return_message != "":
        error_message = str(return_message)
        error_message = error_message.replace("\"", "")
        error_message = error_message.replace("<", "")
        error_message = error_message.replace(">", "")
        error_message = error_message.replace("&", "")
        _create_empty_result_file(suite_result_file, prefix_name, error_message)


def get_cst_time():
    sh_tz = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai',
    )
    return datetime.now(tz=sh_tz)


def main():
    run_test("Functions")


if __name__ == '__main__':
    main()