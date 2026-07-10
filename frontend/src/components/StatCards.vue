<script setup>
defineProps({ stats: { type: Object, required: true } })

const cards = [
  ['total', '总用户数', 'primary'],
  ['enabled', '监控中', 'success'],
  ['expired', 'Session 已过期', 'warning'],
  ['disabled', '已禁用', 'danger'],
  ['totalPush', '总推送次数', 'info'],
]
</script>

<template>
  <section class="stat-grid">
    <el-card v-for="[key, label, tone] in cards" :key="key" shadow="never" class="stat-card">
      <el-statistic :value="stats[key]" :class="`tone-${tone}`" />
      <span>{{ label }}</span>
    </el-card>
  </section>
</template>
