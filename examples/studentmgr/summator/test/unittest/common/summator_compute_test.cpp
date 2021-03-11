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

#include <tuple>
#include "Summator.h"
#include "ParserMock.h"

#include <gtest/gtest.h>

using namespace testing::ext;


class SummatorComputeTest : public testing::TestWithParam<std::tuple<const char*, std::vector<int>, int>>
{
public:
    SummatorComputeTest() { }
    ~SummatorComputeTest() { }
};

/**
 * @tc.name: compute_001
 * @tc.desc: Detecting the function of addition.
 * @tc.type: PERF
 * @tc.require: AR000CQGNT
 */
HWTEST_P(SummatorComputeTest, compute_001, TestSize.Level0)
{
    ParserMock parser;
    Summator summator(parser);

    const char* str = std::get<0>(GetParam());
    std::vector<int> mockRes = std::get<1>(GetParam());
    int result = std::get<2>(GetParam());

    EXPECT_CALL(parser, parse(str)).WillOnce(testing::Return(mockRes));
    EXPECT_EQ(result, summator.compute(str));
}

INSTANTIATE_TEST_CASE_P(ComputeTest, SummatorComputeTest,
    testing::Values(std::tuple<const char*, std::vector<int>, int>("12 -1 14 78", { 12, -1, 14, 78 }, 103),
                    std::tuple<const char*, std::vector<int>, int>("0 0 0 0",     { 0, 0, 0, 0 },     0),
                    std::tuple<const char*, std::vector<int>, int>("1 2 3 4",     { 1, 2, 3, 4 },     10),
                    std::tuple<const char*, std::vector<int>, int>("",            { },                0),
                    std::tuple<const char*, std::vector<int>, int>("10 10 85",    { 10, 10, 85},      105),
                    std::tuple<const char*, std::vector<int>, int>("-1 1 -1 1",   { -1, 1, -1, 1 },   0)));

