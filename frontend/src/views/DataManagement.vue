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

      <div class="management-panel">
        <div class="section-block">
          <div class="section-title centered-title">数据库容量</div>
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

        <div class="section-block">
          <div class="section-title centered-title">当前数据</div>
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
          </div>
        </div>

        <div class="danger-zone">
          <div class="danger-topline">
            <div class="section-title danger-title">按日期范围清除</div>
            <el-date-picker
              v-model="cleanupRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              :unlink-panels="false"
            />
          </div>

          <div class="danger-text">
            会清除所选日期范围内的会话、消息、日报、重叠周报和相关生成任务记录。此操作不可撤销。
          </div>

          <div class="danger-actions">
            <el-button @click="previewCleanup" :loading="previewing">预览清除影响</el-button>
            <el-button type="danger" @click="clearRange" :loading="clearing" :disabled="!preview">
              清除数据
            </el-button>
          </div>

          <div v-if="preview" class="preview-box">
            将删除 {{ preview.start_date }} 至 {{ preview.end_date }}：{{ preview.counts.sessions }} 条会话、{{ preview.counts.messages }} 条消息、{{ preview.counts.daily_reports }} 份日报、{{ preview.counts.weekly_reports }} 份周报。
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { managementAPI } from '../api'

const loading = ref(false)
const previewing = ref(false)
const clearing = ref(false)
const preview = ref(null)
const cleanupRange = ref(null)

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

const selectedRange = computed(() => {
  if (!cleanupRange.value || cleanupRange.value.length !== 2) return null
  return {
    startDate: cleanupRange.value[0],
    endDate: cleanupRange.value[1]
  }
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
  if (!selectedRange.value) {
    ElMessage.warning('请选择清除日期范围')
    return
  }

  previewing.value = true
  try {
    preview.value = await managementAPI.previewCleanup(
      selectedRange.value.startDate,
      selectedRange.value.endDate
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '预览清除影响失败')
    console.error(error)
  } finally {
    previewing.value = false
  }
}

const clearRange = async () => {
  if (!preview.value || !selectedRange.value) {
    ElMessage.warning('请先预览清除影响')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认清除 ${selectedRange.value.startDate} 至 ${selectedRange.value.endDate} 的数据？这个操作不可撤销。`,
      '危险操作',
      {
        confirmButtonText: '确认清除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    clearing.value = true
    const result = await managementAPI.clearRange(
      selectedRange.value.startDate,
      selectedRange.value.endDate
    )
    ElMessage.success(result.message || '数据已清除')
    preview.value = null
    applyOverview(result)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '清除失败')
      console.error(error)
    }
  } finally {
    clearing.value = false
  }
}

watch(cleanupRange, () => {
  preview.value = null
})

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.data-management {
  max-width: 980px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.management-panel {
  max-width: 760px;
  margin: 0 auto;
}

.section-block {
  margin-bottom: 30px;
}

.section-title {
  margin-bottom: 12px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.centered-title {
  text-align: center;
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
  text-align: center;
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
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
  padding: 18px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 6px;
}

.danger-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.danger-title {
  margin-bottom: 0;
  color: #c45656;
}

.danger-topline :deep(.el-date-editor) {
  width: 320px;
  max-width: 100%;
}

.danger-text {
  color: #606266;
  line-height: 1.7;
}

.danger-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.preview-box {
  margin-top: 14px;
  padding: 12px 14px;
  color: #c45656;
  line-height: 1.7;
  background: #fff;
  border: 1px solid #fde2e2;
  border-radius: 6px;
}

@media (max-width: 900px) {
  .data-management,
  .management-panel {
    max-width: none;
  }

  .count-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .danger-topline {
    align-items: flex-start;
    flex-direction: column;
  }

  .danger-actions {
    flex-wrap: wrap;
  }
}
</style>
