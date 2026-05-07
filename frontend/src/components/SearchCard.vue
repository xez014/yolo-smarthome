<template>
  <div class="search-result-card" @click="handlePreview">
    <div class="card-image">
      <img
        v-if="hasSnapshot"
        :src="snapshotUrl"
        :alt="item.object_class"
        @error="handleImageError"
      />
      <div v-else class="snapshot-placeholder">
        <span style="font-size: 40px; opacity: 0.3;">📷</span>
        <span style="font-size: 12px; color: var(--text-muted);">暂无快照</span>
      </div>
      <div class="card-badge">
        <span>{{ item.class_name_zh || item.object_class }}</span>
      </div>
    </div>
    <div class="card-body">
      <div class="card-title">{{ item.class_name_zh || item.object_class }}</div>
      <div class="card-meta">
        <div class="meta-item">
          <span>🕐</span>
          <span>{{ formatTime(item.last_seen_at) }}</span>
        </div>
        <div class="meta-item">
          <span>📍</span>
          <span>位置 ({{ formatPos(item.last_bbox_x) }}, {{ formatPos(item.last_bbox_y) }})</span>
        </div>
        <div class="meta-item">
          <span>📊</span>
          <span>累计出现 {{ item.total_count || 0 }} 次</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { SNAPSHOT_BASE_URL } from '../api/video.js'

const props = defineProps({
  item: { type: Object, required: true }
})

const emit = defineEmits(['preview'])

const imgError = ref(false)

const hasSnapshot = computed(() => Boolean(props.item.last_snapshot_path) && !imgError.value)

const snapshotUrl = computed(() => {
  if (hasSnapshot.value) {
    return `${SNAPSHOT_BASE_URL}${props.item.last_snapshot_path}`
  }
  return ''
})

watch(
  () => props.item.last_snapshot_path,
  () => {
    imgError.value = false
  }
)

function handleImageError() {
  imgError.value = true
}

function handlePreview() {
  if (hasSnapshot.value) {
    emit('preview', props.item)
  }
}

function formatTime(dateStr) {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function formatPos(val) {
  return val != null ? (val * 100).toFixed(1) + '%' : '--'
}
</script>

<style scoped>
.snapshot-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: var(--bg-secondary);
  gap: 8px;
}

.card-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
}
</style>
