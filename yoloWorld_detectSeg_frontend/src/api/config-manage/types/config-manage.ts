// 数据前端对象
export interface ICreateTaskTypeData {
  taskTypeName: string
}
export interface IUpdateTaskTypeData {
  id: string
  taskTypeName: string
}
export interface ICreateTaskData {
  taskName: string
  taskTypeId: string
}
export interface IUpdateTaskData {
  id: string
  taskName: string
  taskTypeId: string
}
export interface ICreateFlowData {
  flowName: string
  taskId: string
}
export interface IUpdateFlowData {
  id: string
  flowName: string
}
export interface ICreateReleaseData {
  releaseName: string
  releaseShowName: string
  flowId: string
}
export interface IUpdateReleaseData {
  id: string
  releaseName: string
  releaseShowName: string
  flowId: string
}
export interface ICreateWeightData {
  weightName: string
  localPath: string
  onlineUrl: string
  enable: number
}
export interface IUpdateWeightData {
  id: string
  weightName: string
  localPath: string
  onlineUrl: string
  enable: number
}
export interface ICreateReleaseWeightData {
  releaseWeightName: string
  releaseId: string
  weightId: string
}
export interface IUpdateReleaseWeightData {
  id: string
  releaseWeightName: string
  releaseId: string
  weightId: string
}
export interface ICreateReleaseArgData {
  argName: string
  argType: string
  argDefault: JSON
  argConfig: JSON
  dynamic: number
  releaseId: string
}
export interface IUpdateReleaseArgData {
  id: string
  argName: string
  argType: string
  argDefault: JSON
  argConfig: JSON
  dynamic: number
  releaseId: string
}


export interface IGetTableRequestData {
  /** 当前页码 */
  currentPage: number
  /** 查询条数 */
  size: number
  /** 查询参数：用户名 */
  username?: string
  /** 查询参数：邮箱 */
  email?: string
}

export interface IGetTableData {
  createTime: string
  email: string
  id: string
  // phone: string
  roles: string
  status: boolean
  username: string
}

export type GetTableResponseData = IApiResponseData<{
  list: IGetTableData[]
  total: number
}>

export type createTableResponseData = IApiResponseData<string>
export type deleteTableResponseData = IApiResponseData<string>
export type upDateTableResponseData = IApiResponseData<string>
