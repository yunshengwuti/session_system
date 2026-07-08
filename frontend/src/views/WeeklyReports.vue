<template>
  <div class="weekly-reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>周报管理</span>
          <div>
            <el-date-picker
              v-model="selectedWeek"
              type="week"
              placeholder="选择周"
              format="YYYY 第 ww 周"
              value-format="YYYY-MM-DD"
              style="margin-right: 10px"
            />
            <el-button type="primary" @click="generateReport" :loading="generating">
              <el-icon><Plus /></el-icon>
              生成周报
            </el-button>
          </div>
        </div>
      </template>

      <!-- 周报列表 -->
      <el-table v-loading="loading" :data="reports" style="width: 100%">
        <el-table-column label="周" width="200">
          <template #default="{ row }">
            {{ row.week_start_date }} 至 {{ row.week_end_date }}
          </template>
        </el-table-column>
        <el-table-column prop="total_sessions" label="会话总数" width="120" />
        <el-table-column label="日均会话" width="120">
          <template #default="{ row }">
            {{ Math.round(row.total_sessions / 7) }}
          </template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewReport(row)">
              查看详情
            </el-button>
            <el-button type="danger" link @click="deleteReport(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 周报详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="周报详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="currentReport" class="report-detail">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="周期">
            {{ currentReport.week_start_date }} 至 {{ currentReport.week_end_date }}
          </el-descriptions-item>
          <el-descriptions-item label="会话总数">
            {{ currentReport.total_sessions }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 每日趋势图 -->
        <div class="section">
          <h3>每日会话趋势</h3>
          <div ref="trendChart" style="width: 100%; height: 300px"></div>
        </div>

        <!-- 问题分类 -->
        <div class="section">
          <h3>问题分类统计</h3>
          <div ref="categoryChart" style="width: 100%; height: 300px"></div>
        </div>

        <!-- AI 总结 -->
        <div class="section">
          <h3>本周总结</h3>
          <el-alert
            :title="currentReport.ai_summary"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { reportAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const loading = ref(false)
const generating = ref(false)
const reports = ref([])
const selectedWeek = ref('')
const dialogVisible = ref(false)
const currentReport = ref(null)

const trendChart = ref(null)
const categoryChart = ref(null)

const loadReports = async () => {
  loading.value = true
  try {
    const data = await reportAPI.getWeeklyList()
    reports.value = data.reports || []
  } catch (error) {
    ElMessage.error('加载周报列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const generateReport = async () => {
  if (!selectedWeek.value) {
    ElMessage.warning('请选择周')
    return
  }

  generating.value = true
  try {
    await reportAPI.createWeeklyReport(selectedWeek.value)
    ElMessage.success('周报生成成功')
    loadReports()
  } catch (error) {
    ElMessage.error('周报生成失败')
    console.error(error)
  } finally {
    generating.value = false
  }
}

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

const viewReport = async (row) => {
  try {
    const data = await reportAPI.getWeeklyReport(row.week_start_date)
    currentReport.value = data
    dialogVisible.value = true

    await nextTick()
    renderCharts()
  } catch (error) {
    ElMessage.error('加载周报详情失败')
    console.error(error)
  }
}

const renderCharts = () => {
  if (!currentReport.value) return

  // 每日趋势折线图
  if (trendChart.value && currentReport.value.daily_trend_json) {
    const chart = echarts.init(trendChart.value)
    const trend = currentReport.value.daily_trend_json || []
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trend.map(item => item.date)
      },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'line',
          data: trend.map(item => item.sessions),
          smooth: true,
          itemStyle: { color: '#409eff' }
        }
      ]
    })
  }

  // 问题分类饼图
  if (categoryChart.value) {
    const chart = echarts.init(categoryChart.value)
    const data = Object.entries(currentReport.value.category_stats_json || {}).map(
      ([name, value]) => ({ name, value })
    )
    chart.setOption({
      tooltip: { trigger: 'item' },
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
}

onMounted(() => {
  loadReports()
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

.section {
  margin-top: 30px;
}

.section h3 {
  margin-bottom: 15px;
  color: #303133;
}
</style>
