<script setup>
import { computed, onMounted, ref } from 'vue'
import { Document, Refresh, Search, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from './api/users'
import ImportPanel from './components/ImportPanel.vue'
import LogDialog from './components/LogDialog.vue'
import StatCards from './components/StatCards.vue'
import SettingsDialog from './components/SettingsDialog.vue'
import UserList from './components/UserList.vue'

const users = ref([])
const loading = ref(false)
const importing = ref(false)
const checking = ref(false)
const checkingAccount = ref('')
const logVisible = ref(false)
const settingsVisible = ref(false)
const stats = computed(() => ({
  total: users.value.length,
  enabled: users.value.filter((user) => user.enabled).length,
  expired: users.value.filter((user) => user.session_expired).length,
  disabled: users.value.filter((user) => !user.enabled).length,
  totalPush: users.value.reduce((sum, user) => sum + (user.push_count || 0), 0),
}))

async function loadUsers() {
  loading.value = true
  try { users.value = (await userApi.list()).users } catch (error) { ElMessage.error(error.message) } finally { loading.value = false }
}

async function importUser(text, clear) {
  if (!text.trim()) return ElMessage.warning('请输入用户信息')
  importing.value = true
  try {
    const result = await userApi.import(text)
    result.success ? ElMessage.success(result.message) : ElMessage.error(result.message)
    if (result.success) { clear(); await loadUsers() }
  } catch (error) { ElMessage.error(error.message) } finally { importing.value = false }
}

async function runAction(action, successMessage) {
  try {
    const result = await action()
    result.success ? ElMessage.success(result.message || successMessage) : ElMessage.error(result.message)
    await loadUsers()
  } catch (error) { ElMessage.error(error.message) }
}

async function checkUser(account) {
  checkingAccount.value = account
  await runAction(() => userApi.check(account), '检测完成')
  checkingAccount.value = ''
}

async function removeUser(account) {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${account} 及其成绩记录吗？`, '删除用户', { type: 'warning' })
    await runAction(() => userApi.remove(account), '删除成功')
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message) }
}

async function checkAll() {
  checking.value = true
  await runAction(userApi.checkAll, '全部检测完成')
  checking.value = false
}

onMounted(loadUsers)
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <div><span class="eyebrow">QFNU SCORE WATCH</span><h1>成绩监控控制台</h1><p>集中管理账号状态、成绩检测与运行日志</p></div>
      <div class="header-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadUsers">刷新</el-button>
        <el-button type="warning" :icon="Search" :loading="checking" @click="checkAll">全部检测</el-button>
        <el-button :icon="Document" @click="logVisible = true">运行日志</el-button>
        <el-button :icon="Setting" @click="settingsVisible = true">系统配置</el-button>
      </div>
    </div>
  </header>
  <main>
    <StatCards :stats="stats" />
    <section class="workspace">
      <ImportPanel :loading="importing" @submit="importUser" />
      <UserList :users="users" :loading="loading" :checking-account="checkingAccount" @check="checkUser" @toggle="(account) => runAction(() => userApi.toggle(account), '状态已更新')" @remove="removeUser" />
    </section>
  </main>
  <LogDialog v-model="logVisible" />
  <SettingsDialog v-model="settingsVisible" />
</template>
