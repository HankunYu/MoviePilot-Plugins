<template>
  <div class="plugin-config">
    <v-card flat class="rounded border">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-cog" class="mr-2" color="primary" size="small" />
        <span>识别词配置</span>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          size="small"
          variant="text"
          @click="switchToPage"
        >
          <v-icon icon="mdi-arrow-left" size="small" class="mr-1"></v-icon>
          返回
        </v-btn>
      </v-card-title>
      
      <v-card-text class="px-3 py-2">
        <v-alert v-if="error" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ error }}</v-alert>
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>

        <!-- 原始数据编辑 -->
        <v-card flat class="rounded mb-3 border">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-code-tags" class="mr-2" color="primary" size="small" />
            <span>原始数据编辑</span>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              size="small"
              variant="text"
              @click="loadRawData"
              :loading="loading"
            >
              <v-icon icon="mdi-refresh" size="small" class="mr-1"></v-icon>
              重新加载
            </v-btn>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-textarea
              v-model="rawData"
              label="识别词原始数据"
              variant="outlined"
              rows="20"
              density="compact"
              placeholder="输入识别词数据..."
              :loading="loading"
            ></v-textarea>
            
            <v-alert type="info" density="compact" variant="tonal" class="mt-3">
              <div class="text-caption">
                <strong>标签格式说明：</strong><br>
                • 使用 <code># 标签名</code> 开始一个新标签<br>
                • 标签下的所有识别词都属于该标签<br>
                • 未在任何标签下的识别词归为"未分类"<br><br>
                
                <strong>识别词格式：</strong><br>
                • 屏蔽词：<code>要屏蔽的词</code><br>
                • 替换词：<code>原词 => 新词</code><br>
                • 集偏移：<code>前定位词 <> 后定位词 >> 偏移量</code><br>
                • 复合格式：<code>原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量</code>
              </div>
            </v-alert>
            
            <div class="d-flex gap-2 mt-3">
              <v-btn
                color="success"
                @click="saveRawData"
                :loading="saving"
              >
                <v-icon icon="mdi-content-save" class="mr-1"></v-icon>
                保存数据
              </v-btn>
              
              <v-btn
                color="info"
                @click="previewParsedData"
                :loading="parsing"
              >
                <v-icon icon="mdi-eye" class="mr-1"></v-icon>
                预览解析
              </v-btn>
              
              <v-btn
                color="warning"
                @click="formatData"
              >
                <v-icon icon="mdi-format-align-left" class="mr-1"></v-icon>
                格式化
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- 解析预览 -->
        <v-card v-if="parsedData.length > 0" flat class="rounded mb-3 border">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-success-lighten-5">
            <v-icon icon="mdi-eye-check" class="mr-2" color="success" size="small" />
            <span>解析预览</span>
            <v-spacer></v-spacer>
            <span class="text-caption">共 {{ parsedData.length }} 条</span>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <div class="preview-container" style="max-height: 300px; overflow-y: auto;">
              <div
                v-for="(item, index) in parsedData"
                :key="index"
                class="preview-item d-flex align-center py-1 px-2 mb-1 rounded"
                :class="getPreviewItemClass(item.type)"
              >
                <v-icon
                  :icon="getTypeIcon(item.type)"
                  :color="getTypeColor(item.type)"
                  size="small"
                  class="mr-2"
                ></v-icon>
                
                <v-chip
                  size="x-small"
                  :color="getTypeColor(item.type)"
                  class="mr-2"
                >
                  {{ item.type }}
                </v-chip>
                
                <v-chip
                  size="x-small"
                  color="primary"
                  variant="outlined"
                  class="mr-2"
                >
                  {{ item.tag }}
                </v-chip>
                
                <span class="text-caption font-mono">{{ item.content }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- 导入导出 -->
        <v-card flat class="rounded border">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-import" class="mr-2" color="primary" size="small" />
            <span>导入导出</span>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12" md="6">
                <v-file-input
                  v-model="importFile"
                  label="导入文件"
                  variant="outlined"
                  density="compact"
                  accept=".txt,.json"
                  prepend-icon="mdi-file-upload"
                  @change="handleFileImport"
                ></v-file-input>
              </v-col>
              <v-col cols="12" md="6">
                <v-btn
                  color="primary"
                  block
                  @click="exportData"
                >
                  <v-icon icon="mdi-download" class="mr-1"></v-icon>
                  导出数据
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue';

export default defineComponent({
  name: 'IdentifierConfig',
  props: {
    api: Object
  },
  emits: ['switch', 'close'],
  
  setup(props, { emit }) {
    // 响应式数据
    const loading = ref(false);
    const saving = ref(false);
    const parsing = ref(false);
    const error = ref('');
    const successMessage = ref('');
    
    const rawData = ref('');
    const parsedData = ref([]);
    const importFile = ref(null);
    
    // 方法
    const switchToPage = () => {
      emit('switch');
    };
    
    const loadRawData = async () => {
      if (!props.api) return;
      
      loading.value = true;
      error.value = '';
      
      try {
        const response = await props.api.get('/get_raw_identifiers');
        if (response.data) {
          rawData.value = response.data;
          successMessage.value = '原始数据加载成功';
          setTimeout(() => { successMessage.value = ''; }, 3000);
        }
      } catch (err) {
        error.value = '加载原始数据失败: ' + (err.message || '未知错误');
      } finally {
        loading.value = false;
      }
    };
    
    const saveRawData = async () => {
      if (!props.api) return;
      
      saving.value = true;
      error.value = '';
      
      try {
        await props.api.post('/save_raw_identifiers', { data: rawData.value });
        successMessage.value = '原始数据保存成功';
        setTimeout(() => { successMessage.value = ''; }, 3000);
      } catch (err) {
        error.value = '保存原始数据失败: ' + (err.message || '未知错误');
      } finally {
        saving.value = false;
      }
    };
    
    const previewParsedData = async () => {
      if (!props.api) return;
      
      parsing.value = true;
      error.value = '';
      
      try {
        const response = await props.api.post('/parse_identifiers', { data: rawData.value });
        if (response.data) {
          parsedData.value = response.data;
          successMessage.value = `解析成功，共 ${response.data.length} 条识别词`;
          setTimeout(() => { successMessage.value = ''; }, 3000);
        }
      } catch (err) {
        error.value = '解析数据失败: ' + (err.message || '未知错误');
      } finally {
        parsing.value = false;
      }
    };
    
    const formatData = () => {
      if (!rawData.value) return;
      
      const lines = rawData.value.split('\n');
      const formatted = [];
      let currentTag = '';
      
      lines.forEach(line => {
        const trimmed = line.trim();
        if (!trimmed) {
          formatted.push('');
          return;
        }
        
        // 检测标签行
        if (trimmed.startsWith('#')) {
          if (formatted.length > 0 && formatted[formatted.length - 1] !== '') {
            formatted.push('');
          }
          formatted.push(trimmed);
          formatted.push('');
          currentTag = trimmed;
        } else {
          formatted.push(trimmed);
        }
      });
      
      rawData.value = formatted.join('\n');
      successMessage.value = '数据格式化完成';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    };
    
    const handleFileImport = (event) => {
      const file = event.target.files?.[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result;
        if (content) {
          rawData.value = content;
          successMessage.value = '文件导入成功';
          setTimeout(() => { successMessage.value = ''; }, 3000);
        }
      };
      reader.readAsText(file);
    };
    
    const exportData = () => {
      if (!rawData.value) {
        error.value = '没有数据可导出';
        return;
      }
      
      const blob = new Blob([rawData.value], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `identifiers_${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      successMessage.value = '数据导出成功';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    };
    
    const getTypeIcon = (type) => {
      const icons = {
        '屏蔽': 'mdi-eye-off',
        '替换': 'mdi-find-replace',
        '集偏移': 'mdi-numeric',
        '替换和集偏移': 'mdi-cog'
      };
      return icons[type] || 'mdi-help';
    };
    
    const getTypeColor = (type) => {
      const colors = {
        '屏蔽': 'error',
        '替换': 'warning',
        '集偏移': 'info',
        '替换和集偏移': 'success'
      };
      return colors[type] || 'grey';
    };
    
    const getPreviewItemClass = (type) => {
      const classes = {
        '屏蔽': 'bg-error-lighten-5',
        '替换': 'bg-warning-lighten-5',
        '集偏移': 'bg-info-lighten-5',
        '替换和集偏移': 'bg-success-lighten-5'
      };
      return classes[type] || 'bg-grey-lighten-5';
    };
    
    // 生命周期
    onMounted(() => {
      loadRawData();
    });
    
    return {
      loading,
      saving,
      parsing,
      error,
      successMessage,
      rawData,
      parsedData,
      importFile,
      switchToPage,
      loadRawData,
      saveRawData,
      previewParsedData,
      formatData,
      handleFileImport,
      exportData,
      getTypeIcon,
      getTypeColor,
      getPreviewItemClass
    };
  }
});
</script>

<style scoped>
.plugin-config {
  width: 100%;
  height: 100%;
}

.preview-container {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  background-color: rgba(var(--v-theme-surface), 0.5);
}

.preview-item {
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.preview-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.font-mono {
  font-family: 'Courier New', monospace;
}

.bg-error-lighten-5 {
  background-color: rgba(var(--v-theme-error), 0.1);
}

.bg-warning-lighten-5 {
  background-color: rgba(var(--v-theme-warning), 0.1);
}

.bg-info-lighten-5 {
  background-color: rgba(var(--v-theme-info), 0.1);
}

.bg-success-lighten-5 {
  background-color: rgba(var(--v-theme-success), 0.1);
}

.bg-grey-lighten-5 {
  background-color: rgba(var(--v-theme-surface-variant), 0.1);
}
</style>