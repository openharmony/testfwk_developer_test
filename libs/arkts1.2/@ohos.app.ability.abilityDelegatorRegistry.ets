import { AbilityDelegator as _AbilityDelegator, AbilityDelegatorInner } from 'AbilityDelegator'
import { AbilityDelegatorArgs as _AbilityDelegatorArgs} from 'AbilityDelegatorArgs'
import { ShellCmdResult as _ShellCmdResult } from 'ShellCmdResult'

export default namespace abilityDelegatorRegistry {
  export type AbilityDelegator = _AbilityDelegator;
  export type AbilityDelegatorArgs = _AbilityDelegatorArgs;
  export type ShellCmdResult = _ShellCmdResult;

  export function getAbilityDelegator(): AbilityDelegator {
    return new AbilityDelegatorInner();
  }
  
  export function getArguments(): AbilityDelegatorArgs {
    return {
      "bundleName": "com.example.myapplication",
      "parameters": {
        "-b": "com.example.myapplication",
        "-m": "entry_test",
        "-s": "600000",
        "moduleName": "",
      },
      "testCaseNames": "example",
      "testRunnerClassName": "./OpenHarmonyTestRunner"
    }
  }
}