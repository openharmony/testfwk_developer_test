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

package ohos.unittest;

import android.app.Activity;

import ohos.aafwk.ability.Ability;


/**
 * Saved App Context for system APP unit test
 */
public class AppContext {
    /**
     * Current test Activity
     */
    private Activity curActivity = null;

    /**
     * Current test Ability
     */
    private Ability curAbility = null;

    /**
     * Message Constructor
     */
    private AppContext() {
    }

    /**
     * Get AppContext singleton instance
     *
     * @return AppContext AppContext instance
     */
    public static AppContext getInstance() {
        return LazyHolder.instance;
    }

    /**
     * Record current test Activity
     *
     * @param activity currentActivity
     */
    public void setCurrentActivity(Activity activity) {
        this.curActivity = activity;
    }

    /**
     * Get Current Activity
     *
     * @return Activity
     */
    public Activity getCurrentActivity() {
        return this.curActivity;
    }

    /**
     * Record current test Ability
     *
     * @param ability currentAbility
     */
    public void setCurrentAbility(Ability ability) {
        this.curAbility = ability;
    }

    /**
     * Get Current Ability
     *
     * @return Ability currentAbility
     */
    public Ability getCurrentAbility() {
        return this.curAbility;
    }

    /**
     * LazyHolder
     */
    private static class LazyHolder {
        static AppContext instance = new AppContext();
    }
}
