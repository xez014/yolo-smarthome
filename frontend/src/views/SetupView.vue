<template>
  <div class="setup-container">
    <div class="setup-card glass-card">
      <div class="setup-header">
        <h1 class="logo-text" style="font-size: 32px; margin-bottom: 8px;">🔌 系统初始化配置</h1>
        <p style="color: var(--text-secondary);">配置外置 MySQL 数据库以启动 YOLO 感知引擎</p>
      </div>

      <el-form :model="form" ref="formRef" @submit.prevent class="setup-form" label-position="top">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="MySQL Host (服务器地址)" required>
              <el-input v-model="form.host" placeholder="例如: 192.168.1.100 或 mydb.xxx.com" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="端口" required>
              <el-input v-model="form.port" placeholder="3306" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" required>
              <el-input v-model="form.user" placeholder="root" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" required>
              <el-input v-model="form.password" type="password" show-password placeholder="数据库密码" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="数据库名称 (自动创建表结构)" required>
          <el-input v-model="form.dbname" placeholder="smarthome_db" />
        </el-form-item>

        <div class="actions">
          <el-button 
            type="primary" 
            size="large" 
            :loading="testing" 
            @click="testConnection"
            class="glow-button"
            style="width: 100%; margin-bottom: 12px;"
          >
            🔌 测试连接并初始化系统
          </el-button>
        </div>
        
        <div v-if="message" :class="['status-msg', statusType]">
          {{ message }}
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = ref({
  host: '127.0.0.1',
  port: '3306',
  user: 'root',
  password: '',
  dbname: 'smarthome_db'
})

const testing = ref(false)
const message = ref('')
const statusType = ref('info')

async function testConnection() {
  if (!form.value.host || !form.value.user || !form.value.dbname) {
    ElMessage.warning('请填写完整的数据库信息')
    return
  }

  testing.value = true
  message.value = '正在验证数据库连通性...'
  statusType.value = 'info'

  try {
    // 1. 测试连接
    const testRes = await axios.post('/api/system/test-db', form.value)
    if (testRes.data.status !== 'ok') {
      message.value = '❌ 测试失败: ' + testRes.data.message
      statusType.value = 'error'
      testing.value = false
      return
    }
    
    message.value = '✅ 连通性测试通过！正在自动生成数据表...'
    
    // 2. 初始化建表并保存凭据
    const initRes = await axios.post('/api/system/init-db', form.value)
    if (initRes.data.status !== 'ok') {
      message.value = '❌ 初始化建表失败: ' + initRes.data.message
      statusType.value = 'error'
      testing.value = false
      return
    }

    message.value = '🎉 系统配置成功！即将跳转大屏...'
    statusType.value = 'success'
    
    // 3. 延时进入系统
    setTimeout(() => {
      router.push('/dashboard')
    }, 1500)

  } catch (error) {
    message.value = '❌ 服务请求失败，请确保后端服务正常运行'
    statusType.value = 'error'
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.setup-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100vh;
  background: radial-gradient(circle at center, #1b213a 0%, #0d1117 100%);
}

.setup-card {
  width: 100%;
  max-width: 500px;
  padding: 40px;
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.setup-header {
  text-align: center;
  margin-bottom: 30px;
}

.glow-button {
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
  transition: all 0.3s ease;
}

.glow-button:hover {
  box-shadow: 0 0 25px rgba(0, 212, 255, 0.6);
  transform: translateY(-2px);
}

.status-msg {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  font-size: 14px;
}

.info { background: rgba(0,212,255,0.1); color: #00d4ff; border: 1px solid rgba(0,212,255,0.2); }
.success { background: rgba(34,197,94,0.1); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.error { background: rgba(239,68,68,0.1); color: #f87171; border: 1px solid rgba(239,68,68,0.2); }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
