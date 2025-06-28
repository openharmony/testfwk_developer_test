import { BusinessError } from '@ohos.base';
import { ShellCmdResult } from 'ShellCmdResult'

type AsyncCallback<T, E = void> = (error: BusinessError<E>, data: T) => void;

export interface AbilityDelegator {
  
  printSync(msg: string): void;
  
  finishTest(msg: string, code: number): void;
  
  executeShellCommand(cmd: String, timeoutSecs: number, callback: AsyncCallback<ShellCmdResult, void>): void;
}

export class AbilityDelegatorInner implements AbilityDelegator {
  
  printSync(msg: string): void {};
  
  finishTest(msg: string, code: number): void {};
  
  executeShellCommand(cmd: String, timeoutSecs: number, callback: AsyncCallback<ShellCmdResult, void>): void {};
}