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

import { RecordData } from '@ohos.base';

// type Record<K extends keyof any, T> = {
//    [P in K]: T;
// };
export default class Want {
  bundleName?: string;
  abilityName?: string;
  deviceId?: string;
  uri?: string;
  type?: string;
  flags?: int;
  action?: string;
  parameters?: Record<string, RecordData>;
  entities?: Array<string>;
  moduleName?: string;
  readonly fds?: Record<string, int>;
}