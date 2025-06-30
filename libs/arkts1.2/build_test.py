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

es2PandaPath = "arkcompiler/runtime_core/static_core/out/bin/es2panda"
arkLinkPath = "arkcompiler/runtime_core/static_core/out/bin/ark_link"
arkPath = "arkcompiler/runtime_core/static_core/out/bin/ark"
etsStdLibPath = "arkcompiler/runtime_core/static_core/out/plugins/ets/etsstdlib.abc"
configPath = "arkcompiler/runtime_core/static_core/out/bin/arktsconfig.json"
hypiumPath = "test/testfwk/arkxtest/jsunit/src_static/"


def build_tools(compileFileList):
    """
    编译工具类
    """
    
    absEs2PandaPath = get_path_code_dircetory(es2PandaPath)
    absTestPath = os.getcwd()
    
    # 1. 创建输出目录
    outputDir = os.path.join(absTestPath, "out")
    os.makedirs(outputDir, exist_ok = True)
    
    # 逐个执行编译命令
    for ets_file in compileFileList:
        try:
            # 获取文件名(不带路径)
            file_name = os.path.basename(ets_file)
            base_name = os.path.splitext(file_name)[0]
            output_file_path = os.path.join(outputDir, f"{base_name}.abc")
            
            # 构造编译命令
            command = [absEs2PandaPath, ets_file, "--output", output_file_path]
            
            # 执行命令并获取输出
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 成功编译
            print(f"成功编译'{ets_file}', 输出路径： {output_file_path}")
            
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
        relative_path = os.path.join(current_dir,ets_file)
        abs_path = get_path_code_dircetory(relative_path)
        file_map[module_name] = [abs_path]
        
    # 3. 定位要写入的 arktsconfig.json文件
    abs_config_path = get_path_code_dircetory(configPath)
    
    # 4. 读取并更新配置
    try:
        with open(abs_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"compilerOptions": { "baseUrl":"/code/arkcompiler/runtime_core/static_core", "paths": {} }}
        
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
    absHypiumPath = get_path_code_dircetory(hypiumPath)
    
    files_to_compile = []
    for root, dirs, files in os.walk(absHypiumPath):
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
    
    absTestPath = os.getcwd()
    test_files = []
    
    for root, dirs, files in os.walk(absTestPath):
        for file in files:
            if file.endswith(".ets"):
                file_abs_path = os.path.join(root, file)
                test_files.append(file_abs_path)
    build_tools(test_files)
    

def link_abc_files(res_file_name):
    """
    链接所有abc文件生成最终的test.abc
    """
    
    absArkLinkPath = get_path_code_dircetory(arkLinkPath)
    absOutPath = os.path.join(os.getcwd(), "out")
    tests_dir_name = res_file_name
    
    abc_files = []

    out_files = [os.path.join("./out", f) for f in os.listdir(absOutPath) if fabc')]
    abc_files.extend(out_files)

    src_json_path = os.path.join(os.getcwd(), "src.json")

    try:
        with open(src_json_path, 'r'):
            src_data = json.load(f)
            src_paths = src_data.get("src_path", [])
            
            for path in src_paths:
                full_path = path
                
                if os.path.isfile(full_path) and full_path.endswith('.abc'):
                    abc_files.append(full_path)
                else:
                    print(f"路径{full_path} 不存在或不是.abc文件，跳过处理。")
    
    except FileNotFoundError:
        print(f"文件 {src_json_path} 未找到，跳过处理")
    except json.JSONDecodeError:
        print(f"文件 {src_json_path} 格式错误无法解析")
    except Exception as e:
        print(f"读取 src.json 时发生错误: {e}")
        
    if abc_files:
        command = [
            absArkLinkPath,
            f"--output={tests_dir_name}.abc",
            "--",
            *abc_files
        ]
        
        print(f"执行命令 {command}")
        
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("命令执行成功")
            print(result.stdout.strip())
            
        except subprocess.CalledProcessError as e:
            print("命令执行失败")
            print(f"错误信息 {e.stderr.strip()}")
            
    else:
        print("没有找到可连接的.abc文件")
        

def run_test(res_file_name):
    """
    执行生成的abc文件并生成报告日志
    """
    absArkPath = get_path_code_dircetory(arkPath)
    absEtsStdLibPath = get_path_code_dircetory(etsStdLibPath)
    tests_dir_name = res_file_name
    log_file = os.path.join(os.getcwd(), f"{tests_dir_name}.log")
    command = [
        absArkPath,
        f"--boot-panda-files={absEtsStdLibPath}",
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