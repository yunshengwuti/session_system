<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1>会话数据管理系统</h1>
        <el-menu
          mode="horizontal"
          :default-active="$route.path"
          router
          class="app-menu"
        >
          <el-menu-item index="/sessions">
            <el-icon><ChatDotRound /></el-icon>
            <span>会话列表</span>
          </el-menu-item>
          <el-menu-item index="/reports/daily">
            <el-icon><Document /></el-icon>
            <span>日报管理</span>
          </el-menu-item>
          <el-menu-item index="/reports/weekly">
            <el-icon><Calendar /></el-icon>
            <span>周报管理</span>
          </el-menu-item>
          <el-menu-item index="/upload">
            <el-icon><Upload /></el-icon>
            <span>数据上传</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ChatDotRound, Document, Calendar, Upload } from '@element-plus/icons-vue'
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 40px;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 100%;
  gap: 40px;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
  color: #409eff;
}

.app-menu {
  flex: 1;
  border-bottom: none;
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
