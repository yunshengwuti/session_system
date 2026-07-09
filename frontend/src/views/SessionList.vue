<template>
  <div class="session-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>会话列表</span>
          <el-button type="primary" @click="loadSessions">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-container">
        <div class="filter-row">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="日期">
              <el-date-picker
                v-model="filters.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                :unlink-panels="false"
                style="width: 260px"
              />
            </el-form-item>
            <el-form-item label="客户名称">
              <el-input
                v-model="filters.customer"
                placeholder="输入客户名称"
                clearable
                style="width: 150px"
              />
            </el-form-item>
            <el-form-item label="机构名称">
              <el-input
                v-model="filters.org"
                placeholder="输入机构名称"
                clearable
                style="width: 150px"
              />
            </el-form-item>
          </el-form>
        </div>
        <div class="filter-row-second">
          <el-form :inline="true" class="filter-form-left">
            <el-form-item label="客服">
              <el-input
                v-model="filters.service"
                placeholder="输入客服名称"
                clearable
                style="width: 150px"
              />
            </el-form-item>
          </el-form>
          <div class="filter-actions-center">
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
      </div>

      <!-- 会话表格 -->
      <el-table
        v-loading="loading"
        :data="sessions"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="customer_name" label="客户名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="org_name" label="机构名称" width="150" show-overflow-tooltip />
        <el-table-column prop="customer_service" label="客服" width="180" show-overflow-tooltip />
        <el-table-column label="时长" width="120" align="center">
          <template #default="{ row }">
            {{ formatDuration(row.duration_seconds) }}
          </template>
        </el-table-column>
        <el-table-column prop="session_date" label="日期" width="120" align="center" />
        <el-table-column label="消息数" width="100" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.message_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="pagination.page"
        :page-size="10"
        :total="total"
        layout="total, prev, pager, next, jumper"
        @current-change="loadSessions"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { sessionAPI } from '../api'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const sessions = ref([])
const total = ref(0)

// 获取今天日期
const getTodayDate = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const filters = reactive({
  dateRange: null,  // 改为日期范围
  customer: '',
  org: '',
  service: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10
})

const stats = reactive({
  total: 0,
  valid: 0,
  today: 0,
  avgDuration: 0
})

// 点击查询按钮
const handleSearch = () => {
  pagination.page = 1  // 重置到第一页
  loadSessions()
}

// 加载会话列表
const loadSessions = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    // 只添加有值的筛选参数
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    if (filters.customer) params.customer_name = filters.customer
    if (filters.org) params.org_name = filters.org
    if (filters.service) params.customer_service = filters.service

    const data = await sessionAPI.getList(params)
    sessions.value = data.sessions || []
    total.value = data.total || 0

    // 更新统计数据
    stats.total = data.total || 0
    stats.valid = data.filtered_sessions || 0
  } catch (error) {
    ElMessage.error('加载会话列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilters = () => {
  filters.dateRange = null
  filters.customer = ''
  filters.org = ''
  filters.service = ''
  pagination.page = 1
  loadSessions()
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0秒'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return minutes > 0 ? `${minutes}分${secs}秒` : `${secs}秒`
}

// 查看详情
const viewDetail = (row) => {
  router.push(`/sessions/${row.session_id}`)
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.session-list {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-container {
  margin-bottom: 20px;
  position: relative;
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.filter-row-second {
  display: flex;
  align-items: center;
  position: relative;
}

.filter-form {
  margin: 0;
}

.filter-form-left {
  margin: 0;
}

.filter-actions-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
}

.stats-row {
  margin: 20px 0;
}

/* 日历中周末样式 */
:deep(.el-date-table tr td:first-child .el-date-table-cell),
:deep(.el-date-table tr td:last-child .el-date-table-cell) {
  background-color: #fafafa;
}

:deep(.el-date-table tr td:first-child:not(.prev-month):not(.next-month) .el-date-table-cell__text),
:deep(.el-date-table tr td:last-child:not(.prev-month):not(.next-month) .el-date-table-cell__text) {
  color: #C0C4CC !important;
}

:deep(.el-date-table tr td.in-range:first-child .el-date-table-cell),
:deep(.el-date-table tr td.in-range:last-child .el-date-table-cell) {
  background-color: #f0f0f0 !important;
}
</style>
