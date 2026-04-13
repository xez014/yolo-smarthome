import axios from 'axios'

const API_BASE = 'http://localhost:8000'

/**
 * 获取 20 类物品列表
 */
export function getClasses() {
  return axios.get(`${API_BASE}/api/detection/classes`)
}

/**
 * 按类别搜索物品最后出现位置
 * @param {string} objectClass - 物品类别英文名
 */
export function searchObject(objectClass) {
  return axios.get(`${API_BASE}/api/detection/search`, {
    params: { object_class: objectClass }
  })
}

/**
 * 获取所有物品最后出现位置
 */
export function getAllLastSeen() {
  return axios.get(`${API_BASE}/api/detection/last-seen`)
}

/**
 * 获取历史检测记录（分页）
 * @param {Object} params - 查询参数
 */
export function getHistory(params) {
  return axios.get(`${API_BASE}/api/detection/history`, { params })
}
