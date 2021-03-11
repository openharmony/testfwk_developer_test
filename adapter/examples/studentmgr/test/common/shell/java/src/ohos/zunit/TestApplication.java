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

import android.content.ComponentCallbacks;

import android.content.res.Configuration;

import ohos.abilityshell.HarmonyApplication;

import ohos.unittest.log.HiLogUtil;


/**
 * System APP test Application
 */
public class TestApplication extends HarmonyApplication {
    /**
     * TestApplication Constructor
     */
    public TestApplication() {
    }

    @Override
    public void onCreate() {
        HiLogUtil.info(this.getClass(), "onCreate begin");
        super.onCreate();
        HiLogUtil.info(this.getClass(), "onCreate end");
    }

    @Override
    public void onTerminate() {
        HiLogUtil.info(this.getClass(), "onTerminate begin");
        super.onTerminate();
        HiLogUtil.info(this.getClass(), "onTerminate end");
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        HiLogUtil.info(this.getClass(), "onConfigurationChanged begin");
        super.onConfigurationChanged(newConfig);
        HiLogUtil.info(this.getClass(), "onConfigurationChanged end");
    }

    @Override
    public void onLowMemory() {
        HiLogUtil.info(this.getClass(), "onLowMemory begin");
        super.onLowMemory();
        HiLogUtil.info(this.getClass(), "onLowMemory end");
    }

    @Override
    public void onTrimMemory(int level) {
        HiLogUtil.info(this.getClass(), "onTrimMemory begin");
        super.onTrimMemory(level);
        HiLogUtil.info(this.getClass(), "onTrimMemory end");
    }

    @Override
    public void registerComponentCallbacks(ComponentCallbacks callback) {
        HiLogUtil.info(this.getClass(), "registerComponentCallbacks begin");
        super.registerComponentCallbacks(callback);
        HiLogUtil.info(this.getClass(), "registerComponentCallbacks end");
    }

    @Override
    public void unregisterComponentCallbacks(ComponentCallbacks callback) {
        HiLogUtil.info(this.getClass(), "unregisterComponentCallbacks begin");
        super.unregisterComponentCallbacks(callback);
        HiLogUtil.info(this.getClass(), "unregisterComponentCallbacks end");
    }

    @Override
    public void registerActivityLifecycleCallbacks(
        ActivityLifecycleCallbacks callback) {
        HiLogUtil.info(this.getClass(),
            "registerActivityLifecycleCallbacks begin");
        super.registerActivityLifecycleCallbacks(callback);
        HiLogUtil.info(this.getClass(), "registerActivityLifecycleCallbacks end");
    }

    @Override
    public void unregisterActivityLifecycleCallbacks(
        ActivityLifecycleCallbacks callback) {
        HiLogUtil.info(this.getClass(),
            "unregisterActivityLifecycleCallbacks begin");
        super.unregisterActivityLifecycleCallbacks(callback);
        HiLogUtil.info(this.getClass(),
            "unregisterActivityLifecycleCallbacks end");
    }
}
