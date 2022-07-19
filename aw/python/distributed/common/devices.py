#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2021 Huawei Device Co., Ltd.
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
import json
import os
import shutil
import platform
import subprocess

##############################################################################
##############################################################################

__all__ = ["DeviceShell"]

import zipfile

if platform.system() != 'Windows':
    QUOTATION_MARKS = "'"
else:
    QUOTATION_MARKS = "\""

HDC_TOOLS = "hdc_std"


##############################################################################
##############################################################################


def get_package_name(hap_filepath):
    package_name = ""

    if os.path.exists(hap_filepath):
        filename = os.path.basename(hap_filepath)

        # unzip the hap file
        hap_bak_path = os.path.abspath(os.path.join(
            os.path.dirname(hap_filepath),
            "%s.bak" % filename))
        zf_desc = zipfile.ZipFile(hap_filepath)
        try:
            zf_desc.extractall(path=hap_bak_path)
        except RuntimeError as error:
            print(error)
        zf_desc.close()

        # verify config.json file
        app_profile_path = os.path.join(hap_bak_path, "config.json")
        if os.path.isfile(app_profile_path):
            load_dict = {}
            with open(app_profile_path, 'r') as json_file:
                load_dict = json.load(json_file)
            profile_list = load_dict.values()
            for profile in profile_list:
                package_name = profile.get("package")
                if not package_name:
                    continue
                break

        # delete hap_bak_path
        if os.path.exists(hap_bak_path):
            shutil.rmtree(hap_bak_path)
    else:
        print("file %s not exists" % hap_filepath)

    return package_name

##############################################################################
##############################################################################


class DeviceShell:
    def __init__(self, conn_type, remote_ip="", device_sn="", repote_port="", name=""):
        self.conn_type = conn_type
        self.device_sn = device_sn
        self.name = name
        self.test_path = "data/test"
        if conn_type:
            self.device_params = self.get_device_hdc_para(
                device_sn
            )
        else:
            self.device_params = self.get_device_para(
                remote_ip, repote_port, device_sn)
        self.init_device()

    @classmethod
    def get_device_para(cls, remote_ip="", remote_port="",
                        device_sn=""):
        if "" == remote_ip or "" == remote_port:
            if "" == device_sn:
                device_para = ""
            else:
                device_para = "-s %s" % device_sn
        else:
            if "" == device_sn:
                device_para = "-H %s -P %s" % (remote_ip, remote_port)
            else:
                device_para = "-H %s -P %s -t %s" % (
                    remote_ip, remote_port, device_sn)
        return device_para

    @classmethod
    def get_device_hdc_para(cls, device_sn=""):
        if " " == device_sn:
            device_para = ""
        else:
            device_para = "-t %s" % device_sn

        return device_para

    def remount(self):
        if self.conn_type:
            remount = "target mount"
        else:
            remount = "remount"
        command = "%s %s %s" % (HDC_TOOLS, self.device_params, remount)
        self.execute_command(command)

    def init_device(self):
        self.remount()
        self.shell('rm -rf %s' % self.test_path)
        self.shell('mkdir -p %s' % self.test_path)
        self.shell('chmod 777 -R %s' % self.test_path)
        self.shell("mount -o rw,remount,rw /%s" % "system")

    def unlock_screen(self):
        self.shell("svc power stayon true")

    def unlock_device(self):
        self.shell("input keyevent 82")
        self.shell("wm dismiss-keyguard")

    def push_file(self, srcpath, despath):
        if self.conn_type:
            push_args = "file send"
        else:
            push_args = "push"
        command = "%s %s %s %s %s" % (
            HDC_TOOLS,
            self.device_params,
            push_args,
            srcpath,
            despath)
        return self.execute_command(command)

    def pull_file(self, srcpath, despath):
        if self.conn_type:
            pull_args = "file recv"
        else:
            pull_args = "pull"
        command = "%s %s %s %s %s" % (
            HDC_TOOLS,
            self.device_params,
            pull_args,
            srcpath,
            despath)
        return self.execute_command(command)

    def lock_screen(self):
        self.shell("svc power stayon false")

    def disable_keyguard(self):
        self.unlock_screen()
        self.unlock_device()

    def shell(self, command=""):
        return self.execute_command("%s %s shell %s%s%s" % (
            HDC_TOOLS,
            self.device_params,
            QUOTATION_MARKS,
            command,
            QUOTATION_MARKS))

    @classmethod
    def execute_command(cls, command, print_flag=True, timeout=900):
        try:
            if print_flag:
                print("command: " + command)
            if subprocess.call(command, shell=True, timeout=timeout) == 0:
                print("results: successed")
                return True
        except Exception as error:
            print("Exception: %s" % str(error))
        print("results: failed")
        return False

    def shell_with_output(self, command=""):
        return self.execute_command_with_output("%s %s shell %s%s%s" % (
            HDC_TOOLS,
            self.device_params,
            QUOTATION_MARKS,
            command,
            QUOTATION_MARKS))

    @classmethod
    def execute_command_with_output(cls, command, print_flag=True):
        if print_flag:
            print("command: " + command)

        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)

        try:
            data, _ = proc.communicate()
            if isinstance(data, bytes):
                data = data.decode('utf-8', 'ignore')
        finally:
            proc.stdout.close()
            proc.stderr.close()
        return data

    @classmethod
    def check_path_legal(cls, path):
        if path and " " in path:
            return "\"%s\"" % path
        return path