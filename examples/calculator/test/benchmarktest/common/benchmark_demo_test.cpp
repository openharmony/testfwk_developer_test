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

#include <benchmark/benchmark.h>
#include <string>
#include <vector>

using namespace std;

namespace {
    /*************************************************************************
     * Demo01--Demonstrate the simple usage of benchmarks.
     */

    /*
     * Feature: benchmark test
     * Function: SimpleExample
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: To be tested function.
     */
    size_t SimpleExample()
    {
        string str = "benchmark test";
        return str.size();
    }
    
    /*
     * Feature: benchmark test
     * Function: BenchmarkTestExample
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Testcase for testing 'SimpleExample' function.
     */
    static void BenchmarkTestExample(benchmark::State &state)
    {
        for (auto _ : state) {
            SimpleExample();
        }
    }
    
    // Register the function as a benchmark
    BENCHMARK(BenchmarkTestExample);
    // Register benchmark and explicitly set the fix iterations.
    BENCHMARK(BenchmarkTestExample)->Iterations(1000);
    
    /*************************************************************************
     * Demo02--By comparing the performance of tow methonds for accessing
     *         elements in the "std::vector" container to demonstrate the
     *         usage of benchmark.
     */
     
    /*
     * Feature: benchmark test
     * Function: AccessVectorElementByOperator
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Access vector container elements using operators[].
     */
    void AccessVectorElementByOperator()
    {
        constexpr int testLen = 5;
        std::vector<int> testVec(testLen, 0);
        for (int i = 0; i < testLen; i++) {
            testVec[i] = i * i;
        }
    }
    
    /*
     * Feature: benchmark test
     * Function: BenchmarkTestVectorOperator
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Testcase for testing "AccessVectorElementByOperator"
     *                  function.
     */
    static void BenchmarkTestVectorOperator(benchmark::State &state)
    {
        for (auto _ : state) {
            AccessVectorElementByOperator();
        }
    }

    /*
     * Register the function as a benchmark, set iterations repetitions.
     * And set "ReportAggregatesOnly", it will display the statistics Mean,
     * Median and Standard Deviation of Repeated Benchmarks.
     */
    BENCHMARK(BenchmarkTestVectorOperator)->Iterations(1000)->Repetitions(3)->
        ReportAggregatesOnly();

    /*
     * Feature: benchmark test
     * Function: AccessVectorElementByAt
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Access vector container elements using at().
     */
    void AccessVectorElementByAt()
    {
        constexpr int testLen = 5;
        std :: vector<int> testVec(testLen, 0);
        for (int i = 0; i < testLen; i++) {
            testVec.at(i) = i * i;
        }
    }
    
    /*
     * Feature: benchmark test
     * Function: BenchmarkTestVectorAt
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Testcase for testing "AccessVectorElementByAt"
     *                  function.
     */
     
    static void BenchmarkTestVectorAt(benchmark::State &state)
    {
        for (auto _ : state) {
            AccessVectorElementByAt();
        }
    }
    
    /*
     * Register the function as a benchmark, set iterations repetitions.
     * And set "ReportAggregatesOnly", it will display the statistics Mean,
     * Median and Standard Deviation of Repeated Benchmarks.
     */
    BENCHMARK(BenchmarkTestVectorAt)->Iterations(1000)->Repetitions(3)->
        ReportAggregatesOnly();

    /*************************************************************************
     * Demo03--Use a example to demonstrate the usage of benchmarks fixtures.
     */
     
    /*
     * Feature: benchmark test
     * Function: BenchmarkDemoTest
     * SubFunction: NA
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Defining a fixture tests class that derives from
     *                  benchmark::Fixture.
     */
    class BenchmarkDemoTest : public benchmark::Fixture {
    public:
        void SetUp(const ::benchmark::State &state)
        {
            phoneWidth_ = 1080;   // 1080 is default width
            phoneHeight_ = 2244;  // 2244 is default height
        }

        void TearDown(const ::benchmark::State &state)
        {
        }
        
        int phoneWidth_;
        int phoneHeight_;
    };
    
    /*
     * Feature: benchmark test
     * Function: CalculatedAreaTestCase
     * FunctionPoint: NA
     * EnvConditions: NA
     * CaseDescription: Define a testcase that accesses a class member
     *                  variable.
     */
    BENCHMARK_F(BenchmarkDemoTest, CalculatedAreaTestCase)(
        benchmark::State &st)
    {
        long int area = 0;
        for (auto _ : st) {
            area = phoneWidth_ * phoneHeight_;
        }
    }
    
    BENCHMARK_REGISTER_F(BenchmarkDemoTest, CalculatedAreaTestCase);
    /************************************************************************/
}

// Run the benchmark
BENCHMARK_MAIN();
