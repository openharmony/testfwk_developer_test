/*
 * Copyright (c) 2021 Huawei Device Co., Ltd.
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

package ohos.zunit;

import ohos.aafwk.content.Intent;
import ohos.unittest.log.HiLogUtil;
import ohos.unittest.TestAbility;
import ohos.unittest.AppContext;


/**
 * The main frame of the AppZUnit testing
 * AppZUnit testing startup processing
 */
public class MainAbility extends TestAbility {
    @Override
    public void onStart(Intent intent) {
        HiLogUtil.info(this.getClass(), "onStart begin");
        AppContext.getInstance().setCurrentAbility(this);
        super.onStart(intent);
        super.setMainRoute(ZtestAppSlice.class.getName());
        executeTestCase(intent);
        HiLogUtil.info(this.getClass(), "onStart end");
    }
}
