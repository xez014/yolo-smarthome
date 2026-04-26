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
      <div class="placeholder-icon">🌐</div>
      <p style="font-size: 16px; color: var(--text-secondary);">网络流未启动</p>
      <p style="font-size: 13px;">请输入网络流地址后点击下方启动检测</p>
    </div>
  </div>
</template>

<script setup>
import { VIDEO_STREAM_URL } from '../api/video.js'

const props = defineProps({
  isRunning: { type: Boolean, default: false },
  fps: { type: Number, default: 0 },
  objectCount: { type: Number, default: 0 },
})

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
