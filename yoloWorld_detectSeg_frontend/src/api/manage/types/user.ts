export interface ICreateUserRequestData {
  username: string
  password: string
  email: string
  roles?: string
}

export interface IUpdateUserRequestData {
  id: string
  username: string
  email?: string
  status?: boolean
  password?: string
  roles?: string
}

export interface IGetUserRequestData {
  currentPage: number
  size: number
  username?: string
  email?: string
}

export interface IGetUserData {
  createTime: string
  email: string
  id: string
  roles: string
  status: boolean
  username: string
}

export type GetUserResponseData = IApiResponseData<{
  list: IGetUserData[]
  total: number
}>

export type createUserResponseData = IApiResponseData<string>
export type deleteUserResponseData = IApiResponseData<string>
export type upDateUserResponseData = IApiResponseData<string>
