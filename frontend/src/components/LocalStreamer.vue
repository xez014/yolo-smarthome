<template>
  <div class="local-streamer">
    <!-- 推理画面显示区 -->
    <div class="stream-display" ref="displayRef">
      <!-- 运行中：显示推理结果图 -->
      <div v-if="isStreaming" class="video-wrapper" style="position:relative;">
        <img :src="resultImage" class="result-img" alt="推理结果" />
        <div class="video-overlay">
          <span class="video-badge live">● LIVE</span>
          <span class="video-badge" style="color: var(--success);">{{ fps }} FPS</span>
          <span class="video-badge" style="color: var(--primary);">🎯 {{ objectCount }} 个物品</span>
          <span class="video-badge" style="color: #f59e0b;">☁️ 云端推理</span>
        </div>
      </div>

      <!-- 摄像头模式：用 video 元素预览 -->
      <video
        v-show="mode === 'local-webcam' && !isStreaming && hasWebcamPreview"
        ref="videoRef"
        autoplay
        muted
        playsinline
        class="preview-video"
      />

      <!-- 本地视频文件模式：用 video 元素预览 -->
      <video
        v-show="mode === 'local-video' && !isStreaming && localVideoUrl"
        ref="fileVideoRef"
        :src="localVideoUrl"
        autoplay
        muted
        loop
        playsinline
        class="preview-video"
      />

      <!-- 未启动占位 -->
      <div
        v-if="!isStreaming && ((mode === 'local-webcam' && !hasWebcamPreview) || (mode === 'local-video' && !localVideoUrl))"
        class="video-placeholder"
      >
        <div class="placeholder-icon">{{ mode === 'local-video' ? '📂' : '📷' }}</div>
        <p style="font-size: 16px; color: var(--text-secondary);">
          {{ mode === 'local-video' ? '请选择本地视频文件' : '摄像头未启动' }}
        </p>
        <p v-if="mode === 'local-webcam'" style="font-size: 13px;">
          点击下方按钮开启本地摄像头推流
        </p>
      </div>
    </div>

    <!-- 文件选择（仅本地视频模式） -->
    <div v-if="mode === 'local-video'" class="file-picker-row" style="margin-top: 10px;">
      <el-button @click="pickFile" :icon="FolderOpened" size="small">选择视频文件</el-button>
      <span v-if="fileName" style="font-size:12px; color: var(--text-secondary); margin-left: 8px;">
        📄 {{ fileName }}
      </span>
      <span v-else style="font-size:12px; color: var(--text-muted); margin-left: 8px;">
        尚未选择文件
      </span>
      <input ref="fileInputRef" type="file" accept="video/*" @change="onFileSelected" style="display:none;" />
    </div>

    <!-- 状态日志条 -->
    <div v-if="statusMsg" class="status-log" :class="statusType">{{ statusMsg }}</div>

    <!-- Canvas（不可见，用于截帧） -->
    <canvas ref="canvasRef" style="display:none;" />
  </div>
</template>

<script setup>
import { nextTick, onActivated, onUnmounted, ref, watch } from 'vue'
import { FolderOpened } from '@element-plus/icons-vue'
import { WS_PUSH_URL } from '../api/video.js'

const props = defineProps({
  mode: { type: String, required: true }, // 'local-webcam' | 'local-video'
  active: { type: Boolean, default: false },
})

const emit = defineEmits(['detections', 'fps-update', 'started', 'stopped'])

// DOM refs
const videoRef = ref(null)
const fileVideoRef = ref(null)
const canvasRef = ref(null)
const fileInputRef = ref(null)
const displayRef = ref(null)

// 状态
const isStreaming = ref(false)
const resultImage = ref('')
const fps = ref(0)
const objectCount = ref(0)
const statusMsg = ref('')
const statusType = ref('info')
const localVideoUrl = ref('')
const fileName = ref('')
const hasWebcamPreview = ref(false)

let ws = null
let captureTimer = null
let stream = null
let currentVideoGetter = null
let frameCount = 0
let fpsTimer = Date.now()

// ── 对外控制接口 ──────────────────────────────────────────
async function start() {
  if (isStreaming.value) return

  if (props.mode === 'local-webcam') {
    await startWebcam()
  } else {
    startFileStream()
  }
}

function stop() {
  stopStreaming()
}

defineExpose({ start, stop })

// ── 摄像头模式 ────────────────────────────────────────────
async function startWebcam() {
  try {
    statusMsg.value = '正在请求摄像头权限...'
    statusType.value = 'info'
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    videoRef.value.srcObject = stream
    hasWebcamPreview.value = true
    await videoRef.value.play()
    connectPushWS(() => videoRef.value)
  } catch (e) {
    statusMsg.value = `❌ 无法打开摄像头: ${e.message}（请确保使用 HTTPS 访问，并允许摄像头权限）`
    statusType.value = 'error'
  }
}

// ── 本地视频文件模式 ──────────────────────────────────────
function pickFile() {
  fileInputRef.value?.click()
}

function onFileSelected(event) {
  const file = event.target.files[0]
  if (!file) return
  fileName.value = file.name
  localVideoUrl.value = URL.createObjectURL(file)
  statusMsg.value = `已选择: ${file.name}，点击"启动检测"开始推理`
  statusType.value = 'info'
}

function startFileStream() {
  if (!localVideoUrl.value) {
    statusMsg.value = '❌ 请先选择本地视频文件'
    statusType.value = 'error'
    return
  }
  const video = fileVideoRef.value
  video.play()
  connectPushWS(() => video)
}

// ── 核心：WebSocket 推流 ───────────────────────────────────
function connectPushWS(getVideoEl) {
  currentVideoGetter = getVideoEl

  if (ws) {
    ws.onclose = null
    ws.onerror = null
    ws.close()
    ws = null
  }

  // WebSocket 鉴权：通过 query 参数附加 JWT Token
  const token = localStorage.getItem('token') || ''
  const params = new URLSearchParams({
    token,
    source_type: props.mode,
  })
  const wsUrl = `${WS_PUSH_URL}?${params.toString()}`
  ws = new WebSocket(wsUrl)
  ws.binaryType = 'arraybuffer'

  ws.onopen = () => {
    isStreaming.value = true
    statusMsg.value = '✅ 已连接云端推理引擎，开始推流...'
    statusType.value = 'success'
    emit('started')
    startCapture(getVideoEl)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.error) {
        statusMsg.value = `⚠️ ${data.error}`
        return
      }
      resultImage.value = data.image
      objectCount.value = data.current_objects || 0
      emit('detections', data.detections || [])

      // 计算 FPS
      frameCount++
      const now = Date.now()
      const elapsed = (now - fpsTimer) / 1000
      if (elapsed >= 1) {
        fps.value = Math.round(frameCount / elapsed)
        emit('fps-update', fps.value)
        frameCount = 0
        fpsTimer = now
      }
    } catch (e) {}
  }

  ws.onclose = () => {
    if (isStreaming.value) stopStreaming()
  }

  ws.onerror = () => {
    statusMsg.value = '❌ 推流连接断开，请稍后重试'
    statusType.value = 'error'
    stopStreaming({ closeSocket: false })
  }
}

function startCapture(getVideoEl) {
  currentVideoGetter = getVideoEl
  if (captureTimer) {
    clearInterval(captureTimer)
    captureTimer = null
  }

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  captureTimer = setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    const video = getVideoEl()
    if (!video || video.readyState < 2) return

    canvas.width = 640
    canvas.height = 480
    ctx.drawImage(video, 0, 0, 640, 480)

    canvas.toBlob((blob) => {
      if (!blob || !ws || ws.readyState !== WebSocket.OPEN) return
      blob.arrayBuffer().then(buf => {
        ws.send(buf)
      })
    }, 'image/jpeg', 0.75)
  }, 200) // 5fps → 每200ms推一帧，控制服务器负载
}

function stopStreaming({ closeSocket = true } = {}) {
  if (captureTimer) { clearInterval(captureTimer); captureTimer = null }
  if (ws && closeSocket) {
    ws.onclose = null
    ws.onerror = null
    ws.close()
  }
  ws = null
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  if (videoRef.value) {
    videoRef.value.pause()
    videoRef.value.srcObject = null
  }
  if (fileVideoRef.value && props.mode === 'local-video') {
    fileVideoRef.value.pause()
  }
  isStreaming.value = false
  resultImage.value = ''
  fps.value = 0
  objectCount.value = 0
  hasWebcamPreview.value = false
  currentVideoGetter = null
  statusMsg.value = '已停止推流'
  statusType.value = 'info'
  emit('stopped')
  emit('detections', [])
}

async function resumeMediaSource() {
  const video = props.mode === 'local-webcam' ? videoRef.value : fileVideoRef.value
  if (!video) return

  if (props.mode === 'local-webcam' && stream && video.srcObject !== stream) {
    video.srcObject = stream
    hasWebcamPreview.value = true
  }

  try {
    await video.play()
  } catch (e) {
    statusMsg.value = `⚠️ 浏览器暂停了媒体播放，请重新启动推流: ${e.message}`
    statusType.value = 'error'
  }
}

onActivated(async () => {
  if (!isStreaming.value) return

  await nextTick()
  await resumeMediaSource()

  const getter = currentVideoGetter || (() => (
    props.mode === 'local-webcam' ? videoRef.value : fileVideoRef.value
  ))

  if (!captureTimer) {
    startCapture(getter)
  }

  if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
    connectPushWS(getter)
  }
})

// 监听 active 状态自动停止
watch(() => props.active, (val) => {
  if (!val && isStreaming.value) stopStreaming()
})

onUnmounted(() => stopStreaming())
</script>

<style scoped>
.local-streamer {
  width: 100%;
}

.stream-display {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-img {
  width: 100%;
  display: block;
  min-height: 400px;
  object-fit: contain;
}

.preview-video {
  width: 100%;
  min-height: 400px;
  object-fit: contain;
  display: block;
}

.video-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.video-badge {
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #ff4444;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.file-picker-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.status-log {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
}

.info    { background: rgba(0,212,255,0.08); color: #7dd3fc; border: 1px solid rgba(0,212,255,0.15); }
.success { background: rgba(34,197,94,0.08); color: #86efac; border: 1px solid rgba(34,197,94,0.15); }
.error   { background: rgba(239,68,68,0.08); color: #fca5a5; border: 1px solid rgba(239,68,68,0.15); }
</style>
