import axios from 'axios'

// 通过空字符串让通过 Nginx 的前端可以走相对路径，从而实现同域 API 转发免跨域
const API_BASE = ''

/**
 * 启动摄像头推理
 * @param {string|number|null} source - 视频源（摄像头索引或文件路径）
 */
export function startDetection(source = null) {
  const params = source !== null ? { source } : {}
  return axios.post(`${API_BASE}/api/video/start`, null, { params })
}

/**
 * 停止推理
 */
export function stopDetection() {
  return axios.post(`${API_BASE}/api/video/stop`)
}

/**
 * 获取推理状态
 */
export function getStatus() {
  return axios.get(`${API_BASE}/api/video/status`)
}

/**
 * MJPEG 视频流地址
 */
export const VIDEO_STREAM_URL = `${API_BASE}/api/video/stream`

/**
 * WebSocket 实时数据地址
 * 在 Nginx 环境下，自动取当前 host
 */
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
export const WS_URL = `${protocol}//${window.location.host}/api/video/ws`

/**
 * 快照基础 URL
 * 空字符串表示从同域下加载 `/snapshots/...`
 */
export const SNAPSHOT_BASE_URL = ''
