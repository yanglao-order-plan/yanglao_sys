import { request } from "@/utils/service"
import type * as Infer from "./types/infer_local"

/** 获取当前 */
export function getCurrentFlowApi() {
  return request<Infer.GetCurrentFlowResponseData>({
    url: "infer_local/flow/current",
    method: "get"
  })
}

export function getCurrentHyperApi() {
  return request<Infer.GetCurrentHyperResponseData>({
    url: "infer_local/hyper/current",
    method: "get"
  })
}
/** 获取所有可调用 */
/** 切换-返回current */
export function switchFlowApi(data: Infer.ISwitchFlowRequestData) {
  return request<null>({
    url: "infer_local/flow/switch",
    method: "post",
    data
  })
}
export function switchHyperApi(data: Infer.ISwitchHyperRequestData) {
  return request<null>({
    url: "infer_local/hyper/switch",
    method: "post",
    data
  })
}
export function getAllFlowsApi() {
  return request<Infer.GetAllFlowsResponseData>({
    url: "infer_local/flow/all",
    method: "get"
  })
}
export function loadModelApi() {
  return request<Infer.LoadModelResponseData>({
    url: "infer_local/model/load",
    method: "get"
  })
}
export function predictModelApi(data: Infer.IpredictModelRequestData) {
  return request<Infer.PredictModelResponseData>({
    url: "infer_local/model/predict",
    method: "post",
    data
  })
}