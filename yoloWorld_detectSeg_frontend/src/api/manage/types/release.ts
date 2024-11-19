
export interface ICreateReleaseRequestData {
  name: string
  showName: string
  flowId: number
}
export interface ICreateModelRequestData {
  name: string
  weightId: number
  releaseId: number
}
export interface ICreateArgumentRequestData {
  name: string
  type: string
  default: JSON
  config: JSON
  dynamic: number
  releaseId: number
}
export interface ISearchArgumentRequestData {
  name: string
  type: string
  default: JSON
  config: JSON
  dynamic: number
  releaseId: number
}
export interface IUpdateReleaseRequestData {
  id: number
  name: string
  showName: string
  flowId: number
}
export interface IUpdateModelRequestData {  // 兼update
  id: number
  name: string
  weight: string
  weightId: number
}
export interface IUpdateArgumentRequestData {  // 兼update
  id: number
  name: string
  type: string
  default: JSON
  config: JSON
  dynamic: number
}
export interface IGetReleaseRequestData {
  currentPage: number
  size: number
  release?: string
  releaseName?: string
  flow?: string
  task?: string
  taskType?: string
}
export interface IGetReleaseData {
  id: number
  release: string 
  releaseName: string
  flowId: number
  flow: string
  task: string
  taskId: number
  taskType: string
  typeId: number
}
export type GetReleaseResponseData = IApiResponseData<{
  list: IGetReleaseData[]
  whole: { [key: number]: string }
  total: number
}>
export interface IGetModelRequestData {
  model: string
  releaseId: number
}
export interface IGetArgumentRequestData {
  argument: string
  type: string
  dynamic: number
  releaseId: number
}
export type IGetModelData = IUpdateModelRequestData;
export type GetModelResponseData = IApiResponseData<{
  list: IGetModelData[]
  total: number
}>
export type IGetArgumentData = IUpdateArgumentRequestData;
export type GetArgumentResponseData = IApiResponseData<{
  list: IGetArgumentData[]
  total: number
}>

export type createReleaseResponseData = IApiResponseData<string>
export type deleteReleaseResponseData = IApiResponseData<string>
export type upDateReleaseResponseData = IApiResponseData<string>

export type createModelResponseData = IApiResponseData<string>
export type deleteModelResponseData = IApiResponseData<string>
export type upDateModelResponseData = IApiResponseData<string>

export type createArgumentResponseData = IApiResponseData<string>
export type deleteArgumentResponseData = IApiResponseData<string>
export type upDateArgumentResponseData = IApiResponseData<string>