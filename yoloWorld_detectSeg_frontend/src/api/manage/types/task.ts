export interface ICreateTaskRequestData {
  name: string
  typeId: number
}
export interface IUpdateTaskRequestData {
  id: number
  name: string
  typeId: number
}
export interface IGetTaskRequestData {
  currentPage: number
  size: number
  task?: string
  taskType?: string
}
export interface IGetTaskData {
  id: number
  task: string
  taskType: string
  typeId: number
}
export type GetTaskResponseData = IApiResponseData<{
  list: IGetTaskData[]
  total: number
}>
export type createTaskResponseData = IApiResponseData<string>
export type deleteTaskResponseData = IApiResponseData<string>
export type upDateTaskResponseData = IApiResponseData<string>