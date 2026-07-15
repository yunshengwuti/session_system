import axios from 'axios'

const DEFAULT_TIMEOUT = 60000
const RETRY_DELAY = 3000

const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: DEFAULT_TIMEOUT,
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  async error => {
    const config = error.config || {}
    const isGet = (config.method || 'get').toLowerCase() === 'get'
    const isRetryable = !error.response || error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK'

    if (isGet && isRetryable && !config.__retried) {
      config.__retried = true
      await wait(RETRY_DELAY)
      return api(config)
    }

    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 会话相关接口
export const sessionAPI = {
  // 获取会话列表
  getList(params) {
    return api.get('/sessions', { params })
  },

  // 获取会话详情
  getDetail(sessionId) {
    return api.get(`/sessions/${sessionId}`)
  },
}

// 数据管理接口
export const managementAPI = {
  getStorage() {
    return api.get('/management/storage')
  },

  previewCleanup(startDate, endDate) {
    return api.get('/management/cleanup/preview', {
      params: { start_date: startDate, end_date: endDate }
    })
  },

  clearRange(startDate, endDate) {
    return api.delete('/management/cleanup/range', {
      params: { start_date: startDate, end_date: endDate, confirm: 'CLEAR_RANGE' }
    })
  },
}

// 上传相关接口
export const uploadAPI = {
  // 上传 Excel 文件
  upload(formData) {
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}

// 报告相关接口
export const reportAPI = {
  // 获取日报列表
  getDailyList() {
    return api.get('/reports/daily/list')
  },

  // 获取日报详情
  getDailyReport(date) {
    return api.get(`/reports/daily/${date}`)
  },

  // 生成日报
  createDailyReport(date) {
    return api.post(`/reports/daily?report_date=${date}`, null, {
      timeout: 10 * 60 * 1000
    })
  },

  // 启动日报后台生成任务
  createDailyReportTask(date) {
    return api.post(`/reports/daily/task?report_date=${date}`)
  },

  // 导出日报 Word
  exportDailyReport(date) {
    return api.get(`/reports/daily/${date}/export`, { responseType: 'blob' })
  },

  // 删除日报
  deleteDailyReport(date) {
    return api.delete(`/reports/daily/${date}`)
  },

  // 查询报告生成任务
  getReportTask(taskId) {
    return api.get(`/reports/tasks/${taskId}`)
  },

  // 获取周报列表
  getWeeklyReports() {
    return api.get('/reports/weekly/list')
  },

  // 获取周报详情
  getWeeklyReport(weekStartDate) {
    return api.get(`/reports/weekly/${weekStartDate}`)
  },

  // 生成周报（新版：支持自定义日期范围）
  createWeeklyReport(startDate, endDate) {
    return api.post(`/reports/weekly?start_date=${startDate}&end_date=${endDate}`, null, {
      timeout: 15 * 60 * 1000
    })
  },

  // 启动周报后台生成任务
  createWeeklyReportTask(startDate, endDate) {
    return api.post(`/reports/weekly/task?start_date=${startDate}&end_date=${endDate}`)
  },

  // 导出周报 Word
  exportWeeklyReport(weekStartDate) {
    return api.get(`/reports/weekly/${weekStartDate}/export`, { responseType: 'blob' })
  },

  // 删除周报
  deleteWeeklyReport(weekStartDate) {
    return api.delete(`/reports/weekly/${weekStartDate}`)
  },
}

export default api
