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

import com.ohos.aa.st.abilitydelegator.SecondAbility;

import ohos.aafwk.ability.AbilitySlice;
import ohos.aafwk.content.Intent;
import ohos.agp.colors.RgbColor;
import ohos.agp.components.PositionLayout;
import ohos.agp.components.Button;
import ohos.agp.utils.Color;
import ohos.agp.components.ComponentContainer.LayoutConfig;
import ohos.agp.components.element.ShapeElement;
import ohos.bundle.ElementName;

/**
 * PageAbilitySlice for test hap.
 */
public class PageAbilitySlice extends AbilitySlice {
    private static final int COLOR_WHITE = 0xFFFFFFFF;

    private PositionLayout myLayout = new PositionLayout(this);

    @Override
    public void onStart(Intent intent) {
        super.onStart(intent);

        LayoutConfig params = new LayoutConfig(LayoutConfig.MATCH_PARENT, LayoutConfig.MATCH_PARENT);
        myLayout.setLayoutConfig(params);

        {
            ShapeElement drawable = new ShapeElement();
            drawable.setShape(ShapeElement.RECTANGLE);
            drawable.setRgbColor(new RgbColor(COLOR_WHITE));
            myLayout.setBackground(drawable);
        }

        {
            ShapeElement drawable = new ShapeElement();
            drawable.setShape(ShapeElement.RECTANGLE);
            drawable.setRgbColor(new RgbColor(Color.GRAY.getValue()));

            Button button = new Button(this);
            button.setWidth(400);
            button.setHeight(200);
            button.setBackground(drawable);
            button.setText("JUMP");
            button.setTextSize(50);
            button.setTextColor(Color.RED);
            button.setContentPosition(100, 100);

            button.setClickedListener(view -> {
                Intent intent1 = new Intent();
                ElementName elementName = new ElementName();
                elementName.setBundleName(SecondAbility.class.getPackage().getName());
                elementName.setAbilityName(SecondAbility.class.getSimpleName());
                intent1.setElement(elementName);
                startAbility(intent1);
            });

            myLayout.addComponent(button);
        }

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
