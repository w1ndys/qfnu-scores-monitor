<script setup>
import { ref } from 'vue'
import { Delete, Upload } from '@element-plus/icons-vue'

defineProps({ loading: Boolean })
const emit = defineEmits(['submit'])
const text = ref('')

function submit() {
  emit('submit', text.value, () => { text.value = '' })
}
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header><strong>导入新用户</strong></template>
    <el-alert title="请依次输入学号、密码、钉钉 Webhook、钉钉签名密钥，每项一行。" type="info" :closable="false" />
    <el-input v-model="text" class="import-input" type="textarea" :rows="9" placeholder="202312345678&#10;your_password&#10;https://oapi.dingtalk.com/...&#10;SECxxxxxxxx" />
    <div class="button-row">
      <el-button type="primary" :icon="Upload" :loading="loading" @click="submit">导入用户</el-button>
      <el-button :icon="Delete" @click="text = ''">清空</el-button>
    </div>
  </el-card>
</template>
