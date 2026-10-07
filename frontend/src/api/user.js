import request from '@/utils/request'
//获取用户信息
export function getUserInfoAPI() {
  return request({
    url: '/api/user/me',
    method: 'get'
  })
}

//修改个人信息
export function updateUserInfoAPI(data) {
  return request({
    url: '/api/user/me',
    method: 'put',
    data
  })
}

//修改密码
export function updatePasswordAPI(data) {
  return request({
    url: '/api/user/password',
    method: 'put',
    data
  })
}
