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
import shutil
import json
import re

STATICCOREPATH = "arkcompiler/runtime_core/static_core/"
ES2PANDAPATH = "arkcompiler/runtime_core/static_core/out/bin/es2panda"
CONFIGPATH = "arkcompiler/runtime_core/static_core/out/bin/arktsconfig.json"
HYPIUMPATH = "test/testfwk/arkxtest/jsunit/src_static/"
DESTHYPIUMPATH = "test/testfwk/developer_test/libs/destHypium"
TOOLSPATH = "test/testfwk/developer_test/libs/arkts1.2"
ARKLINKPATH = "arkcompiler/runtime_core/static_core/out/bin/ark_link"


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


def run_command(command):
    """
    执行编译工具链命令
    """
    try:
        print(f'{"*" * 35}开始执行命令：{command}{"*" * 35}')
        command_list = command.split(" ")
        result = subprocess.run(command_list,
                                capture_output=True, text=True, check=True)
        if result.returncode == 0:
            print("命令执行成功")
            print("输出:", result.stdout)
        else:
            print("命令执行失败")
            print("错误:", result.stderr)
        print(f'{"*" * 35}命令：{command}执行结束{"*" * 35}')
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败（返回码: {e.returncode}）")
        print("错误输出:", e.stderr.strip())
        raise
    except FileNotFoundError:
        print("错误：未找到 sudo 命令。请确保已安装 sudo。")
        raise
    except Exception as e:
        print(f"发生错误: {e}")
        raise


def create_soft_link(target_path, link_path):
    try:
        print(f'{"*" * 35}开始创建软连接{"*" * 35}')
        os.symlink(target_path, link_path)
        print(f'{"*" * 35}成功创建软链接：{link_path} -> {target_path}{"*" * 35}')
    except OSError as e:
        print(f'创建软连接失败：{e}')


def run_toolchain_build():
    """
    调用公共方法执行编译工具链命令
    """
    static_core_path = get_path_code_directory(STATICCOREPATH)
    os.path.join(static_core_path, "tools")
    tools_path = os.path.join(static_core_path, "tools")
    os.chdir(tools_path)
    # 创建软链接
    target_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(tools_path))), 'ets_frontend/ets2panda')
    link_path = os.path.join(tools_path, 'es2panda')
    # 删除旧链接
    if os.path.exists(link_path):
        try:
            os.remove(link_path)
            print(f"软连接 {link_path} 已成功删除。")
        except OSError as e:
            print(f"删除软连接 时出错: {e}")
            raise

    relative_path = os.path.relpath(target_path, os.path.dirname(link_path))
    # 创建软链接ln -s ../../../ets_frontend/ets2panda es2panda
    create_soft_link(relative_path, link_path)

    os.chdir(static_core_path)

    command_1 = "sudo -S ./scripts/install-deps-ubuntu -i=dev -i=test"
    command_2 = "sudo apt install gdb"
    command_3 = "pip3 install tqdm"
    command_4 = "pip3 install python-dotenv"
    command_5 = "./scripts/install-third-party --force-clone"
    command_6 = "cmake -B out -DCMAKE_BUILD_TYPE=Debug -DCMAKE_TOOLCHAIN_FILE=./cmake/toolchain/host_clang_default.cmake -GNinja ."
    command_7 = "cmake --build out"
    command_list = [command_1, command_2, command_3, command_4, command_5, command_6, command_7]

    for command in command_list:
        try:
            run_command(command)
        except Exception as e:
            print(f"命令执行失败: {command}")
            print(f"错误详情: {e}")
            print("工具链构建失败，将跳过后续的 hypium 编译。")
            raise


# 删除目录下的特定文件
def delete_specific_files(directory, target_extension):
    for root_path, _, file_names in os.walk(directory):
        for file_name in file_names:
            if file_name != target_extension:
                continue
            file_path = os.path.join(root_path, file_name)
            try:
                os.remove(file_path)
                print(f"已删除文件：{file_path}")
            except Exception as e:
                print(f"删除文件 {file_path} 时出错：{str(e)}")


# 删除某个目录下所有的文件和文件夹
def remove_directory_contents(dir_path):
    print(f'dir_path:{dir_path}')
    if dir_path is not None:
        for root_path, dir_paths, file_names in os.walk(dir_path, topdown=False):
            # 第一步：删除文件
            for file_name in file_names:
                os.remove(os.path.join(root_path, file_name))
            # 第二步：删除空文件夹
            for name in dir_paths:
                os.rmdir(os.path.join(root_path, name))

        if os.path.exists(dir_path):
            print(f'删除路径：{dir_path}')
            os.rmdir(dir_path)


# *************hypium build***************
def write_arktsconfig_file():
    """
    将当前目录下的 .ets文件生成 file_map, 并追加写入 arktsconfig.json
    """
    tools_path = get_path_code_directory(TOOLSPATH)

    # 1. 获取当前目录下的所有.ets文件
    ets_files = [f for f in os.listdir(tools_path) if f.endswith('.ets')]

    # 2. 构建file_map:{文件名:[文件绝对路径]}
    file_map = {}
    for ets_file in ets_files:
        module_name = os.path.splitext(ets_file)[0]
        relative_path = os.path.join(tools_path, ets_file)
        print(f'relative_path:{relative_path}')
        file_map[module_name] = [relative_path]

    # 3. 定位要写入的 arktsconfig.json文件
    abs_config_path = get_path_code_directory(CONFIGPATH)

    # 4. 读取并更新配置
    try:
        with open(abs_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"compilerOptions": {"baseUrl": "/code/arkcompiler/runtime_core/static_core", "paths": {}}}

    # 5. 更新配置中的paths(保留之前的配置项)
    config.setdefault("compilerOptions", {})
    config["compilerOptions"].setdefault("paths", {})
    config["compilerOptions"]["paths"].update(file_map)

    with open(abs_config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"已成功更新 {abs_config_path}")


def build_tools(compile_filelist, hypium_output_dir):
    """
    编译工具类
    """
    abs_es2panda_path = get_path_code_directory(ES2PANDAPATH)

    # 1. 创建输出目录
    output_dir = os.path.join(hypium_output_dir, "out")
    os.makedirs(output_dir, exist_ok=True)

    # 逐个执行编译命令
    for ets_file in compile_filelist:
        try:
            # 获取文件名(不带路径)
            file_name = os.path.basename(ets_file)
            base_name = os.path.splitext(file_name)[0]
            output_filepath = os.path.join(output_dir, f"{base_name}.abc")

            # 构造编译命令
            command = [abs_es2panda_path, ets_file, f"--output={output_filepath}"]
            print(f"执行命令: {' '.join(command)}")

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

        except subprocess.CalledProcessError as e:
            print(f"'{ets_file}' 编译失败（返回码: {e.returncode}）")
            if e.stderr:
                print("错误输出:", e.stderr.strip())
            print(f"编译失败，流程终止。请检查上述文件。")
            raise
        except Exception as e:
            print(f"'{ets_file}'编译失败:{e}")
            break
    # 所有文件都成功编译，统计 .abc 文件数量
    count = 0
    for root, _, filenames in os.walk(output_dir):
        for filename in filenames:
            if filename.endswith(".abc"):
                count += 1

    # 判断是否全部编译成功
    if count != len(compile_filelist):
        print(f"WARNING: 预期编译 {len(compile_filelist)} 个文件，"
              f"但只找到 {count} 个 .abc 文件。")
        print("可能有文件未正确生成，流程终止。")
        raise RuntimeError("编译结果不完整，部分文件未生成 .abc 输出。")

    # 如果hypium和tools所有的文件都编译成功,则把所有abc文件link成一个abc文件
    link_abc_files(output_dir)

    print(f"工具链编译与链接完成！在{hypium_output_dir}目录下生成hypium_tools.abc")


def collect_abc_files(output_dir):
    abc_files = []

    # 收集out目录下的.abc文件
    if os.path.exists(output_dir):
        out_files = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith('.abc')
        ]
        abc_files.extend(out_files)

    return abc_files


def build_ets_files(hypium_output_dir):
    # 将当前目录下的 .ets文件生成 file_map, 并追加写入 arktsconfig.json
    write_arktsconfig_file()
    """
    编译hypium、tools文件
    """
    if os.path.exists(hypium_output_dir):
        try:
            shutil.rmtree(hypium_output_dir)
            print(f'已成功清除文件夹：{hypium_output_dir}')
        except OSError as e:
            print(f'清空文件夹失败：{e}')
    else:
        print(f'文件夹不存在：{hypium_output_dir}')

    abs_hypium_path = get_path_code_directory(HYPIUMPATH)
    abs_dest_hypium_path = get_path_code_directory(DESTHYPIUMPATH)

    changeHypium(abs_hypium_path, abs_dest_hypium_path)

    files_to_compile = []
    for root, dirs, files in os.walk(abs_dest_hypium_path):
        if "testAbility" in dirs:
            dirs.remove("testAbility")
        if "testrunner" in dirs:
            dirs.remove("testrunner")

        for f in files:
            if f.endswith(".ets"):
                file_path = os.path.join(root, f)
                files_to_compile.append(file_path)

    abs_tools_path = get_path_code_directory(TOOLSPATH)
    ets_files = [os.path.join(abs_tools_path, f) for f in os.listdir(abs_tools_path) if f.endswith('.ets')]
    files_to_compile.extend(ets_files)

    if not files_to_compile:
        print("未找到可编译的 .ets 文件，跳过编译。")
        return
    build_tools(files_to_compile, hypium_output_dir)


def link_abc_files(output_dir):
    """
    链接所有abc文件生成最终的test.abc
    """
    abs_arklink_path = get_path_code_directory(ARKLINKPATH)
    abc_files = collect_abc_files(output_dir)

    if not abc_files:
        print("终止: 没有找到可连接的.abc文件")
        return

    out_path = os.path.join(os.path.dirname(output_dir), "hypium_tools.abc")

    command = [
        abs_arklink_path,
        f"--output={out_path}",
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


def copy_hypium2dest(src_path, dest_path):
    """复制目录中除了testAbility和testrunner以外的文件和目录"""
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)

    os.makedirs(dest_path)

    # 需要排除的目录名
    exclude_dirs = {'testAbility', 'testrunner'}

    for root, dirs, files in os.walk(src_path):
        # 过滤掉需要排除的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # 计算相对路径
        rel_path = os.path.relpath(root, src_path)
        if rel_path == '.':
            rel_path = ''

        # 创建目标目录
        if rel_path:
            dest_dir = os.path.join(dest_path, rel_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
        
        # 复制文件
        for file in files:
            if file not in exclude_dirs:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_path, rel_path, file)
                shutil.copy2(src_file, dest_file)


def get_ets_files(dest_path):
    """获取目标路径中所有.ets后缀的文件名"""
    ets_files = []
    for root, dirs, files in os.walk(dest_path):
        for file in files:
            if file.endswith('.ets'):
                # 保存相对路径和文件名
                ets_files.append(os.path.relpath(os.path.join(root, file), dest_path))
    return ets_files


def modify_filename(filename):
    """修改文件名，在后缀前加上_hypiumTool"""
    # index.ets不修改文件名
    if filename == 'index.ets':
        return filename
    name, ext = os.path.splitext(filename)
    return f"{name}_hypiumTool{ext}"


def process_import_lines(line):
    """处理import语句，修改相对路径"""
    # 匹配 import ... from 'path' 或 export ... from 'path' 格式
    pattern = r"(import|export)\s+(.*?from\s+')([^']+)'"

    def replace_path(match):
        import_type = match.group(1)
        import_content = match.group(2)  # from '
        path = match.group(3)

        # 检查是否为相对路径且不是node_modules等系统路径
        if path.startswith('.') and not path.startswith('./node_modules') and not path.startswith('@ohos'):
            # 分离目录和文件名
            if '/' in path:
                dir_part, file_part = os.path.split(path)
                name, ext = os.path.splitext(file_part)
                if name != 'index':  # 不修改index文件
                    new_path = f"{dir_part}/{name}_hypiumTool{ext}"
                else:
                    new_path = path
            else:
                name, ext = os.path.splitext(path)
                if name != 'index':  # 不修改index文件
                    new_path = f"{name}_hypiumTool{ext}"
                else:
                    new_path = path
            return f"{import_type} {import_content}{new_path}'"
        return match.group(0)

    # 处理import语句
    result = re.sub(pattern, replace_path, line)
    return result


def process_special_case_line(line):
    """处理特殊格式： } from './xxx'; 这种情况"""
    # 匹配 } from './xxx'; 这种格式
    pattern = r'}\s+from\s+[\'"]([^\'"]+)[\'"]'

    def replace_path(match):
        path = match.group(1)

        # 检查是否为相对路径且不是node_modules等系统路径
        if path.startswith('.') and not path.startswith('./node_modules') and not path.startswith('@ohos'):
            # 分离目录和文件名
            if '/' in path:
                dir_part, file_part = os.path.split(path)
                name, ext = os.path.splitext(file_part)
                if name != 'index':  # 不修改index文件
                    new_path = f"{dir_part}/{name}_hypiumTool{ext}"
                else:
                    new_path = path
            else:
                name, ext = os.path.splitext(path)
                if name != 'index':  # 不修改index文件
                    new_path = f"{name}_hypiumTool{ext}"
                else:
                    new_path = path
            return f"}} from '{new_path}'"
        return match.group(0)

    # 处理特殊格式
    result = re.sub(pattern, replace_path, line)
    return result


def process_file_content(file_path, ets_files_list):
    """处理单个文件的内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_lines = []
    for line in lines:
        # 先处理特殊格式: } from './xxx';
        if line.strip().startswith('}') and 'from \'' in line:
            modified_line = process_special_case_line(line)
            modified_lines.append(modified_line)
        # 处理import/export语句
        elif 'from \'' in line and ('import' in line or 'export' in line):
            modified_line = process_import_lines(line)
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)

    # 写回修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)


def changeHypium(src_path, dest_path):
    # 1. 复制文件
    print(f"复制文件从 {src_path} 到 {dest_path}")
    copy_hypium2dest(src_path, dest_path)

    # 2. 读取所有.ets文件名
    ets_files = get_ets_files(dest_path)
    print(f"找到 {len(ets_files)} 个.ets文件")
    
    # 3. 修改文件名 (index.ets不修改，其他文件修改)
    print("修改文件名...")
    renamed_files = []
    for file_path in ets_files:
        # 获取文件名
        filename = os.path.basename(file_path)
        if filename != 'index.ets':
            # 获取目录路径
            dir_path = os.path.dirname(file_path)
            if dir_path:
                full_old_path = os.path.join(dest_path, file_path)
                new_filename = modify_filename(filename)
                full_new_path = os.path.join(dest_path, dir_path, new_filename)
            else:
                full_old_path = os.path.join(dest_path, file_path)
                new_filename = modify_filename(filename)
                full_new_path = os.path.join(dest_path, new_filename)

            if os.path.exists(full_old_path):
                os.rename(full_old_path, full_new_path)
                renamed_files.append((file_path, os.path.join(dir_path, new_filename) if dir_path else new_filename))
                print(f"重命名: {file_path} -> {os.path.join(dir_path, new_filename) if dir_path else new_filename}")
        else:
            print(f"跳过index.ets文件名修改: {file_path}")

    # 更新文件列表(注意：index.ets保持原名)
    updated_ets_files = []
    for file_path in ets_files:
        filename = os.path.basename(file_path)
        if filename != 'index.ets':
            dir_path = os.path.dirname(file_path)
            new_filename = modify_filename(filename)
            if dir_path:
                updated_ets_files.append(os.path.join(dir_path, new_filename))
            else:
                updated_ets_files.append(new_filename)
        else:
            updated_ets_files.append(file_path)

    # 4.处理文件内容
    print("处理文件内容...")
    for file_path in updated_ets_files:
        if file_path.endswith('.ets'):
            full_file_path = os.path.join(dest_path, file_path)
            if os.path.exists(full_file_path):
                print(f"处理文件: {file_path}")
                process_file_content(full_file_path, updated_ets_files)

    print("处理完成！")


def main():
    # 先编译工具链(必须全部成功)
    try:
        static_core_path = get_path_code_directory(STATICCOREPATH)
        remove_directory_contents(os.path.join(static_core_path, "out"))
        run_toolchain_build() # 会中断失败流程
    except Exception as e:
        print(f"工具链构建失败，无法继续后续流程：{e}")
        return
    third_party_path = os.path.join(static_core_path, "third_party")
    # 删除third_party路径下的bundle.json防止编译出错
    delete_specific_files(third_party_path, 'bundle.json')
    # hypium编译
    arktstest_output_path = 'out/generic_generic_arm_64only/general_all_phone_standard/tests/arktstdd/hypium'
    hypium_output_dir = get_path_code_directory(arktstest_output_path)
    if not os.path.exists(hypium_output_dir):
        os.makedirs(hypium_output_dir)
        print(f"目录 {hypium_output_dir} 已创建")
    else:
        print(f"目录 {hypium_output_dir} 已存在")
    # 3. 执行 hypium 编译
    try:
        build_ets_files(hypium_output_dir)
    except Exception as e:
        print(f"hypium 编译失败：{e}")
        return


if __name__ == '__main__':
    main()  