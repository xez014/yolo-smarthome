<template>
  <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: Number, default: 350 }
})

const chartRef = ref(null)
let chartInstance = null

onMounted(() => {
  nextTick(() => {
    if (chartRef.value) {
      chartInstance = echarts.init(chartRef.value, 'dark')
      chartInstance.setOption(getBaseOption())
      if (props.option) {
        chartInstance.setOption(props.option)
      }
    }
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(() => props.option, (newOption) => {
  if (chartInstance && newOption) {
    chartInstance.setOption(newOption, true)
  }
}, { deep: true })

function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

function getBaseOption() {
  return {
    backgroundColor: 'transparent',
    textStyle: {
      fontFamily: "'Inter', 'Noto Sans SC', sans-serif",
      color: '#94a3b8'
    },
    grid: {
      top: 40,
      right: 20,
      bottom: 30,
      left: 50,
      containLabel: true
    }
  }
}
</script>
