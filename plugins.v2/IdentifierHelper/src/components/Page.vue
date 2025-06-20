<template>
  <div class="plugin-page">
    <v-card flat class="rounded border">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-tag-text" class="mr-2" color="primary" size="small" />
        <span>自定义识别词管理</span>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          size="small"
          variant="text"
          @click="switchToConfig"
        >
          <v-icon icon="mdi-cog" size="small" class="mr-1"></v-icon>
          配置
        </v-btn>
      </v-card-title>
      
      <v-card-text class="px-3 py-2">
        <v-alert v-if="error" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ error }}</v-alert>
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>

        <!-- 操作按钮区域 -->
        <v-card flat class="rounded mb-3 border">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-wrench" class="mr-2" color="primary" size="small" />
            <span>操作面板</span>
          </v-card-title>
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12" md="4">
                <v-btn
                  color="primary"
                  block
                  @click="loadIdentifiers"
                  :loading="loading"
                >
                  <v-icon icon="mdi-refresh" class="mr-1"></v-icon>
                  重新加载
                </v-btn>
              </v-col>
              <v-col cols="12" md="4">
                <v-btn
                  color="success"
                  block
                  @click="saveIdentifiers"
                  :loading="saving"
                >
                  <v-icon icon="mdi-content-save" class="mr-1"></v-icon>
                  保存修改
                </v-btn>
              </v-col>
              <v-col cols="12" md="4">
                <v-btn
                  color="warning"
                  block
                  @click="showAddDialog = true"
                >
                  <v-icon icon="mdi-plus" class="mr-1"></v-icon>
                  添加标签
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- 搜索和过滤 -->
        <v-card flat class="rounded mb-3 border">
          <v-card-text class="px-3 py-2">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="searchKeyword"
                  density="compact"
                  variant="outlined"
                  hide-details
                  placeholder="搜索识别词..."
                  prepend-inner-icon="mdi-magnify"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="selectedTag"
                  :items="tagOptions"
                  density="compact"
                  variant="outlined"
                  hide-details
                  placeholder="选择标签过滤..."
                  prepend-inner-icon="mdi-tag"
                  clearable
                ></v-select>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- 识别词管理 -->
        <v-card flat class="rounded border">
          <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
            <v-icon icon="mdi-format-list-bulleted" class="mr-2" color="primary" size="small" />
            <span>识别词列表</span>
            <v-spacer></v-spacer>
            <span class="text-caption">共 {{ filteredIdentifiers.length }} 条</span>
          </v-card-title>
          <v-card-text class="px-0 py-0">
            <v-progress-linear v-if="loading" indeterminate color="primary"></v-progress-linear>
            
            <!-- 标签分组展示 -->
            <div v-if="groupedIdentifiers && Object.keys(groupedIdentifiers).length > 0">
              <v-expansion-panels v-model="expandedPanels" multiple>
                <v-expansion-panel
                  v-for="(items, tag) in groupedIdentifiers"
                  :key="tag"
                  :value="tag"
                >
                  <v-expansion-panel-title>
                    <div class="d-flex align-center w-100">
                      <v-icon :icon="getTagIcon(tag)" class="mr-2" size="small"></v-icon>
                      <span class="font-weight-medium">{{ tag }}</span>
                      <v-spacer></v-spacer>
                      <v-chip size="small" color="primary" class="mr-2">{{ items.length }}</v-chip>
                      <v-btn
                        icon
                        size="small"
                        variant="text"
                        @click.stop="deleteTag(tag)"
                        v-if="tag !== '未分类'"
                      >
                        <v-icon icon="mdi-delete" size="small"></v-icon>
                      </v-btn>
                    </div>
                  </v-expansion-panel-title>
                  
                  <v-expansion-panel-text>
                    <div class="identifier-list">
                      <div
                        v-for="(item, index) in items"
                        :key="index"
                        class="identifier-item d-flex align-center py-2 px-2 mb-2 rounded border"
                      >
                        <v-icon
                          :icon="getTypeIcon(item.type)"
                          :color="getTypeColor(item.type)"
                          size="small"
                          class="mr-3"
                        ></v-icon>
                        
                        <div class="flex-grow-1">
                          <div class="d-flex align-center">
                            <v-chip
                              size="x-small"
                              :color="getTypeColor(item.type)"
                              class="mr-2"
                            >
                              {{ item.type }}
                            </v-chip>
                            <span class="text-subtitle-2">{{ item.content }}</span>
                          </div>
                        </div>
                        
                        <div class="action-buttons">
                          <v-btn
                            icon
                            size="small"
                            variant="text"
                            @click="editIdentifier(item, tag)"
                          >
                            <v-icon icon="mdi-pencil" size="small"></v-icon>
                          </v-btn>
                          <v-btn
                            icon
                            size="small"
                            variant="text"
                            color="error"
                            @click="deleteIdentifier(item, tag)"
                          >
                            <v-icon icon="mdi-delete" size="small"></v-icon>
                          </v-btn>
                        </div>
                      </div>
                      
                      <!-- 添加新识别词到当前标签 -->
                      <v-btn
                        color="primary"
                        size="small"
                        variant="outlined"
                        block
                        @click="addToTag(tag)"
                      >
                        <v-icon icon="mdi-plus" size="small" class="mr-1"></v-icon>
                        添加到 {{ tag }}
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
            
            <div v-else class="text-center py-8">
              <v-icon icon="mdi-emoticon-sad" size="large" color="grey" class="mb-2"></v-icon>
              <div class="text-subtitle-2 text-grey">暂无识别词</div>
              <div class="text-caption text-grey">点击"重新加载"获取数据</div>
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>

    <!-- 添加标签对话框 -->
    <v-dialog v-model="showAddDialog" max-width="500">
      <v-card>
        <v-card-title class="text-subtitle-1">添加新标签</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newTagName"
            label="标签名称"
            variant="outlined"
            density="compact"
            placeholder="输入标签名称（不需要#前缀）"
            :rules="[v => !!v || '标签名称不能为空']"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showAddDialog = false">取消</v-btn>
          <v-btn color="primary" @click="addNewTag">确认</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑识别词对话框 -->
    <v-dialog v-model="showEditDialog" max-width="600">
      <v-card>
        <v-card-title class="text-subtitle-1">编辑识别词</v-card-title>
        <v-card-text>
          <v-select
            v-model="editingItem.type"
            :items="typeOptions"
            label="类型"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          
          <v-select
            v-model="editingItem.tag"
            :items="tagOptions"
            label="标签"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          
          <v-textarea
            v-model="editingItem.content"
            label="内容"
            variant="outlined"
            density="compact"
            rows="3"
            placeholder="输入识别词内容..."
          ></v-textarea>
          
          <v-alert type="info" density="compact" variant="tonal" class="mt-3">
            <div class="text-caption">
              <strong>格式说明：</strong><br>
              • 屏蔽词：直接输入要屏蔽的词<br>
              • 替换词：原词 => 新词<br>
              • 集偏移：前定位词 <> 后定位词 >> 偏移量<br>
              • 替换和集偏移：原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量
            </div>
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showEditDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveEdit">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 添加识别词到标签对话框 -->
    <v-dialog v-model="showAddToTagDialog" max-width="600">
      <v-card>
        <v-card-title class="text-subtitle-1">添加识别词到 {{ currentTag }}</v-card-title>
        <v-card-text>
          <v-select
            v-model="newItem.type"
            :items="typeOptions"
            label="类型"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          
          <v-textarea
            v-model="newItem.content"
            label="内容"
            variant="outlined"
            density="compact"
            rows="3"
            placeholder="输入识别词内容..."
          ></v-textarea>
          
          <v-alert type="info" density="compact" variant="tonal" class="mt-3">
            <div class="text-caption">
              <strong>格式说明：</strong><br>
              • 屏蔽词：直接输入要屏蔽的词<br>
              • 替换词：原词 => 新词<br>
              • 集偏移：前定位词 <> 后定位词 >> 偏移量<br>
              • 替换和集偏移：原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量
            </div>
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showAddToTagDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveNewItem">添加</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue';

export default defineComponent({
  name: 'IdentifierPage',
  props: {
    api: Object
  },
  emits: ['switch', 'close'],
  
  setup(props, { emit }) {
    // 响应式数据
    const loading = ref(false);
    const saving = ref(false);
    const error = ref('');
    const successMessage = ref('');
    
    // 识别词数据
    const identifiers = ref([]);
    const searchKeyword = ref('');
    const selectedTag = ref('');
    const expandedPanels = ref([]);
    
    // 对话框控制
    const showAddDialog = ref(false);
    const showEditDialog = ref(false);
    const showAddToTagDialog = ref(false);
    const newTagName = ref('');
    const currentTag = ref('');
    
    // 编辑相关
    const editingItem = ref({
      type: '屏蔽',
      tag: '未分类',
      content: '',
      originalTag: '',
      originalIndex: -1
    });
    
    const newItem = ref({
      type: '屏蔽',
      content: ''
    });
    
    // 类型选项
    const typeOptions = [
      { title: '屏蔽词', value: '屏蔽' },
      { title: '替换词', value: '替换' },
      { title: '集偏移', value: '集偏移' },
      { title: '替换和集偏移', value: '替换和集偏移' }
    ];
    
    // 计算属性
    const tagOptions = computed(() => {
      const tags = [...new Set(identifiers.value.map(item => item.tag))];
      return tags.map(tag => ({ title: tag, value: tag }));
    });
    
    const filteredIdentifiers = computed(() => {
      let filtered = identifiers.value;
      
      if (searchKeyword.value) {
        filtered = filtered.filter(item => 
          item.content.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
          item.tag.toLowerCase().includes(searchKeyword.value.toLowerCase())
        );
      }
      
      if (selectedTag.value) {
        filtered = filtered.filter(item => item.tag === selectedTag.value);
      }
      
      return filtered;
    });
    
    const groupedIdentifiers = computed(() => {
      const grouped = {};
      filteredIdentifiers.value.forEach(item => {
        if (!grouped[item.tag]) {
          grouped[item.tag] = [];
        }
        grouped[item.tag].push(item);
      });
      return grouped;
    });
    
    // 方法
    const switchToConfig = () => {
      emit('switch');
    };
    
    const loadIdentifiers = async () => {
      if (!props.api) return;
      
      loading.value = true;
      error.value = '';
      
      try {
        const response = await props.api.get('/get_identifiers');
        if (response.data) {
          identifiers.value = response.data;
          successMessage.value = '识别词加载成功';
          setTimeout(() => { successMessage.value = ''; }, 3000);
        }
      } catch (err) {
        error.value = '加载识别词失败: ' + (err.message || '未知错误');
      } finally {
        loading.value = false;
      }
    };
    
    const saveIdentifiers = async () => {
      if (!props.api) return;
      
      saving.value = true;
      error.value = '';
      
      try {
        await props.api.post('/save_identifiers', { identifiers: identifiers.value });
        successMessage.value = '识别词保存成功';
        setTimeout(() => { successMessage.value = ''; }, 3000);
      } catch (err) {
        error.value = '保存识别词失败: ' + (err.message || '未知错误');
      } finally {
        saving.value = false;
      }
    };
    
    const addNewTag = () => {
      if (!newTagName.value.trim()) return;
      
      // 添加一个空的标签占位符
      identifiers.value.push({
        tag: newTagName.value.trim(),
        type: '屏蔽',
        content: `# ${newTagName.value.trim()} 标签创建占位符（请删除此条目）`
      });
      
      newTagName.value = '';
      showAddDialog.value = false;
      successMessage.value = `标签 "${newTagName.value}" 创建成功`;
      setTimeout(() => { successMessage.value = ''; }, 3000);
    };
    
    const deleteTag = (tag) => {
      if (confirm(`确定要删除标签 "${tag}" 及其下的所有识别词吗？`)) {
        identifiers.value = identifiers.value.filter(item => item.tag !== tag);
        successMessage.value = `标签 "${tag}" 删除成功`;
        setTimeout(() => { successMessage.value = ''; }, 3000);
      }
    };
    
    const editIdentifier = (item, tag) => {
      const index = identifiers.value.findIndex(i => 
        i.tag === tag && i.content === item.content && i.type === item.type
      );
      
      editingItem.value = {
        type: item.type,
        tag: item.tag,
        content: item.content,
        originalTag: tag,
        originalIndex: index
      };
      
      showEditDialog.value = true;
    };
    
    const saveEdit = () => {
      if (editingItem.value.originalIndex >= 0) {
        identifiers.value[editingItem.value.originalIndex] = {
          tag: editingItem.value.tag,
          type: editingItem.value.type,
          content: editingItem.value.content
        };
        
        successMessage.value = '识别词修改成功';
        setTimeout(() => { successMessage.value = ''; }, 3000);
      }
      
      showEditDialog.value = false;
    };
    
    const deleteIdentifier = (item, tag) => {
      if (confirm('确定要删除这个识别词吗？')) {
        const index = identifiers.value.findIndex(i => 
          i.tag === tag && i.content === item.content && i.type === item.type
        );
        
        if (index >= 0) {
          identifiers.value.splice(index, 1);
          successMessage.value = '识别词删除成功';
          setTimeout(() => { successMessage.value = ''; }, 3000);
        }
      }
    };
    
    const addToTag = (tag) => {
      currentTag.value = tag;
      newItem.value = {
        type: '屏蔽',
        content: ''
      };
      showAddToTagDialog.value = true;
    };
    
    const saveNewItem = () => {
      if (!newItem.value.content.trim()) return;
      
      identifiers.value.push({
        tag: currentTag.value,
        type: newItem.value.type,
        content: newItem.value.content.trim()
      });
      
      successMessage.value = `识别词添加到 "${currentTag.value}" 成功`;
      setTimeout(() => { successMessage.value = ''; }, 3000);
      
      showAddToTagDialog.value = false;
    };
    
    const getTagIcon = (tag) => {
      if (tag === '未分类') return 'mdi-tag-outline';
      return 'mdi-tag';
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
    
    // 生命周期
    onMounted(() => {
      loadIdentifiers();
    });
    
    return {
      loading,
      saving,
      error,
      successMessage,
      identifiers,
      searchKeyword,
      selectedTag,
      expandedPanels,
      showAddDialog,
      showEditDialog,
      showAddToTagDialog,
      newTagName,
      currentTag,
      editingItem,
      newItem,
      typeOptions,
      tagOptions,
      filteredIdentifiers,
      groupedIdentifiers,
      switchToConfig,
      loadIdentifiers,
      saveIdentifiers,
      addNewTag,
      deleteTag,
      editIdentifier,
      saveEdit,
      deleteIdentifier,
      addToTag,
      saveNewItem,
      getTagIcon,
      getTypeIcon,
      getTypeColor
    };
  }
});
</script>

<style scoped>
.plugin-page {
  width: 100%;
  height: 100%;
}

.status-card {
  background-color: rgba(var(--v-theme-surface), 0.7);
}

.identifier-item {
  background-color: rgba(var(--v-theme-surface), 0.5);
  transition: all 0.2s ease;
}

.identifier-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.search-field {
  max-width: 200px;
}

.cursor-pointer {
  cursor: pointer;
}

.directory-item:hover,
.media-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.back-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>