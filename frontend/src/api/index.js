import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
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
    return api.post(`/reports/daily?report_date=${date}`)
  },

  // 删除日报
  deleteDailyReport(date) {
    return api.delete(`/reports/daily/${date}`)
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
    return api.post(`/reports/weekly?start_date=${startDate}&end_date=${endDate}`)
  },

  // 删除周报
  deleteWeeklyReport(weekStartDate) {
    return api.delete(`/reports/weekly/${weekStartDate}`)
  },
}

export default api
