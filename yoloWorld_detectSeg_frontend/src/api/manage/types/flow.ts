export interface ICreateFlowRequestData {
  name: string
  taskId: number
}
export interface IUpdateFlowRequestData {
  id: number
  name: string
  taskId: number
}
export interface IGetFlowRequestData {
  currentPage: number
  size: number
  flow?: string
  task?: string
  taskType?: string
}
export interface IGetFlowData {
  id: number
  flow: string
  task: string
  taskId: number
  taskType: string
  typeId: number
}
export type GetFlowResponseData = IApiResponseData<{
  list: IGetFlowData[]
  total: number
}>
export type createFlowResponseData = IApiResponseData<string>
export type deleteFlowResponseData = IApiResponseData<string>
export type upDateFlowResponseData = IApiResponseData<string>