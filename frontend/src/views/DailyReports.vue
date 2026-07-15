<template>
  <div class="daily-reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>日报管理</span>
          <div>
            <el-date-picker
              v-model="selectedDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="margin-right: 10px"
            />
            <el-button type="primary" @click="generateReport" :loading="generating" :disabled="generationTask.active">
              <el-icon><Plus /></el-icon>
              生成日报
            </el-button>
          </div>
        </div>
      </template>

      <!-- 生成进度 -->
      <div v-if="generationTask.active" class="generation-progress">
        <div class="progress-header">
          <span>{{ generationTask.message || '报告生成中' }}</span>
          <span class="progress-status">{{ generationTask.progress }}%</span>
        </div>
        <el-progress :percentage="generationTask.progress" :status="progressStatus" />
      </div>

      <!-- 日报列表 -->
      <el-table v-loading="loading" :data="reports" style="width: 100%">
        <el-table-column prop="report_date" label="日期" width="120" />
        <el-table-column prop="total_sessions" label="会话数" width="100" />
        <el-table-column label="关键问题">
          <template #default="{ row }">
            <el-tag v-for="(count, keyword, index) in row.keywords_json" :key="keyword" v-show="index < 3" size="small" style="margin-right: 5px">
              {{ keyword }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewReport(row)">查看详情</el-button>
            <el-button type="danger" size="small" @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 日报详情对话框 -->
    <el-dialog v-model="dialogVisible" title="日报详情" width="90%" @opened="renderCharts">
      <div v-if="currentReport" class="report-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="日期">
            {{ currentReport.report_date }}
          </el-descriptions-item>
          <el-descriptions-item label="总会话数">
            {{ currentReport.total_sessions }}
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            {{ currentReport.generated_at }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 关键问题统计 -->
        <div class="section">
          <h3>关键问题统计</h3>
          <div class="keywords-grid">
            <el-tag
              v-for="(count, keyword) in currentReport.keywords_json"
              :key="keyword"
              size="large"
              style="margin: 5px"
            >
              {{ keyword }}: {{ count }}次
            </el-tag>
          </div>
        </div>

        <!-- 问题分类 -->
        <div class="section">
          <h3>问题业务分类</h3>
          <div ref="categoryChart" style="width: 100%; height: 300px"></div>
        </div>

        <!-- 今日问题概览 -->
        <div class="section">
          <h3>今日问题概览</h3>
          <div class="overview-content">
            {{ currentReport.long_duration_issues }}
          </div>
        </div>

        <!-- 异常与风险 -->
        <div class="section" v-if="risks.length > 0">
          <h3>异常与风险</h3>
          <el-table :data="risks" border>
            <el-table-column prop="risk_type" label="风险类型" width="150" />
            <el-table-column prop="description" label="问题描述" />
            <el-table-column prop="affected_customers" label="影响客户数" width="120" align="center" />
            <el-table-column prop="urgency" label="紧急程度" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="urgencyType(row.urgency)">{{ row.urgency }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="建议处理方式" width="200" />
          </el-table>
        </div>

        <!-- 行动建议 -->
        <div class="section" v-if="suggestions.length > 0">
          <h3>行动建议</h3>
          <el-timeline class="action-timeline">
            <el-timeline-item
              v-for="(suggestion, index) in suggestions"
              :key="index"
              :timestamp="'建议' + (index + 1)"
              placement="top"
            >
              <div class="suggestion-content">{{ suggestion }}</div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 客服工作量 -->
        <div class="section">
          <h3>客服工作量</h3>
          <div ref="serviceChart" style="width: 100%; height: 300px"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { reportAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const loading = ref(false)
const generating = ref(false)
const reports = ref([])
const selectedDate = ref('')
const dialogVisible = ref(false)
const currentReport = ref(null)

const categoryChart = ref(null)
const serviceChart = ref(null)

const generationTask = ref({
  active: false,
  progress: 0,
  message: '',
  status: ''
})
const taskTimer = ref(null)
const TASK_STORAGE_KEY = 'session_system_daily_report_task_id'

const progressStatus = computed(() => {
  if (generationTask.value.status === 'succeeded') return 'success'
  if (generationTask.value.status === 'failed') return 'exception'
  return undefined
})

const stopTaskPolling = () => {
  if (taskTimer.value) {
    clearTimeout(taskTimer.value)
    taskTimer.value = null
  }
}

const saveActiveTask = (taskId) => {
  if (!taskId) return
  localStorage.setItem(TASK_STORAGE_KEY, taskId)
}

const clearActiveTask = () => {
  localStorage.removeItem(TASK_STORAGE_KEY)
}

const restoreActiveTask = () => {
  const taskId = localStorage.getItem(TASK_STORAGE_KEY)
  if (taskId) {
    pollReportTask(taskId)
  }
}

const setGenerationTask = (task, active = true) => {
  generationTask.value = {
    active,
    progress: task.progress || 0,
    message: task.message || '',
    status: task.status || ''
  }
}

const pollReportTask = async (taskId) => {
  stopTaskPolling()
  try {
    const task = await reportAPI.getReportTask(taskId)
    setGenerationTask(task)

    if (task.status === 'succeeded') {
      clearActiveTask()
      ElMessage.success(task.message || '日报生成成功')
      await loadReports()
      setTimeout(() => {
        generationTask.value.active = false
      }, 1200)
      return
    }

    if (task.status === 'failed') {
      clearActiveTask()
      ElMessage.error(task.error || task.message || '日报生成失败')
      setTimeout(() => {
        generationTask.value.active = false
      }, 2000)
      return
    }

    taskTimer.value = setTimeout(() => pollReportTask(taskId), 2000)
  } catch (error) {
    if (error.response?.status === 404) {
      clearActiveTask()
      generationTask.value.active = false
    }
    ElMessage.error('获取生成进度失败')
    console.error(error)
  }
}


// 从 org_distribution_json 中提取风险和建议
const risks = computed(() => {
  if (!currentReport.value?.org_distribution_json) return []
  return currentReport.value.org_distribution_json.risks || []
})

const suggestions = computed(() => {
  if (!currentReport.value?.org_distribution_json) return []
  return currentReport.value.org_distribution_json.suggestions || []
})

// 紧急程度标签类型
const urgencyType = (urgency) => {
  if (urgency === '高') return 'danger'
  if (urgency === '中') return 'warning'
  return 'info'
}

// 加载日报列表
const loadReports = async () => {
  loading.value = true
  try {
    const data = await reportAPI.getDailyList()
    reports.value = data.reports || []
  } catch (error) {
    ElMessage.error('加载日报列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 生成日报
const generateReport = async () => {
  if (!selectedDate.value) {
    ElMessage.warning('请选择日期')
    return
  }

  stopTaskPolling()
  generating.value = true
  try {
    const task = await reportAPI.createDailyReportTask(selectedDate.value)
    setGenerationTask(task)
    saveActiveTask(task.task_id)
    ElMessage.info('日报生成任务已开始')
    pollReportTask(task.task_id)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '日报任务启动失败')
    console.error(error)
  } finally {
    generating.value = false
  }
}

// 删除日报
const deleteReport = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这份日报吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await reportAPI.deleteDailyReport(row.report_date)
    ElMessage.success('删除成功')
    loadReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 查看详情
const viewReport = async (row) => {
  try {
    const data = await reportAPI.getDailyReport(row.report_date)
    currentReport.value = data
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载日报详情失败')
    console.error(error)
  }
}

// 渲染图表
const renderCharts = () => {
  nextTick(() => {
    setTimeout(() => {
      renderCategoryChart()
      renderServiceChart()
    }, 300)
  })
}

// 问题分类饼图
const renderCategoryChart = () => {
  if (!categoryChart.value || !currentReport.value) return

  const chart = echarts.init(categoryChart.value)
  const data = currentReport.value.category_stats_json || {}

  const chartData = Object.entries(data).map(([name, value]) => ({
    name,
    value: typeof value === 'string' ? parseFloat(value.replace('%', '')) : value
  }))

  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}%'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '问题分类',
        type: 'pie',
        radius: '50%',
        data: chartData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

// 客服工作量柱状图
const renderServiceChart = () => {
  if (!serviceChart.value || !currentReport.value) return

  const chart = echarts.init(serviceChart.value)
  const data = currentReport.value.service_stats_json || {}

  const services = Object.keys(data)
  const counts = Object.values(data)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: services,
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '接待会话数',
        type: 'bar',
        data: counts,
        itemStyle: {
          color: '#409EFF'
        }
      }
    ]
  })
}

onMounted(() => {
  loadReports()
  restoreActiveTask()
})

onBeforeUnmount(() => {
  stopTaskPolling()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-detail {
  padding: 20px;
}

.generation-progress {
  margin-bottom: 18px;
  padding: 14px 16px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: #606266;
  font-size: 14px;
}

.progress-status {
  color: #409EFF;
  font-weight: 600;
}

.section {
  margin-top: 30px;
}

.section h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 18px;
}

.keywords-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.overview-content {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.summary-card {

  background: #ecf5ff;
  border: 1px solid #d9ecff;
  line-height: 1.8;
}
/* 保持原时间线风格，将建议内容约束到居中的阅读列。 */
.action-timeline {
  box-sizing: border-box;
  max-width: 760px;
  margin: 0 auto;
  padding: 0 16px;
  text-align: left;
}

.action-timeline :deep(.el-timeline-item) {
  padding-bottom: 24px;
}

.action-timeline :deep(.el-timeline-item:last-child) {
  padding-bottom: 0;
}

.action-timeline :deep(.el-timeline-item__wrapper) {
  padding-left: 24px;
}

.action-timeline :deep(.el-timeline-item__timestamp) {
  margin-bottom: 6px;
  color: #909399;
  line-height: 1.4;
}

.suggestion-content {
  max-width: 680px;
  color: #303133;
  line-height: 1.8;
  word-break: break-word;
}

@media (max-width: 768px) {
  .action-timeline {
    max-width: none;
    padding: 0 8px;
  }
}
</style>
