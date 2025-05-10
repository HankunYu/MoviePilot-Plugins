<template>
  <div class="plugin-config">
    <v-card flat class="rounded border">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-cog" class="mr-2" color="primary" size="small" />
        <span>弹幕刮削配置</span>
      </v-card-title>
      
      <v-card-text class="px-3 py-2">
        <v-alert v-if="error" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ error }}</v-alert>
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>

        <v-form ref="form" v-model="isFormValid" @submit.prevent="saveFullConfig">
          <!-- 基本设置卡片 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-tune" class="mr-2" color="primary" size="small" />
              <span>基本设置</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-power" size="small" :color="editableConfig.enable ? 'success' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">启用插件</div>
                          <div class="text-caption text-grey">是否启用弹幕刮削功能</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.enable"
                          color="primary"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-bilibili" size="small" :color="editableConfig.onlyFromBili ? 'info' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">仅从B站获取</div>
                          <div class="text-caption text-grey">是否仅从B站获取弹幕</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.onlyFromBili"
                          color="info"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-database" size="small" :color="editableConfig.useTmdbID ? 'info' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">使用TMDB ID</div>
                          <div class="text-caption text-grey">是否使用TMDB ID进行匹配</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.useTmdbID"
                          color="info"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-auto-fix" size="small" :color="editableConfig.auto_scrape ? 'success' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">入库自动刮削</div>
                          <div class="text-caption text-grey">是否在媒体入库时自动刮削弹幕</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.auto_scrape"
                          color="success"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 弹幕参数设置 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-video" class="mr-2" color="primary" size="small" />
              <span>弹幕参数设置</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.width"
                    label="视频宽度"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :rules="[v => v > 0 || '宽度必须大于0']"
                    hint="弹幕视频的宽度"
                    persistent-hint
                    prepend-inner-icon="mdi-arrow-expand-horizontal"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.height"
                    label="视频高度"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :rules="[v => v > 0 || '高度必须大于0']"
                    hint="弹幕视频的高度"
                    persistent-hint
                    prepend-inner-icon="mdi-arrow-expand-vertical"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.fontsize"
                    label="字体大小"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :rules="[v => v > 0 || '字体大小必须大于0']"
                    hint="弹幕字体大小"
                    persistent-hint
                    prepend-inner-icon="mdi-format-font-size-increase"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.alpha"
                    label="透明度"
                    type="number"
                    variant="outlined"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    :rules="[v => v >= 0 && v <= 1 || '透明度必须在0-1之间']"
                    hint="弹幕透明度(0-1)"
                    persistent-hint
                    prepend-inner-icon="mdi-opacity"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.duration"
                    label="持续时间"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :rules="[v => v > 0 || '持续时间必须大于0']"
                    hint="弹幕显示持续时间(秒)"
                    persistent-hint
                    prepend-inner-icon="mdi-clock-outline"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 刮削路径设置 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-folder" class="mr-2" color="primary" size="small" />
              <span>手动控制媒体库路径</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-textarea
                v-model="editableConfig.path"
                label="/"
                variant="outlined"
                hint="每行一个路径,在状态页手动控制刮削"
                persistent-hint
                prepend-inner-icon="mdi-folder-multiple"
                :disabled="saving"
                density="compact"
                class="text-caption"
                rows="3"
              ></v-textarea>
            </v-card-text>
          </v-card>

          <!-- 帮助信息卡片 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-text class="d-flex align-center px-3 py-2">
              <v-icon icon="mdi-information" color="info" class="mr-2" size="small"></v-icon>
              <span class="text-caption">
                此插件用于生成视频的弹幕字幕文件.弹幕来源为弹弹play平台.
              </span>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="px-2 py-1">
        <v-btn color="info" @click="emit('switch')" prepend-icon="mdi-view-dashboard" :disabled="saving" variant="text" size="small">状态页</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="secondary" variant="text" @click="resetConfigToFetched" :disabled="!initialConfigLoaded || saving" prepend-icon="mdi-restore" size="small">重置</v-btn>
        <v-btn color="primary" :disabled="!isFormValid || saving" @click="saveFullConfig" :loading="saving" prepend-icon="mdi-content-save" variant="text" size="small">保存配置</v-btn>
        <v-btn color="grey" @click="emit('close')" prepend-icon="mdi-close" :disabled="saving" variant="text" size="small">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

const props = defineProps({
  api: { 
    type: [Object, Function],
    required: true,
  },
  initialConfig: {
    type: Object,
    default: () => ({}),
  }
});

const emit = defineEmits(['close', 'switch', 'config-updated-on-server', 'save']);

const form = ref(null);
const isFormValid = ref(true);
const error = ref(null);
const successMessage = ref(null);
const saving = ref(false);
const initialConfigLoaded = ref(false);

// Holds the config as fetched from server, used for reset
const serverFetchedConfig = reactive({}); 

// Holds the config being edited in the form
const editableConfig = reactive({
  enable: false,
  width: 1920,
  height: 1080,
  fontsize: 50,
  alpha: 0.8,
  duration: 15,
  path: '',
  onlyFromBili: false,
  useTmdbID: true,
  auto_scrape: true
});

const getPluginId = () => {
  return "Danmu";
};

async function loadInitialData() {
  error.value = null;
  saving.value = true;
  initialConfigLoaded.value = false;
  
  try {
    const pluginId = getPluginId();
    if (!pluginId) { 
      throw new Error('获取插件ID失败'); 
    }
    
    const data = await props.api.get(`plugin/${pluginId}/config`);
    
    if (data) {
      // 更新服务器配置
      Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(data)));
      // 更新编辑中的配置
      Object.assign(editableConfig, {
        enable: data.enabled,
        width: data.width,
        height: data.height,
        fontsize: data.fontsize,
        alpha: data.alpha,
        duration: data.duration,
        path: data.path,
        onlyFromBili: data.onlyFromBili,
        useTmdbID: data.useTmdbID,
        auto_scrape: data.auto_scrape
      });
      initialConfigLoaded.value = true;
      successMessage.value = '成功加载配置';
    } else {
      throw new Error('加载配置失败');
    }
  } catch (err) {
    console.error('加载配置失败:', err);
    error.value = err.message || '加载配置失败，请检查网络或API';
    // 使用初始配置
    if (props.initialConfig) {
      Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(props.initialConfig)));
      Object.assign(editableConfig, {
        enable: props.initialConfig.enabled,
        width: props.initialConfig.width,
        height: props.initialConfig.height,
        fontsize: props.initialConfig.fontsize,
        alpha: props.initialConfig.alpha,
        duration: props.initialConfig.duration,
        path: props.initialConfig.path,
        onlyFromBili: props.initialConfig.onlyFromBili,
        useTmdbID: props.initialConfig.useTmdbID,
        auto_scrape: props.initialConfig.auto_scrape
      });
    }
    successMessage.value = null;
  } finally {
    saving.value = false;
    setTimeout(() => { successMessage.value = null; error.value = null; }, 4000);
  }
}

async function saveFullConfig() {
  error.value = null;
  successMessage.value = null;
  if (!form.value) return;
  
  const validation = await form.value.validate();
  if (!validation.valid) {
    error.value = '请检查表单中的错误';
    return;
  }

  saving.value = true;

  try {
    const pluginId = getPluginId();
    if (!pluginId) {
      throw new Error('获取插件ID失败');
    }

    // 转换配置格式
    const configToSave = {
      enabled: editableConfig.enable,
      width: editableConfig.width,
      height: editableConfig.height,
      fontsize: editableConfig.fontsize,
      alpha: editableConfig.alpha,
      duration: editableConfig.duration,
      path: editableConfig.path,
      onlyFromBili: editableConfig.onlyFromBili,
      useTmdbID: editableConfig.useTmdbID,
      auto_scrape: editableConfig.auto_scrape
    };

    // 发送保存请求
    const result = await props.api.post(`plugin/${pluginId}/config`, configToSave);
    
    if (result && result.success) {
      // 更新服务器配置
      Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(configToSave)));
      successMessage.value = '配置已保存';
      emit('config-updated-on-server');
    } else {
      throw new Error(result?.message || '保存配置失败');
    }
  } catch (err) {
    console.error('保存配置失败:', err);
    error.value = err.message || '保存配置失败，请检查网络或查看日志';
  } finally {
    saving.value = false;
    setTimeout(() => { 
      successMessage.value = null; 
      if (error.value && !error.value.startsWith('保存配置失败') && !error.value.startsWith('配置已部分保存')) { 
        error.value = null; 
      }
    }, 5000); 
  }
}

function resetConfigToFetched() {
  if (initialConfigLoaded.value) {
    Object.assign(editableConfig, {
      enable: serverFetchedConfig.enabled,
      width: serverFetchedConfig.width,
      height: serverFetchedConfig.height,
      fontsize: serverFetchedConfig.fontsize,
      alpha: serverFetchedConfig.alpha,
      duration: serverFetchedConfig.duration,
      path: serverFetchedConfig.path,
      onlyFromBili: serverFetchedConfig.onlyFromBili,
      useTmdbID: serverFetchedConfig.useTmdbID,
      auto_scrape: serverFetchedConfig.auto_scrape
    });
    error.value = null;
    successMessage.value = '配置已重置为上次加载的状态';
    if (form.value) form.value.resetValidation();
  } else {
    error.value = '重置失败';
  }
  setTimeout(() => { successMessage.value = null; error.value = null; }, 3000);
}

onMounted(() => {
  // 初始化时使用初始配置
  if (props.initialConfig) {
    Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(props.initialConfig)));
    Object.assign(editableConfig, {
      enable: props.initialConfig.enabled,
      width: props.initialConfig.width,
      height: props.initialConfig.height,
      fontsize: props.initialConfig.fontsize,
      alpha: props.initialConfig.alpha,
      duration: props.initialConfig.duration,
      path: props.initialConfig.path,
      onlyFromBili: props.initialConfig.onlyFromBili,
      useTmdbID: props.initialConfig.useTmdbID,
      auto_scrape: props.initialConfig.auto_scrape
    });
  }
  loadInitialData();
});
</script>

<style scoped>
.plugin-config {
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

.config-card {
  background-image: linear-gradient(to right, rgba(var(--v-theme-surface), 0.98), rgba(var(--v-theme-surface), 0.95)), 
                    repeating-linear-gradient(45deg, rgba(var(--v-theme-primary), 0.03), rgba(var(--v-theme-primary), 0.03) 10px, transparent 10px, transparent 20px);
  background-attachment: fixed;
  box-shadow: 0 1px 2px rgba(var(--v-border-color), 0.05) !important;
  transition: all 0.3s ease;
}

.config-card:hover {
  box-shadow: 0 3px 6px rgba(var(--v-border-color), 0.1) !important;
}

.setting-item {
  border-radius: 8px;
  transition: all 0.2s ease;
  padding: 0.5rem;
  margin-bottom: 4px;
}

.setting-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.small-switch {
  transform: scale(0.8);
  margin-right: -8px;
}

.text-subtitle-2 {
  font-size: 14px !important;
  font-weight: 500;
  margin-bottom: 2px;
}
</style>
