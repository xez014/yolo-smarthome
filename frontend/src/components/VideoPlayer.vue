<template>
  <div class="video-container">
    <!-- 视频流画面 -->
    <div v-if="isRunning" class="video-wrapper">
      <img :src="streamUrl" alt="实时视频流" @error="handleStreamError" />
      <div class="video-overlay">
        <span class="video-badge live">● LIVE</span>
        <span class="video-badge" style="color: var(--success);">
          {{ fps }} FPS
        </span>
        <span class="video-badge" style="color: var(--primary);">
          🎯 {{ objectCount }} 个物品
        </span>
      </div>
    </div>

    <!-- 未启动状态 -->
    <div v-else class="video-placeholder">
      <div class="placeholder-icon">📷</div>
      <p style="font-size: 16px; color: var(--text-secondary);">摄像头未启动</p>
      <p style="font-size: 13px;">点击下方按钮开启实时检测</p>
      <el-button
        type="primary"
        size="large"
        :icon="VideoCamera"
        @click="$emit('start')"
        style="margin-top: 8px;"
      >
        启动摄像头
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { VideoCamera } from '@element-plus/icons-vue'
import { VIDEO_STREAM_URL } from '../api/video.js'

const props = defineProps({
  isRunning: { type: Boolean, default: false },
  fps: { type: Number, default: 0 },
  objectCount: { type: Number, default: 0 },
})

defineEmits(['start'])

const streamUrl = VIDEO_STREAM_URL

function handleStreamError() {
  console.warn('视频流加载失败')
}
</script>

<style scoped>
.video-wrapper {
  position: relative;
  min-height: 400px;
  background: #000;
}

.video-wrapper img {
  width: 100%;
  display: block;
  min-height: 400px;
  object-fit: contain;
}
</style>
