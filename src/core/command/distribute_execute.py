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

import os
import unittest

from distributed.common.manager import DeviceManager
from distributed.distribute.distribute import Distribute
from distributed.common.common import create_empty_result_file


class DbinderTest(unittest.TestCase):
    def __init__(self, result_path, suits_dir):
        self.result_path = result_path
        self.suits_dir = suits_dir

    def setUp(self):
        print('setUp')

        self.manager = DeviceManager(self.result_path)
        self.major = self.manager.PHONE1
        self.angent_list = [self.manager.PHONE2]
        self.hdc = "hdc"

    def test_distribute(self, major_target_name="", agent_target_name="", options=""):

        major_target_name = major_target_name
        agent_target_name = agent_target_name

        distribute = Distribute(self.suits_dir, self.major, self.angent_list, self.hdc)

        for agent in self.angent_list:
            if not distribute.exec_agent(agent, agent_target_name, self.result_path, options):
                print(agent, agent_target_name)
                create_empty_result_file(self.result_path, major_target_name)
                return
        distribute.exec_major(self.major, major_target_name, self.result_path, options)

        result = os.path.join(self.result_path, 'result',
                              self.suits_dir.split("distributedtest\\")[1])
        source_path = "%s/%s.xml" % (self.major.test_path, major_target_name)
        if not os.path.exists(result):
            os.makedirs(result)
        distribute.pull_result(self.major, source_path, result)

    def tearDown(self):
        print('tearDown')

