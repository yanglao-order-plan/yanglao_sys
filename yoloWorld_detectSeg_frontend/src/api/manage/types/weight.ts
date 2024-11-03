export interface ICreateWeightRequestData {
  name: string
  localPath: string
  onlineUrl: string
  enable: number
}
export interface IUpdateWeightTypeRequestData {
  id: number
  name: string
  localPath: string
  onlineUrl: string
  enable: number
}
export interface IGetWeightRequestData {
  currentPage: number
  size: number
  name?: string
  enable?: number
}
export interface IGetWeightRequestData {
  currentPage: number
  size: number
  weight?: string
  enbale?: number
}

export interface IGetWeightData {
  id: number
  name: string
  localPath: string
  onlineUrl: string
  enable: number
}

export type GetWeightResponseData = IApiResponseData<{
  list: IGetWeightData[]
  total: number
}>

export type createWeightResponseData = IApiResponseData<string>
export type deleteWeightResponseData = IApiResponseData<string>
export type upDateWeightResponseData = IApiResponseData<string>