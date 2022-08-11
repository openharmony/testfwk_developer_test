#!/bin/bash
#
# Copyright (c) 2022 Shenzhen Kaihong Digital Industry Development Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#



sudo cp -r  core __main__
sudo cp -r ../../xdevice/src/xdevice __main__/
sudo cp -r  __main__/*  /usr/bin
sudo chmod 777 /usr/bin/core/_init_global_config.py __main__/core __main__/xdevice
