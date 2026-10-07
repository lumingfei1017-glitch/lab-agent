<template>
  <div class="register-container">
    <div class="register-box">
      <h1 style="text-align: center; font-size: 28px; margin-bottom: 30px">
        欢迎注册实验室预约系统
      </h1>
      <el-form ref="formRef" :rules="rules" :model="form" label-width="0px" style="width: 100%">
        <el-form-item prop="username">
          <el-input
            size="large"
            v-model="form.username"
            placeholder="请输入账号"
            :prefix-icon="User"
          >
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
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

        <el-form-item prop="confirmPassword">
          <el-input
            type="password"
            size="large"
            v-model="form.confirmPassword"
            placeholder="请确认密码"
            :prefix-icon="Lock"
            show-password
          >
          </el-input>
        </el-form-item>

        <div>
          <el-button size="large" type="primary" style="width: 100%" @click="register"
            >注 册</el-button
          >
        </div>
        <div style="text-align: right; margin-top: 5px">
          已有账号？请
          <router-link style="color: var(--el-color-primary)" to="/login">登录</router-link>
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
import { getValidDateOfQuarter } from 'element-plus/es/components/date-picker-panel/src/utils.mjs'
import { registerApi } from '@/api/auth'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else {
    if (value !== form.password) {
      callback(new Error('两次密码输入不一致'))
    } else {
      callback()
    }
  }
}

const formRef = ref()
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validatePass, trigger: 'blur' }]
}

const loadingValue = ref(false)

const register = async () => {
  const avalid = await formRef.value.validate().catch(() => false) //表单校验
  if (!avalid) {
    return
  }

  loadingValue.value = true
  try {
    const res = await registerApi(form)
    if (res.code === 200) {
      ElMessage.success('注册成功')
      await router.push('/login')
    }
  } finally {
    loadingValue.value = false
  }
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
