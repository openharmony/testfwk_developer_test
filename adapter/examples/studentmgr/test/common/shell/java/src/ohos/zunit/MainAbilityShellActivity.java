/*
 * Copyright (c) 2021 Huawei Device Co., Ltd.
 * Copyright (C) 2013 The Android Open Source Project
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

import android.os.Bundle;

import android.view.WindowManager;

import ohos.abilityshell.AbilityShellActivity;

import ohos.unittest.AppContext;

import ohos.unittest.log.HiLogUtil;


/**
 * Main ability shell activity
 */
public class MainAbilityShellActivity extends AbilityShellActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        HiLogUtil.info(this.getClass(), "onCreate begin");
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        AppContext.getInstance().setCurrentActivity(this);
        HiLogUtil.info(this.getClass(), "onCreate end");
    }

    @Override
    protected void onResume() {
        HiLogUtil.info(this.getClass(), "onResume begin");
        super.onResume();
        AppContext.getInstance().setCurrentActivity(this);
        HiLogUtil.info(this.getClass(), "onResume end");
    }

    @Override
    protected void onPause() {
        HiLogUtil.info(this.getClass(), "onPause begin");
        super.onPause();
        AppContext.getInstance().setCurrentActivity(this);
        HiLogUtil.info(this.getClass(), "onPause end");
    }

    @Override
    protected void onDestroy() {
        HiLogUtil.info(this.getClass(), "onDestroy begin");
        super.onDestroy();
        HiLogUtil.info(this.getClass(), "onDestroy end");
    }
}
