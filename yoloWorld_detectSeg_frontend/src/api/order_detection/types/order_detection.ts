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



  // 数据回显对象（current）

  // 数据回显对象（switch）

  // 数据回显对象（all）
  export type GetOrderResponseData = IApiResponseData<{
    list: IGetOrderData[]
    total: number
  }>
  export type GetAllOrderResponseData = IApiResponseData<IOrderData>
  export type DetectOrderResponseData = IApiResponseData<IResultsResponseData>
  // 处理
  