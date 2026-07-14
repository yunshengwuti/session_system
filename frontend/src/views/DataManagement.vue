<template>
  <div class="data-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据管理</span>
          <el-button type="primary" @click="loadOverview" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <div class="storage-section">
        <div class="section-title">数据库容量</div>
        <div class="storage-summary">
          <div class="storage-number">
            {{ storage.used_mb }} MB
            <span>/ {{ storage.limit_mb }} MB</span>
          </div>
          <el-progress :percentage="storagePercent" :status="storageStatus" />
          <div class="storage-meta">
            <span>使用率 {{ storage.used_percent }}%</span>
            <span>数据库类型 {{ storage.dialect || '-' }}</span>
          </div>
        </div>
      </div>

      <div class="section-title">当前数据</div>
      <div class="count-grid">
        <div class="count-item">
          <div class="count-value">{{ counts.sessions }}</div>
          <div class="count-label">会话</div>
        </div>
        <div class="count-item">
          <div class="count-value">{{ counts.messages }}</div>
          <div class="count-label">消息</div>
        </div>
        <div class="count-item">
          <div class="count-value">{{ counts.daily_reports }}</div>
          <div class="count-label">日报</div>
        </div>
        <div class="count-item">
          <div class="count-value">{{ counts.weekly_reports }}</div>
          <div class="count-label">周报</div>
        </div>
        <div class="count-item">
          <div class="count-value">{{ counts.report_tasks }}</div>
          <div class="count-label">生成任务</div>
        </div>
      </div>

      <div class="danger-zone">
        <div>
          <div class="section-title danger-title">全部清除</div>
          <div class="danger-text">
            清除后会删除所有会话、消息、日报、周报和报告生成任务记录。这个操作不可撤销。
          </div>
          <div v-if="preview" class="preview-box">
            将删除：{{ preview.counts.sessions }} 条会话、{{ preview.counts.messages }} 条消息、{{ preview.counts.daily_reports }} 份日报、{{ preview.counts.weekly_reports }} 份周报、{{ preview.counts.report_tasks }} 条任务记录。
          </div>
        </div>
        <div class="danger-actions">
          <el-button @click="previewCleanup" :loading="previewing">预览清除影响</el-button>
          <el-button type="danger" @click="clearAll" :loading="clearing" :disabled="!preview">
            全部清除
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { managementAPI } from '../api'

const loading = ref(false)
const previewing = ref(false)
const clearing = ref(false)
const preview = ref(null)

const storage = reactive({
  used_mb: 0,
  limit_mb: 512,
  used_percent: 0,
  dialect: ''
})

const counts = reactive({
  sessions: 0,
  messages: 0,
  daily_reports: 0,
  weekly_reports: 0,
  report_tasks: 0
})

const storagePercent = computed(() => Math.min(100, Number(storage.used_percent || 0)))
const storageStatus = computed(() => {
  if (storagePercent.value >= 90) return 'exception'
  if (storagePercent.value >= 75) return 'warning'
  return undefined
})

const applyOverview = (data) => {
  Object.assign(storage, data.storage || {})
  Object.assign(counts, data.counts || {})
}

const loadOverview = async () => {
  loading.value = true
  try {
    const data = await managementAPI.getStorage()
    applyOverview(data)
  } catch (error) {
    ElMessage.error('加载数据管理信息失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const previewCleanup = async () => {
  previewing.value = true
  try {
    preview.value = await managementAPI.previewCleanup()
  } catch (error) {
    ElMessage.error('预览清除影响失败')
    console.error(error)
  } finally {
    previewing.value = false
  }
}

const clearAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确认清除全部数据？会话、消息、日报、周报和任务记录都会被删除，且不可撤销。',
      '危险操作',
      {
        confirmButtonText: '确认全部清除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    clearing.value = true
    const result = await managementAPI.clearAll()
    ElMessage.success(result.message || '数据已全部清除')
    preview.value = null
    applyOverview(result)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '全部清除失败')
      console.error(error)
    }
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.data-management {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.storage-section {
  margin-bottom: 28px;
}

.section-title {
  margin-bottom: 12px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.storage-summary {
  padding: 18px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.storage-number {
  margin-bottom: 12px;
  color: #303133;
  font-size: 28px;
  font-weight: 700;
}

.storage-number span {
  color: #909399;
  font-size: 16px;
  font-weight: 500;
}

.storage-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  color: #909399;
  font-size: 13px;
}

.count-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 30px;
}

.count-item {
  padding: 16px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  text-align: center;
}

.count-value {
  color: #303133;
  font-size: 24px;
  font-weight: 700;
}

.count-label {
  margin-top: 6px;
  color: #909399;
  font-size: 13px;
}

.danger-zone {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 18px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 6px;
}

.danger-title {
  color: #c45656;
}

.danger-text {
  color: #606266;
  line-height: 1.7;
}

.preview-box {
  margin-top: 12px;
  color: #c45656;
  line-height: 1.7;
}

.danger-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .count-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .danger-zone {
    flex-direction: column;
  }

  .danger-actions {
    justify-content: flex-start;
  }
}
</style>
