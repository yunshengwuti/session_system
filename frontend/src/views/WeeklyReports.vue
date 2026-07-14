<template>
  <div class="weekly-reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>周报管理</span>
          <div>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              :unlink-panels="false"
              style="margin-right: 10px"
              @change="validateDateRange"
            />
            <el-text v-if="dateRangeError" type="danger" style="margin-right: 10px; font-size: 12px">
              {{ dateRangeError }}
            </el-text>
            <el-button type="primary" @click="generateReport" :loading="generating" :disabled="!!dateRangeError || !dateRange || generationTask.active">
              <el-icon><Plus /></el-icon>
              生成周报
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

      <!-- 周报列表 -->
      <el-table v-loading="loading" :data="reports" style="width: 100%">
        <el-table-column label="周期" width="280" align="center">
          <template #default="{ row }">
            {{ row.week_start_date }} 至 {{ row.week_end_date }}
          </template>
        </el-table-column>
        <el-table-column prop="total_sessions" label="总会话数" width="150" align="center" />
        <el-table-column label="生成时间" width="220" align="center">
          <template #default="{ row }">
            {{ new Date(row.generated_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewReport(row)">查看详情</el-button>
            <el-button type="danger" link @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 周报详情对话框 -->
    <el-dialog v-model="showDetail" :title="`周报详情 (${currentReport?.week_start_date} 至 ${currentReport?.week_end_date})`" width="80%" top="5vh">
      <div v-if="currentReport" class="report-detail">

        <!-- 高频问题TOP10 -->
        <div class="section">
          <h3>高频问题TOP10</h3>
          <el-table :data="topProblems" border stripe>
            <el-table-column type="index" label="排名" width="80" align="center" />
            <el-table-column prop="problem" label="问题描述" />
            <el-table-column prop="count" label="累计次数" width="120" align="center" />
          </el-table>
        </div>

        <!-- 问题业务分类 -->
        <div class="section">
          <h3>问题业务分类</h3>
          <div ref="categoryChart" style="width: 100%; height: 300px"></div>
        </div>

        <!-- 每日趋势 -->
        <div class="section" v-if="currentReport.daily_trend_json && currentReport.daily_trend_json.length > 0">
          <h3>每日趋势</h3>
          <div ref="trendChart" style="width: 100%; height: 300px"></div>
        </div>

        <!-- 重点风险 -->
        <div class="section" v-if="keyRisks.length > 0">
          <h3>重点风险</h3>
          <el-table :data="keyRisks" border>
            <el-table-column prop="risk_type" label="风险类型" width="150" />
            <el-table-column prop="description" label="问题描述" />
            <el-table-column prop="suggestion" label="建议" width="200" />
          </el-table>
        </div>

        <!-- 典型案例 -->
        <div class="section" v-if="cases.length > 0">
          <h3>典型案例</h3>
          <div v-for="(caseItem, index) in cases" :key="index" class="case-item">
            <div class="case-title">{{ caseItem.title }}</div>
            <div class="case-description">{{ caseItem.description }}</div>
            <div class="case-outcome" v-if="caseItem.outcome">处理结果：{{ caseItem.outcome }}</div>
          </div>
        </div>

        <!-- 下周改进计划 -->
        <div class="section" v-if="nextWeekPlan.length > 0">
          <h3>下周改进计划</h3>
          <div v-for="(plan, index) in nextWeekPlan" :key="index" class="plan-item">
            <span class="plan-number">{{ index + 1 }}</span>
            <span class="plan-text">{{ plan }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { reportAPI } from '@/api/index'

const dateRange = ref(null)
const dateRangeError = ref('')
const loading = ref(false)
const generating = ref(false)
const reports = ref([])
const currentReport = ref(null)
const showDetail = ref(false)
const categoryChart = ref(null)
const trendChart = ref(null)

const generationTask = ref({
  active: false,
  progress: 0,
  message: '',
  status: ''
})
const taskTimer = ref(null)

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
      ElMessage.success(task.message || '周报生成成功')
      await loadReports()
      setTimeout(() => {
        generationTask.value.active = false
      }, 1200)
      return
    }

    if (task.status === 'failed') {
      ElMessage.error(task.error || task.message || '周报生成失败')
      return
    }

    taskTimer.value = setTimeout(() => pollReportTask(taskId), 2000)
  } catch (error) {
    ElMessage.error('获取生成进度失败')
    console.error(error)
  }
}


// 验证日期范围（3-7天）
const validateDateRange = () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    dateRangeError.value = ''
    return
  }

  const [start, end] = dateRange.value
  const startDate = new Date(start)
  const endDate = new Date(end)
  const daysDiff = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1

  if (daysDiff < 3) {
    dateRangeError.value = '时间段至少需要3天'
  } else if (daysDiff > 7) {
    dateRangeError.value = '时间段最多7天'
  } else {
    dateRangeError.value = ''
  }
}

// 加载周报列表
const loadReports = async () => {
  loading.value = true
  try {
    const data = await reportAPI.getWeeklyReports()
    reports.value = data
  } catch (error) {
    ElMessage.error('加载周报列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 生成周报
const generateReport = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择日期范围')
    return
  }

  if (dateRangeError.value) {
    ElMessage.warning(dateRangeError.value)
    return
  }

  const [startDate, endDate] = dateRange.value

  stopTaskPolling()
  generating.value = true
  try {
    const task = await reportAPI.createWeeklyReportTask(startDate, endDate)
    setGenerationTask(task)
    ElMessage.info('周报生成任务已开始')
    pollReportTask(task.task_id)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '周报任务启动失败')
    console.error(error)
  } finally {
    generating.value = false
  }
}

// 查看周报详情
const viewReport = async (row) => {
  currentReport.value = row
  showDetail.value = true

  await nextTick()
  renderCategoryChart()
  renderTrendChart()
}

// 删除周报
const deleteReport = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这份周报吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await reportAPI.deleteWeeklyReport(row.week_start_date)
    ElMessage.success('删除成功')
    loadReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

// 计算属性
const dailyAvg = computed(() => {
  if (!currentReport.value) return 0
  const days = reportDays.value
  return days > 0 ? (currentReport.value.total_sessions / days).toFixed(1) : 0
})

const reportDays = computed(() => {
  if (!currentReport.value) return 0
  return currentReport.value.daily_trend_json?.length || 0
})

const topProblems = computed(() => {
  if (!currentReport.value?.keywords_json) return []
  return Object.entries(currentReport.value.keywords_json)
    .map(([problem, count]) => ({ problem, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const trends = computed(() => {
  return currentReport.value?.org_distribution_json?.trends || ''
})

const keyRisks = computed(() => {
  return currentReport.value?.org_distribution_json?.key_risks || []
})

const cases = computed(() => {
  return currentReport.value?.org_distribution_json?.cases || []
})

const nextWeekPlan = computed(() => {
  return currentReport.value?.org_distribution_json?.next_week_plan || []
})

// 渲染分类饼图
const renderCategoryChart = () => {
  if (!categoryChart.value || !currentReport.value?.category_stats_json) return

  const chart = echarts.init(categoryChart.value)
  const data = Object.entries(currentReport.value.category_stats_json).map(
    ([name, value]) => ({ name, value })
  )

  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        type: 'pie',
        radius: '50%',
        data,
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

// 渲染趋势折线图
const renderTrendChart = () => {
  if (!trendChart.value || !currentReport.value?.daily_trend_json) return

  const chart = echarts.init(trendChart.value)
  const trendData = currentReport.value.daily_trend_json

  // 获取星期
  const getWeekday = (dateStr) => {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const date = new Date(dateStr)
    return weekdays[date.getDay()]
  }

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const data = params[0]
        const dateStr = trendData[data.dataIndex].date
        const weekday = getWeekday(dateStr)
        return `${dateStr} (${weekday})<br/>会话数: ${data.value}`
      }
    },
    xAxis: {
      type: 'category',
      data: trendData.map(d => `${d.date}\n${getWeekday(d.date)}`),
      axisLabel: {
        rotate: 0,
        interval: 0,
        fontSize: 11
      }
    },
    yAxis: { type: 'value', name: '会话数' },
    series: [
      {
        type: 'line',
        data: trendData.map(d => d.sessions),
        smooth: true,
        itemStyle: { color: '#409EFF' },
        areaStyle: { color: 'rgba(64, 158, 255, 0.2)' }
      }
    ]
  })
}

onMounted(() => {
  loadReports()
})

onBeforeUnmount(() => {
  stopTaskPolling()
})
</script>

<style scoped>
.weekly-reports {
  max-width: 1400px;
  margin: 0 auto;
}

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

.section:first-child {
  margin-top: 0;
}

.section h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 18px;
  font-weight: bold;
}

.overview-content {
  line-height: 1.8;
  white-space: pre-wrap;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

/* 典型案例样式 */
.case-item {
  padding: 15px;
  margin-bottom: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409EFF;
}

.case-title {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
  margin-bottom: 10px;
}

.case-description {
  line-height: 1.8;
  color: #606266;
  margin-bottom: 8px;
}

.case-outcome {
  color: #67C23A;
  font-size: 14px;
}

/* 改进计划样式 */
.plan-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 15px;
  margin-bottom: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.plan-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  background-color: #409EFF;
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: bold;
  margin-right: 12px;
  flex-shrink: 0;
}

.plan-text {
  line-height: 1.8;
  color: #303133;
  flex: 1;
}

/* 日历中周末样式 */
/* 周六（每行第7列）和周日（每行第1列）背景色 */
:deep(.el-date-table tr td:first-child:not(.prev-month):not(.next-month) .el-date-table-cell__text),
:deep(.el-date-table tr td:last-child:not(.prev-month):not(.next-month) .el-date-table-cell__text) {
  color: #C0C4CC !important;
}

:deep(.el-date-table tr td:first-child:not(.prev-month):not(.next-month)),
:deep(.el-date-table tr td:last-child:not(.prev-month):not(.next-month)) {
  background-color: #f5f7fa !important;
}

/* 周末单元格 */
:deep(.el-date-table tr td:first-child .el-date-table-cell),
:deep(.el-date-table tr td:last-child .el-date-table-cell) {
  background-color: #fafafa;
}

/* 周末选中范围内也保持区分 */
:deep(.el-date-table tr td.in-range:first-child .el-date-table-cell),
:deep(.el-date-table tr td.in-range:last-child .el-date-table-cell) {
  background-color: #f0f0f0 !important;
}

</style>
