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

import os

from distributed.common.devices import DeviceShell


##############################################################################
##############################################################################

class DeviceManager:
    def __init__(self, result_path):
        self.is_hdc = True
        self.phone_device_list = []
        self.ivi_device_list = []
        self.tv_device_list = []
        self.watch_device_list = []
        self.make_device_list(result_path)

    def make_device_adapter(self, device_info_list, device_name):
        device = DeviceShell(self.is_hdc, device_sn=device_info_list[0],
                             remote_ip=device_info_list[2],
                             repote_port=device_info_list[3],
                             name=device_name)
        return device

    def make_device_list(self, result_path):
        device_info_list = self.get_device_info_list(result_path)
        for item in device_info_list:
            if len(item) != 4:
                continue
            if item[1] == "phone":
                index = len(self.phone_device_list) + 1
                device_name = "PHONE%s" % index
                device = self.make_device_adapter(item, device_name)
                self.phone_device_list.append(device)
                setattr(self, device.name, device)
            elif item[1] == "ivi":
                index = len(self.ivi_device_list) + 1
                device_name = "IVI%s" % index
                device = self.make_device_adapter(item, device_name)
                self.ivi_device_list.append(device)
                setattr(self, device.name, device)
            elif item[1] == "tv":
                index = len(self.tv_device_list) + 1
                device_name = "TV%s" % index
                device = self.make_device_adapter(item, device_name)
                self.tv_device_list.append(device)
                setattr(self, device.name, device)
            elif item[1] == "watch":
                index = len(self.watch_device_list) + 1
                device_name = "WATCH%s" % index
                device = self.make_device_adapter(item, device_name)
                self.watch_device_list.append(device)
                setattr(self, device.name, device)
        return

    @staticmethod
    def get_device_info_list(result):
        device_info_list = []
        tmp_path = os.path.join(result, "temp")
        device_info_file_path = os.path.join(tmp_path, 
                                             "device_info_file.txt")

        if os.path.exists(device_info_file_path):
            with open(device_info_file_path, "r") as file_handle:
                lines = file_handle.readlines()
                for line in lines:
                    line = line.replace("\n", "")
                    line = line.strip()
                    temp = line.split(",")
                    device_info_list.append(temp)
        return device_info_list

##############################################################################
##############################################################################
