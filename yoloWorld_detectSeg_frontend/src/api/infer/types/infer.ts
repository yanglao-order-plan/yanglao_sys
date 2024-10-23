import internal from "stream"

// 数据前端对象
export interface ITaskData {
  taskTypeName: string
  taskName: string
}
export interface IFlowData {
  flowName: string
  releaseName: string
  releaseShowName: string
}
export interface OFlowData {
  flowName: string
  releaseName: string
}
export interface IWeightData {
  weightKey: string
  weightName: string
  weightEnable: string
}
export interface OWeightData {
  weightKey: string
  weightName: string
}
export interface IParamData {
  paramName: string
  paramValue: any
}
export interface IHyperData {
  hyperName: string
  hyperType: string
  hyperDefault: any
  hyperConfig: JSON  //自动解析
}
export interface OHyperData {
  hyperName: string
  hyperValue: any
}
export interface IResultData {
  resultBase64: string
  predictResult: IPredictData[]
  predictDescription: string,
  period: number
}
export interface IPredictData {
  resultBase64: string
  predictResult: string
  predictDescription: string,
  period: number
}
// 数据请求对象
export interface ISwitchTaskRequestData {
  switchTaskTypeName: string
  switchTaskName: string
}
export interface ISwitchFlowRequestData {
  switchFlowName: string
  switchReleaseName: string
}
export interface ISwitchWeightRequestData {
  switchWeightKey: string | number
  switchWeightName: string
}
export interface ISwitchParamRequestData {
  switchParamName: string | number
  switchParamValue: any
}
export interface ISwitchHyperRequestData {
  switchHyperName: string
  switchHyperValue: any
}
export interface IpredictModelRequestData {
  originalBase64: string
}
// 数据回显对象（current）
export type GetCurrentTaskResponseData = IApiResponseData<ITaskData>
export type GetCurrentFlowResponseData = IApiResponseData<OFlowData>  // 字典转数组
export type GetCurrentParamResponseData = IApiResponseData<[IParamData]>
export type GetCurrentWeightResponseData = IApiResponseData<[OWeightData]>
export type GetCurrentHyperResponseData = IApiResponseData<[OHyperData]>
// 数据回显对象（switch）
export type SwitchTaskResponseData = IApiResponseData<IFlowData[]>
export type SwitchFlowResponseData = IApiResponseData<{weight: IWeightData[]; param: IParamData[];}>
// 数据回显对象（all）
export type GetAllTasksResponseData = IApiResponseData<ITaskData>
export type GetAllFlowsResponseData = IApiResponseData<IFlowData>
export type GetAllParamsResponseData = IApiResponseData<IParamData>
// 处理
export type LoadModelResponseData = IApiResponseData<IHyperData[]>
export type PredictModelResponseData = IApiResponseData<IResultData>