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

type AsyncCallback<T, E = void> = (error: BusinessError<E>, data: T) => void;

export default namespace systemDateTime {
  
  export enum TimeType {
    STARTUP,
    ACTIVE
  }

  export function getUptime(timeType: TimeType, isNanoseconds?: boolean): number {
    const nowTime:number = new Date().getTime();
    return nowTime;
  }
  
  const SYSTEM_ERROR: number = 401
  
  export function getCurrentTime(isNano: boolean, callback: AsyncCallback<number>): void {}
  
  export function getCurrentTime(callback: AsyncCallback<number>): void {}
  
  export function getCurrentTime(isNano?: boolean): void {}
  
  export function getTimezone(callback: AsyncCallback<string>): void {}
  
  export function getTimezone(): void {}
}