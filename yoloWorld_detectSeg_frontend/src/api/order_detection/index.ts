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
  export function detectOrderApi(id : number) {
    return request<Detection.DetectOrderResponseData>({
      url: `work_order/infer/${id}`,
      method: "get"
    })
  }

  
  export function getOrderDataApi(params: Detection.IGetOrderRequestData) {
    return request<Detection.GetOrderResponseData>({
      url: "work_order/list",
      method: "get",
      params
    })
  }