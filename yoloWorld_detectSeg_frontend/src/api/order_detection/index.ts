import { request } from "@/utils/service"
import type * as Detection from "./types/order_detection.ts"

/** 获取当前 */

  /** 获取所有可调用 */
  export function getAllOrdersApi() {
    return request<Detection.GetAllOrderResponseData>({
      url: "work_order/list/all",
      method: "get" 
    })
  }
  /** 切换-返回current */
  // export function detectOrderApi(id : number) {
  //   return request<Detection.DetectOrderResponseData>({
  //     url: `work_order/infer/${id}`,
  //     method: "get"
  //   })
  // }
  // 旧
  // export function switchModelApi(order_id : number) {
  //   return request<Detection.SwitchModelResponseData>({
  //     url: `work_order/order/switch/${order_id}`,
  //     method: "post",
  //   })
  // }
  //新
    export function switchModelApi(order_id : number) {
    return request<{}>({
      url: `work_order/order/switch/${order_id}`,
      method: "post",
    })
  }
  export function switchFlowApi(flow_name : string) {
    return request<Detection.SwitchFlowResponseData>({
      url: `work_order/release/switch/${flow_name}`,
      method: "post",
    })
  }

  
  export function getOrderDataApi(params: Detection.IGetOrderRequestData) {
    return request<Detection.GetOrderResponseData>({
      url: "work_order/list",
      method: "get",
      params
    })
  }

  export function switchWeightApi(data: Detection.ISwitchWeightRequestData) {
    return request<null>({
      url: "work_order/order/weight/switch",
      method: "post",
      data
    })
  }

  export function getCurrentWeightApi(data: Detection.ICurrentWeightRequestData) {
    return request<Detection.GetCurrentWeightResponseData>({
      url: "work_order/order/weight/current",
      method: "post",
      data
    })
  }
  export function switchParamApi(data: Detection.ISwitchParamRequestData) {
    return request<null>({
      url: "work_order/order/param/switch",
      method: "post",
      data
    })
  }
  export function getCurrentParamApi(data: Detection.ICurrentParamRequestData) {
    return request<Detection.GetCurrentParamResponseData>({
      url: "work_order/order/param/current",
      method: "post",
      data
    })
  }
  
  export function getDetectDataApi(id : number ){
    return request<Detection.GetDetectResponseData>({
      url: `work_order/order/handler/infer`,
      method: "get"
    })
  }