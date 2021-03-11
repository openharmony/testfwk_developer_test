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

package com.ohos.demo.test.model;

import com.ohos.demo.model.Calculator;
import ohos.unittest.perf.BaseLine;
import ohos.unittest.perf.PerfVerify;
import ohos.unittest.log.Logger;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import ohos.unittest.CaseLevel;
import ohos.unittest.CaseType;
import ohos.unittest.Level;
import ohos.unittest.Type;
import ohos.unittest.TestTarget;

import java.util.Locale;

/**
 * 〈PerformanceTest〉
 */
public class PerformanceTest {
    private static BaseLine baseLine = null;

    /**
     * Calculator instance
     */
    private Calculator instance = new Calculator();

    /**
     * beforeClass
     *
     * @apiNote beforeClass
     * @throws Exception beforeClass Exception
     */
    @BeforeClass
    public static void beforeClass() throws Exception {
        String baseLineConfigFile = "/data/test/perftimetest.xml";
        baseLine = new BaseLine(baseLineConfigFile);
    }

    /**
     * afterClass
     *
     * @apiNote afterClass
     * @throws Exception afterClass Exception
     */
    @AfterClass
    public static void afterClass() throws Exception {
    }

    /**
     * before
     *
     * @apiNote before
     * @throws Exception before Exception
     */
    @Before
    public void before() throws Exception {
    }

    /**
     * after
     *
     * @apiNote after
     * @throws Exception after Exception
     */
    @After
    public void after() throws Exception {
    }

    /**
     * testSub1
     */
    @Test
    @CaseType(type = Type.SECU)
    @CaseLevel(level = Level.LEVEL_0)
    public void testSub1() {
        PerfVerify verify = new PerfVerify(baseLine, 1);
        long startTime = System.currentTimeMillis();

        int cyclesNumber = 100;
        for (int time = 0; time <= cyclesNumber; time++) {
            Assert.assertEquals(80, instance.sub(100, 20));
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                Logger.info(String.format(Locale.ROOT, "InterruptedException: %s", e.getMessage()));
            }
        }

        long endTime = System.currentTimeMillis();
        double spentTime = (endTime - startTime) / cyclesNumber;
        verify.expectSmaller(spentTime);
    }

    /**
     * testSub2
     */
    @Test
    @CaseType(type = Type.SECU)
    @CaseLevel(level = Level.LEVEL_1)
    public void testSub2() {
        PerfVerify verify = new PerfVerify(baseLine, 1);
        long startTime = System.currentTimeMillis();

        int cyclesNumber = 100;
        for (int time = 0; time <= cyclesNumber; time++) {
            Assert.assertEquals(40, instance.sub(60, 20));
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                Logger.info(String.format(Locale.ROOT, "InterruptedException: %s", e.getMessage()));
            }
        }

        long endTime = System.currentTimeMillis();
        double spentTime = (endTime - startTime) / cyclesNumber;
        verify.expectLarger(spentTime);
    }

    /**
     * testSub3
     */
    @Test
    @CaseType(type = Type.SECU)
    @CaseLevel(level = Level.LEVEL_2)
    public void testSub3() {
        PerfVerify verify = new PerfVerify(baseLine, 1);
        long startTime = System.currentTimeMillis();

        int cyclesNumber = 100;
        for (int time = 0; time <= cyclesNumber; time++) {
            Assert.assertEquals(-20, instance.sub(0, 20));
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                Logger.info(String.format(Locale.ROOT, "InterruptedException: %s", e.getMessage()));
            }
        }

        long endTime = System.currentTimeMillis();
        double spentTime = (endTime - startTime) / cyclesNumber;
        verify.expectSmaller(spentTime);
    }

    /**
     * testAddAndSub
     */
    @Test
    @CaseType(type = Type.SECU)
    @CaseLevel(level = Level.LEVEL_3)
    @TestTarget(className = "com.ohos.demo.model.Calculator", methodName = "public int sub(int data1, int data2)")
    public void testAddAndSub() {
        PerfVerify verify = new PerfVerify(baseLine, 1);
        long startTime = System.currentTimeMillis();

        int cyclesNumber = 50;
        for (int time = 0; time <= cyclesNumber; time++) {
            Assert.assertEquals(80, instance.sub(100, 20));
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                Logger.info(String.format(Locale.ROOT, "InterruptedException: %s", e.getMessage()));
            }
        }

        long endTime = System.currentTimeMillis();
        double spentTime = (endTime - startTime) / cyclesNumber;
        verify.expectLarger(spentTime);
    }

    /**
     * testAdd5
     */
    @Test
    @CaseType(type = Type.SECU)
    @CaseLevel(level = Level.LEVEL_4)
    @TestTarget(className = "com.ohos.demo.model.Calculator", methodName = "public int add(int data1, int data2)")
    public void testAdd() {
        PerfVerify verify = new PerfVerify(baseLine, 1);
        long startTime = System.currentTimeMillis();

        int cyclesNumber = 50;
        for (int time = 0; time <= cyclesNumber; time++) {
            Assert.assertEquals(50, instance.add(30, 20));
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                Logger.info(String.format(Locale.ROOT, "InterruptedException: %s", e.getMessage()));
            }
        }

        long endTime = System.currentTimeMillis();
        double spentTime = (endTime - startTime) / cyclesNumber;
        verify.expectLarger(spentTime);
    }
}
