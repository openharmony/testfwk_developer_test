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

package com.ohos.demo.test;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;

/**
 * Demo BaseJunit
 */
public class BaseJunit {
    /**
     * beforeClass
     *
     * @apiNote beforeClass
     * @throws Exception beforeClass Exception
     */
    @BeforeClass
    public static void beforeClass() throws Exception {
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
}
