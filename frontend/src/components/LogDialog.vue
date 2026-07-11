<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logApi } from '../api/logs'

const visible = defineModel({ type: Boolean })
const lines = ref(200)
const logs = ref([])
const level = ref('ALL')
const keyword = ref('')
const loading = ref(false)
const autoRefresh = ref(false)
let timer

async function loadContent() {
  loading.value = true
  try {
    const result = await logApi.list(lines.value)
    if (!result.success) throw new Error(result.message)
    logs.value = [...result.logs].reverse()
  } catch (error) { ElMessage.error(error.message) } finally { loading.value = false }
}

watch(visible, (value) => { if (value) loadContent() })
watch(autoRefresh, (value) => {
  clearInterval(timer)
  if (value) timer = setInterval(loadContent, 5000)
})
onBeforeUnmount(() => clearInterval(timer))

const levels = computed(() => [...new Set(logs.value.map((item) => item.level))])
const filteredLogs = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return logs.value.filter((item) => {
    if (level.value !== 'ALL' && item.level !== level.value) return false
    if (!query) return true
    return [item.message, item.module, item.function, item.exception]
      .some((value) => String(value || '').toLowerCase().includes(query))
  })
})

function levelType(value) {
  return { ERROR: 'danger', CRITICAL: 'danger', WARNING: 'warning', SUCCESS: 'success', INFO: 'primary' }[value] || 'info'
}
</script>

<template>
  <el-dialog v-model="visible" title="系统日志" width="min(1180px, 96vw)" class="log-dialog">
    <div class="log-tools">
      <el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索消息、模块或异常" clearable class="log-search" />
      <el-select v-model="level" class="log-level-select">
        <el-option label="全部级别" value="ALL" />
        <el-option v-for="item in levels" :key="item" :label="item" :value="item" />
      </el-select>
      <el-input-number v-model="lines" :min="50" :max="1000" :step="50" />
      <el-button :icon="Refresh" :loading="loading" @click="loadContent">刷新</el-button>
      <el-checkbox v-model="autoRefresh">自动刷新</el-checkbox>
      <span class="log-count">显示 {{ filteredLogs.length }} / {{ logs.length }} 条</span>
    </div>
    <el-table v-loading="loading" :data="filteredLogs" height="60vh" stripe empty-text="暂无日志记录">
      <el-table-column prop="created_at" label="时间" width="168" sortable />
      <el-table-column label="级别" width="105" align="center">
        <template #default="{ row }">
          <el-tag :type="levelType(row.level)" effect="light" size="small">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="220">
        <template #default="{ row }">
          <span class="log-source">{{ row.module }}:{{ row.function }}:{{ row.line }}</span>
        </template>
      </el-table-column>
      <el-table-column label="消息" min-width="360">
        <template #default="{ row }">
          <div class="log-message">{{ row.message }}</div>
          <details v-if="row.exception" class="log-exception">
            <summary>查看异常详情</summary>
            <pre>{{ row.exception }}</pre>
          </details>
        </template>
      </el-table-column>
    </el-table>
  </el-dialog>
</template>
