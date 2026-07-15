<template>
  <div class="upload-page">
    <el-card>
      <template #header>
        <span>数据上传</span>
      </template>

      <el-steps :active="currentStep" align-center style="margin-bottom: 30px">
        <el-step title="选择文件" :icon="Upload" />
        <el-step title="上传中" :icon="Loading" />
        <el-step title="完成" :icon="Select" />
      </el-steps>

      <!-- 上传区域 -->
      <div v-if="currentStep === 0" class="upload-area">
        <el-card>
          <template #header>
            <span>选择会话记录文件</span>
          </template>
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".xlsx,.xls"
            :file-list="fileList"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽 Excel 文件到此处 或 <em>点击选择</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx 或 .xls 格式
              </div>
            </template>
          </el-upload>
        </el-card>

        <!-- 文件信息 -->
        <div v-if="file" class="file-info">
          <el-descriptions title="文件信息" :column="1" border>
            <el-descriptions-item label="文件名">{{ file.name }}</el-descriptions-item>
            <el-descriptions-item label="文件大小">{{ formatFileSize(file.size) }}</el-descriptions-item>
          </el-descriptions>

          <div style="margin-top: 20px; text-align: center">
            <el-button type="primary" size="large" @click="startUpload" :loading="uploading">
              <el-icon><Upload /></el-icon>
              开始上传
            </el-button>
          </div>
        </div>
      </div>

      <!-- 上传中 -->
      <div v-if="currentStep === 1" class="uploading-area">
        <el-result icon="loading" title="正在处理" :sub-title="uploadMessage">
          <template #extra>
            <el-progress :percentage="uploadProgress" />
          </template>
        </el-result>
      </div>

      <!-- 完成 -->
      <div v-if="currentStep === 2" class="result-area">
        <el-result
          :icon="uploadSuccess ? 'success' : 'error'"
          :title="uploadSuccess ? '上传成功' : '上传失败'"
          :sub-title="uploadMessage"
        >
          <template #extra>
            <div v-if="uploadSuccess && uploadResult" class="result-stats">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="导入会话数">{{ uploadResult.total_sessions }}</el-descriptions-item>
                <el-descriptions-item label="导入消息数">{{ uploadResult.message_count }}</el-descriptions-item>
                <el-descriptions-item label="跳过重复">{{ uploadResult.skipped_count }}</el-descriptions-item>
                <el-descriptions-item label="错误数">{{ uploadResult.error_count || 0 }}</el-descriptions-item>
              </el-descriptions>

              <div style="margin-top: 30px">
                <el-button type="primary" @click="goToSessions">前往会话列表</el-button>
                <el-button @click="reset">继续上传</el-button>
              </div>
            </div>
            <div v-else>
              <el-button type="primary" @click="reset">重新上传</el-button>
            </div>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Upload, Loading, Select } from '@element-plus/icons-vue'
import { uploadAPI } from '../api'

const router = useRouter()
const currentStep = ref(0)
const uploading = ref(false)
const uploadRef = ref(null)
const file = ref(null)
const fileList = ref([])
const uploadProgress = ref(0)
const uploadMessage = ref('')
const uploadSuccess = ref(false)
const uploadResult = ref(null)

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
  fileList.value = [uploadFile]
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const startUpload = async () => {
  if (!file.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  currentStep.value = 1
  uploading.value = true
  uploadProgress.value = 0
  uploadMessage.value = '正在上传并解析文件...'

  try {
    const formData = new FormData()
    formData.append('file', file.value)

    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 300)

    const response = await uploadAPI.upload(formData)

    clearInterval(progressInterval)
    uploadProgress.value = 100
    uploadMessage.value = response.message || '导入成功'
    uploadSuccess.value = true
    uploadResult.value = response

    setTimeout(() => {
      currentStep.value = 2
    }, 500)
  } catch (error) {
    uploadProgress.value = 0
    uploadMessage.value = error.response?.data?.detail || '上传失败，请重试'
    uploadSuccess.value = false
    currentStep.value = 2
  } finally {
    uploading.value = false
  }
}

const reset = () => {
  currentStep.value = 0
  file.value = null
  fileList.value = []
  uploadProgress.value = 0
  uploadMessage.value = ''
  uploadSuccess.value = false
  uploadResult.value = null
  uploadRef.value?.clearFiles()
}

const goToSessions = () => {
  router.push('/sessions')
}
</script>

<style scoped>
.upload-page {
  max-width: 1000px;
  margin: 0 auto;
}

.upload-area,
.uploading-area,
.result-area {
  padding: 40px 20px;
}

.file-info {
  margin-top: 30px;
}

.result-stats {
  max-width: 600px;
  margin: 0 auto;
}

.upload-demo {
  width: 100%;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
