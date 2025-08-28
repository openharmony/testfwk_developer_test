/*
 * Copyright (c) 2025 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { AbilityDelegator as _AbilityDelegator, AbilityDelegatorInner } from 'AbilityDelegator'
import { AbilityDelegatorArgs as _AbilityDelegatorArgs} from 'AbilityDelegatorArgs'
import { ShellCmdResult as _ShellCmdResult } from 'ShellCmdResult'


export default namespace abilityDelegatorRegistry {
  export type AbilityDelegator = _AbilityDelegator;
  export type AbilityDelegatorArgs = _AbilityDelegatorArgs;
  export type ShellCmdResult = _ShellCmdResult;

  export function getAbilityDelegator(): AbilityDelegator {
    return new AbilityDelegatorInner();
  }
  
  export function getArguments(): AbilityDelegatorArgs {
    return {
      "bundleName": "com.example.myapplication",
      "parameters": {
        "-b": "com.example.myapplication",
        "-m": "entry_test",
        "-s timeout": "600000",
        "moduleName": "",
      },
      "testCaseNames": "example",
      "testRunnerClassName": "./OpenHarmonyTestRunner"
    }
  }
}