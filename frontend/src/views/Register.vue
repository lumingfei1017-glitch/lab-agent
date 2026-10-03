<template>
  <div class="register-container">
    <div class="register-box">
      <h1 style="text-align: center; font-size: 28px; margin-bottom: 30px">
        欢迎注册实验室预约系统
      </h1>
      <el-form :model="form" label-width="auto" style="max-width: 600px">
        <el-form-item>
          <el-input
            size="large"
            v-model="form.username"
            placeholder="请输入账号"
            :prefix-icon="User"
          >
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-input
            type="password"
            size="large"
            v-model="form.password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          >
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-input
            type="password"
            size="large"
            v-model="form.confirmpassword"
            placeholder="请确认密码"
            :prefix-icon="Lock"
            show-password
          >
          </el-input>
        </el-form-item>

        <div>
          <el-button size="large" type="primary" style="width: 100%">注 册</el-button>
        </div>
        <div style="text-align: right; margin-top: 5px">
          没有账号？请 <a style="color: var(--el-color-primary)" href="/login">登录</a>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import router from '@/router'

const form = reactive({
  username: '',
  password: '',
  confirmpassword: ''
})

const loadingValue = ref(false)
const login = () => {
  loadingValue.value = true
  setTimeout(() => {
    loadingValue.value = false
    ElMessage.success('登录成功')
    router.push('/login')
  }, 2000)
}
</script>
<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.register-box {
  width: 380px;
  border-radius: 8px;
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0);
  padding: 30px;
  text-align: center;
}
</style>
