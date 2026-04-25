<template>
  <div class="dashboard-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">📡 实时监控大屏</h1>
      <p class="page-subtitle">基于 YOLOv11 的家居物品实时检测与追踪</p>
    </div>

    <!-- 顶部统计条 -->
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,168,204,0.1));">
          ⚡
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ realtimeData.fps || 0 }}</div>
          <div class="stat-label">实时 FPS</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(91,33,182,0.1));">
          🎯
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ realtimeData.current_objects || 0 }}</div>
          <div class="stat-label">画面物品数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(22,163,74,0.1));">
          📦
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ overview.today_total || 0 }}</div>
          <div class="stat-label">今日累计检测</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(217,119,6,0.1));">
          🏷️
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ overview.active_classes || 0 }}</div>
          <div class="stat-label">活跃物品种类</div>
        </div>
      </div>
    </div>

    <!-- 主内容区：视频 + 检测列表 -->
    <div class="main-area">
      <!-- 左：视频播放器 -->
      <div class="video-section">
        <VideoPlayer
          v-if="!isLocalMode"
          :is-running="engineStatus.is_running"
          :fps="realtimeData.fps"
          :object-count="realtimeData.current_objects"
          @start="handleStart"
        />
        <LocalStreamer
          v-if="isLocalMode"
          ref="localStreamerRef"
          :mode="sourceType"
          :active="isLocalStreaming"
          @detections="onPushDetections"
          @fps-update="onPushFps"
          @started="isLocalStreaming = true"
          @stopped="isLocalStreaming = false"
        />
        <!-- 控制条 -->
        <div class="control-bar glass-card" style="margin-top: 12px; padding: 16px 20px;">
          <!-- 视频源选择 -->
          <div class="source-selector">
            <div class="source-tabs">
              <div
                v-for="opt in sourceOptions"
                :key="opt.value"
                class="source-tab"
                :class="{ active: sourceType === opt.value }"
                @click="sourceType = opt.value"
              >
                <span class="source-tab-icon">{{ opt.icon }}</span>
                <span class="source-tab-label">{{ opt.label }}</span>
              </div>
            </div>

            <!-- RTSP 地址输入 -->
            <div v-if="sourceType === 'rtsp'" class="source-input-row">
              <el-input
                v-model="rtspUrl"
                placeholder="输入 RTSP/RTMP/HTTP 流地址，如 rtsp://192.168.1.100:554/stream"
                clearable
                style="flex: 1;"
              >
                <template #prepend>🌐</template>
              </el-input>
            </div>

            <!-- 本地摄像头提示 -->
            <div v-if="sourceType === 'local-webcam'" class="source-input-row">
              <span style="font-size:13px; color: var(--text-secondary);">
                📷 将使用您当前浏览器的摄像头推流至服务端推理（需要 HTTPS）
              </span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="control-actions">
            <div style="display: flex; align-items: center; gap: 12px;">
              <el-button
                v-if="!engineStatus.is_running && !isLocalStreaming"
                type="primary"
                :icon="VideoCamera"
                @click="handleStart"
                size="large"
              >
                启动检测
              </el-button>
              <el-button
                v-else-if="isLocalStreaming"
                type="danger"
                :icon="VideoPause"
                @click="handleLocalStop"
                size="large"
              >
                停止推流
              </el-button>
              <el-button
                v-else
                type="danger"
                :icon="VideoPause"
                @click="handleStop"
                size="large"
              >
                停止检测
              </el-button>
              <el-tag :type="engineStatus.is_running ? 'success' : 'info'" effect="dark" size="large">
                {{ statusLabel }}
              </el-tag>
            </div>
            <div style="font-size: 12px; color: var(--text-muted);">
              已处理 {{ engineStatus.frame_count || 0 }} 帧
            </div>
          </div>
        </div>
      </div>

      <!-- 右：实时检测列表 -->
      <div class="detection-section">
        <DetectionPanel :detections="realtimeData.detections || []" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { VideoCamera, VideoPause } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import VideoPlayer from '../components/VideoPlayer.vue'
import LocalStreamer from '../components/LocalStreamer.vue'
import DetectionPanel from '../components/DetectionPanel.vue'
import { startDetection, stopDetection, getStatus, WS_URL } from '../api/video.js'
import { getOverview } from '../api/stats.js'

const engineStatus = ref({ is_running: false, frame_count: 0, source_type: 'none' })
const overview = ref({ today_total: 0, active_classes: 0 })
const realtimeData = ref({
  fps: 0, current_objects: 0, detections: [], frame_count: 0
})

// 视频源选择
const sourceType = ref('rtsp')
const rtspUrl = ref('')

// 本地推流状态
const localStreamerRef = ref(null)
const isLocalStreaming = ref(false)
const isLocalMode = computed(() => sourceType.value === 'local-webcam' || sourceType.value === 'local-video')

const sourceOptions = [
  { value: 'rtsp',         label: '网络流',     icon: '🌐' },
  { value: 'local-webcam', label: '本地摄像头', icon: '📷' },
  { value: 'local-video',  label: '本地视频',   icon: '📂' },
]

const statusLabel = computed(() => {
  if (isLocalStreaming.value) return '📷 本地推流中 → 服务端推理'
  if (!engineStatus.value.is_running) return '已停止'
  const labels = { rtsp: '🌐 网络流接入中' }
  return labels[engineStatus.value.source_type] || '运行中'
})

let ws = null
let statusTimer = null
let overviewTimer = null

onMounted(() => {
  fetchStatus()
  fetchOverview()
  connectWebSocket()
  statusTimer = setInterval(fetchStatus, 3000)
  overviewTimer = setInterval(fetchOverview, 10000)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (statusTimer) clearInterval(statusTimer)
  if (overviewTimer) clearInterval(overviewTimer)
})

async function fetchStatus() {
  try {
    const res = await getStatus()
    engineStatus.value = res.data
    // 同步源类型到界面
    if (res.data.is_running && res.data.source_type) {
      sourceType.value = res.data.source_type
    }
  } catch (e) {}
}

async function fetchOverview() {
  try {
    const res = await getOverview()
    overview.value = res.data
  } catch (e) {}
}

function connectWebSocket() {
  try {
    ws = new WebSocket(WS_URL)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        realtimeData.value = data
      } catch (e) {}
    }
    ws.onclose = () => {
      setTimeout(connectWebSocket, 3000)
    }
    ws.onerror = () => {
      ws.close()
    }
  } catch (e) {
    setTimeout(connectWebSocket, 3000)
  }
}

function getSourceValue() {
  if (sourceType.value === 'rtsp') {
    if (!rtspUrl.value.trim()) {
      ElMessage.warning('请输入网络流地址')
      return null
    }
    return rtspUrl.value.trim()
  }
  return null
}

async function handleStart() {
  // 本地推流模式：启动 LocalStreamer
  if (isLocalMode.value) {
    localStreamerRef.value?.start()
    return
  }

  // 服务端模式：原有逻辑
  const source = getSourceValue()
  if (source === null) return

  try {
    const res = await startDetection(source)
    if (res.data.status === 'started') {
      ElMessage.success('网络流推理已启动')
      engineStatus.value.is_running = true
      engineStatus.value.source_type = sourceType.value
    } else if (res.data.status === 'already_running') {
      ElMessage.info('推理已在运行中，请先停止再切换视频源')
    } else {
      ElMessage.error(res.data.message || '启动失败')
    }
  } catch (e) {
    ElMessage.error('启动失败，请检查后端服务是否运行')
  }
}

async function handleLocalStop() {
  localStreamerRef.value?.stop()
}

// 接收 LocalStreamer 推流检测结果，同步到实时检测面板
function onPushDetections(dets) {
  realtimeData.value.detections = dets
  realtimeData.value.current_objects = dets.length
}

function onPushFps(val) {
  realtimeData.value.fps = val
}

async function handleStop() {
  try {
    await stopDetection()
    ElMessage.success('推理已停止')
    engineStatus.value.is_running = false
    engineStatus.value.source_type = 'none'
    realtimeData.value = { fps: 0, current_objects: 0, detections: [], frame_count: 0 }
  } catch (e) {
    ElMessage.error('停止失败')
  }
}
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.main-area {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
  align-items: start;
}

.video-section {
  min-width: 0;
}

.detection-section {
  min-width: 0;
}

/* 视频源选择器 */
.source-selector {
  margin-bottom: 16px;
}

.source-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.source-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  color: var(--text-secondary);
  user-select: none;
}

.source-tab:hover {
  border-color: var(--border-glow);
  color: var(--text-primary);
}

.source-tab.active {
  border-color: var(--primary);
  background: rgba(0, 212, 255, 0.1);
  color: var(--primary);
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.15);
}

.source-tab-icon {
  font-size: 16px;
}

.source-tab-label {
  font-weight: 500;
}

.source-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.control-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

@media (max-width: 1200px) {
  .stats-bar {
    grid-template-columns: repeat(2, 1fr);
  }
  .main-area {
    grid-template-columns: 1fr;
  }
}
</style>
