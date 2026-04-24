import axios from 'axios'

const API_BASE = ''

/**
 * 获取 20 类物品列表
 */
export function getClasses() {
  return axios.get(`${API_BASE}/api/detection/classes`)
}

/**
 * 按类别或中文关键词搜索物品最后出现位置
 * @param {string|null} objectClass - 物品类别英文名（可选）
 * @param {string|null} keyword - 中英文关键词（可选）
 */
export function searchObject(objectClass, keyword) {
  const params = {}
  if (objectClass) params.object_class = objectClass
  if (keyword) params.keyword = keyword
  return axios.get(`${API_BASE}/api/detection/search`, { params })
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
