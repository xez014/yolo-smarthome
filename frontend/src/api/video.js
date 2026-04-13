import axios from 'axios'

const API_BASE = 'http://localhost:8000'

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
 */
export const WS_URL = `ws://localhost:8000/api/video/ws`

/**
 * 快照基础 URL
 */
export const SNAPSHOT_BASE_URL = API_BASE
