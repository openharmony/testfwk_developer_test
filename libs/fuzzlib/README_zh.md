# 测试框架DTFuzz测试指导

- [简介](#section7730298375831)
- [使用测试框架DTFuzz](#section0009871491)
- [测试结果与日志](#section016190470)

## 简介<a name="section7730298375831"></a>

模糊测试（fuzzing test）是一种软件测试技术，其核心思想是将自动或半自动生成的随机数据输入到一个程序中，并监视程序异常，如崩溃，断言（assertion）失败，以发现可能的程序错误，比如内存泄漏，访问越界等。

使用测试框架DTFuzz，需要完成DTFuzz初始化、DTFuzz用例编写、DTFuzz用例编译和DTFuzz用例执行几步。



## 使用测试框架DTFuzz<a name="section0009871491"></a>

- 测试框架配置

  文件：config/user_config.xml

  配置测试用例的编译参数

  ```
  <build>
      <example>false</example>
      <version>false</version>
      <testcase>true</testcase>
      ... ...
  </build>
  ```

  ![img](../../public_sys-resources/icon-note.gif) **说明：** 测试用例的编译参数说明如下：

  example：是否编译测试用例示例，默认false。

  version：是否编译测试版本，默认false。

  testcase：是否编译测试用例，默认true。

- 启动测试框架

  打开test/developertest目录，Windows环境启动测试框架执行

  ```
  start.bat
  ```

  Linux环境启动测试框架执行

  ```
  ./start.sh
  ```

- 设备形态选择

  根据实际的开发板选择，设备形态配置：developertest/config/framework_config.xml。

- 单个DTFuzz初始化

  1. DTFuzz源文件生成

     执行gen命令用于DTFuzz源文件生成，会自动生成DTFuzz源文件、DTFuzz options配置文件和corpus语料，目录结构如下

     ```
     parse_fuzzer/
     ├── corpus                        # DTFuzz语料目录
     │   ├── init                      # DTFuzz语料
     ├── BUILD.gn                      # DTFuzz用例编译配置
     ├── parse_fuzzer.cpp              # DTFuzz用例源文件
     ├── parse_fuzzer.h                # DTFuzz用例头文件
     ├── project.xml                   # DTFuzz选项配置文件
     ```

  2. 命令参数说明，参数可以指定DTFuzz名称和DTFuzz路径

     ```
     gen -t TESTTYPE -fn FUZZERNAME -dp DIRECTORYPATH
     ```

     | 参数 | 说明           | 备注                                                     |
     | ---- | -------------- | -------------------------------------------------------- |
     | -t   | 测试类型       | 目前仅支持"FUZZ"                                         |
     | -fn  | DTFuzz名称     | 为显式区分DTFuzz，名称必须以"fuzzer"结尾                 |
     | -dp  | DTFuzz生成路径 | 执行命令前需要手动创建fuzztest目录和对应形态目录如common |

  3. gen命令示例，-t、-fn和-dp均为必选项

     ```
     gen -t FUZZ -fn parse_fuzzer -dp test/developertest/example/calculator/test/fuzztest/common
     ```

- DTFuzz用例编写

  1. 源文件编写

     DTFuzz用例主要在${DTFuzz名称}.cpp源文件中，一个DTFuzz仅支持一个接口进行fuzz测试。

     源文件包含两个接口：

     | 接口                            | 说明                             |
     | ------------------------------- | -------------------------------- |
     | LLVMFuzzerTestOneInput          | DTFuzz入口函数，由Fuzz框架调用   |
     | DoSomethingInterestingWithMyAPI | 被测试接口，实现各业务被测试逻辑 |

     ![img](../../public_sys-resources/icon-note.gif) **说明：** DoSomethingInterestingWithMyAPI接口名称允许依据业务逻辑修改。两接口参数data和size为fuzz测试标准化参数，不可修改。

  2. BUILD.gn编写

     [ohos_fuzztest] # 配置DTFuzz模板，例如：

     ```
     ohos_fuzztest("CalculatorFuzzTest") {     #定义测试套名称CalculatorFuzzTest
     
       module_out_path = module_output_path
       
       include_dirs = []
       cflags = [
         "-g",
         "-O0",
         "-Wno-unused-variable",
         "-fno-omit-frame-pointer",
       ]
       sources = [ "parse_fuzzer.cpp" ]
     }
     ```

     [group] # 引用测试套，例如：

     ```
     group("fuzztest") {
       testonly = true
       deps = []
       
       deps += [
         # deps file
         ":CalculatorFuzzTest",     #引用测试套
       ]
     }
     ```

  3. DTFuzz配置编写

     project.xml为DTFuzz参数配置文件，包括：

     ```
     <!-- maximum length of a test input -->
     <max_len>1000</max_len>
     <!-- maximum total time in seconds to run the DTFuzz -->
     <max_total_time>300</max_total_time>
     <!-- memory usage limit in Mb -->
     <rss_limit_mb>4096</rss_limit_mb>
     ```

- DTFuzz用例编译

  添加DTFuzz用例编译：

  1. 在需要DTFuzz测试的对应模块ohos.build添加DTFuzz用例路径，如在examples/ohos.build添加：

     ```
     "test_list": [
       "//test/developertest/examples/calculator/test:unittest",
       "//test/developertest/examples/calculator/test:fuzztest", #添加DTFuzz用例路径
       "//test/developertest/examples/detector/test:unittest",
       "//test/developertest/examples/sleep/test:performance",
       "//test/developertest/examples/distributedb/test:distributedtest"
     ]
     ```

  2. 在用例路径下的BUILD.gn添加group，如examples/calculator/test的BUILD.gn

     ```
     group("fuzztest") {
       testonly = true
       deps = []
       
       deps += [ "fuzztest/common/parse_fuzzer:fuzztest" ]
     }
     ```

- DTFuzz用例执行

  DTFuzz能力集成在测试类型-t中新增FUZZ类型，执行DTFuzz测试指令示例，其中-t为必选，-ss和-tm为可选

  ```
  run -t FUZZ -ss subsystem_examples -tm calculator
  ```
  
- Windows环境脱离源码执行

  Windows环境可通过归档DTFuzz用例配置文件project.xml、语料corpus和可执行文件执行DTFuzz。

  1. 归档用例配置文件、语料

     新建目录，如：

     ```
     D:\test\res\parse_fuzzer
     ```

     parse_fuzzer用例的配置文件project.xml、语料corpus拷贝到该路径下。如有多个需要执行的用例，在res目录下新建多个xxx_fuzzer目录。

  2. 归档用例可执行文件

     用例可执行文件为DTFuzz源文件编译产出文件，为DTFuzz用例在设备中实际执行文件，以二进制形式存储在out/release/package/phone/tests/fuzztest下，名称为对应的测试套名。
     
     新建目录，如：
     
     ```
     D:\test\cases
     ```
     
     将fuzztest目录拷贝到该路径下。
     
  3. 配置执行用例
  
     libs\fuzzlib中新建fuzzer_list.txt，其中配置需要执行的DTFuzz用例，如需要执行parse_fuzzer用例：
  
     ```
     #格式：用例配置文件和语料归档路径 可执行文件名
     D:\test\res\parse_fuzzer CalculatorFuzzTest
     ```
  
     ![img](../../public_sys-resources/icon-note.gif) **说明：** 
  
     1.fuzzer_list.txt中可配置多行，每行对应一个DTFuzz用例
  
     2.路径与可执行文件名严格一一对应，如例子中路径归档的是parse_fuzzer用例的配置文件和语料，CalculatorFuzzTest为parse_fuzzer用例的可执行文件。
  
  4. 配置用例路径
  
     config\user_config.xml中配置用例归档路径：
  
     ```
     <!-- configure test cases path -->
     <test_cases>
       <dir>D:\test\cases</dir>     #用例可执行文件归档路径
     </test_cases>
     ```
  
  5. 执行用例
  
     执行DTFuzz命令示例，无需参数-ss、-tm
  
     ```
     run -t FUZZ
     ```

## 测试结果与日志<a name="section016190470"></a>

- 通过在测试框架中执行测试指令，即可以生成测试日志和测试报告。

- 测试结果

  测试用例的结果会直接显示在控制台上，执行一次的测试结果根路径如下：

  ```
  reports/xxxx-xx-xx-xx-xx-xx
  ```

  测试用例格式化结果

  ```
  result/
  ```

  测试用例日志

  ```
  log/plan_log_xxxx-xx-xx-xx-xx-xx.log
  ```

  测试报告汇总

  ```
  summary_report.html
  ```

  测试报告详情

  ```
  details_report.html
  ```

  最新测试报告

  ```
  reports/latest
  ```

