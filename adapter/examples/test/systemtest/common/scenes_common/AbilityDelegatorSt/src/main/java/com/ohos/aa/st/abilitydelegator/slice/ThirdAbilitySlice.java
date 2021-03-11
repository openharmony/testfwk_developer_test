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

package com.ohos.aa.st.abilitydelegator.slice;

import ohos.aafwk.ability.AbilitySlice;
import ohos.aafwk.content.Intent;
import ohos.agp.colors.RgbColor;
import ohos.agp.components.PositionLayout;
import ohos.agp.components.Text;
import ohos.agp.utils.Color;
import ohos.agp.components.ComponentContainer.LayoutConfig;
import ohos.agp.components.element.ShapeElement;

/**
 * ThirdAbilitySlice for test hap.
 */
public class ThirdAbilitySlice extends AbilitySlice {
    private static final int COLOR_WHITE = 0xFFFFFFFF;

    private PositionLayout myLayout = new PositionLayout(this);

    @Override
    public void onStart(Intent intent) {
        super.onStart(intent);

        LayoutConfig params = new LayoutConfig(LayoutConfig.MATCH_PARENT, LayoutConfig.MATCH_PARENT);
        myLayout.setLayoutConfig(params);

        ShapeElement drawable = new ShapeElement();
        drawable.setShape(ShapeElement.RECTANGLE);
        drawable.setRgbColor(new RgbColor(COLOR_WHITE));
        myLayout.setBackground(drawable);

        Text text = new Text(this);
        text.setText("Hello World");
        text.setTextColor(Color.BLACK);
        myLayout.addComponent(text);

        super.setUIContent(myLayout);
    }

    @Override
    public void onActive() {
        super.onActive();
    }

    @Override
    public void onForeground(Intent intent) {
        super.onForeground(intent);
    }
}
