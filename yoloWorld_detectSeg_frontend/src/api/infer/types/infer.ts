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
export interface IArgData {
  argName: string
  argType: string
  argDefault: any
  argConfig: Record<string, any>  //自动解析
}
export interface OArgData {
  argName: string
  argValue: any
}
export interface IResultData {
  resultBase64: string[]
  inferResult: IInferData[]
  inferDescription: string,
  inferPeriod: number
}
export interface IInferData {
  label: string;
  score: number;
  points: number[];  // 假设 points 是一个数组
  groupId: number;   // group_id 映射到 groupId
  predictDescription: string;  // description 映射到 predictDescription
  difficult: boolean;
  shapeType: string;
  flags: object;  // 假设 flags 是一个对象
  attributes: object;  // 假设 attributes 是一个对象
  kieLinking: any[];  // 假设 kie_linking 是一个数组
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
export interface ICurrentWeightRequestData {
  currentWeightKey: string | number
}
export interface ISwitchParamRequestData {
  switchParamName: string | number
  switchParamValue: any
}
export interface ICurrentParamRequestData {
  currentParamName: string | number
}
export interface ISwitchHyperRequestData {
  switchHyperName: string|number
  switchHyperValue: any
}
export interface ICurrentHyperRequestData {
  currentHyperName: string | number
}
export interface IpredictModelRequestData {
  originalBase64: string
}
// 数据回显对象（current）
export type GetCurrentTaskResponseData = IApiResponseData<ITaskData>
export type GetCurrentFlowResponseData = IApiResponseData<OFlowData>  // 字典转数组
export type GetCurrentParamResponseData = IApiResponseData<OArgData>
export type GetCurrentWeightResponseData = IApiResponseData<OWeightData>
export type GetAllCurrentWeightsResponseData = IApiResponseData<OWeightData[]>
export type GetCurrentHyperResponseData = IApiResponseData<OArgData>
// 数据回显对象（switch）
export type SwitchTaskResponseData = IApiResponseData<IFlowData[]>
export type SwitchFlowResponseData = IApiResponseData<{weight: IWeightData[]; param: IArgData[];}>
// 数据回显对象（all）
export type GetAllTasksResponseData = IApiResponseData<ITaskData>
export type GetAllFlowsResponseData = IApiResponseData<IFlowData>
export type GetAllParamsResponseData = IApiResponseData<IArgData>
// 处理
export type LoadModelResponseData = IApiResponseData<IArgData[]>
export type PredictModelResponseData = IApiResponseData<IResultData>