<template>
  <div class="stats-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">📊 数据统计分析</h1>
      <p class="page-subtitle">家庭物品检测频次、时间分布与类别分析</p>
    </div>

    <!-- 顶部控制 -->
    <div class="glass-card" style="padding: 16px 20px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
      <span style="font-size: 14px; color: var(--text-secondary);">统计范围：</span>
      <el-radio-group v-model="days" @change="fetchData">
        <el-radio-button :value="1">今天</el-radio-button>
        <el-radio-button :value="3">近3天</el-radio-button>
        <el-radio-button :value="7">近7天</el-radio-button>
        <el-radio-button :value="30">近30天</el-radio-button>
      </el-radio-group>
      <el-date-picker
        v-model="targetDate"
        type="date"
        placeholder="选择日期(时间轴)"
        style="width: 180px; margin-left: auto;"
        @change="fetchTimeline"
      />
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 物品频次排行 -->
      <div class="glass-card chart-card">
        <div class="chart-header">
          <h3>📊 物品出现频次排行</h3>
        </div>
        <StatsChart :option="barChartOption" :height="380" />
      </div>

      <!-- 时间轴分布 -->
      <div class="glass-card chart-card">
        <div class="chart-header">
          <h3>⏰ 检测时间分布（按小时）</h3>
        </div>
        <StatsChart :option="lineChartOption" :height="380" />
      </div>

      <!-- 物品分布饼图 -->
      <div class="glass-card chart-card">
        <div class="chart-header">
          <h3>🥧 物品类别分布</h3>
        </div>
        <StatsChart :option="pieChartOption" :height="380" />
      </div>

      <!-- 实时状态 -->
      <div class="glass-card chart-card realtime-card">
        <div class="chart-header">
          <h3>🔴 实时检测状态</h3>
        </div>
        <div class="realtime-content">
          <div class="realtime-item">
            <span class="realtime-label">运行状态</span>
            <el-tag :type="realtime.is_running ? 'success' : 'info'" effect="dark" size="large">
              {{ realtime.is_running ? '🟢 运行中' : '⚪ 已停止' }}
            </el-tag>
          </div>
          <div class="realtime-item">
            <span class="realtime-label">实时 FPS</span>
            <span class="realtime-value" style="color: var(--primary);">{{ realtime.fps }}</span>
          </div>
          <div class="realtime-item">
            <span class="realtime-label">画面物品数</span>
            <span class="realtime-value" style="color: var(--accent-light);">{{ realtime.total_objects }}</span>
          </div>
          <div v-if="Object.keys(realtime.class_counts || {}).length > 0" class="realtime-classes">
            <span class="realtime-label" style="margin-bottom: 8px; display: block;">当前检测物品</span>
            <div class="class-tags">
              <el-tag
                v-for="(count, name) in realtime.class_counts"
                :key="name"
                type="primary"
                effect="dark"
                style="margin: 2px;"
              >
                {{ name }} × {{ count }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import StatsChart from '../components/StatsChart.vue'
import { getFrequency, getTimeline, getRealtime } from '../api/stats.js'

const days = ref(7)
const targetDate = ref(new Date())
const frequencyData = ref([])
const timelineData = ref([])
const realtime = ref({ fps: 0, total_objects: 0, is_running: false, class_counts: {} })

let realtimeTimer = null

onMounted(() => {
  fetchData()
  fetchTimeline()
  fetchRealtime()
  realtimeTimer = setInterval(fetchRealtime, 2000)
})

onUnmounted(() => {
  if (realtimeTimer) clearInterval(realtimeTimer)
})

async function fetchData() {
  try {
    const res = await getFrequency(days.value)
    frequencyData.value = res.data
  } catch (e) {
    frequencyData.value = []
  }
}

async function fetchTimeline() {
  try {
    const dateStr = targetDate.value
      ? new Date(targetDate.value).toISOString().split('T')[0]
      : undefined
    const res = await getTimeline(dateStr)
    timelineData.value = res.data
  } catch (e) {
    timelineData.value = []
  }
}

async function fetchRealtime() {
  try {
    const res = await getRealtime()
    realtime.value = res.data
  } catch (e) {}
}

// === ECharts 配置 ===

const barChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(15,23,41,0.9)',
    borderColor: 'rgba(0,212,255,0.3)',
    textStyle: { color: '#e2e8f0' }
  },
  xAxis: {
    type: 'category',
    data: frequencyData.value.map(d => d.class_name_zh),
    axisLabel: { rotate: 30, color: '#94a3b8', fontSize: 11 },
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
  },
  series: [{
    type: 'bar',
    data: frequencyData.value.map(d => d.count),
    barWidth: '50%',
    itemStyle: {
      borderRadius: [6, 6, 0, 0],
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#00d4ff' },
          { offset: 1, color: '#7c3aed' }
        ]
      }
    }
  }]
}))

const lineChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(15,23,41,0.9)',
    borderColor: 'rgba(0,212,255,0.3)',
    textStyle: { color: '#e2e8f0' }
  },
  xAxis: {
    type: 'category',
    data: timelineData.value.map(d => `${d.hour}:00`),
    axisLabel: { color: '#94a3b8', fontSize: 11 },
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
  },
  series: [{
    type: 'line',
    data: timelineData.value.map(d => d.count),
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { color: '#00d4ff', width: 3 },
    itemStyle: { color: '#00d4ff' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0,212,255,0.3)' },
          { offset: 1, color: 'rgba(0,212,255,0.02)' }
        ]
      }
    }
  }]
}))

const pieChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(15,23,41,0.9)',
    borderColor: 'rgba(0,212,255,0.3)',
    textStyle: { color: '#e2e8f0' }
  },
  legend: {
    type: 'scroll',
    orient: 'vertical',
    right: 10,
    top: 20,
    bottom: 20,
    textStyle: { color: '#94a3b8', fontSize: 12 }
  },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['40%', '50%'],
    avoidLabelOverlap: true,
    label: { show: false },
    emphasis: {
      label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#fff' },
      itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }
    },
    data: frequencyData.value.map((d, i) => ({
      name: d.class_name_zh,
      value: d.count,
      itemStyle: {
        color: [
          '#00d4ff', '#7c3aed', '#22c55e', '#f59e0b', '#ef4444',
          '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6',
          '#06b6d4', '#84cc16', '#e11d48', '#0ea5e9', '#a855f7',
          '#10b981', '#f43f5e', '#6366f1', '#eab308', '#64748b'
        ][i % 20]
      }
    }))
  }]
}))
</script>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.chart-card {
  padding: 0;
  overflow: hidden;
}

.chart-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.chart-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-bright);
}

.realtime-card {
  display: flex;
  flex-direction: column;
}

.realtime-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

.realtime-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.realtime-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.realtime-value {
  font-size: 32px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.class-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
