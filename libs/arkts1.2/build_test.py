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
import sys
import json
import subprocess

ES2PANDAPATH = "arkcompiler/runtime_core/static_core/out/bin/es2panda"
ARKLINKPATH = "arkcompiler/runtime_core/static_core/out/bin/ark_link"
ARKPATH = "arkcompiler/runtime_core/static_core/out/bin/ark"
ETSSTDLIBPATH = "arkcompiler/runtime_core/static_core/out/plugins/ets/etsstdlib.abc"
CONFIGPATH = "arkcompiler/runtime_core/static_core/out/bin/arktsconfig.json"
HYPIUMPATH = "test/testfwk/arkxtest/jsunit/src_static/"


def build_tools(compile_filelist):
    """
    编译工具类
    """
    
    abs_es2panda_path = get_path_code_dircetory(ES2PANDAPATH)
    abs_test_path = os.getcwd()
    
    # 1. 创建输出目录
    output_dir = os.path.join(abs_test_path, "out")
    os.makedirs(output_dir, exist_ok = True)
    
    # 逐个执行编译命令
    for ets_file in compile_filelist:
        try:
            # 获取文件名(不带路径)
            file_name = os.path.base_name(ets_file)
            base_name = os.path.splitext(file_name)[0]
            output_filepath = os.path.join(output_dir, f"{base_name}.abc")
            
            # 构造编译命令
            command = [abs_es2panda_path, ets_file, "--output", output_filepath]
            
            # 执行命令并获取输出
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 成功编译
            print(f"成功编译'{ets_file}', 输出路径： {output_filepath}")
            
        except Exception as e:
            print(f"'{ets_file}'编译失败")
   
   
def get_path_code_dircetory(after_dir):
    """
    拼接绝对路径工具类
    """
    
    current_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_path)
    
    # 查找 /code/ 目录的位置
    code_marker = "/code/"
    code_index = current_dir.find(code_marker)
    
    if code_index == -1:
        raise FileNotFoundError(
            f"路径中没有找到 '/code/',当前路径为: {current_dir}"
        )
    
    # 提取code路径 (包含code目录本身)
    code_base = current_dir[:code_index + len(code_marker)]
    
    # 拼接用户传入路径
    full_path = os.path.join(code_base, after_dir)
    
    return full_path
    
    
def write_arktsconfig_file():
    """
    将当前目录下的 .ets文件生成 file_map, 并追加写入 arktsconfig.json
    """
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 获取当前目录下的所有.ets文件
    ets_files = [f for f in os.listdir(current_dir) if f.endswith('.ets')]
    
    # 2. 构建file_map:{文件名:[文件绝对路径]}
    file_map = {}
    for ets_file in ets_files:
        module_name = os.path.splitext(ets_file)[0]
        relative_path = os.path.join(current_dir, ets_file)
        abs_path = get_path_code_dircetory(relative_path)
        file_map[module_name] = [abs_path]
        
    # 3. 定位要写入的 arktsconfig.json文件
    abs_config_path = get_path_code_dircetory(CONFIGPATH)
    
    # 4. 读取并更新配置
    try:
        with open(abs_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = { "compilerOptions": { "baseUrl": "/code/arkcompiler/runtime_core/static_core", "paths": {} } }
        
    # 5. 更新配置中的paths(保留之前的配置项)
    config.setdefault("compilerOptions", {})
    config["compilerOptions"].setdefault("paths", {})
    config["compilerOptions"]["paths"].update(file_map)
    
    with open(abs_config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    print(f"已成功更新 {abs_config_path}")
    
    
def build_ets_files():
    """
    编译hypium、tools、测试用例文件
    """
    abs_hypium_path = get_path_code_dircetory(HYPIUMPATH)
    
    files_to_compile = []
    for root, dirs, files in os.walk(abs_hypium_path):
        if "testAbility" in dirs:
            dirs.remove("testAbility")
        if "testrunner" in dirs:
            dirs.remove("testrunner")
            
        for f in files:
            if f.endswith(".ets"):
                file_path = os.path.join(root, f)
                files_to_compile.append(file_path)
                
    if not files_to_compile:
        print("未找到可编译的 .ets 文件，跳过编译。")
        return
    build_tools(files_to_compile)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ets_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.ets')]
    build_tools(ets_files)
    
    abs_test_path = os.getcwd()
    test_files = []
    
    for root, dirs, files in os.walk(abs_test_path):
        for file in files:
            if file.endswith(".ets"):
                file_abs_path = os.path.join(root, file)
                test_files.append(file_abs_path)
    build_tools(test_files)
    

def collect_abc_files(res_file_name):
    abs_out_path = os.path.join(os.getcwd(), "out")
    abc_files = []

    # 1. 收集out目录下的.abc文件
    if os.path.exists(abs_out_path):
        out_files = [
            os.path.join("./out", f)
            for f in os.listdir(abs_out_path)
            if f.endswith('.abc')
        ]
        abc_files.extend(out_files)

    # 2. 收集src.json中配置的.abc文件
    abc_files.extend(load_abc_from_src_json())

    return abc_files


def load_abc_from_src_json():
    abc_files = []
    src_json_path = os.path.join(os.getcwd(), "src.json")

    if not os.path.exists(src_json_path):
        print(f"提示: 配置文件 {src_json_path} 未找到，跳过src.json收集")
        return abc_files

    try:
        with open(src_json_path, 'r') as f:
            src_data = json.load(f)
    except json.JSONDecodeError:
        print(f"错误: 配置文件 {src_json_path} JSON格式错误")
        return abc_files
    except Exception as e:
        print(f"读取src.json时发生意外错误: {str(e)}")
        return abc_files

    for path in src_data.get("src_path", []):
        if os.path.isfile(path) and path.endswith('.abc'):
            abc_files.append(path)
        else:
            print(f"警告: 路径 {path} 不存在或不是.abc文件，已跳过")

    return abc_files


def link_abc_files(res_file_name):
    """
    链接所有abc文件生成最终的test.abc
    """
    abs_arklink_path = get_path_code_dircetory(ARKLINKPATH)
    abc_files = collect_abc_files(res_file_name)
    
    if not abc_files:
        print("终止: 没有找到可连接的.abc文件")
        return

    command = [
        abs_arklink_path,
        f"--output={res_file_name}.abc",
        "--",
        *abc_files
    ]
    
    print(f"执行命令: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("状态: 链接成功\n输出:", result.stdout.strip())
        
    except subprocess.CalledProcessError as e:
        print("错误: 链接失败")
        print("错误详情:", e.stderr.strip())
        raise  # 可以选择抛出异常或处理错误
        

def run_test(res_file_name):
    """
    执行生成的abc文件并生成报告日志
    """
    abs_ark_path = get_path_code_dircetory(ARKPATH)
    abs_etsstdlib_path = get_path_code_dircetory(ETSSTDLIBPATH)
    tests_dir_name = res_file_name
    log_file = os.path.join(os.getcwd(), f"{tests_dir_name}.log")
    command = [
        abs_ark_path,
        f"--boot-panda-files={abs_etsstdlib_path}",
        f"--load-runtimes=ets",
        f"{tests_dir_name}.abc",
        f"OpenHarmonyTestRunner/ETSGLOBAL::main"
    ]
    print(f"执行命令 {command}")
    with open(log_file, "w") as f:
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("命令执行成功")
        except subprocess.CalledProcessError as e:
            print("命令执行失败")
            print(f"错误信息 {e.stderr.strip()}")
            
            
def main():
    if len(sys.argv) < 2:
        print("使用方式： python3 build_test.py <resultFileName> ")
        print("实例:")
        print("python3 build_test.py functionsTest")
        sys.exit(1)
        
        res_file_name = sys.argv[1]
        write_arktsconfig_file()
        build_ets_files()
        link_abc_files(res_file_name)
        run_test(res_file_name)
        

if __name__ == '__main__':
    main()