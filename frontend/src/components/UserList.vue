<script setup>
import { Delete, Search, Switch } from '@element-plus/icons-vue'

defineProps({ users: { type: Array, required: true }, loading: Boolean, checkingAccount: String })
defineEmits(['check', 'toggle', 'remove'])

const formatTime = (timestamp) => timestamp ? new Date(timestamp * 1000).toLocaleString('zh-CN') : '从未检查'
</script>

<template>
  <el-card shadow="never" class="panel-card user-panel" v-loading="loading">
    <template #header>
      <div class="panel-title"><strong>用户列表</strong><el-tag type="info">{{ users.length }} 位</el-tag></div>
    </template>
    <el-empty v-if="!users.length" description="暂无用户，请先导入" />
    <div v-else class="user-grid">
      <article v-for="user in users" :key="user.user_account" class="user-card">
        <div class="user-heading">
          <strong>{{ user.user_account }}</strong>
          <span class="tags">
            <el-tag size="small" :type="user.enabled ? 'success' : 'info'">{{ user.enabled ? '监控中' : '已暂停' }}</el-tag>
            <el-tag size="small" :type="user.session_expired ? 'danger' : 'success'">{{ user.session_expired ? 'Session 过期' : 'Session 正常' }}</el-tag>
          </span>
        </div>
        <dl>
          <div><dt>推送次数</dt><dd>{{ user.push_count || 0 }}</dd></div>
          <div><dt>最近检查</dt><dd>{{ formatTime(user.last_check_at) }}</dd></div>
          <div><dt>创建时间</dt><dd>{{ formatTime(user.created_at) }}</dd></div>
        </dl>
        <div class="button-row compact">
          <el-button size="small" type="primary" :icon="Search" :loading="checkingAccount === user.user_account" @click="$emit('check', user.user_account)">检测</el-button>
          <el-button size="small" :type="user.enabled ? 'warning' : 'success'" :icon="Switch" @click="$emit('toggle', user.user_account)">{{ user.enabled ? '暂停' : '启用' }}</el-button>
          <el-button size="small" type="danger" plain :icon="Delete" @click="$emit('remove', user.user_account)">删除</el-button>
        </div>
      </article>
    </div>
  </el-card>
</template>
