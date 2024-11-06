import { request } from "@/utils/service"
import type * as Table from "./types/config-manage"

/** 增 */
export function createTaskTypeDataApi(data: Table.ICreateTableRequestData) {
  return request<Table.createTableResponseData>({
    url: "config-manage/add",
    // url: "table",
    method: "post",
    data
  })
}

/** 删 */
export function deleteTaskTypeDataApi(id: string) {
  return request<Table.deleteTableResponseData>({
    url: `config-manage/delete/${id}`,
    // url: `table/${id}`,
    method: "delete"
  })
}

/** 改 */
export function updateTaskTypeDataApi(data: Table.IUpdateTableRequestData) {
  return request<Table.upDateTableResponseData>({
    url: "config-manage/update",
    // url: "table",
    method: "put",
    data
  })
}

/** 查 */
export function getTableDataApi(params: Table.IGetTableRequestData) {
  return request<Table.GetTableResponseData>({
    url: "configmanage/list",
    // url: "table",
    method: "get",
    params
  })
}
