<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logApi } from '../api/logs'

const visible = defineModel({ type: Boolean })
const lines = ref(200)
const content = ref('')
const loading = ref(false)
const autoRefresh = ref(false)
let timer

async function loadContent() {
  loading.value = true
  try {
    const result = await logApi.list(lines.value)
    if (!result.success) throw new Error(result.message)
    content.value = result.content
  } catch (error) { ElMessage.error(error.message) } finally { loading.value = false }
}

watch(visible, (value) => { if (value) loadContent() })
watch(autoRefresh, (value) => {
  clearInterval(timer)
  if (value) timer = setInterval(loadContent, 5000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <el-dialog v-model="visible" title="系统日志" width="min(900px, 92vw)">
    <div class="log-tools">
      <el-input-number v-model="lines" :min="50" :max="1000" :step="50" />
      <el-button :icon="Refresh" :loading="loading" @click="loadContent">刷新</el-button>
      <el-checkbox v-model="autoRefresh">自动刷新</el-checkbox>
    </div>
    <pre class="log-content">{{ content || '暂无日志内容' }}</pre>
  </el-dialog>
</template>
