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

import { BusinessError } from '@ohos.base';
import { ShellCmdResult } from 'ShellCmdResult'

type AsyncCallback<T, E = void> = (error: BusinessError<E>, data: T) => void;

export interface AbilityDelegator {
  
  printSync(msg: string): void;
  
  finishTest(msg: string, code: number): void;
  
  executeShellCommand(cmd: String, timeoutSecs?: number): Promise<ShellCmdResult>;
  
  executeShellCommand(cmd: String, callback: AsyncCallback<ShellCmdResult>): void;
  
  executeShellCommand(cmd: String, timeoutSecs: number, callback: AsyncCallback<ShellCmdResult>): void;
}

export class AbilityDelegatorInner implements AbilityDelegator {
  
  printSync(msg: string): void {};
  
  finishTest(msg: string, code: number): void {};
  
  executeShellCommand(cmd: String, timeoutSecs?: number): Promise<ShellCmdResult>{
    return new Promise<ShellCmdResult>((resolve, reject) => {
      resolve({} as ShellCmdResult);
    });
  }
  
  executeShellCommand(cmd: String, callback: AsyncCallback<ShellCmdResult, void>): void{};
  
  executeShellCommand(cmd: String, timeoutSecs: number, callback: AsyncCallback<ShellCmdResult, void>): void{};
}