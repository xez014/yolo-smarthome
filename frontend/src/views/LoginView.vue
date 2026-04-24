<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card glass-card">
        <div class="login-header">
          <div class="login-logo">🏠</div>
          <h1 class="login-title">YOLO-SmartHome</h1>
          <p class="login-subtitle">智能家居视觉感知与检索系统</p>
        </div>

        <el-form @submit.prevent="handleLogin" class="login-form">
          <el-form-item>
            <el-input
              v-model="password"
              type="password"
              placeholder="请输入管理员密码"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            >
              <template #prefix>🔑</template>
            </el-input>
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            style="width: 100%; margin-top: 8px;"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>

          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  if (!password.value.trim()) {
    errorMsg.value = '请输入密码'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await axios.post('/api/auth/login', {
      password: password.value.trim()
    })
    // 保存 token
    localStorage.setItem('token', res.data.access_token)
    // 跳转首页
    router.push('/dashboard')
  } catch (e) {
    if (e.response && e.response.status === 401) {
      errorMsg.value = '密码错误，请重试'
    } else {
      errorMsg.value = '登录失败，请检查网络连接'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 50%, rgba(0, 212, 255, 0.05) 0%, transparent 50%),
              radial-gradient(circle at 70% 50%, rgba(124, 58, 237, 0.05) 0%, transparent 50%);
  animation: bgShift 20s ease-in-out infinite alternate;
}

@keyframes bgShift {
  0% { transform: translate(0, 0); }
  100% { transform: translate(-5%, 3%); }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.login-card {
  padding: 48px 36px;
  border-radius: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-logo {
  font-size: 52px;
  margin-bottom: 12px;
  filter: drop-shadow(0 4px 16px rgba(0, 212, 255, 0.3));
}

.login-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-bright);
  margin: 0 0 4px 0;
  letter-spacing: 1px;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.login-form {
  margin-top: 20px;
}

.error-msg {
  color: #f56c6c;
  font-size: 13px;
  text-align: center;
  margin-top: 12px;
}
</style>
