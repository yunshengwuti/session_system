<template>
  <div class="session-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span>会话详情</span>
        </div>
      </template>

      <div v-if="session" class="detail-content">
        <!-- 会话基本信息 -->
        <el-descriptions title="基本信息" :column="3" border>
          <el-descriptions-item label="客户名称">
            {{ session.customer_name }}
          </el-descriptions-item>
          <el-descriptions-item label="机构名称">
            {{ session.org_name }}
          </el-descriptions-item>
          <el-descriptions-item label="客服">
            {{ session.customer_service }}
          </el-descriptions-item>
          <el-descriptions-item label="会话日期">
            {{ session.session_date }}
          </el-descriptions-item>
          <el-descriptions-item label="会话时长">
            {{ formatDuration(session.duration_seconds) }}
          </el-descriptions-item>
          <el-descriptions-item label="消息数量">
            {{ session.messages?.length || 0 }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 对话记录 -->
        <div class="messages-section">
          <h3>对话记录</h3>
          <div class="messages-container">
            <div
              v-for="(msg, index) in session.messages"
              :key="index"
              :class="['message-bubble', getMessageClass(msg.speaker)]"
            >
              <div class="message-avatar" v-if="!isCustomerService(msg.speaker)">
                <el-icon size="32"><User /></el-icon>
              </div>
              <div class="message-content-wrapper">
                <div class="message-header">
                  <span class="speaker">{{ msg.speaker }}</span>
                  <span class="time">{{ formatTime(msg.message_time) }}</span>
                </div>
                <div class="message-body">
                  <!-- 文本消息 -->
                  <div v-if="msg.message_type === 'text'" class="message-text">
                    {{ msg.content }}
                  </div>
                  <!-- 图片消息 -->
                  <div v-else-if="msg.message_type === 'image'" class="message-image">
                    <el-image
                      :src="msg.image_url"
                      :preview-src-list="[msg.image_url]"
                      fit="cover"
                      style="max-width: 200px; border-radius: 8px"
                    >
                      <template #error>
                        <div class="image-error">
                          <el-icon><Picture /></el-icon>
                          <span>图片加载失败</span>
                        </div>
                      </template>
                    </el-image>
                  </div>
                </div>
              </div>
              <div class="message-avatar" v-if="isCustomerService(msg.speaker)">
                <el-icon size="32"><Service /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessionAPI } from '../api'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Picture, User, Service } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const session = ref(null)

// 加载会话详情
const loadDetail = async () => {
  loading.value = true
  try {
    const sessionId = route.params.id
    const data = await sessionAPI.getDetail(sessionId)
    session.value = data
  } catch (error) {
    ElMessage.error('加载会话详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0秒'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return minutes > 0 ? `${minutes}分${secs}秒` : `${secs}秒`
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

// 判断是否为客服消息
const isCustomerService = (speaker) => {
  if (!speaker) return false
  // 包含"客服"或"在线客服"关键词的都是客服
  return speaker.includes('客服')
}

// 获取消息样式类
const getMessageClass = (speaker) => {
  return isCustomerService(speaker) ? 'service-message' : 'customer-message'
}

// 返回列表
const goBack = () => {
  router.back()
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.session-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.detail-content {
  margin-top: 20px;
}

.messages-section {
  margin-top: 30px;
}

.messages-section h3 {
  margin-bottom: 20px;
  color: #303133;
}

.messages-container {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

.message-bubble {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.message-content-wrapper {
  max-width: 60%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #909399;
  padding: 0 4px;
}

.speaker {
  font-weight: 500;
  color: #606266;
}

.time {
  font-size: 12px;
  color: #909399;
}

.message-body {
  padding: 12px 16px;
  border-radius: 12px;
  word-break: break-word;
  line-height: 1.6;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 客户消息（左侧，蓝色） */
.customer-message {
  justify-content: flex-start;
}

.customer-message .message-avatar {
  background: #409eff;
}

.customer-message .message-body {
  background: white;
  border: 1px solid #e4e7ed;
  border-top-left-radius: 4px;
}

/* 客服消息（右侧，绿色） */
.service-message {
  justify-content: flex-end;
  flex-direction: row-reverse;
}

.service-message .message-avatar {
  background: #67c23a;
}

.service-message .message-header {
  flex-direction: row-reverse;
}

.service-message .message-content-wrapper {
  align-items: flex-end;
}

.service-message .message-body {
  background: #e1f3d8;
  border: 1px solid #c0e6b4;
  border-top-right-radius: 4px;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  color: #303133;
}

.message-image {
  cursor: pointer;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #909399;
  gap: 8px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>
