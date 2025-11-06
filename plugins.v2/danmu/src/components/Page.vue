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
              placeholder="搜索文件/目录"
              prepend-inner-icon="mdi-magnify"
              class="search-field"
              style="max-width: 200px;"
            ></v-text-field>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12">
                <div v-if="directoryContent" class="directory-content">
                  <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2"></v-progress-linear>
                  
                  <!-- 返回按钮 -->
                  <div v-if="currentPath" 
                       class="back-item d-flex align-center py-2 mb-2"
                       @click="goBack()">
                    <v-icon icon="mdi-keyboard-backspace" size="small" color="primary" class="mr-2"></v-icon>
                    <span class="text-subtitle-2 text-primary cursor-pointer">
                      {{ directoryContent.is_root ? '返回目录列表' : '返回上级目录' }}
                    </span>
                  </div>
                  
                  <template v-for="(item, index) in filteredItems" :key="index">
                    <!-- 目录项 -->
                    <div v-if="item.type === 'directory'" 
                         class="directory-item d-flex align-center py-2"
                         @click="navigateToPath(item.path)">
                      <v-icon icon="mdi-folder" size="small" color="primary" class="mr-2"></v-icon>
                      <div class="flex-grow-1 d-flex align-center">
                        <span class="text-subtitle-2 cursor-pointer">{{ item.name }}</span>
                        <v-chip
                          v-if="item.manual_match"
                          size="small"
                          color="secondary"
                          class="ml-2"
                          closable
                          @click.stop
                          @click:close.stop="clearManualMatch(item, item.manual_scope)"
                        >
                          {{ manualChipText(item) }}
                        </v-chip>
                      </div>
                      <v-btn
                        icon="mdi-magnify"
                        size="small"
                        variant="text"
                        color="secondary"
                        class="mr-1"
                        @click.stop="openManualMatch(item)"
                      ></v-btn>
                      <v-icon icon="mdi-chevron-right" size="small" color="grey"></v-icon>
                    </div>
                    
                    <!-- 媒体文件项 -->
                    <div v-else-if="item.type === 'media'" 
                         class="media-item d-flex align-center py-2">
                      <v-icon icon="mdi-video" size="small" color="info" class="mr-2"></v-icon>
                      <div class="flex-grow-1">
                        <div class="d-flex align-center">
                          <span class="text-subtitle-2">{{ item.name }}</span>
                          <v-chip size="small" color="info" class="ml-2" v-if="item.danmu_count > 0">
                            弹幕: {{ item.danmu_count }}
                          </v-chip>
                          <v-chip size="small" color="grey" class="ml-2" v-else>
                            无弹幕
                          </v-chip>
                          <v-chip
                            v-if="item.manual_match"
                            size="small"
                            color="secondary"
                            class="ml-2"
                            closable
                            @click:close.stop="clearManualMatch(item, item.manual_scope)"
                          >
                            {{ manualChipText(item) }}
                          </v-chip>
                        </div>
                      </div>
                      <v-btn
                        color="secondary"
                        size="small"
                        variant="text"
                        class="mr-1"
                        @click="openManualMatch(item)"
                      >
                        <v-icon icon="mdi-magnify" size="small" class="mr-1"></v-icon>
                        手动匹配
                      </v-btn>
                      <v-btn
                        color="primary"
                        size="small"
                        variant="text"
                        :loading="item.generating"
                        @click="generateDanmu(item)"
                      >
                        <v-icon icon="mdi-download" size="small" class="mr-1"></v-icon>
                        刮削
                      </v-btn>
                    </div>
                  </template>
                  
                  <!-- 空目录提示 -->
                  <div v-if="directoryContent.children && directoryContent.children.length === 0" 
                       class="text-center py-4">
                    <v-alert type="info" density="compact" class="mb-2 text-caption" variant="tonal">
                      该目录为空或没有支持的媒体文件
                    </v-alert>
                  </div>
                </div>
                
                <!-- 错误提示 -->
                <div v-else-if="!directoryContent && error" class="text-center py-4">
                  <v-alert type="error" density="compact" class="mb-2 text-caption" variant="tonal">{{ error }}</v-alert>
                </div>
                
                <!-- 未设置路径提示 -->
                <div v-else class="text-center py-4">
                  <v-alert type="info" density="compact" class="mb-2 text-caption" variant="tonal">
                    请先在配置中设置刮削路径
                  </v-alert>
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

    <v-dialog v-model="manualDialog" max-width="720">
      <v-card>
        <v-card-title class="text-subtitle-1">
          手动匹配弹幕
        </v-card-title>
        <v-card-text>
          <div class="text-caption text-grey mb-2">
            当前选择：{{ manualTargetItem?.name || '未选择文件' }}
          </div>
          <v-alert
            v-if="manualExistingMatch"
            type="info"
            density="compact"
            variant="tonal"
            class="mb-2 text-caption"
          >
            已匹配（{{ scopeLabel(manualExistingScope) }}）：{{ manualExistingMatch.animeTitle || `ID ${manualExistingMatch.animeId}` }}
          </v-alert>
          <v-alert
            v-if="manualSearchError"
            type="error"
            density="compact"
            variant="tonal"
            class="mb-2 text-caption"
            closable
            @click:close="manualSearchError = null"
          >
            {{ manualSearchError }}
          </v-alert>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="manualSearchKeyword"
                label="搜索关键字"
                density="compact"
                variant="outlined"
                clearable
                hide-details
                @keyup.enter="performManualSearch"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="4">
              <v-select
                v-model="manualSearchType"
                :items="manualTypeOptions"
                item-title="title"
                item-value="value"
                density="compact"
                variant="outlined"
                hide-details
                label="类型"
              ></v-select>
            </v-col>
            <v-col cols="12" md="2" class="d-flex align-center">
              <v-btn
                color="primary"
                block
                :loading="manualSearchLoading"
                @click="performManualSearch"
              >
                搜索
              </v-btn>
            </v-col>
          </v-row>
          <v-progress-linear
            v-if="manualSearchLoading"
            indeterminate
            color="primary"
            class="mb-2"
          ></v-progress-linear>
          <v-row v-if="manualTargetItem && manualTargetItem.type === 'media'">
            <v-col cols="12">
              <v-radio-group
                v-model="manualScope"
                inline
                density="compact"
                hide-details
              >
                <v-radio label="仅当前文件" value="file"></v-radio>
                <v-radio label="整目录" value="directory"></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>
          <v-alert
            v-if="!manualSearchLoading && manualSearchPerformed && manualSearchResults.length === 0"
            type="info"
            density="compact"
            variant="tonal"
            class="mb-2 text-caption"
          >
            未找到匹配结果，请调整关键字后再试。
          </v-alert>
          <v-list v-if="manualSearchResults.length > 0" lines="two" density="comfortable">
            <v-list-item
              v-for="anime in manualSearchResults"
              :key="anime.animeId"
              :active="manualSelected && manualSelected.animeId === anime.animeId"
              @click="selectManualResult(anime)"
            >
              <v-list-item-title>{{ anime.animeTitle }}</v-list-item-title>
              <v-list-item-subtitle>
                {{ anime.typeDescription || '未知类型' }}
                <span v-if="anime.episodeCount"> · {{ anime.episodeCount }} 集</span>
                <span v-if="anime.rating"> · 评分 {{ anime.rating }}</span>
                <span v-if="anime.startDate"> · {{ formatDate(anime.startDate) }}</span>
              </v-list-item-subtitle>
              <template #append>
                <v-btn
                  icon="mdi-check"
                  size="small"
                  variant="text"
                  :color="manualSelected && manualSelected.animeId === anime.animeId ? 'primary' : 'grey'"
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-btn
            color="grey"
            variant="text"
            v-if="manualExistingMatch"
            @click="clearManualMatch(manualTargetItem, manualExistingScope || (manualTargetItem?.type === 'directory' ? 'directory' : 'file'), true)"
          >
            清除匹配
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeManualDialog">取消</v-btn>
          <v-btn
            color="primary"
            :disabled="!manualSelected"
            :loading="manualSaving"
            @click="confirmManualMatch"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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

// 当前目录内容和导航
const directoryContent = ref(null);
const currentPath = ref('');
const loading = ref(false);
const pathHistory = ref([]);

// 搜索关键字
const searchKeyword = ref('');

// 手动匹配相关状态
const manualDialog = ref(false);
const manualContext = ref(null);
const manualSearchKeyword = ref('');
const manualSearchType = ref('tvseries');
const manualTypeOptions = [
  { title: '全部类型', value: 'all' },
  { title: '电视动画', value: 'tvseries' },
  { title: 'OVA/特别篇', value: 'ova' },
  { title: '剧场版', value: 'movie' }
];
const manualSearchResults = ref([]);
const manualSearchLoading = ref(false);
const manualSearchError = ref(null);
const manualSearchPerformed = ref(false);
const manualSelected = ref(null);
const manualSaving = ref(false);
const manualScope = ref('directory');

const manualTargetItem = computed(() => manualContext.value?.item || null);
const manualExistingMatch = computed(() => manualTargetItem.value?.manual_match || null);
const manualExistingScope = computed(() => manualExistingMatch.value?.scope || null);

// 计算属性：过滤后的项目
const filteredItems = computed(() => {
  if (!directoryContent.value || !directoryContent.value.children) {
    return [];
  }
  
  if (!searchKeyword.value) {
    return directoryContent.value.children;
  }
  
  const keyword = searchKeyword.value.toLowerCase();
  return directoryContent.value.children.filter(item => {
    return item.name.toLowerCase().includes(keyword);
  });
});

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

// 导航到指定路径
async function navigateToPath(path) {
  try {
    loading.value = true;
    error.value = null;
    
    // 如果是空路径，加载根目录
    if (!path) {
      const data = await props.api.get('plugin/Danmu/scan_path');
      if (data && data.success) {
        directoryContent.value = data.data;
        currentPath.value = '';
        // 如果是多根目录，保存根路径历史
        if (data.data.type === 'root') {
          pathHistory.value = [];
        }
      } else {
        error.value = data?.message || '加载根目录失败';
      }
    } else {
      // 加载指定路径
      const data = await props.api.get('plugin/Danmu/scan_subfolder', {
        params: { subfolder_path: path }
      });
      
      if (data && data.success) {
        directoryContent.value = data.data;
        currentPath.value = path;
        
        // 更新路径历史
        if (!pathHistory.value.includes(path)) {
          pathHistory.value.push(path);
        }
      } else {
        error.value = data?.message || '加载目录失败';
      }
    }
  } catch (err) {
    console.error('导航失败:', err);
    error.value = '加载目录失败，请检查网络或API';
  } finally {
    loading.value = false;
  }
}

// 返回上级目录
function goBack() {
  if (!currentPath.value) return;
  
  // 如果当前目录是用户设定的根目录，返回到初始目录列表
  if (directoryContent.value?.is_root) {
    navigateToPath('');
  } else {
    // 如果不是根目录，正常返回上级目录
    const parentPath = currentPath.value.split('/').slice(0, -1).join('/');
    navigateToPath(parentPath || '');
  }
}

function closeManualDialog() {
  manualDialog.value = false;
  manualContext.value = null;
  manualSelected.value = null;
  manualScope.value = 'directory';
}

function scopeLabel(scope) {
  if (!scope) {
    return '目录';
  }
  if (scope === 'file') {
    return '单文件';
  }
  if (scope === 'directory') {
    return '目录';
  }
  return '未知';
}

function manualChipText(item) {
  if (!item?.manual_match) return '';
  const scopeText = item.manual_scope === 'file' ? '【单文件】' : '';
  const title = item.manual_match.animeTitle || `ID ${item.manual_match.animeId}`;
  return `${scopeText}${title}`;
}

function resolveDirectoryPath(item) {
  if (!item) return null;
  if (item.type === 'directory') {
    return item.path;
  }
  return item.directory_path || (item.path ? item.path.split('/').slice(0, -1).join('/') : null);
}

function sanitizeKeyword(name) {
  if (!name) return '';
  return name.replace(/\.[^/.]+$/, '').replace(/[\._]/g, ' ').trim();
}

function openManualMatch(item) {
  manualContext.value = { item };
  manualDialog.value = true;
  manualSearchError.value = null;
  manualSearchResults.value = [];
  manualSearchPerformed.value = false;
  manualSearchLoading.value = false;
  manualSaving.value = false;
  manualSelected.value = item.manual_match ? { ...item.manual_match } : null;
  const existingScope = item.manual_scope || item.manual_match?.scope;
  if (item.type === 'directory') {
    manualScope.value = 'directory';
  } else if (existingScope === 'directory') {
    manualScope.value = 'directory';
  } else if (existingScope === 'file') {
    manualScope.value = 'file';
  } else {
    manualScope.value = 'file';
  }
  manualSearchKeyword.value = sanitizeKeyword(item.name) || manualSearchKeyword.value || '';
  manualSearchType.value = 'tvseries';
}

function selectManualResult(anime) {
  manualSelected.value = anime;
}

async function performManualSearch() {
  const keyword = manualSearchKeyword.value?.trim();
  if (!keyword) {
    manualSearchError.value = '请输入搜索关键字';
    manualSearchResults.value = [];
    manualSearchPerformed.value = true;
    return;
  }
  manualSearchLoading.value = true;
  manualSearchError.value = null;
  manualSearchPerformed.value = true;
  try {
    const params = {
      keyword,
    };
    if (manualSearchType.value && manualSearchType.value !== 'all') {
      params.type = manualSearchType.value;
    }
    const res = await props.api.get('plugin/Danmu/search_anime', { params });
    if (res && res.success) {
      manualSearchResults.value = (res.data?.animes || []).slice(0, 50);
    } else {
      manualSearchResults.value = [];
      manualSearchError.value = res?.message || '搜索失败，请稍后重试';
    }
  } catch (err) {
    console.error('搜索弹弹失败:', err);
    manualSearchResults.value = [];
    manualSearchError.value = '搜索失败，请检查网络或API';
  } finally {
    manualSearchLoading.value = false;
  }
}

async function confirmManualMatch() {
  const targetItem = manualTargetItem.value;
  if (!targetItem || !manualSelected.value) {
    manualSearchError.value = '请选择一条匹配记录';
    return;
  }
  manualSaving.value = true;
  manualSearchError.value = null;
  try {
    const scope = manualScope.value;
    const directoryPath = scope === 'directory'
      ? resolveDirectoryPath(targetItem)
      : undefined;
    const payload = {
      file_path: scope === 'file' ? targetItem.path : undefined,
      directory: directoryPath,
      scope,
      anime: manualSelected.value
    };
    const res = await props.api.post('plugin/Danmu/manual_match', payload);
    if (res && res.success) {
      successMessage.value = '手动匹配已保存';
      if (manualContext.value?.item) {
        manualContext.value.item.manual_match = res.data?.manual_match || manualSelected.value;
        manualContext.value.item.manual_scope = scope;
      }
      manualDialog.value = false;
      await navigateToPath(currentPath.value);
    } else {
      manualSearchError.value = res?.message || '保存匹配失败';
    }
  } catch (err) {
    console.error('保存手动匹配失败:', err);
    manualSearchError.value = '保存失败，请检查网络或API';
  } finally {
    manualSaving.value = false;
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) {
    return (dateStr || '').split('T')[0] || dateStr;
  }
  return date.toISOString().split('T')[0];
}

// 生成弹幕
async function generateDanmu(item) {
  error.value = null; // 清空旧错误
  try {
    item.generating = true;
    const result = await props.api.get('plugin/Danmu/generate_danmu', {
      params: { file_path: item.path }
    });
    if (result && result.success) {
      successMessage.value = '弹幕生成成功';
      // 重新加载当前目录以更新弹幕计数
      await navigateToPath(currentPath.value);
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

async function clearManualMatch(item, scopeOverride = null, keepDialog = false) {
  if (!item) {
    return;
  }
  manualSearchError.value = null;
  try {
    const scope = (scopeOverride || item?.manual_scope || (item?.type === 'directory' ? 'directory' : 'file'));
    const params = { scope };
    if (scope === 'file') {
      params.file_path = item.path;
    } else {
      params.directory = resolveDirectoryPath(item);
      if (!params.directory) {
        manualSearchError.value = '未能确定需要移除的目录';
        return;
      }
    }
    const res = await props.api.get('plugin/Danmu/remove_manual_match', { params });
    if (res && res.success) {
      successMessage.value = '已移除手动匹配';
      if (manualContext.value?.item?.path === item.path) {
        manualContext.value.item.manual_match = null;
        manualContext.value.item.manual_scope = null;
        manualSelected.value = null;
        if (keepDialog && manualTargetItem.value?.type === 'media') {
          manualScope.value = 'file';
        }
        if (!keepDialog) {
          manualDialog.value = false;
        }
      }
      await navigateToPath(currentPath.value);
    } else {
      manualSearchError.value = res?.message || '移除手动匹配失败';
    }
  } catch (err) {
    console.error('移除手动匹配失败:', err);
    manualSearchError.value = '移除手动匹配失败，请检查网络或API';
  }
}

// 初始化
onMounted(async () => {
  await getStatus();
  // 加载根目录
  await navigateToPath('');
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

.directory-content {
  max-height: 600px;
  overflow-y: auto;
}

.directory-item {
  border-radius: 4px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.directory-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.back-item {
  border-radius: 4px;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 1px dashed rgba(var(--v-theme-primary), 0.3);
}

.back-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-color: rgba(var(--v-theme-primary), 0.5);
}

.media-item {
  border-radius: 4px;
  transition: all 0.2s ease;
}

.media-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.cursor-pointer {
  cursor: pointer;
}
</style>
