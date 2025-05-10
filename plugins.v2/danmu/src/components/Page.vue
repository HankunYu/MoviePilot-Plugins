<template>
  <div class="plugin-page">
    <v-card flat class="rounded border">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-video" class="mr-2" color="primary" size="small" />
        <span>弹幕刮削</span>
      </v-card-title>
      
      <v-card-text class="px-3 py-2">
        <v-alert v-if="error" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ error }}</v-alert>
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>

        <!-- 状态卡片 -->
        <v-card flat class="rounded mb-3 border status-card">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-information" class="mr-2" color="primary" size="small" />
            <span>插件状态</span>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12" md="6">
                <div class="status-item d-flex align-center py-2">
                  <v-icon icon="mdi-power" size="small" :color="status.enabled ? 'success' : 'grey'" class="mr-3"></v-icon>
                  <div class="status-content flex-grow-1">
                    <div class="text-subtitle-2">插件状态</div>
                    <div class="text-caption text-grey">{{ status.enabled ? '已启用' : '已禁用' }}</div>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- 刮削状态 -->
        <v-card v-if="scrapingStatus.running" flat class="rounded mb-3 border status-card">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-progress-clock" class="mr-2" color="primary" size="small" />
            <span>刮削进度</span>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12">
                <div class="status-item d-flex align-center py-2">
                  <v-icon icon="mdi-file-document" size="small" color="primary" class="mr-3"></v-icon>
                  <div class="status-content flex-grow-1">
                    <div class="text-subtitle-2">当前文件</div>
                    <div class="text-caption text-grey">{{ scrapingStatus.current_file || '等待中...' }}</div>
                  </div>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="status-item d-flex align-center py-2">
                  <v-icon icon="mdi-counter" size="small" color="primary" class="mr-3"></v-icon>
                  <div class="status-content flex-grow-1">
                    <div class="text-subtitle-2">处理进度</div>
                    <div class="text-caption text-grey">
                      {{ scrapingStatus.processed }}/{{ scrapingStatus.total }} 个文件
                      ({{ scrapingStatus.success }} 成功, {{ scrapingStatus.failed }} 失败)
                    </div>
                  </div>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="status-item d-flex align-center py-2">
                  <v-icon icon="mdi-clock-outline" size="small" color="primary" class="mr-3"></v-icon>
                  <div class="status-content flex-grow-1">
                    <div class="text-subtitle-2">运行时间</div>
                    <div class="text-caption text-grey">{{ formatDuration(scrapingStatus.duration) }}</div>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- 目录浏览 -->
        <v-card flat class="rounded mb-3 border status-card">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-folder" class="mr-2" color="primary" size="small" />
            <span>目录浏览</span>
            <v-spacer></v-spacer>
            <v-text-field
              v-model="searchKeyword"
              density="compact"
              variant="outlined"
              hide-details
              placeholder="仅过滤目录"
              prepend-inner-icon="mdi-magnify"
              class="search-field"
              style="max-width: 200px;"
            ></v-text-field>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12">
                <div v-if="directoryTree" class="directory-tree">
                  <div v-for="(item, index) in directoryTree.children" :key="index" 
                       class="tree-item"
                       :class="{ 'hidden': searchKeyword && item.type === 'directory' && !isDirectoryMatch(item, false) }">
                    <!-- 目录 -->
                    <div v-if="item.type === 'directory'" class="directory-item">
                      <div class="d-flex align-center py-2" @click="toggleDirectory(item)">
                        <v-icon :icon="item.expanded ? 'mdi-folder-open' : 'mdi-folder'" size="small" color="primary" class="mr-2"></v-icon>
                        <span class="text-subtitle-2">{{ item.name }}</span>
                      </div>
                      <!-- 子目录和文件 -->
                      <div v-if="item.expanded" class="pl-4">
                        <div v-for="(child, childIndex) in item.children" :key="childIndex" 
                             class="tree-item"
                             :class="{ 'hidden': searchKeyword && child.type === 'directory' && !isDirectoryMatch(child, isDirectoryMatch(item, false)) }">
                          <!-- 媒体文件 -->
                          <div v-if="child.type === 'media'" class="media-item d-flex align-center py-2">
                            <v-icon icon="mdi-video" size="small" color="info" class="mr-2"></v-icon>
                            <div class="flex-grow-1">
                              <div class="d-flex align-center">
                                <span class="text-subtitle-2">{{ child.name }}</span>
                                <v-chip size="small" color="info" class="ml-2" v-if="child.danmu_count > 0">
                                  弹幕: {{ child.danmu_count }}
                                </v-chip>
                                <v-chip size="small" color="grey" class="ml-2" v-else>
                                  无弹幕
                                </v-chip>
                              </div>
                            </div>
                            <v-btn
                              color="primary"
                              size="small"
                              variant="text"
                              :loading="child.generating"
                              @click="generateDanmu(child, item)"
                            >
                              <v-icon icon="mdi-download" size="small" class="mr-1"></v-icon>
                              刮削
                            </v-btn>
                          </div>
                          <!-- 子目录 -->
                          <div v-else-if="child.type === 'directory'" class="directory-item">
                            <div class="d-flex align-center py-2" @click="toggleDirectory(child)">
                              <v-icon :icon="child.expanded ? 'mdi-folder-open' : 'mdi-folder'" size="small" color="primary" class="mr-2"></v-icon>
                              <span class="text-subtitle-2">{{ child.name }}</span>
                            </div>
                            <!-- 递归显示子目录内容 -->
                            <div v-if="child.expanded" class="pl-4">
                              <div v-for="(grandChild, grandChildIndex) in child.children" :key="grandChildIndex" class="tree-item">
                                <!-- 媒体文件 -->
                                <div v-if="grandChild.type === 'media'" class="media-item d-flex align-center py-2">
                                  <v-icon icon="mdi-video" size="small" color="info" class="mr-2"></v-icon>
                                  <div class="flex-grow-1">
                                    <div class="d-flex align-center">
                                      <span class="text-subtitle-2">{{ grandChild.name }}</span>
                                      <v-chip size="small" color="info" class="ml-2" v-if="grandChild.danmu_count > 0">
                                        弹幕: {{ grandChild.danmu_count }}
                                      </v-chip>
                                      <v-chip size="small" color="grey" class="ml-2" v-else>
                                        无弹幕
                                      </v-chip>
                                    </div>
                                  </div>
                                  <v-btn
                                    color="primary"
                                    size="small"
                                    variant="text"
                                    :loading="grandChild.generating"
                                    @click="generateDanmu(grandChild, child)"
                                  >
                                    <v-icon icon="mdi-download" size="small" class="mr-1"></v-icon>
                                    刮削
                                  </v-btn>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else-if="!directoryTree && error" class="text-center py-4">
                  <v-alert type="error" density="compact" class="mb-2 text-caption" variant="tonal">{{ error }}</v-alert>
                </div>
                <div v-else class="text-center py-4">
                  <v-alert type="info" density="compact" class="mb-2 text-caption" variant="tonal">请先在配置中设置刮削路径</v-alert>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="px-2 py-1">
        <v-btn color="info" @click="emit('switch')" prepend-icon="mdi-cog" variant="text" size="small">配置</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="grey" @click="emit('close')" prepend-icon="mdi-close" variant="text" size="small">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';

const props = defineProps({
  api: { 
    type: [Object, Function],
    required: true,
  }
});

const emit = defineEmits(['close', 'switch']);

// 状态变量
const error = ref(null);
const successMessage = ref(null);
const running = ref(false);
let statusTimer = null;

// 状态数据
const status = reactive({
  enabled: false
});

// 刮削状态
const scrapingStatus = reactive({
  running: false,
  total: 0,
  processed: 0,
  success: 0,
  failed: 0,
  current_file: "",
  duration: 0
});

// 目录树数据
const directoryTree = ref(null);

// 搜索关键字
const searchKeyword = ref('');

// 检查目录是否匹配关键字
function isDirectoryMatch(item, parentMatched) {
  if (!searchKeyword.value) return true;
  if (item.type !== 'directory') return true;
  
  // 如果父目录已匹配，则子目录也显示
  if (parentMatched) return true;
  
  // 检查当前目录是否匹配
  return item.name.toLowerCase().includes(searchKeyword.value.toLowerCase());
}

// 格式化时间
function formatDuration(seconds) {
  if (!seconds) return '0秒';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const parts = [];
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分钟`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`);
  return parts.join('');
}

// 获取状态
async function getStatus() {
  try {
    const data = await props.api.get('plugin/Danmu/status');
    if (data) {
      Object.assign(status, {
        enabled: data.enabled
      });
      
      Object.assign(scrapingStatus, {
        running: data.running,
        total: data.total,
        processed: data.processed,
        success: data.success,
        failed: data.failed,
        current_file: data.current_file,
        duration: data.duration
      });
      
      running.value = data.running;
    }
  } catch (err) {
    console.error('获取状态失败:', err);
    error.value = '获取状态失败，请检查网络或API';
  }
}

// 切换目录展开状态
function toggleDirectory(item) {
  if (!item.expanded) {
    // 展开目录时加载子目录内容
    loadDirectoryContent(item);
  }
  item.expanded = !item.expanded;
}

// 加载目录内容
async function loadDirectoryContent(item) {
  try {
    const data = await props.api.get('plugin/Danmu/scan_path', {
      params: {
        path: item.path
      }
    });
    if (data && data.success) {
      item.children = data.data.children;
    }
  } catch (err) {
    console.error('加载目录内容失败:', err);
    error.value = '加载目录内容失败，请检查网络或API';
  }
}

// 生成弹幕
async function generateDanmu(item, parent = null) {
  error.value = null; // 清空旧错误
  try {
    item.generating = true;
    const result = await props.api.get('plugin/Danmu/generate_danmu', {
      params: { file_path: item.path }
    });
    if (result && result.success) {
      successMessage.value = '弹幕生成成功';
      if (parent) {
        await loadDirectoryContent(parent);
      } else {
        await loadDirectoryContent(directoryTree.value);
      }
    } else {
      console.log('后端返回：', result);
      error.value = result?.message || '弹幕生成失败';
    }
  } catch (err) {
    error.value = '生成弹幕失败，请检查网络或API';
  } finally {
    item.generating = false;
  }
}

// 初始化
onMounted(async () => {
  await getStatus();
  try {
    const data = await props.api.get('plugin/Danmu/scan_path');
    if (data && data.success) {
      directoryTree.value = data.data;
    }
  } catch (err) {
    console.error('加载目录结构失败:', err);
    error.value = '加载目录结构失败，请检查网络或API';
  }
});

// 清理
onUnmounted(() => {
  // 移除不需要的清理代码
});
</script>

<style scoped>
.plugin-page {
  max-width: 80rem;
  margin: 0 auto;
  padding: 0.5rem;
}

.bg-primary-lighten-5 {
  background-color: rgba(var(--v-theme-primary), 0.07);
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.status-card {
  background-image: linear-gradient(to right, rgba(var(--v-theme-surface), 0.98), rgba(var(--v-theme-surface), 0.95)), 
                    repeating-linear-gradient(45deg, rgba(var(--v-theme-primary), 0.03), rgba(var(--v-theme-primary), 0.03) 10px, transparent 10px, transparent 20px);
  background-attachment: fixed;
  box-shadow: 0 1px 2px rgba(var(--v-border-color), 0.05) !important;
  transition: all 0.3s ease;
}

.status-card:hover {
  box-shadow: 0 3px 6px rgba(var(--v-border-color), 0.1) !important;
}

.status-item {
  border-radius: 8px;
  transition: all 0.2s ease;
  padding: 0.5rem;
  margin-bottom: 4px;
}

.status-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.text-subtitle-2 {
  font-size: 14px !important;
  font-weight: 500;
  margin-bottom: 2px;
}

.directory-tree {
  max-height: 600px;
  overflow-y: auto;
}

.tree-item {
  border-radius: 4px;
  transition: all 0.2s ease;
}

.tree-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.directory-item {
  cursor: pointer;
}

.media-item {
  border-radius: 4px;
  transition: all 0.2s ease;
}

.media-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.hidden {
  display: none !important;
}
</style>
