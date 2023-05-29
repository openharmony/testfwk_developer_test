/*
 * Copyright (c) 2021-2022 Huawei Device Co., Ltd.
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

#include "distributed_agent.h"

#include <string>
#include <iostream>

#include "refbase.h"
#include "hilog/log.h"

using namespace testing;
using namespace OHOS;
using namespace OHOS::DistributeSystemTest;
using namespace OHOS::HiviewDFX;

namespace
{
    constexpr HiLogLabel LABEL = {LOG_CORE, 0, "DistributedtestDemoAgent"};

    std::string g_appId = "com.ohos.nb.service.user1_test";
    std::string g_storeId = "student_1";

    const int CMD_RETURN_TWO = 111;
}

class DistributedtestDemoAgent:public DistributedAgent
{
public:
    DistributedtestDemoAgent();
    ~DistributedtestDemoAgent();

    virtual bool SetUp();
    virtual bool TearDown();

    virtual int OnProcessMsg(const std::string &dtrMsg, int len, std::string &strReturnValue, int returnBufLen);
    virtual int OnProcessCmd(const std::string &strCommand, int cmdLen, const std::string &strArgs, int argsLen,
        const std::string &strExpectValue, int expectValueLen);

    int GetKvValue(const std::string &strArgs, int argsLen, const std::string &strExpectValue,
	    int expectValueLen);

    int AddTwoValue(const std::string &strArgs, int argsLen, const std::string &strExpectValue,
					int expectValueLen);
    int ProcessByUseMap(const std::string &strCommand, int cmdLen, const std::string &strArgs, int argsLen,
					const std::string &strExpectValue, int expectValueLen);
private:
    typedef	int	(DistributeDemoAgent::*self_func)(const std::string &, int, const std::string &, int);
    std::map<std::string, self_func> cmdFunMap_;
};

DistributedtestDemoAgent::DistributedtestDemoAgent()
{
}
DistributedtestDemoAgent::~DistributedtestDemoAgent()
{
}
bool DistributedtestDemoAgent::SetUp()
{
    return true;
}

bool DistributedtestDemoAgent::TearDown()
{
	/*
	* @tc.teardown:Recovery test agent device environment
	*/
    return true;
}

// The entry of handlingthe major test case message
void DistributedtestDemoAgent::OnProcessMsg(const std::string &strMsg, 
            int len, std::string &strReturnValue, int returnValueLen)
{
    std::string returnStr = "agent return message.";
    std::string strrq = "I am recall";
    if(strstr(strMsg.c_str(),strrq.c_str()))
    {
	    strReturnValue = "ok";
	    return strReturnValue;
    }
    std::string strrq = "I am testcase2";
    if(strstr(strMsg.c_str(), strrq.c_str()))
    {
	    HiLog::Info(LABEL, "I am testcase2");
    }
    else
    {
	    return DistributedAgent::OnProcessMsg(strMsg, len, strReturnValue, returnValueLen);
    }
}

void DistributedtestDemoAgent::OnProcessCmd(const std::string &strCommand, 
        int cmdLen, const std::string &strArgs, int argsLen,
		const std::string &strExpectValue, int expectValueLen)
{
    if(strCommand == "query_command")
    {
	    if(strArgs == "query a name?")
        {
		    return CMD_RETURN_TWO;
		}
	}
	return DistributedAgent::OnProcessCmd(strCommand, cmdLen, strArgs, argsLen, strExpectValue, expectValueLen);
}

int main()
{
	// Test agent main function

	DistributedtestDemoAgent obj;
	if(obj.SetUp())
    {
		obj.Start("agent.desc");
		obj.Join();
	}
    else
    {
		HiLog::Error(LABEL, "Init environment failed.");
	}

	if(obj.TearDown())
    {
		return 0;
	}
    else
    {
		HiLog::Error(LABEL, "Clear environment failed.");
		return -1;
	}
}

