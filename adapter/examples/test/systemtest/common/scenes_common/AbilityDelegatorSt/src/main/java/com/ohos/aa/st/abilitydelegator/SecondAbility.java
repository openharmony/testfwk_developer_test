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

package com.ohos.aa.st.abilitydelegator;

import com.ohos.aa.st.abilitydelegator.slice.SecondAbilitySlice;

import ohos.aafwk.ability.Ability;
import ohos.aafwk.content.Intent;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import ohos.rpc.IRemoteObject;
import ohos.utils.PacMap;

/**
 * SecondAbility for test hap.
 */
public class SecondAbility extends Ability {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "SecondAbility");

    @Override
    public void onStart(Intent intent) {
        super.onStart(intent);
        super.setMainRoute(SecondAbilitySlice.class.getName());
        HiLog.info(LABEL_LOG, "onStart() end");
    }

    @Override
    protected void onPostStart(PacMap pacMap) {
        super.onPostStart(pacMap);
        HiLog.info(LABEL_LOG, "onPostStart() end");
    }

    @Override
    protected void onStop() {
        super.onStop();
        HiLog.info(LABEL_LOG, "onStop() end");
        Global.ON_STOP_HITS += 1;
    }

    @Override
    protected void onActive() {
        super.onActive();
        HiLog.info(LABEL_LOG, "onActive() end");
        Global.ON_ACTIVE_HITS += 1;
    }

    @Override
    protected void onPostActive() {
        super.onPostActive();
        HiLog.info(LABEL_LOG, "onPostActive() end");
    }

    @Override
    protected void onInactive() {
        super.onInactive();
        HiLog.info(LABEL_LOG, "onInactive() end");
        Global.ON_INACTIVE_HITS += 1;
    }

    @Override
    protected void onForeground(Intent intent) {
        super.onForeground(intent);
        HiLog.info(LABEL_LOG, "onForeground() end");
        Global.ON_FOREGROUND_HITS += 1;
    }

    @Override
    protected void onBackground() {
        super.onBackground();
        HiLog.info(LABEL_LOG, "onBackground() end");
        Global.ON_BACKGROUND_HITS += 1;
    }

    @Override
    protected IRemoteObject onConnect(Intent intent) {
        return super.onConnect(intent);
    }

    @Override
    protected void onDisconnect(Intent intent) {
        super.onDisconnect(intent);
    }

    @Override
    protected void onCommand(Intent intent, boolean restart, int startId) {
        super.onCommand(intent, restart, startId);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
    }
}
