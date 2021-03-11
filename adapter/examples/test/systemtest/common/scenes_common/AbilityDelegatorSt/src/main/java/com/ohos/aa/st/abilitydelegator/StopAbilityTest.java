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
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Optional;

/**
 * Test stop ability.
 */
public class StopAbilityTest {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "StopAbilityTest");

    private static IAbilityDelegator abilityDelegator;

    /**
     * setUp, get abilityDelegator
     *
     * @apiNote BeforeClass setUp
     */
    @BeforeClass
    public static void setUp() {
        abilityDelegator = AbilityDelegatorRegistry.getAbilityDelegator();
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
     * testStopAbility
     *
     * @apiNote testStopAbility
     * @throws InterruptedException
     */
    @Test
    public void testStopAbility() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        /**
         * @tc.steps: step1. start second ability.
         */
        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("get Secondability", ability.isPresent());

        if (ability.get() instanceof SecondAbility) {
            /**
             * @tc.steps: step2. stop second ability.
             */
            SecondAbility secondability = (SecondAbility) ability.get();
            Assert.assertTrue("inactive ability", abilityDelegator.doAbilityInactive(secondability));
            Assert.assertTrue("background ability", abilityDelegator.doAbilityBackground(secondability));
            abilityDelegator.print("start stop ability" + System.lineSeparator());
            boolean result = abilityDelegator.stopAbility(secondability);
            abilityDelegator.print("stop ability " + result + System.lineSeparator() + System.lineSeparator());

            /**
             * @tc.steps: step3. start second ability again.
             */
            Optional<Ability> bb = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
            Assert.assertTrue("restart ability", bb.isPresent());
        } else {
            Assert.fail("get second ability failed");
        }
    }
}
