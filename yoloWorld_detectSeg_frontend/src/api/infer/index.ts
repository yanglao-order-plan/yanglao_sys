import { request } from "@/utils/service"
import type * as Infer from "./types/infer"

/** 获取当前 */
export function getCurrentTaskApi() {
  return request<Infer.GetCurrentTaskResponseData>({
    url: "infer/task/current",
    method: "get"
  })
}
export function getCurrentFlowApi() {
  return request<Infer.GetCurrentFlowResponseData>({
    url: "infer/flow/current",
    method: "get"
  })
}
export function getCurrentWeightApi(data: Infer.ICurrentWeightRequestData) {
  return request<Infer.GetCurrentWeightResponseData>({
    url: "infer/weight/current",
    method: "post",
    data
  })
}
export function getAllCurrentWeightsApi() {
  return request<Infer.GetAllCurrentWeightsResponseData>({
    url: "infer/weight/all",
    method: "get",
  })
}
export function getCurrentParamApi(data: Infer.ICurrentParamRequestData) {
  return request<Infer.GetCurrentParamResponseData>({
    url: "infer/param/current",
    method: "post",
    data
  })
}
export function getCurrentHyperApi(data: Infer.ICurrentHyperRequestData) {
  return request<Infer.GetCurrentHyperResponseData>({
    url: "infer/hyper/current",
    method: "post",
    data
  })
}
/** 获取所有可调用 */
export function getAllTasksApi() {
  return request<Infer.GetAllTasksResponseData>({
    url: "infer/task/all",
    method: "get"
  })
}
/** 切换-返回current */
export function switchTaskApi(data: Infer.ISwitchTaskRequestData) {
  return request<Infer.SwitchTaskResponseData>({
    url: "infer/task/switch",
    method: "post",
    data
  })
}
export function switchFlowApi(data: Infer.ISwitchFlowRequestData) {
  return request<Infer.SwitchFlowResponseData>({
    url: "infer/flow/switch",
    method: "post",
    data
  })
}
export function switchWeightApi(data: Infer.ISwitchWeightRequestData) {
  return request<null>({
    url: "infer/weight/switch",
    method: "post",
    data
  })
}
export function switchParamApi(data: Infer.ISwitchParamRequestData) {
  return request<null>({
    url: "infer/param/switch",
    method: "post",
    data
  })
}
export function switchHyperApi(data: Infer.ISwitchHyperRequestData) {
  return request<null>({
    url: "infer/hyper/switch",
    method: "post",
    data
  })
}
export function loadModelApi() {
  return request<Infer.LoadModelResponseData>({
    url: "infer/model/load",
    method: "get"
  })
}
export function predictModelApi() {
  return request<Infer.PredictModelResponseData>({
    url: "infer/model/predict",
    method: "get",
  })
}