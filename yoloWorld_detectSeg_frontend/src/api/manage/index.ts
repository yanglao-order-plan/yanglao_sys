import { request } from "@/utils/service"
import type * as Flow from "./types/flow"
import type * as Release from "./types/release"
import type * as Weight from "./types/weight"
import type * as Task from "./types/task"
import type * as TaskType from "./types/task_type"
import type * as User from "./types/user"

export function createUserDataApi(data: User.ICreateUserRequestData) {
  return request<User.createUserResponseData>({
    url: "user-manage/add",
    method: "post",
    data
  })
}
export function deleteUserDataApi(id: string) {
  return request<User.deleteUserResponseData>({
    url: `user-manage/delete/${id}`,
    method: "delete"
  })
}
export function updateUserDataApi(data: User.IUpdateUserRequestData) {
  return request<User.upDateUserResponseData>({
    url: "user-manage/update",
    method: "put",
    data
  })
}
export function getUserDataApi(params: User.IGetUserRequestData) {
  return request<User.GetUserResponseData>({
    url: "user-manage/list",
    method: "get",
    params
  })
}
export function createTaskTypeDataApi(data: TaskType.ICreateTaskTypeRequestData) {
  return request<TaskType.createTaskTypeResponseData>({
    url: "task_type-manage/add",
    method: "post",
    data
  })
}
export function deleteTaskTypeDataApi(id: number) {
  return request<TaskType.deleteTaskTypeResponseData>({
    url: `task_type-manage/delete/${id}`,
    method: "delete"
  })
}
export function updateTaskTypeDataApi(data: TaskType.IUpdateTaskTypeRequestData) {
  return request<TaskType.upDateTaskTypeResponseData>({
    url: "task_type-manage/update",
    method: "put",
    data
  })
}

export function getTaskTypeDataApi(params: TaskType.IGetTaskTypeRequestData) {
  return request<TaskType.GetTaskTypeResponseData>({
    url: "task_type-manage/list",
    method: "get",
    params
  })
}

export function createTaskDataApi(data: Task.ICreateTaskRequestData) {
  return request<Task.createTaskResponseData>({
    url: "task-manage/add",
    method: "post",
    data
  })
}
export function deleteTaskDataApi(id: number) {
  return request<Task.deleteTaskResponseData>({
    url: `task-manage/delete/${id}`,
    method: "delete"
  })
}
export function updateTaskDataApi(data: Task.IUpdateTaskRequestData) {
  return request<Task.upDateTaskResponseData>({
    url: "task-manage/update",
    method: "put",
    data
  })
}
export function getTaskDataApi(params: Task.IGetTaskRequestData) {
  return request<Task.GetTaskResponseData>({
    url: "task-manage/list",
    method: "get",
    params
  })
}

export function createFlowDataApi(data: Flow.ICreateFlowRequestData) {
  return request<Flow.createFlowResponseData>({
    url: "flow-manage/add",
    method: "post",
    data
  })
}
export function deleteFlowDataApi(id: number) {
  return request<Flow.deleteFlowResponseData>({
    url: `flow-manage/delete/${id}`,
    method: "delete"
  })
}
export function updateFlowDataApi(data: Flow.IUpdateFlowRequestData) {
  return request<Flow.upDateFlowResponseData>({
    url: "flow-manage/update",
    method: "put",
    data
  })
}
export function getFlowDataApi(params: Flow.IGetFlowRequestData) {
  return request<Flow.GetFlowResponseData>({
    url: "flow-manage/list",
    method: "get",
    params
  })
}


export function createReleaseDataApi(data: Release.ICreateReleaseRequestData) {
  return request<Release.createReleaseResponseData>({
    url: "release-manage/add",
    method: "post",
    data
  })
}
export function deleteReleaseDataApi(id: number) {
  return request<Release.deleteReleaseResponseData>({
    url: `release-manage/delete/${id}`,
    method: "delete"
  })
}
export function updateReleaseDataApi(data: Release.IUpdateReleaseRequestData) {
  return request<Release.upDateReleaseResponseData>({
    url: "release-manage/update",
    method: "put",
    data
  })
}
export function getReleaseDataApi(params: Release.IGetReleaseRequestData) {
  return request<Release.GetReleaseResponseData>({
    url: "release-manage/list",
    method: "get",
    params
  })
}
export function getAllReleaseIdApi() {
  return request<IApiResponseData<number[]>>({
    url: "release-manage/all",
    method: "get",
  })
}
export function createWeightDataApi(data: Weight.ICreateWeightRequestData) {
  return request<Weight.createWeightResponseData>({
    url: "weight-manage/add",
    method: "post",
    data
  })
}
export function deleteWeightDataApi(id: number) {
  return request<Weight.deleteWeightResponseData>({
    url: `weight-manage/delete/${id}`,
    method: "delete"
  })
}
export function updateWeightDataApi(data: Weight.IUpdateWeightTypeRequestData) {
  return request<Weight.upDateWeightResponseData>({
    url: "weight-manage/update",
    method: "put",
    data
  })
}
export function getWeightDataApi(params: Weight.IGetWeightRequestData) {
  return request<Weight.GetWeightResponseData>({
    url: "weight-manage/list",
    method: "get",
    params
  })
}

export function createModelDataApi(data: Release.ICreateModelRequestData) {
  return request<Release.createModelResponseData>({
    url: "release-manage/model_add",
    method: "post",
    data
  })
}
export function deleteModelDataApi(id: number) {
  return request<Release.deleteModelResponseData>({
    url: `release-manage/model_delete/${id}`,
    method: "delete"
  })
}
export function updateModelDataApi(data: Release.IUpdateModelRequestData) {
  return request<Release.upDateModelResponseData>({
    url: "release-manage/model_update",
    method: "put",
    data
  })
}
export function getModelDataApi(data: Release.IGetModelRequestData) {
  return request<Release.GetModelResponseData>({
    url: "release-manage/model_list",
    method: "post",
    data
  })
}

export function createArgumentDataApi(data: Release.ICreateArgumentRequestData) {
  return request<Release.createArgumentResponseData>({
    url: "release-manage/argument_add",
    method: "post",
    data
  })
}
export function deleteArgumentDataApi(id: number) {
  return request<Release.deleteArgumentResponseData>({
    url: `release-manage/argument_delete/${id}`,
    method: "delete"
  })
}
export function deleteArgumentBlurApi(data: Release.IGetArgumentRequestData) {
  return request<null>({
    url: `release-manage/argument_delete_blur`,
    method: "POST",
    data
  })
}

export function updateArgumentDataApi(data: Release.IUpdateArgumentRequestData) {
  return request<Release.upDateArgumentResponseData>({
    url: "release-manage/argument_update",
    method: "put",
    data
  })
}
export function getArugmentDataApi(data: Release.IGetArgumentRequestData) {
  return request<Release.GetArgumentResponseData>({
    url: "release-manage/argument_list",
    method: "post",
    data
  })
}