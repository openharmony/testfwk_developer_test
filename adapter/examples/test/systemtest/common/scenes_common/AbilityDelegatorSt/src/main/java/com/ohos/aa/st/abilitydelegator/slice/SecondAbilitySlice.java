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

import com.ohos.aa.st.abilitydelegator.Global;

import ohos.aafwk.ability.AbilitySlice;
import ohos.aafwk.content.Intent;
import ohos.agp.colors.RgbColor;
import ohos.agp.components.PositionLayout;
import ohos.agp.components.Text;
import ohos.agp.utils.Color;
import ohos.agp.components.Component;
import ohos.agp.components.ComponentContainer.LayoutConfig;
import ohos.agp.components.element.ShapeElement;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import ohos.multimodalinput.event.KeyEvent;
import ohos.multimodalinput.event.TouchEvent;

/**
 * SecondAbilitySlice for test hap.
 */
public class SecondAbilitySlice extends AbilitySlice {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "SecondAbility");
    private static final int COLOR_WHITE = 0xFFFFFFFF;

    private PositionLayout myLayout = new PositionLayout(this);

    private void initClickTextView() {
        ShapeElement drawable = new ShapeElement();
        drawable.setShape(ShapeElement.RECTANGLE);
        drawable.setRgbColor(new RgbColor(Color.GRAY.getValue()));

        Text textView = new Text(this);
        textView.setId(Global.CLICK_RESULT_TEXTVIEW_ID);
        textView.setWidth(100);
        textView.setHeight(100);
        textView.setText("0");
        textView.setTextSize(50);
        textView.setTextColor(new Color(0x7F000000));
        textView.setContentPosition(100, 100);
        textView.setBackground(drawable);

        textView.setClickedListener(new Component.ClickedListener() {
            @Override
            public void onClick(Component view) {
                HiLog.info(LABEL_LOG, "1111111111111~~");
                textView.setText(String.valueOf(Integer.valueOf(textView.getText()) + 1));
                textView.invalidate();
            }
        });

        myLayout.addComponent(textView);
    }

    private void initTouchTextView() {
        ShapeElement drawable = new ShapeElement();
        drawable.setShape(ShapeElement.RECTANGLE);
        drawable.setRgbColor(new RgbColor(Color.GRAY.getValue()));

        Text textView = new Text(this);
        textView.setId(Global.TOUCH_RESULT_TEXTVIEW_ID);
        textView.setWidth(100);
        textView.setHeight(100);
        textView.setText("0");
        textView.setTextSize(50);
        textView.setTextColor(new Color(0x7F000000));
        textView.setContentPosition(220, 100);
        textView.setBackground(drawable);

        myLayout.addComponent(textView);

        myLayout.setTouchEventListener(new Component.TouchEventListener() {
            @Override
            public boolean onTouchEvent(Component view, TouchEvent touchEvent) {
                HiLog.info(LABEL_LOG, "22222222222222~~");
                textView.setText(Integer.valueOf(textView.getText()) + 1 + "");
                textView.invalidate();
                return false;
            }
        });
    }

    private void initKeyEventTextView() {
        ShapeElement drawable = new ShapeElement();
        drawable.setShape(ShapeElement.RECTANGLE);
        drawable.setRgbColor(new RgbColor(Color.GRAY.getValue()));

        Text textView = new Text(this);
        textView.setId(Global.KEYEVENT_RESULT_TEXTVIEW_ID);
        textView.setWidth(100);
        textView.setHeight(100);
        textView.setText("");
        textView.setTextSize(50);
        textView.setTextColor(new Color(0x7F000000));
        textView.setContentPosition(340, 100);
        textView.setBackground(drawable);

        myLayout.setKeyEventListener(new Component.KeyEventListener() {
            @Override
            public boolean onKeyEvent(Component view, KeyEvent keyEvent) {
                HiLog.info(LABEL_LOG, "33333333333~~");
                textView.setText(keyEvent.getKeyCode() + "");
                textView.invalidate();
                return true;
            }
        });

        myLayout.addComponent(textView);
    }

    @Override
    public void onStart(Intent intent) {
        super.onStart(intent);

        LayoutConfig params = new LayoutConfig(LayoutConfig.MATCH_PARENT, LayoutConfig.MATCH_PARENT);
        myLayout.setLayoutConfig(params);
        myLayout.setId(100);

        {
            ShapeElement drawable = new ShapeElement();
            drawable.setShape(ShapeElement.RECTANGLE);
            drawable.setRgbColor(new RgbColor(COLOR_WHITE));
            myLayout.setBackground(drawable);
        }

        initClickTextView();

        initTouchTextView();

        initKeyEventTextView();

        super.setUIContent(myLayout);
    }

    @Override
    public void onActive() {
        super.onActive();
    }
}
