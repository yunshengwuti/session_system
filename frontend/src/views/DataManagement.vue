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
            注意：会清除所选日期范围内的会话、消息、日报、周报和相关生成任务记录。此操作不可撤销。
          </div>

          <div class="danger-actions">
            <el-button type="danger" @click="clearRange" :loading="clearing">清除数据</el-button>
          </div>
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
const clearing = ref(false)
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

const clearRange = async () => {
  if (!selectedRange.value) {
    ElMessage.warning('请选择清除日期范围')
    return
  }

  clearing.value = true
  let cleanupPreview
  try {
    cleanupPreview = await managementAPI.previewCleanup(
      selectedRange.value.startDate,
      selectedRange.value.endDate
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取清除影响失败')
    console.error(error)
    clearing.value = false
    return
  }
  clearing.value = false

  const previewCounts = cleanupPreview.counts || {}
  const confirmMessage = [
    '<div style="line-height: 1.8;">',
    '<div>清除范围：' + cleanupPreview.start_date + ' 至 ' + cleanupPreview.end_date + '</div>',
    '<div>将删除：' + (previewCounts.sessions || 0) + ' 条会话、' +
      (previewCounts.messages || 0) + ' 条消息、' +
      (previewCounts.daily_reports || 0) + ' 份日报、' +
      (previewCounts.weekly_reports || 0) + ' 份周报。</div>',
    '<div style="margin-top: 8px; color: #c45656;">此操作不可撤销。</div>',
    '</div>'
  ].join('')

  try {
    await ElMessageBox.confirm(confirmMessage, '清除影响', {
      confirmButtonText: '确认',
      cancelButtonText: '返回',
      type: 'warning',
      dangerouslyUseHTMLString: true,
      confirmButtonClass: 'el-button--danger'
    })
  } catch {
    return
  }

  clearing.value = true
  try {
    const result = await managementAPI.clearRange(
      selectedRange.value.startDate,
      selectedRange.value.endDate
    )
    ElMessage.success(result.message || '数据已清除')
    cleanupRange.value = null
    applyOverview(result)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '清除失败')
    console.error(error)
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
  padding: 20px 70px 15px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 6px;
}

.danger-topline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 0 0 12px 0;
}

.danger-title {
  flex: none;
  margin-bottom: 0;
  color: #606266;
  font-size: 14px;
  font-weight: 600;
  line-height: 32px;
}

.danger-topline :deep(.el-date-editor.el-input__wrapper),
.danger-topline :deep(.el-date-editor--daterange.el-input__wrapper),
.danger-topline :deep(.el-date-editor) {
  flex: none;
  width: 240px !important;
  max-width: 240px !important;
  min-width: 240px !important;
}

.danger-topline :deep(.el-range-input) {
  width: 84px;
}

.danger-topline :deep(.el-range-separator) {
  flex: 0 0 18px;
  padding: 0;
}

.danger-text {
  margin-left: 0;
  color: #c45656;
  font-size: 13px;
  line-height: 1.5;
  white-space: nowrap;
}

.danger-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
  padding-right: 0;
  transform: translateX(8px);
}

@media (max-width: 900px) {
  .data-management,
  .management-panel {
    max-width: none;
  }

  .count-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .danger-zone {
    padding: 18px;
  }

  .danger-topline {
    align-items: flex-start;
    flex-direction: column;
    margin-left: 0;
  }

  .danger-text {
    margin-left: 0;
    white-space: normal;
  }

  .danger-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
    padding-right: 0;
  }
}
</style>
