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

import ohos.aafwk.ability.Ability;
import ohos.aafwk.ability.delegation.AbilityDelegatorRegistry;
import ohos.aafwk.ability.delegation.IAbilityDelegator;
import ohos.aafwk.ability.delegation.IAbilityMonitor;

import ohos.aafwk.content.Intent;
import ohos.aafwk.content.IntentFilter;

import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import org.junit.AfterClass;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Optional;


/**
 * Test AbilityMonitor.
 */
public class AbilityMonitorTest {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100,
            "AbilityMonitorTestCases");
    private static IAbilityDelegator abilityDelegator;

    /**
     * setUp
     *
     * @apiNote BeforeClass process for all test
     */
    @BeforeClass
    public static void setUp() {
        abilityDelegator = AbilityDelegatorRegistry.getAbilityDelegator();
    }

    /**
     * stopAbility
     *
     * @apiNote AfterClass process for all test
     */
    @AfterClass
    public static void stopAbility() {
        // stop ability at here for clean test environment.
    }

    /**
     * testWaitForAbility
     *
     * @apiNote testWaitForAbility
     * @throws InterruptedException
     */
    @Test
    public void testWaitForAbility() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started",
            new Object() {
            }.getClass().getEnclosingMethod().getName());
        Thread.sleep(10);

        IAbilityMonitor monitor = abilityDelegator.addAbilityMonitor(SecondAbility.class.getName());
        abilityDelegator.startAbilitySync(Global.intentSecondAbility);

        Ability aa = monitor.waitForAbility();
        Assert.assertNotNull("ability is null", aa);
        Assert.assertEquals("there is 1 monitor in memory", 1,
            abilityDelegator.getMonitorsNum());
        abilityDelegator.removeAbilityMonitor(monitor); // remove monitor
        Assert.assertEquals("there is no monitor in memory", 0,
            abilityDelegator.getMonitorsNum());
    }

    /**
     * testIntentFilter
     *
     * @apiNote testIntentFilter
     * @throws InterruptedException
     */
    @Test
    public void testIntentFilter() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started",
            new Object() {
            }.getClass().getEnclosingMethod().getName());
        Thread.sleep(10);

        Intent newIntent = new Intent(Global.intentThirdAbility);
        newIntent.setAction("custom action");

        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction("custom action");
        Assert.assertTrue("match intent", intentFilter.match(newIntent));

        IAbilityMonitor monitor = abilityDelegator.addAbilityMonitor(intentFilter);
        abilityDelegator.startAbilitySync(newIntent);

        Ability aa = monitor.waitForAbility(50);
        Assert.assertNotNull("ability is null", aa);
        abilityDelegator.clearAllMonitors();
    }

    /**
     * testWaitAbilityMonitor
     *
     * @apiNote testWaitAbilityMonitor
     * @throws InterruptedException
     */
    @Test
    public void testWaitAbilityMonitor() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started",
            new Object() {
            }.getClass().getEnclosingMethod().getName());

        IAbilityMonitor monitor = abilityDelegator.addAbilityMonitor(SecondAbility.class.getName());
        abilityDelegator.startAbilitySync(Global.intentSecondAbility);

        Optional<Ability> aaOpt = abilityDelegator.waitAbilityMonitor(monitor);
        Assert.assertTrue("ability is null", aaOpt.isPresent());
        Assert.assertEquals("There is no ability monitor in memory",
            abilityDelegator.getMonitorsNum(), 0);
    }

    /**
     * testClearAbilityMonitor
     *
     * @apiNote testClearAbilityMonitor
     * @throws InterruptedException
     */
    @Test
    public void testClearAbilityMonitor() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started",
            new Object() {
            }.getClass().getEnclosingMethod().getName());
        abilityDelegator.addAbilityMonitor(SecondAbility.class.getName());
        Assert.assertEquals("there is 1 monitor in memory", 1,
            abilityDelegator.getMonitorsNum());
        abilityDelegator.clearAllMonitors(); // remove monitor
        Assert.assertEquals("there is no monitor in memory", 0,
            abilityDelegator.getMonitorsNum());
    }

    /**
     * jumpBack
     *
     * @apiNote Before process for test
     */
    @Before
    public void jumpBack() {
        abilityDelegator.startAbilitySync(Global.intentPageAbility);
        abilityDelegator.clearAllMonitors();

        try {
            Thread.sleep(10);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
