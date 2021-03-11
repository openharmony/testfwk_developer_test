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
import ohos.agp.components.Component;
import ohos.agp.components.Text;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import ohos.multimodalinput.event.KeyBoardEvent;
import ohos.multimodalinput.event.KeyEvent;
import ohos.multimodalinput.event.MmiPoint;
import ohos.multimodalinput.event.TouchEvent;

import org.junit.AfterClass;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Optional;

/**
 * Test AbilityDelegator dispatch events.
 */
public class AbilityDelegatorEventTest {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "TestKeyEvent");

    private static IAbilityDelegator abilityDelegator;

    private TouchEvent touchEvent = new TouchEvent() {
        @Override
        public float getForcePrecision() {
            return 0;
        }

        @Override
        public float getMaxForce() {
            return 0;
        }

        @Override
        public int getTapCount() {
            return 0;
        }

        @Override
        public int getAction() {
            return TouchEvent.PRIMARY_POINT_UP;
        }

        @Override
        public int getIndex() {
            return 0;
        }

        @Override
        public long getStartTime() {
            return 0;
        }

        @Override
        public int getPhase() {
            return 0;
        }

        @Override
        public MmiPoint getPointerPosition(int i) {
            return new MmiPoint(0, 0);
        }

        @Override
        public void setScreenOffset(float v, float v1) {
        }

        @Override
        public MmiPoint getPointerScreenPosition(int i) {
            return new MmiPoint(0, 0);
        }

        @Override
        public int getPointerCount() {
            return 0;
        }

        @Override
        public int getPointerId(int i) {
            return 0;
        }

        @Override
        public float getForce(int i) {
            return 0;
        }

        @Override
        public float getRadius(int i) {
            return 0;
        }

        @Override
        public int getSourceDevice() {
            return 0;
        }

        @Override
        public String getDeviceId() {
            return "";
        }

        @Override
        public int getInputDeviceId() {
            return 0;
        }

        @Override
        public long getOccurredTime() {
            return 0;
        }
    };

    private KeyBoardEvent keyBoardEvent = new KeyBoardEvent() {
        @Override
        public boolean isNoncharacterKeyPressed(int i) {
            return false;
        }

        @Override
        public boolean isNoncharacterKeyPressed(int i, int i1) {
            return false;
        }

        @Override
        public boolean isNoncharacterKeyPressed(int i, int i1, int i2) {
            return false;
        }

        @Override
        public int getUnicode() {
            return 0;
        }

        @Override
        public boolean isKeyDown() {
            return true;
        }

        @Override
        public int getKeyCode() {
            return KeyEvent.KEY_VOLUME_DOWN;
        }

        @Override
        public long getKeyDownDuration() {
            return 0;
        }

        @Override
        public int getSourceDevice() {
            return 0;
        }

        @Override
        public String getDeviceId() {
            return "";
        }

        @Override
        public int getInputDeviceId() {
            return 0;
        }

        @Override
        public long getOccurredTime() {
            return System.currentTimeMillis();
        }
    };

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
     * testTriggerTouchEvent
     *
     * @apiNote testTriggerTouchEvent
     * @throws InterruptedException
     */
    @Test
    public void testTriggerTouchEvent() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        if (ability.get() instanceof SecondAbility) {
            SecondAbility secondability = (SecondAbility) ability.get();

            Thread.sleep(10);
            Component view = secondability.findComponentById(Global.TOUCH_RESULT_TEXTVIEW_ID);
            if (view instanceof Text) {
                Text textView = (Text) view;
                Assert.assertNotNull("touch result textview is null", textView);

                String expectedValue = Integer.valueOf(textView.getText()) + 1 + "";
                abilityDelegator.triggerTouchEvent(secondability, touchEvent);
                HiLog.info(LABEL_LOG, "textview value: %{public}s", textView.getText());
                Assert.assertEquals("textview value must be " + expectedValue, expectedValue, textView.getText());
            } else {
                Assert.fail("get textview failed!");
            }
        } else {
            Assert.fail("get secondability failed");
        }
    }

    /**
     * testTriggerClickEvent
     *
     * @apiNote testTriggerClickEvent
     * @throws InterruptedException
     */
    @Test
    public void testTriggerClickEvent() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        if (ability.get() instanceof SecondAbility) {
            SecondAbility secondability = (SecondAbility) ability.get();

            Thread.sleep(10);
            Component view = secondability.findComponentById(Global.CLICK_RESULT_TEXTVIEW_ID);
            if (view instanceof Text) {
                Text textView = (Text) view;
                Assert.assertNotNull("clieck result textview is null", textView);
                String expectedValue = Integer.valueOf(textView.getText()) + 1 + "";
                abilityDelegator.triggerClickEvent(secondability, textView);
                HiLog.info(LABEL_LOG, "textview content: %{public}s", textView.getText());
                Assert.assertTrue("textview value must be " + expectedValue, textView.getText().equals(expectedValue));
            } else {
                Assert.fail("get textview failed!");
            }
        } else {
            Assert.fail("get secondability failed");
        }
    }

    /**
     * testTriggerKeyEvent
     *
     * @apiNote testTriggerKeyEvent
     * @throws InterruptedException
     */
    @Test
    public void testTriggerKeyEvent() throws InterruptedException {
        HiLog.info(LABEL_LOG, "%{public}s started", new Object() {}.getClass().getEnclosingMethod().getName());

        Optional<Ability> ability = abilityDelegator.startAbilitySync(Global.intentSecondAbility);
        Assert.assertTrue("Get Secondability failed", ability.isPresent());
        if (ability.get() instanceof SecondAbility) {
            SecondAbility secondability = (SecondAbility) ability.get();
            Component textView = secondability.findComponentById(Global.KEYEVENT_RESULT_TEXTVIEW_ID);
            Assert.assertNotNull("keyevent result textview is null", textView);
            abilityDelegator.triggerKeyEvent(secondability, keyBoardEvent);
        } else {
            Assert.fail("get secondability failed");
        }
    }
}
