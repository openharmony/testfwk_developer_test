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

import org.junit.Assert;
import org.junit.Test;
import com.ohos.demo.model.Calculator;
import com.ohos.demo.test.BaseJunit;
import ohos.unittest.AppContext;
import ohos.unittest.log.Logger;
import ohos.unittest.CaseLevel;
import ohos.unittest.CaseType;
import ohos.unittest.Level;
import ohos.unittest.Type;

/**
 * Demo CalculatorTest
 */
public class CalculatorTest extends BaseJunit {
    /**
     * test data 180
     */
    private static final int DATA_180 = 180;

    /**
     * test data 900
     */
    private static final int DATA_900 = 900;

    /**
     * test data 40
     */
    private static final int DATA_40 = 40;

    /**
     * test data 30
     */
    private static final int DATA_30 = 30;

    /**
     * test data 80
     */
    private static final int DATA_80 = 80;

    /**
     * test data 10
     */
    private static final int DATA_10 = 10;

    /**
     * test data 450
     */
    private static final int DATA_450 = 450;

    /**
     * test data 200
     */
    private static final int DATA_200 = 200;

    /**
     * test data 100
     */
    private static final int DATA_100 = 100;

    /**
     * test data 20
     */
    private static final int DATA_20 = 20;

    /**
     * Calculator instance
     */
    private Calculator instance = new Calculator();

    /**
     * construction method
     */
    public CalculatorTest() {
    }

    /**
     * testAdd0
     */
    @Test
    @CaseType(type = Type.FUNC)
    @CaseLevel(level = Level.LEVEL_0)
    public void testAdd0() {
        Assert.assertEquals(DATA_30, instance.add(DATA_10, DATA_20));
    }

    /**
     * testAdd1
     */
    @Test
    @CaseType(type = Type.PERF)
    @CaseLevel(level = Level.LEVEL_1)
    public void testAdd1() {
        Assert.assertEquals(DATA_40, instance.add(DATA_20, DATA_20));
    }

    /**
     * testAdd2
     */
    @Test
    @CaseType(type = Type.RELI)
    @CaseLevel(level = Level.LEVEL_2)
    public void testAdd2() {
        Assert.assertEquals(DATA_900, instance.add(DATA_450, DATA_450));
    }

    /**
     * testAdd3
     */
    @Test
    @CaseType(type = Type.RELI)
    @CaseLevel(level = Level.LEVEL_2)
    public void testAdd3() {
        Assert.assertEquals(DATA_180, instance.add(DATA_450, DATA_450));
    }

    /**
     * testSub3
     */
    @Test
    @CaseType(type = Type.COMP)
    @CaseLevel(level = Level.LEVEL_3)
    public void testSub3() {
        if (AppContext.getInstance().getCurrentActivity() != null) {
            Logger.info("AppContext.getInstance().getCurrentActivity()!=null");
        } else {
            Logger.info("AppContext.getInstance().getCurrentActivity()==null");
        }
        Assert.assertTrue(AppContext.getInstance().getCurrentActivity() != null);

        if (AppContext.getInstance().getCurrentAbility() != null) {
            Logger.info("AppContext.getInstance().getCurrentAbility()!=null");
        } else {
            Logger.info("AppContext.getInstance().getCurrentAbility()==null");
        }
        Assert.assertTrue(AppContext.getInstance().getCurrentAbility() != null);

        Assert.assertEquals(-DATA_10, instance.sub(DATA_10, DATA_20));
    }

    /**
     * testSub4
     */
    @Test
    @CaseType(type = Type.USAB)
    @CaseLevel(level = Level.LEVEL_4)
    public void testSub4() {
        Assert.assertEquals(DATA_80, instance.sub(DATA_100, DATA_20));
    }

    /**
     * testSub5
     */
    @Test
    @CaseType(type = Type.SERV)
    @CaseLevel(level = Level.LEVEL_4)
    public void testSub5() {
        Assert.assertEquals(-DATA_100, instance.sub(DATA_100, DATA_200));
    }

    /**
     * testSub6
     */
    @Test
    @CaseType(type = Type.SECU)
    @CaseLevel(level = Level.LEVEL_4)
    public void testSub6() {
        Assert.assertEquals(DATA_180, instance.sub(DATA_200, DATA_20));
    }
}
