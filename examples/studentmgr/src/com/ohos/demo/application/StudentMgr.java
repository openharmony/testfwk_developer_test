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
package com.ohos.demo.application;

import com.ohos.demo.service.Istudent;


/**
 * Demo StudentMgr
 */
public class StudentMgr {
    private Istudent student = null;

    /**
     * construction method
     */
    public StudentMgr() {
    }

    /**
     * get student Info
     *
     * @apiNote getInfo
     * @return student Info
     */
    public String getInfo() {
        StringBuffer buffer = new StringBuffer(student.getName());
        buffer.append(" ");
        buffer.append(student.getAge());
        buffer.append(" ");
        buffer.append(student.getGrade());

        return buffer.toString();
    }

    public Istudent getStudent() {
        return student;
    }

    public void setStudent(Istudent student) {
        this.student = student;
    }
}
