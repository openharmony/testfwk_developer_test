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
package com.ohos.demo.test.service;

import com.ohos.demo.application.StudentMgr;
import com.ohos.demo.service.Istudent;

import ohos.unittest.CaseLevel;
import ohos.unittest.CaseType;
import ohos.unittest.Level;
import ohos.unittest.Type;

import org.easymock.EasyMock;

import org.junit.Assert;
import org.junit.Ignore;
import org.junit.Test;


/**
 * Demo EasyMockStudentMgrTest
 */
public class EasyMockStudentMgrTest {
    /**
     * @tc.name: testGetInfo
     * @tc.desc: Test of obtaining stub information.
     * @tc.type: FUNC
     * @tc.require: AR00000000 SR00000000
     */
    @Test
    @CaseType(type = Type.FUNC)
    @CaseLevel(level = Level.LEVEL_1)
    public void testGetInfo() {
        // 1. use easymock create mock object
        Istudent student = EasyMock.createMock(Istudent.class);

        // 2. set expected behavior and output for mock object
        EasyMock.expect(student.getName()).andReturn("ZhangSan").times(1);
        EasyMock.expect(student.getAge()).andReturn("Nine").times(1);
        EasyMock.expect(student.getGrade()).andReturn("Grade3").times(1);

        // 3. switch replay status for mock object
        EasyMock.replay(student);

        // 4. execute unit test by mock method
        StudentMgr studentMgr = new StudentMgr();
        studentMgr.setStudent(student);

        String getStr = studentMgr.getInfo();

        // 5. validate action of mock object
        String cstr = "ZhangSan Nine Grade3";
        Assert.assertEquals(getStr, cstr);
        EasyMock.verify(student);
    }

    /**
     * @tc.name: testGetInfo1
     * @tc.desc: Test of obtaining stub information.
     * @tc.type: FUNC
     * @tc.require: AR00000000 SR00000000
     */
    @Test
    @CaseType(type = Type.FUNC)
    @CaseLevel(level = Level.LEVEL_1)
    public void testGetInfo1() {
        // 1. use easymock create mock object
        Istudent student = EasyMock.createMock(Istudent.class);

        // 2. set expected behavior and output for mock object
        EasyMock.expect(student.getName()).andReturn("Lisi").times(1);
        EasyMock.expect(student.getAge()).andReturn("Nine").times(1);
        EasyMock.expect(student.getGrade()).andReturn("Grade3").times(1);

        // 3. switch replay status for mock object
        EasyMock.replay(student);

        // 4. execute unit test by mock method
        StudentMgr studentMgr = new StudentMgr();
        studentMgr.setStudent(student);

        String getStr = studentMgr.getInfo();

        // 5. validate action of mock object
        String cstr = "Lisi Nine Grade3";
        Assert.assertEquals(getStr, cstr);
        EasyMock.verify(student);
    }

    /**
     * @tc.name: testGetInfo2
     * @tc.desc: Test of obtaining stub information.
     * @tc.type: FUNC
     * @tc.require: AR00000000 SR00000000
     */
    @Test
    @CaseType(type = Type.FUNC)
    @CaseLevel(level = Level.LEVEL_1)
    public void testGetInfo2() {
        // 1. use easymock create mock object
        Istudent student = EasyMock.createMock(Istudent.class);

        // 2. set expected behavior and output for mock object
        EasyMock.expect(student.getName()).andReturn("Lisi").times(1);
        EasyMock.expect(student.getAge()).andReturn("Nine").times(1);
        EasyMock.expect(student.getGrade()).andReturn("Grade3").times(1);

        // 3. switch replay status for mock object
        EasyMock.replay(student);

        // 4. execute unit test by mock method
        StudentMgr studentMgr = new StudentMgr();
        studentMgr.setStudent(student);

        String getStr = studentMgr.getInfo();

        // 5. validate action of mock object
        String cstr = "Lisi Nine Grade3 false";
        Assert.assertEquals(getStr, cstr);
        EasyMock.verify(student);
    }

    /**
     * @tc.name: testGetInfoIgnore
     * @tc.desc: Test of obtaining stub information.
     * @tc.type: FUNC
     * @tc.require: AR00000000 SR00000000
     */
    @Test
    @Ignore
    @CaseType(type = Type.FUNC)
    @CaseLevel(level = Level.LEVEL_1)
    public void testGetInfoIgnore() {
        // 1. use easymock create mock object
        Istudent student = EasyMock.createMock(Istudent.class);

        // 2. set expected behavior and output for mock object
        EasyMock.expect(student.getName()).andReturn("ZhangSan2").times(1);
        EasyMock.expect(student.getAge()).andReturn("Nine").times(1);
        EasyMock.expect(student.getGrade()).andReturn("Grade3").times(1);

        // 3. switch replay status for mock object
        EasyMock.replay(student);

        // 4. execute unit test by mock method
        StudentMgr studentMgr = new StudentMgr();
        studentMgr.setStudent(student);

        String getStr = studentMgr.getInfo();

        // 5. validate action of mock object
        String cstr = "ZhangSan2 Nine Grade3";
        Assert.assertEquals(getStr, cstr);
        EasyMock.verify(student);
    }
}
