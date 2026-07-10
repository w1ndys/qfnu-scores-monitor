<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logApi } from '../api/logs'

const visible = defineModel({ type: Boolean })
const files = ref([])
const selected = ref('')
const lines = ref(200)
const content = ref('')
const loading = ref(false)
const autoRefresh = ref(false)
let timer

async function loadFiles() {
  const result = await logApi.list()
  files.value = result.logs
  if (!selected.value && files.value.length) selected.value = files.value[0].name
  await loadContent()
}

async function loadContent() {
  if (!selected.value) return
  loading.value = true
  try {
    const result = await logApi.content(selected.value, lines.value)
    if (!result.success) throw new Error(result.message)
    content.value = result.content
  } catch (error) { ElMessage.error(error.message) } finally { loading.value = false }
}

watch(visible, (value) => { if (value) loadFiles() })
watch(autoRefresh, (value) => {
  clearInterval(timer)
  if (value) timer = setInterval(loadContent, 5000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <el-dialog v-model="visible" title="系统日志" width="min(900px, 92vw)">
    <div class="log-tools">
      <el-select v-model="selected" placeholder="选择日志" @change="loadContent">
        <el-option v-for="file in files" :key="file.name" :label="file.name" :value="file.name" />
      </el-select>
      <el-input-number v-model="lines" :min="50" :max="1000" :step="50" />
      <el-button :icon="Refresh" :loading="loading" @click="loadContent">刷新</el-button>
      <el-checkbox v-model="autoRefresh">自动刷新</el-checkbox>
    </div>
    <pre class="log-content">{{ content || '暂无日志内容' }}</pre>
  </el-dialog>
</template>
