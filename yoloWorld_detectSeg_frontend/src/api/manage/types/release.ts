
export interface ICreateReleaseRequestData {
  name: string
  showName: string
  models: ICreateModelRequestData[]
  arguments: ICreateArgumentRequestData[]
  flowId: number
}
export interface ICreateModelRequestData {
  name: string
  weightId: string
}
export interface ICreateArgumentRequestData {
  name: string
  type: string
  default: any
  config: JSON
  dynamic: number
}
export interface IUpdateReleaseRequestData {
  id: number
  name: string
  showName: string
  models: IUpdateModelRequestData[]
  arguments: IUpdateModelRequestData[]
  flowId: number
}
export interface IUpdateModelRequestData {  // 兼update
  id: number
  name: string
  weightId: string
}
export interface IUpdateModelRequestData {  // 兼update
  id: number
  name: string
  type: string
  default: any
  config: JSON
  dynamic: number
}
export interface IGetReleaseRequestData {
  currentPage: number
  size: number
  release?: string
  flow?: string
  task?: string
  taskType?: string
}
export interface IGetReleaseData {
  id: number
  name: string 
  showName: string
  flow: string
  models: IGetModelData[]
  arguments: IGetArgumentData[]
}
export type GetReleaseResponseData = IApiResponseData<{
  list: IGetReleaseData[]
  total: number
}>
export type IGetModelData = IUpdateModelRequestData;
export type IGetArgumentData = IUpdateModelRequestData;

export type createReleaseResponseData = IApiResponseData<string>
export type deleteReleaseResponseData = IApiResponseData<string>
export type upDateReleaseResponseData = IApiResponseData<string>