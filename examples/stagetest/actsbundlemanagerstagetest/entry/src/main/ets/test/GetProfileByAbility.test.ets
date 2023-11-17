/**
 * Copyright (c) 2022 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or impligetProfileByAbilityEmptyAbilityCalled.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import manager from '@ohos.bundle.bundleManager';
import { describe, beforeAll, beforeEach, afterEach, afterAll, it, expect } from "@ohos/hypium"
import { BusinessError } from '@ohos.base';

const MODULE_NAME = "testModule"
const MODULE_NAME_TEST = "testModule1"
const ABILITY_NAME = "ohos.acts.bundle.stage.test.MainAbility"
const ABILITY_NAME1 = "ohos.acts.bundle.stage.test.MainAbility1"
const ABILITY_NAME_TEST = "ohos.acts.bundle.stage.test.MainAbilityTest"
const METADATA_NAME = "ohos.ability.form"
const METADATA_NAME1 = "ohos.ability.form1"
const METADATA_NAME2 = "ohos.ability.form2"
const METADATA_NAME3 = "ohos.ability.form3"
const METADATA_NAME4 = "ohos.ability.form4"
const METADATA_NAME_TEST = "ohos.test.form"
const PROFILE_JSON_STRING = "{\"src\":[\"MainAbility/pages/index/index\",\"MainAbility/pages/second/second\"]}"
const ERROR_ABILITY_NOT_EXIST = 17700003
const ERROR_PROFILE_NOT_EXIST = 17700024
const ERROR_MODULE_NOT_EXIST = 17700002

export default function getProfileByAbility() {
  describe('getProfileByAbility', () => {
   /*
    * @tc.number: SUB_BMS_APPINFO_QUERYMETAFILE_0011
    * @tc.name: getProfileByAbilityInvalidModulePro
    * @tc.desc: Check the invalid moduleName (by promise)
    * @tc.level   0
    */
    it('getProfileByAbilityInvalidModulePro', 0, async (done: Function) => {
      await manager.getProfileByAbility(MODULE_NAME_TEST, ABILITY_NAME, METADATA_NAME).then(data => {
        console.info('getProfileByAbilityInvalidModulePro success' + JSON.stringify(data))
        expect(data).assertFail()
        done()
      }).catch((err: BusinessError) => {
        console.info('getProfileByAbilityInvalidModulePro failed' + JSON.stringify(err))
        expect(err.code).assertEqual(ERROR_ABILITY_NOT_EXIST)
        done()
      })
    })

   /*
    * @tc.number: SUB_BMS_APPINFO_QUERYMETAFILE_0015
    * @tc.name: getProfileByAbilityEmptyModulePro
    * @tc.desc: Check the empty moduleName (by promise)
    * @tc.level   0
    */
    it('getProfileByAbilityEmptyModulePro', 0, async (done: Function) => {
      await manager.getProfileByAbility('', ABILITY_NAME, METADATA_NAME).then(data => {
        console.info('getProfileByAbilityEmptyModulePro success' + JSON.stringify(data))
        expect(data).assertFail()
        done()
      }).catch((err: BusinessError) => {
        console.info('getProfileByAbilityEmptyModulePro failed' + JSON.stringify(err))
        expect(err.code).assertEqual(ERROR_MODULE_NOT_EXIST)
        done()
      })
    })
  })
}