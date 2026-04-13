import axios from 'axios'

const API_BASE = ''

/**
 * 获取首页统计概览
 */
export function getOverview() {
  return axios.get(`${API_BASE}/api/stats/overview`)
}

/**
 * 获取物品频次排行
 * @param {number} days - 统计最近 N 天
 * @param {number} limit - 返回前 N 类
 */
export function getFrequency(days = 7, limit = 20) {
  return axios.get(`${API_BASE}/api/stats/frequency`, {
    params: { days, limit }
  })
}

/**
 * 获取按小时时间轴统计
 * @param {string} targetDate - 目标日期 YYYY-MM-DD
 */
export function getTimeline(targetDate) {
  return axios.get(`${API_BASE}/api/stats/timeline`, {
    params: { target_date: targetDate }
  })
}

/**
 * 获取实时统计（当前帧）
 */
export function getRealtime() {
  return axios.get(`${API_BASE}/api/stats/realtime`)
}
