export enum LogLevel {
  DEBUG = 3,
  INFO = 4,
  WARN = 5,
  ERROR = 6,
  FATAL = 7
}

export default namespace hilog {
  
  export function debug(domain: number, tag: string, format: string, ...args: (number | boolean | string | object | null | undefined)[]): void{}
  
  export function info(domain: number, tag: string, format: string, ...args: (number | boolean | string | object | null | undefined)[]): void{}
  
  export function warn(domain: number, tag: string, format: string, ...args: (number | boolean | string | object | null | undefined)[]): void{}
  
  export function error(domain: number, tag: string, format: string, ...args: (number | boolean | string | object | null | undefined)[]): void{}
  
  export function fatal(domain: number, tag: string, format: string, ...args: (number | boolean | string | object | null | undefined)[]): void{}
}