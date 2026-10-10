import request from '@/utils/request'

//分页查询实验室
export function getLabPageListApi(params) {
  return request({
    url: '/api/lab/list',
    method: 'get',
    params
  })
}

//创建实验室
export function createLabApi(data) {
  return request({
    url: '/api/lab',
    method: 'post',
    data
  })
}

//修改实验室
export function updateLabApi(labId, data) {
  return request({
    url: `/api/lab/${labId}`,
    method: 'put',
    data
  })
}

//删除实验室
export function deleteLabApi(labId) {
  return request({
    url: `/api/lab/${labId}`,
    method: 'delete'
  })
}
