export interface AbilityDelegatorArgs {
  bundleName: string;
  parameters: Record<string, string>;
  testCaseNames: string;
  testRunnerClassName: string;
}

class AbilityDelegatorArgsInner implements AbilityDelegatorArgs {
  public bundleName: string = '';
  
  public parameters: Record<string, string> = {};
  
  public testCaseNames: string = '';
  
  public testRunnerClassName: string = '';
}