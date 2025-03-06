import internal from "stream"
import { StringLiteral } from "typescript";

// 数据前端对象
  export interface IOrderData {
    orderId: number;
    serviceId: number;
    orderContent: string; 
  }
  export interface IGetOrderData{
    orderId:number
    no:string
    serviceId:number
    projectType:string
    flag:number
  }
  export interface IFlowData {
    flowName: string
    releaseName: string
    releaseShowName: string
  }
  export interface IInferResults{
    originImage:string,
    resultBase64: string
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
  export interface IResultsResponseData{
      startImg:IInferResults[];
      imgUrl:IInferResults[];
      endImg:IInferResults[];
  }
  // 数据请求对象
  export interface IGetOrderRequestData {
    currentPage: number
    size: number
    orderId?: number
    serviceId?: number
  }
  export interface IGetOrderRequestData {
    currentPage: number
    size: number
    orderId?: number
    serviceId?: number
  }
  export interface ISwitchModelRequestData {
    order_id: number,
    service_id: number
  }

  export interface IModelsponseData{
    flow_name : string,
  }
  
  export interface IFlowsponseData{
    flow_name : string,
  }
  export interface IWeightData {
    weightKey: string
    weightName: string
    weightEnable: string
  }
  export interface IArgData {
    argName: string
    argType: string
    argDefault: any
    argConfig: Record<string, any>  //自动解析
  }
  export interface OWeightData {
    weightKey: string
    weightName: string
  }
  export interface OArgData {
    argName: string
    argValue: any
  }
  export interface ISwitchWeightRequestData {
    switchParamRelease: string
    switchWeightKey: string | number
    switchWeightName: string
  }
  export interface ICurrentWeightRequestData {
    switchParamRelease: string
    currentWeightKey: string | number
  }
  export interface ISwitchParamRequestData {
    switchParamRelease: string
    switchParamName: string | number
    switchParamValue: any
  }
  export interface ICurrentParamRequestData {
    switchParamRelease: string
    currentParamName: string | number
  }
  export interface IDetectData {
    field: string;
    msg: string;
    type: string;
    avatars: string[];
  }
  export interface IDOrigin{
    stage: string;
    url: string[]
  }
  // 数据回显对象（all）
  export type GetOrderResponseData = IApiResponseData<{
    list: IGetOrderData[]
    total: number
  }>
  export type GetDetectResponseData =IApiResponseData<{
    origin:IDOrigin[]
    result:IDetectData[]
    }>
  export type GetAllOrderResponseData = IApiResponseData<IOrderData>
  export type DetectOrderResponseData = IApiResponseData<IResultsResponseData>
  export type SwitchModelResponseData = IApiResponseData<IFlowData[]>
  export type SwitchFlowResponseData = IApiResponseData<{weight: IWeightData[]; param: IArgData[];}>
  export type GetCurrentParamResponseData = IApiResponseData<OArgData>
  export type GetCurrentWeightResponseData = IApiResponseData<OWeightData>

  