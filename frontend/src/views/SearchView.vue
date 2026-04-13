<template>
  <div class="search-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">🔍 物品历史检索</h1>
      <p class="page-subtitle">查找物品最后出现的位置和时间 — "我的钥匙/笔记本最后出现在哪里？"</p>
    </div>

    <!-- 搜索栏 -->
    <div class="glass-card search-bar">
      <div class="search-controls">
        <el-select
          v-model="selectedClass"
          placeholder="选择物品类别"
          clearable
          filterable
          style="width: 220px;"
          @change="handleSearch"
        >
          <el-option
            v-for="cls in classList"
            :key="cls.class_id"
            :label="`${cls.class_name_zh} (${cls.class_name})`"
            :value="cls.class_name"
          />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          style="width: 380px;"
          @change="handleSearch"
        />

        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="RefreshRight" @click="handleReset">重置</el-button>
      </div>
    </div>

    <!-- 物品最后出现位置一览 -->
    <div v-if="!selectedClass && lastSeenList.length > 0" class="section">
      <h2 class="section-title">📍 各物品最后出现位置</h2>
      <div class="card-grid">
        <SearchCard
          v-for="item in lastSeenList"
          :key="item.object_class"
          :item="item"
          @preview="handlePreview"
        />
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="selectedClass && searchResult" class="section">
      <h2 class="section-title">
        🎯 「{{ searchResult.class_name_zh }}」的最后出现位置
      </h2>
      <div class="card-grid" style="grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));">
        <SearchCard :item="searchResult" @preview="handlePreview" />
      </div>
    </div>

    <!-- 历史记录 -->
    <div v-if="selectedClass" class="section">
      <h2 class="section-title">📋 历史检测记录</h2>
      <div class="glass-card" style="padding: 16px;">
        <el-table
          :data="historyList"
          style="width: 100%; background: transparent;"
          :header-cell-style="{ background: 'var(--bg-secondary)', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)' }"
          :cell-style="{ background: 'transparent', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.04)' }"
          empty-text="暂无记录"
        >
          <el-table-column prop="object_class" label="物品类别" width="120">
            <template #default="{ row }">
              <span style="color: var(--primary); font-weight: 500;">
                {{ classNameZh(row.object_class) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="{ row }">
              <el-progress
                :percentage="(row.confidence * 100)"
                :stroke-width="6"
                :show-text="true"
                :format="() => (row.confidence * 100).toFixed(0) + '%'"
                style="width: 80px;"
              />
            </template>
          </el-table-column>
          <el-table-column label="位置坐标" width="180">
            <template #default="{ row }">
              ({{ (row.bbox_x * 100).toFixed(1) }}%, {{ (row.bbox_y * 100).toFixed(1) }}%)
            </template>
          </el-table-column>
          <el-table-column prop="track_id" label="追踪ID" width="90" />
          <el-table-column prop="detected_at" label="检测时间" min-width="180">
            <template #default="{ row }">
              {{ formatTime(row.detected_at) }}
            </template>
          </el-table-column>
          <el-table-column label="快照" width="80">
            <template #default="{ row }">
              <el-button
                v-if="row.snapshot_path"
                type="primary"
                size="small"
                link
                @click="handlePreviewSnapshot(row.snapshot_path)"
              >
                查看
              </el-button>
              <span v-else style="color: var(--text-muted);">—</span>
            </template>
          </el-table-column>
        </el-table>

        <div style="margin-top: 16px; display: flex; justify-content: center;">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalRecords"
            layout="prev, pager, next, total"
            @current-change="fetchHistory"
          />
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!selectedClass && lastSeenList.length === 0" class="empty-state" style="padding: 80px 20px;">
      <div class="empty-icon">🔍</div>
      <div class="empty-text">暂无检测数据，请先启动实时检测</div>
    </div>

    <!-- 快照预览弹窗 -->
    <el-dialog v-model="previewVisible" title="快照预览" width="60%" center>
      <img :src="previewUrl" alt="快照" style="width: 100%; border-radius: 8px;" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, RefreshRight } from '@element-plus/icons-vue'

import SearchCard from '../components/SearchCard.vue'
import { getClasses, searchObject, getAllLastSeen, getHistory } from '../api/detection.js'
import { SNAPSHOT_BASE_URL } from '../api/video.js'

// 中文名映射
const classNameMap = ref({})
const classList = ref([])
const selectedClass = ref('')
const dateRange = ref(null)
const searchResult = ref(null)
const lastSeenList = ref([])
const historyList = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalRecords = ref(0)
const previewVisible = ref(false)
const previewUrl = ref('')

onMounted(async () => {
  await fetchClasses()
  await fetchLastSeen()
})

async function fetchClasses() {
  try {
    const res = await getClasses()
    classList.value = res.data
    res.data.forEach(cls => {
      classNameMap.value[cls.class_name] = cls.class_name_zh
    })
  } catch (e) {}
}

async function fetchLastSeen() {
  try {
    const res = await getAllLastSeen()
    lastSeenList.value = res.data
  } catch (e) {}
}

async function handleSearch() {
  if (!selectedClass.value) {
    searchResult.value = null
    historyList.value = []
    return
  }

  try {
    const res = await searchObject(selectedClass.value)
    searchResult.value = res.data
  } catch (e) {
    searchResult.value = null
  }

  currentPage.value = 1
  fetchHistory()
}

async function fetchHistory() {
  if (!selectedClass.value) return

  const params = {
    object_class: selectedClass.value,
    page: currentPage.value,
    page_size: pageSize.value
  }

  if (dateRange.value && dateRange.value.length === 2) {
    params.start_time = dateRange.value[0].toISOString()
    params.end_time = dateRange.value[1].toISOString()
  }

  try {
    const res = await getHistory(params)
    historyList.value = res.data.items
    totalRecords.value = res.data.total
  } catch (e) {
    historyList.value = []
    totalRecords.value = 0
  }
}

function handleReset() {
  selectedClass.value = ''
  dateRange.value = null
  searchResult.value = null
  historyList.value = []
  fetchLastSeen()
}

function handlePreview(item) {
  if (item.last_snapshot_path) {
    previewUrl.value = `${SNAPSHOT_BASE_URL}${item.last_snapshot_path}`
    previewVisible.value = true
  }
}

function handlePreviewSnapshot(path) {
  previewUrl.value = `${SNAPSHOT_BASE_URL}${path}`
  previewVisible.value = true
}

function classNameZh(name) {
  return classNameMap.value[name] || name
}

function formatTime(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-bar {
  padding: 20px;
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.section {
  margin-top: 4px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-bright);
  margin-bottom: 16px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
</style>
