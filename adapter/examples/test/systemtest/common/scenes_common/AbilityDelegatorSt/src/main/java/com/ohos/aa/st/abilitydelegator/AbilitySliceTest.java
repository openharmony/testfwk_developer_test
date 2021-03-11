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
import ohos.aafwk.ability.AbilitySlice;
import ohos.aafwk.ability.delegation.AbilityDelegatorRegistry;
import ohos.aafwk.ability.delegation.IAbilityDelegator;
import ohos.aafwk.content.Intent;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import org.junit.AfterClass;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Ignore;
import org.junit.Test;

import java.util.Optional;

/**
 * Test AbilitySlice base functions.
 */
public class AbilitySliceTest {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "AbilitySliceTest");

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
     * jumpBack
     *
     * @apiNote Before process for test
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
     * testAbilitySliceOperations
     *
     * @apiNote testAbilitySliceOperations
     * @throws InterruptedException
     */
    @Ignore
    @Test
    public void testAbilitySliceOperations() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        SecondAbility secondability = null;
        if (ability.get() instanceof SecondAbility) {
            secondability = (SecondAbility) ability.get();

            AbilitySlice slice = abilityDelegator.getCurrentAbilitySlice(secondability);
            Assert.assertNotNull(slice);
            Assert.assertEquals("getAllAbilitySlice", abilityDelegator.getAllAbilitySlice(secondability).size(), 1);
            Assert.assertTrue("doAbilitySliceInactive", abilityDelegator.doAbilitySliceInactive(secondability));
            Assert.assertTrue("doAbilitySliceBackground", abilityDelegator.doAbilitySliceBackground(secondability));
            Assert.assertTrue("doAbilitySliceStop", abilityDelegator.doAbilitySliceStop(secondability));
            Assert.assertFalse("doAbilitySliceStop", abilityDelegator.doAbilitySliceStart(secondability, new Intent()));
            Assert.assertEquals(IAbilityDelegator.INITIAL, abilityDelegator.getAbilitySliceState(slice));
        } else {
            Assert.fail("get second ability failed");
        }
    }

    /**
     * testErrorLifeCycle
     *
     * @apiNote testErrorLifeCycle
     * @throws InterruptedException
     */
    @Test
    public void testErrorLifeCycle() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        SecondAbility secondability = null;
        if (ability.get() instanceof SecondAbility) {
            secondability = (SecondAbility) ability.get();

            AbilitySlice slice = abilityDelegator.getCurrentAbilitySlice(secondability);
            Assert.assertEquals(abilityDelegator.getAbilitySliceState(slice), IAbilityDelegator.ACTIVE);
            Assert.assertFalse("background ability slice", abilityDelegator.doAbilitySliceBackground(secondability));
        } else {
            Assert.fail("get second ability failed");
        }
    }

}
