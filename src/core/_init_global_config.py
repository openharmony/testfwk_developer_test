#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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

from xdevice import platform_logger

LOG = platform_logger("init_global_config")

def init_global_config():
    import sys
    import os

    # insert src path for loading xdevice modules
    # 当前脚本运行的绝对路径 去掉最后两个路径
    # 变量注释 framework_src_dir = OpenHarmony/test/developertest
    sys.framework_src_dir = os.path.abspath(os.path.dirname(
        os.path.dirname(__file__)))

    # 将目录存放到sys.path模块中，新添加的目录会优先于其他目录被import检查 0代表最高优先级
    sys.path.insert(0, sys.framework_src_dir)

    # 变量注释 framework_root_dir = OpenHarmony/test/developertest
    # sys.framework_root_dir = "/home/dongwei/OpenHarmony/test/developertest"
    dir = os.getcwd()
    split_dir = dir.split("/",4)
    root_dir = "/"+split_dir[1]+"/"+split_dir[2]+"/"+split_dir[3]
    sys.framework_root_dir = os.path.join(
        root_dir,
        "test",
        "developertest")
    if os.path.exists(sys.framework_root_dir) == False :
        LOG.error("Please execute in the source code.")

    # 变量注释 sys.xdevice_dir = OpenHarmony/test/xdevice/src
    sys.xdevice_dir = os.path.join(
        sys.framework_root_dir,
        "..",
        "xdevice",
        "src")
    sys.path.insert(0, sys.xdevice_dir)

    # 变量注释 sys.xdevice_extension_dir = OpenHarmony/test/xdevice/extension/src
    sys.xdevice_extension_dir = os.path.join(
        sys.framework_root_dir,
        "..",
        "xdevice",
        "extension",
        "src")
    sys.path.insert(1, sys.xdevice_extension_dir)

    # 变量注释 pytest_dir = OpenHarmony/test/developertest/aw/python
    sys.pytest_dir = os.path.join(
        sys.framework_root_dir,
        "aw",
        "python")
    sys.path.insert(2, sys.pytest_dir)

    # 变量注释 adapter_dir = OpenHarmony/test/developertest/adapter/aw/python
    sys.adapter_dir = os.path.abspath(os.path.join(
        sys.framework_root_dir,
        "adapter"
        "aw",
        "python"))
    sys.path.insert(3, sys.adapter_dir)

    # 变量注释 hmh_script = OpenHarmony/test/developertest/libs
    sys.hmh_script = os.path.abspath(os.path.join(
        sys.framework_root_dir,
        "libs"))
    sys.path.insert(4, sys.hmh_script)

    # 变量注释 framework_res_dir = OpenHarmony/test/developertest
    sys.framework_res_dir = sys.framework_root_dir

    # 变量注释 exec_dir = OpenHarmony/test/developertest
    sys.exec_dir = sys.framework_root_dir

    from core.common import get_source_code_root_path
    sys.source_code_root_path = get_source_code_root_path(
        sys.framework_root_dir)

    # python的参数配置 设置脚本路径 调度python的xdevice
    from xdevice import Variables
    Variables.exec_dir = sys.framework_root_dir


def _iter_module_plugins(packages):
    import importlib
    import pkgutil
    for package in packages:

        # 获取__path__对象属性的值，若不存在，默认为“”
        pkg_path = getattr(package, "__path__", "")
        pkg_name = getattr(package, "__name__", "")
        if not pkg_name or not pkg_path:
            continue
        _iter_modules = pkgutil.iter_modules(pkg_path, "%s%s" % (
            pkg_name, "."))
        for _, name, _ in _iter_modules:
            importlib.import_module(name)


def _load_internal_plugins():
    import core.driver
    import benchmark.report.benchmark_reporter
    _iter_module_plugins([core.driver, benchmark.report.benchmark_reporter])

    try:
        import xdevice_extension._core.environment
        _iter_module_plugins([xdevice_extension._core.environment])
        import xdevice_extension._core.driver
        _iter_module_plugins([xdevice_extension._core.driver])
    except (ModuleNotFoundError, ImportError):
        pass

    try:
        import script.report
        _iter_module_plugins([script.report])
    except (ModuleNotFoundError, ImportError):
        pass
        

init_global_config()
del init_global_config

_load_internal_plugins()
del _load_internal_plugins

