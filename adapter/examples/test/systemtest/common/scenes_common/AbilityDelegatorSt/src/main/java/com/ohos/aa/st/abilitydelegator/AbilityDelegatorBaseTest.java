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

import org.junit.AfterClass;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Ignore;
import org.junit.Test;

import java.util.Map;
import java.util.Optional;

import ohos.aafwk.ability.Ability;
import ohos.aafwk.ability.delegation.AbilityDelegatorRegistry;
import ohos.aafwk.ability.delegation.IAbilityDelegator;
import ohos.aafwk.ability.delegation.IAbilityDelegatorArgs;
import ohos.aafwk.ability.delegation.IAbilityMonitor;
import ohos.aafwk.content.Intent;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * Test AbilityDelegator base functions.
 */
public class AbilityDelegatorBaseTest {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "PageAbilityTest");

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
     * @apiNote AfterClass test stopAbility
     */
    @AfterClass
    public static void stopAbility() {
        // stop ability at here for clean test environment.
    }

    /**
     * jumpBack
     *
     * @apiNote Before test jumpBack
     */
    @Before
    public void jumpBack() {
        abilityDelegator.startAbilitySync(Global.intentPageAbility);
        try {
            Thread.sleep(10);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    /**
     * testChangeAbiltiyState
     *
     * @apiNote testChangeAbiltiyState
     * @throws InterruptedException
     */
    @Ignore
    @Test
    public void testChangeAbiltiyState() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        SecondAbility secondability = null;
        if (ability.get() instanceof SecondAbility) {
            secondability = (SecondAbility) ability.get();
            int expect = Global.ON_INACTIVE_HITS + 1;
            Assert.assertTrue("inactive ability", abilityDelegator.doAbilityInactive(secondability));
            Assert.assertEquals(Global.ON_INACTIVE_HITS, expect);

            expect = Global.ON_BACKGROUND_HITS + 1;
            Assert.assertTrue("background ability", abilityDelegator.doAbilityBackground(secondability));
            Assert.assertEquals(Global.ON_BACKGROUND_HITS, expect);

            expect = Global.ON_FOREGROUND_HITS + 1;
            Assert.assertTrue("foreground ability", abilityDelegator.doAbilityForeground(secondability, new Intent()));
            Assert.assertEquals(Global.ON_FOREGROUND_HITS, expect);

            expect = Global.ON_ACTIVE_HITS + 1;
            Assert.assertTrue("active ability", abilityDelegator.doAbilityActive(secondability, new Intent()));
            Assert.assertEquals(Global.ON_ACTIVE_HITS, expect);
        } else {
            Assert.fail("get second ability failed");
        }
    }

    /**
     * testStartAbilitySync
     *
     * @apiNote testStartAbilitySync
     * @throws InterruptedException
     */
    @Test
    public void testStartAbilitySync() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        {
            Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
            Assert.assertTrue("Get Secondability failed", ability.isPresent());
        }

        {
            Thread.sleep(10);
            Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentPageAbility);
            Assert.assertTrue("Get PageAbility failed", ability.isPresent());
        }
    }

    /**
     * testRunOnUIThreadSync
     *
     * @apiNote testRunOnUIThreadSync
     * @throws InterruptedException
     */
    @Test
    public void testRunOnUIThreadSync() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        if (ability.get() instanceof SecondAbility) {
            SecondAbility secondability = (SecondAbility) ability.get();
            IAbilityMonitor monitor = abilityDelegator.addAbilityMonitor(PageAbility.class.getName());
            abilityDelegator.runOnUIThreadSync(() -> secondability.startAbility(Global.intentPageAbility));
            Ability aa = monitor.waitForAbility();
            Assert.assertNotNull("PagetAbility is null", aa);
        } else {
            Assert.fail("get second ability failed");
        }
    }

    /**
     * testGetCurrentTopAbility
     *
     * @apiNote testGetCurrentTopAbility
     * @throws InterruptedException
     */
    @Test
    public void testGetCurrentTopAbility() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        if (ability.get() instanceof SecondAbility) {
            ability.get();
            Thread.sleep(10);
            Ability aa = abilityDelegator.getCurrentTopAbility();
            Assert.assertNotNull("PagetAbility is null", aa);
            Assert.assertEquals("top ability is SecondAbility.class", aa, ability.get());
        } else {
            Assert.fail("get second ability failed");
        }
    }

    /**
     * testGetCurrentTopAbility
     *
     * @apiNote testGetCurrentTopAbility
     */
    @Test
    public void invaidArgTest0() {
        Assert.assertFalse("startAbilitySync", abilityDelegator.startAbilitySync(null).isPresent());
        Assert.assertFalse("startAbilitySync", abilityDelegator.startAbilitySync(null, 10L).isPresent());
        Assert.assertFalse("doAbilityBackground", abilityDelegator.doAbilityBackground(null));
        Assert.assertFalse("doAbilityForeground", abilityDelegator.doAbilityForeground(null, null));
        Assert.assertFalse("doAbilityInactive", abilityDelegator.doAbilityInactive(null));
        Assert.assertFalse("stopAbility", abilityDelegator.stopAbility(null));
        Assert.assertFalse("triggerClickEvent", abilityDelegator.triggerClickEvent(null, null));
        Assert.assertFalse("triggerKeyEvent", abilityDelegator.triggerKeyEvent(null, null));
        Assert.assertFalse("triggerTouchEvent", abilityDelegator.triggerTouchEvent(null, null));
        Assert.assertFalse("runOnUIThreadSync", abilityDelegator.runOnUIThreadSync(null));
    }

    /**
     * invaidArgTest1
     *
     * @apiNote invaidArgTest1
     */
    @Test(expected = IllegalArgumentException.class)
    public void invaidArgTest1() {
        abilityDelegator.getAbilityState(null);
    }

    /**
     * invaidArgTest2
     *
     * @apiNote invaidArgTest2
     */
    @Test
    public void invaidArgTest2() {
        abilityDelegator.removeAbilityMonitor(null);
    }

    /**
     * getTestParameters
     *
     * @apiNote getTestParameters
     */
    @Test
    public void getTestParameters() {
        IAbilityDelegatorArgs iAbilityDelegatorArgs = AbilityDelegatorRegistry.getArguments();
        Assert.assertNotNull("abilitydelegator args", iAbilityDelegatorArgs);
        Assert.assertFalse("abilitydelegator args parameters", iAbilityDelegatorArgs.getTestParameters().isEmpty());
        Map<String, Object> parameters = iAbilityDelegatorArgs.getTestParameters();
        for (Map.Entry<String, Object> entry : parameters.entrySet()) {
            abilityDelegator.print("unittest parameter key is:" + entry.getKey() + System.lineSeparator());
        }
    }
}
