<template>
  <div class="glass-card" style="padding: 0; height: 100%;">
    <div style="padding: 16px 20px; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between;">
      <h3 style="font-size: 15px; font-weight: 600; color: var(--text-bright);">🎯 实时检测列表</h3>
      <span style="font-size: 12px; color: var(--text-muted);">{{ detections.length }} 个目标</span>
    </div>

    <div class="detection-panel">
      <div v-if="detections.length === 0" class="empty-state" style="padding: 40px 20px;">
        <div class="empty-icon">🔎</div>
        <div class="empty-text">暂无检测到的物品</div>
      </div>

      <div
        v-for="(det, index) in detections"
        :key="det.track_id || index"
        class="detection-item"
      >
        <div
          class="detection-dot"
          :style="{ backgroundColor: getColor(det.class_id) }"
        ></div>
        <div class="detection-name">
          <span v-if="det.track_id" style="color: var(--text-muted); font-size: 11px;">[#{{ det.track_id }}] </span>
          {{ det.class_name_zh || det.class_name }}
        </div>
        <div class="detection-conf">{{ (det.confidence * 100).toFixed(0) }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  detections: { type: Array, default: () => [] }
})

const colors = [
  '#00ff7f', '#ffbf00', '#00bfff', '#ff69b4', '#7fff00',
  '#ffd700', '#00ffff', '#ff4500', '#8a2be2', '#32cd32',
  '#ff1493', '#00ced1', '#ffa500', '#1e90ff', '#9acd32',
  '#ff6347', '#008080', '#ba55d3', '#f4a460', '#48d1cc'
]

function getColor(classId) {
  return colors[classId % colors.length]
}
</script>
