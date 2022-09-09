#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

# 执行如下命令 获取到的信息
#    show subsystemlist 通过show subsystemlist得到子系统名称列表
#    show partlist      通过show partlist得到对应子系统下的部件名

import sys
import os

from core.constants import ToolCommandType
from core.utils import get_file_list
from core.utils import get_file_list_by_postfix
from core.utils import get_build_output_path
from core.utils import scan_support_product
from core.config.config_manager import UserConfigManager
from core.config.config_manager import FrameworkConfigManager
from core.config.parse_parts_config import ParsePartsConfig

# 支持的设备名称
#    1. ohos-sdk
#    2. rk3568
#    3. Hi3516DV300
#    4. DAYU
#    5. ohos-arm64
#    6. ipcamera_hispark_aries
#    7. ipcamera_hispark_taurus
#    8. wifiiot_hispark_pegasus
CMD_KEY_PRODUCTLIST = "productlist"

# 测试用例类型
#     1. UT
#     2. ACTS
#     3. MST
#     4. ST
#     5. PERF
#     6. SEC
#     7. FUZZ
#     8. RELI
#     9. DST
#     10. BENCHMARK
#     11. ALL
CMD_KEY_TYPELIST = "typelist"

# 子系统名称列表
CMD_KEY_SUBSYSTEMLIST = "subsystemlist"

# 子系统下的部件名
CMD_KEY_PARTLIST = "partlist"

# acts子系统名称列表
CMD_KEY_SUBSYSTEMLIST_ACTS = "actssubsystemlist"

TOOL_VERSION_INFO = """Welcome to DeveloperTest V3.2.2.0
"""

HLEP_COMMAND_INFOMATION = """use help [follow command] for more information:
    """ + \
    "show: " + """Display a list of supported show command.
    """ + \
    "run:  " + """Display a list of supported run command.
    """ + \
    "list: " + """Display a list of supported device.
    """ + \
    "quit: " + """Exit the test framework application.
"""

SUPPORT_COMMAND_SHOW = """use show [follow command] for more information:
    """ + \
    "productlist" + """
    """ + \
    "typelist" + """
    """ + \
    "subsystemlist" + """
    """ + \
    "partlist" + """
"""

RUNCASES_INFOMATION = """run:
    This command is used to execute the selected testcases.
    It includes a series of processes such as use case compilation, \
execution, and result collection.

usage: run [-p PRODUCTFORM]
           [-t [TESTTYPE [TESTTYPE ...]]]
           [-ss [SUBSYSTEM [SUBSYSTEM ...]]]
           [-tp [TESTPART [TESTPART ...]]]
           [-ts TESTSUIT]
           [-tc TESTCASE]
           [-tl TESTLEVEL]
           [-repeat NUMBER]
           [-hl]
           [-rh HISCOMMAND-INDEX]
           [-retry]

optional arguments:
  -p PRODUCTFORM, --productform PRODUCTFORM
                        Specified product form
  -t [TESTTYPE [TESTTYPE ...]], --testtype [TESTTYPE [TESTTYPE ...]]
                        Specify test type(UT,MST,ST,PERF,ALL)
  -ss [SUBSYSTEM [SUBSYSTEM ...]], --subsystem [SUBSYSTEM [SUBSYSTEM ...]]
                        Specify test subsystem
  -tp [TESTPART [TESTPART ...]], --testpart [TESTPART [TESTPART ...]]
                        Specify test testpart
  -ts TESTSUIT, --testsuit TESTSUIT
                        Specify test suit
  -tc TESTCASE, --testcase TESTCASE
                        Specify test case
  -tl TESTLEVEL, --testlevel TESTLEVEL
  --repeat NUMBER
  -hl, --hisotrylist
  -rh INDEX, --runhistory INDEX
  --retry

Examples:
    run -t UT
    run -t UT -ss aafwk
    run -t UT -ss aafwk -tm base_test
    run -t UT -ss aafwk -tm base_test -ts base_test
    run -t UT -ss aafwk -tm base_test -ts base_test -tl 2
    run -t UT -ss aafwk -tm base_test -ts base_test -tc \
AAFwkBaseTest.*
    run -t UT -ss aafwk -tm base_test -ts base_test -tc \
AAFwkBaseTest.object_test_001
    run -t UT -ss aafwk -tm base_test --repeat 3
    run -t MST
    ...
    run -t ALL
    ...
    run -hl
    run -rh 1
    run --retry
    run -t ACTS -ss arkui,ability -ts ActsAceEtsTest;ActsAceEtsStTest;ActsApiTest
"""

LIST_INFOMATION = "list\n" + """
    This command is used to display device list.
"""

QUIT_INFOMATION = "quit\n" + """
    This command is used to exit the test framework application.
"""


#############################################################################
#############################################################################

def select_user_input(data_list):
    data_item_count = len(data_list)
    select_item_value = ""
    select_item_index = -1

    if len(data_list) != 0:
        count = 0
        while True:
            input_data = input("")
            if "" != input_data and input_data.isdigit():
                input_num = int(input_data)
                if input_num > 0 and (input_num <= data_item_count):
                    select_item_index = input_num - 1
                    select_item_value = data_list[input_num - 1]
                    break
                else:
                    print("The data you entered is out of range, \
                        please re-enter:")
                    count += 1
            else:
                if "" == input_data:
                    select_item_index = 0
                    select_item_value = data_list[0]
                    break
                else:
                    print("You entered a non-numeric character, \
                        please re-enter:")
                    count += 1

            if count >= 3:
                print("You entered the error three times in a row, \
                    exit the frame.")
                quit()
                sys.exit(0)
        return select_item_value, select_item_index


# 选择productform
def select_productform():
    select_value = "phone"

    # 列表注释 scan_support_product() = [DAYU,Hi3516,ohos_arm64,ohos_sdk,rk3568]
    scan_product_list = scan_support_product()

    # 从framework_config.xml里取productform节点的value:ipcamera_hispark_aries、ipcamera_hispark_taurus、wifiiot_hispark_pegasus
    config_product_list = \
        FrameworkConfigManager().get_framework_config("productform")

    # 列表注释 productform_list = [DAYU,Hi3516,ohos_arm64,ohos_sdk,rk3568,
    # 列表注释 ipcamera_hispark_aries、ipcamera_hispark_taurus、wifiiot_hispark_pegasus]

    productform_list = scan_product_list + config_product_list
    if len(productform_list) != 0:
        print("Please select the current tested product form:")
        for index, element in enumerate(productform_list):
            print("%d. %s" % (index + 1, element))
        print("default is [1] %s" % productform_list[0])
        select_value, _ = select_user_input(productform_list)
    print(select_value)
    return select_value


def show_wizard_mode():
    wizard_data_dic = {}
    print("+++++++++++++++++++++++++++++++++++++++++++++")

    productform = select_productform()
    if productform == "":
        productform = "phone"
    wizard_data_dic["productform"] = productform

    print("+++++++++++++++++++++++++++++++++++++++++++++")
    print("The environment is ready, please use the run command to test.")
    return wizard_data_dic


#############################################################################
#############################################################################

def display_help_info(para_list):
    if len(para_list) == 0 or para_list[0] != ToolCommandType.TOOLCMD_KEY_HELP:
        print("This command is not support.")
        return

    if len(para_list) > 1:
        display_help_command_info(para_list[1])
    else:
        print(TOOL_VERSION_INFO)
        print(HLEP_COMMAND_INFOMATION)


def display_show_info(para_list, productform):
    if len(para_list) == 0 or para_list[0] != ToolCommandType.TOOLCMD_KEY_SHOW:
        print("This command is not support.")
        return

    if len(para_list) > 1:
        display_show_command_info(para_list[1], productform)
    else:
        print(SUPPORT_COMMAND_SHOW)


def display_version_info(para_list):
    print(TOOL_VERSION_INFO)


#############################################################################
#############################################################################


#############################################################################
#############################################################################


def show_product_list():
    print("List of currently supported productform:")
    scan_product_list = scan_support_product()
    config_product_list = \
        FrameworkConfigManager().get_framework_config("productform")
    productform_list = scan_product_list + config_product_list
    if 0 != len(productform_list):
        for index, element in enumerate(productform_list):
            print("    %d. %s" % (index + 1, element))
    else:
        print("No category specified.")


def show_testtype_list():
    print("List of currently supported test types:")
    testtype_list = FrameworkConfigManager().get_framework_config(
        "test_category")
    if 0 != len(testtype_list):
        for index, element in enumerate(testtype_list):
            print("    %d. %s" % (index + 1, element))
    else:
        print("No category specified.")


# 从OpenHarmony/out/rk3568/build_configs/infos_for_testfwk.json里的subsystem_infos中subsystem_infos下获取subsystemlist
def show_subsystem_list(product_form):
    print("List of currently supported subsystem names:")
    parser = ParsePartsConfig(product_form)
    subsystem_name_list = parser.get_subsystem_name_list()
    if len(subsystem_name_list) == 0:
        return

    subsystem_name_list.sort()
    for index, element in enumerate(subsystem_name_list):
        print("    %d. %s" % (index + 1, element))


def show_acts_subsystem_list():
    print("List of currently supported acts subsystem names:")
    sub_list = ['global', 'security', 'useriam', 'multimedia', 'appexecfwk', 'account', 'communication', 'notification',
    'ability', 'miscservices', 'powermgr', 'startup', 'sensor', 'distributeddatamgr', 'update', 'graphic', 'arkui',
    'storage', 'compileruntime', 'usb', 'multimodalinput', 'resourceschedule',
    'telephony', 'hiviewdfx', 'location', 'barrierfree', 'customization']
    sub_list.sort()
    for index, element in enumerate(sub_list):
        print("    %d. %s" % (index + 1, element.strip()))
    print("end")


# 从OpenHarmony/out/rk3568/build_configs/infos_for_testfwk.json里的subsystem_infos中subsystem_infos下获取partlist
def show_partname_list(product_form):
    print("List of currently supported part names:")
    parser = ParsePartsConfig(product_form)
    subsystem_name_list = parser.get_subsystem_name_list()

    if len(subsystem_name_list) == 0:
        return

    subsystem_name_list.sort()
    subsystem_infos = parser.get_subsystem_infos()
    for subsystem in subsystem_name_list:
        print("%s:" % subsystem)
        part_name_list = subsystem_infos[subsystem]
        part_name_list.sort()
        for index, element in enumerate(part_name_list):
            print("    %d. %s" % (index + 1, element))


def display_help_command_info(command):
    if command == ToolCommandType.TOOLCMD_KEY_SHOW:
        print(SUPPORT_COMMAND_SHOW)
    elif command == ToolCommandType.TOOLCMD_KEY_RUN:
        print(RUNCASES_INFOMATION)
    elif command == ToolCommandType.TOOLCMD_KEY_LIST:
        print(LIST_INFOMATION)
    elif command == ToolCommandType.TOOLCMD_KEY_QUIT:
        print(QUIT_INFOMATION)
    else:
        print("'%s' command no help information." % command)


def display_show_command_info(command, product_form="phone"):
    if command == CMD_KEY_PRODUCTLIST:
        show_product_list()
    elif command == CMD_KEY_TYPELIST:
        show_testtype_list()
    elif command == CMD_KEY_SUBSYSTEMLIST:
        show_subsystem_list(product_form)
    elif command == CMD_KEY_PARTLIST:
        show_partname_list(product_form)
    elif command == CMD_KEY_SUBSYSTEMLIST_ACTS:
        show_acts_subsystem_list()
    else:
        print("This command is not support.")


#############################################################################
#############################################################################
