export interface ShellCmdResult {
  stdResult: string;
  exitCode: number;
}

export class ShellCmdResultImpl implements ShellCmdResult {
  
  public stdResult: string = '';
  
  public exitCode: number = 0;
}