export interface ICreateTaskTypeRequestData {
  name: string
}
export interface IUpdateTaskTypeRequestData {
  id: number
  name: string
}
export interface IGetTaskTypeRequestData {
  currentPage: number
  size: number
  taskType?: string
}
export interface IGetTaskTypeData {
  id: number
  taskType: string
}

export type GetTaskTypeResponseData = IApiResponseData<{
  list: IGetTaskTypeData[]
  total: number
}>

export type createTaskTypeResponseData = IApiResponseData<string>
export type deleteTaskTypeResponseData = IApiResponseData<string>
export type upDateTaskTypeResponseData = IApiResponseData<string>
