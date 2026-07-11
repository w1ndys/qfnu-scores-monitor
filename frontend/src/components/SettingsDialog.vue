<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi } from '../api/settings'

const visible = defineModel({ type: Boolean })
const ocrUrl = ref('')
const checkInterval = ref(5)
const loading = ref(false)

watch(visible, async (value) => {
  if (!value) return
  loading.value = true
  try {
    const settings = (await settingsApi.get()).settings
    ocrUrl.value = settings.ocr_url || ''
    checkInterval.value = settings.check_interval_minutes || 5
  }
  catch (error) { ElMessage.error(error.message) }
  finally { loading.value = false }
})

async function save() {
  loading.value = true
  try {
    const result = await settingsApi.update({
      ocr_url: ocrUrl.value,
      check_interval_minutes: checkInterval.value,
    })
    if (!result.success) return ElMessage.error(result.message)
    ElMessage.success(result.message)
    visible.value = false
  } catch (error) { ElMessage.error(error.message) }
  finally { loading.value = false }
}
</script>

<template>
  <el-dialog v-model="visible" title="系统配置" width="min(560px, 92vw)">
    <el-form label-position="top" v-loading="loading">
      <el-form-item label="OCR 服务地址">
        <el-input v-model="ocrUrl" placeholder="例如：https://ocr.example.com" clearable />
        <div class="form-help">登录时将验证码以表单字段 image 发送到该地址的 /ocr 接口。</div>
      </el-form-item>
      <el-form-item label="成绩监控间隔">
        <el-input-number v-model="checkInterval" :min="1" :max="1440" :step="1" />
        <span class="setting-unit">分钟</span>
        <div class="form-help full-line">保存后立即生效，无需重启后端服务。</div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="save">保存配置</el-button>
    </template>
  </el-dialog>
</template>
