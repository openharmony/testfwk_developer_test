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

package ohos.unittest;

import ohos.aafwk.ability.Ability;
import ohos.aafwk.content.Intent;
import ohos.unittest.log.HiLogUtil;
import ohos.unittest.runner.UtTestRunner;

/**
 * TestAbility
 */
public class TestAbility extends Ability {
    @Override
    public void onStart(Intent intent) {
        HiLogUtil.info(this.getClass(), "onStart begin");
        AppContext.getInstance().setCurrentAbility(this);
        super.onStart(intent);
        HiLogUtil.info(this.getClass(), "onStart end");
    }

    /**
     * executeTestCase
     *
     * @apiNote executeTestCase
     * @param intent intent object
     */
    public void executeTestCase(Intent intent) {
        new Thread(() -> {
            HiLogUtil.info(this.getClass(), "Run test in child thread begin");
            executeTesting(intent);
            HiLogUtil.info(this.getClass(), "Run test in child thread end");
        }).start();
    }

    /**
     * executeTestCaseInMainThread
     *
     * @apiNote executeTestCaseInMainThread
     * @param intent intent object
     */
    public void executeTestCaseInMainThread(Intent intent) {
        HiLogUtil.info(this.getClass(), "runTestCase begin");
        executeTesting(intent);
        HiLogUtil.info(this.getClass(), "runTestCase end");
    }

    /**
     * executeTesting
     *
     * @apiNote execute Testing by TestRunner
     * @param intent intent object
     */
    private void executeTesting(Intent intent) {
        HiLogUtil.info(this.getClass(), "ExecuteTesting begin");
        String param = "";
        if (intent != null) {
            if (intent.hasParameter("param")) {
                param = intent.getStringParam("param");
                HiLogUtil.info(this.getClass(), "param = " + param);
            } else {
                HiLogUtil.info(this.getClass(), "param is empty");
            }
        } else {
            HiLogUtil.info(this.getClass(), "intent is null");
        }
        HiLogUtil.info(this.getClass(), "Run test by TestRunner begin");
        String xmlPath = "/data/data/" + getAbilityInfo().getBundleName() + "/files/test/result/";
        param += "#OUTPUT_DIR=" + xmlPath;
        param += "#OUTPUT_FILE=testcase_result";
        String[] args = param.split("#");
        UtTestRunner testRunner = new UtTestRunner();
        testRunner.run(args);
        HiLogUtil.info(this.getClass(), "Run test by TestRunner end");
        HiLogUtil.info(this.getClass(), "ExecuteTesting end");
    }
}