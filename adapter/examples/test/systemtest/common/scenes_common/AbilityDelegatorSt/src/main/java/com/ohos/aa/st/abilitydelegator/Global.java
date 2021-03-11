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

import ohos.aafwk.content.Intent;
import ohos.bundle.ElementName;

/**
 * Storing global variables.
 */
public class Global {
    /**
     * result textview
     */
    public static int CLICK_RESULT_TEXTVIEW_ID = 1001;
    /**
     * result textview
     */
    public static int TOUCH_RESULT_TEXTVIEW_ID = 1002;
    /**
     * result textview
     */
    public static int KEYEVENT_RESULT_TEXTVIEW_ID = 1003;
    /**
     * result hits
     */
    public static int ON_STOP_HITS = 0;
    /**
     * result hits
     */
    public static int ON_ACTIVE_HITS = 0;
    /**
     * result hits
     */
    public static int ON_INACTIVE_HITS = 0;
    /**
     * result hits
     */
    public static int ON_BACKGROUND_HITS = 0;
    /**
     * result hits
     */
    public static int ON_FOREGROUND_HITS = 0;

    /**
     * intent for jump
     */
    public static Intent intentPageAbility = new Intent();
    /**
     * intent for jump
     */
    public static Intent intentSecondAbility = new Intent();
    /**
     * intent for jump
     */
    public static Intent intentThirdAbility = new Intent();

    static {
        ElementName elementName = new ElementName();
        elementName.setBundleName(SecondAbility.class.getPackage().getName());
        elementName.setAbilityName(SecondAbility.class.getSimpleName());
        intentSecondAbility.setElement(elementName);
    }

    static {
        ElementName elementName = new ElementName();
        elementName.setBundleName(PageAbility.class.getPackage().getName());
        elementName.setAbilityName(PageAbility.class.getSimpleName());
        intentPageAbility.setElement(elementName);
    }

    static {
        ElementName elementName = new ElementName();
        elementName.setBundleName(ThirdAbility.class.getPackage().getName());
        elementName.setAbilityName(ThirdAbility.class.getSimpleName());
        intentThirdAbility.setElement(elementName);
    }
}
