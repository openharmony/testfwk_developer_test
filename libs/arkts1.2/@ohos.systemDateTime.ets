import { BusinessError } from '@ohos.base';

type AsyncCallback<T, E = void> = (error: BusinessError<E>, data: T) => void;

export default namespace systemDateTime {
  
  export enum TimeType {
    STARTUP,
    ACTIVE
  }

  export function getUptime(timeType: TimeType, isNanoseconds?: boolean): number {
    const nowTime:number = new Date().getTime();
    return nowTime;
  }
  
  const SYSTEM_ERROR: number = 401
  
  export function getCurrentTime(isNano: boolean, callback: AsyncCallback<number>): void {}
  
  export function getCurrentTime(callback: AsyncCallback<number>): void {}
  
  export function getCurrentTime(isNano?: boolean): void {}
  
  export function getTimezone(callback: AsyncCallback<string>): void {}
  
  export function getTimezone(): void {}
}