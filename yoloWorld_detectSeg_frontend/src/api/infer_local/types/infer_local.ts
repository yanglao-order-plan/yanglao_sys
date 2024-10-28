import internal from "stream"

// 数据前端对象
export interface IFlowData {
  taskTypeName: string
  taskName: string
  flowName: string
  releaseName: string
  releaseShowName: string
}
export interface OFlowData {
  taskTypeName: string
  taskName: string
  flowName: string
  releaseName: string
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
  inferResult: IInferData[]
  inferDescription: string,
  inferPeriod: number
}
export interface IInferData {
  resultBase64: string
  predictResult: string
  predictDescription: string,
  period: number
}
// 数据请求对象
export interface ISwitchFlowRequestData {
  switchTaskTypeName: string
  switchTaskName: string
  switchFlowName: string
  switchReleaseName: string
}
export interface ISwitchHyperRequestData {
  switchHyperName: string | number
  switchHyperValue: any
}
export interface IpredictModelRequestData {
  originalBase64: string
}
// 数据回显对象（current）
export type GetCurrentFlowResponseData = IApiResponseData<OFlowData>  // 字典转数组
export type GetCurrentHyperResponseData = IApiResponseData<[OHyperData]>

export type GetAllFlowsResponseData = IApiResponseData<IFlowData>
// 处理
export type LoadModelResponseData = IApiResponseData<IHyperData[]>
export type PredictModelResponseData = IApiResponseData<IResultData>