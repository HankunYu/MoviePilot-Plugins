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
              <v-col cols="12" md="3">
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
              <v-col cols="12" md="3">
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
              <v-col cols="12" md="3">
                <v-btn
                  color="info"
                  block
                  @click="showAddCategoryDialog = true"
                >
                  <v-icon icon="mdi-folder-plus" class="mr-1"></v-icon>
                  添加分类
                </v-btn>
              </v-col>
              <v-col cols="12" md="3">
                <v-btn
                  color="warning"
                  block
                  @click="showQuickAddDialog = true"
                >
                  <v-icon icon="mdi-plus-circle" class="mr-1"></v-icon>
                  快速添加
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
            <v-icon icon="mdi-file-tree" class="mr-2" color="primary" size="small" />
            <span>识别词树形管理</span>
            <v-spacer></v-spacer>
            <span class="text-caption">共 {{ filteredIdentifiers.length }} 条</span>
          </v-card-title>
          <v-card-text class="px-0 py-0">
            <v-progress-linear v-if="loading" indeterminate color="primary"></v-progress-linear>
            
            <!-- 树形分类展示 -->
            <div v-if="hierarchicalData && hierarchicalData.length > 0">
              <div class="tree-container pa-3">
                <div
                  v-for="category in hierarchicalData"
                  :key="category.id"
                  class="category-node mb-3"
                >
                  <!-- 主分类 -->
                  <v-card class="mb-2" :class="{'expanded': category.expanded}">
                    <v-card-title class="py-2 px-3 category-header" @click="toggleCategory(category)">
                      <div class="d-flex align-center w-100">
                        <v-icon 
                          :icon="category.expanded ? 'mdi-folder-open' : 'mdi-folder'" 
                          class="mr-2" 
                          size="small"
                          color="primary"
                        ></v-icon>
                        <span class="font-weight-medium text-subtitle-2">{{ category.name }}</span>
                        <v-spacer></v-spacer>
                        <v-chip size="x-small" color="primary" class="mr-2">{{ getTotalCount(category) }}</v-chip>
                        <v-btn
                          icon
                          size="x-small"
                          variant="text"
                          @click.stop="addSubCategory(category)"
                        >
                          <v-icon icon="mdi-folder-plus" size="small"></v-icon>
                        </v-btn>
                        <v-btn
                          icon
                          size="x-small"
                          variant="text"
                          @click.stop="addIdentifierToCategory(category)"
                        >
                          <v-icon icon="mdi-plus" size="small"></v-icon>
                        </v-btn>
                        <v-btn
                          v-if="category.name !== '未分类'"
                          icon
                          size="x-small"
                          variant="text"
                          color="error"
                          @click.stop="deleteCategory(category)"
                        >
                          <v-icon icon="mdi-delete" size="small"></v-icon>
                        </v-btn>
                      </div>
                    </v-card-title>
                    
                    <!-- 分类内容 -->
                    <v-expand-transition>
                      <div v-show="category.expanded">
                        <v-card-text class="px-3 py-2">
                          
                          <!-- 子分类 -->
                          <div v-if="category.subCategories && category.subCategories.length > 0" class="mb-3">
                            <div
                              v-for="subCategory in category.subCategories"
                              :key="subCategory.id"
                              class="sub-category-node mb-2 ml-4"
                            >
                              <v-card variant="outlined" class="sub-category-card">
                                <v-card-title class="py-1 px-2 text-caption" @click="toggleSubCategory(subCategory)">
                                  <div class="d-flex align-center w-100">
                                    <v-icon 
                                      :icon="subCategory.expanded ? 'mdi-folder-open-outline' : 'mdi-folder-outline'" 
                                      class="mr-2" 
                                      size="small"
                                      color="info"
                                    ></v-icon>
                                    <span class="font-weight-medium">{{ subCategory.name }}</span>
                                    <v-spacer></v-spacer>
                                    <v-chip size="x-small" color="info" class="mr-2">{{ subCategory.identifiers.length }}</v-chip>
                                    <v-btn
                                      icon
                                      size="x-small"
                                      variant="text"
                                      @click.stop="addIdentifierToSubCategory(subCategory)"
                                    >
                                      <v-icon icon="mdi-plus" size="small"></v-icon>
                                    </v-btn>
                                    <v-btn
                                      icon
                                      size="x-small"
                                      variant="text"
                                      color="error"
                                      @click.stop="deleteSubCategory(category, subCategory)"
                                    >
                                      <v-icon icon="mdi-delete" size="small"></v-icon>
                                    </v-btn>
                                  </div>
                                </v-card-title>
                                
                                <!-- 子分类内的识别词 -->
                                <v-expand-transition>
                                  <div v-show="subCategory.expanded">
                                    <v-card-text class="px-2 py-1">
                                      <div
                                        v-for="(identifier, idx) in subCategory.identifiers"
                                        :key="idx"
                                        class="identifier-item d-flex align-center py-1 px-2 mb-1 rounded"
                                      >
                                        <v-icon
                                          :icon="getTypeIcon(identifier.type)"
                                          :color="getTypeColor(identifier.type)"
                                          size="small"
                                          class="mr-2"
                                        ></v-icon>
                                        <v-chip
                                          size="x-small"
                                          :color="getTypeColor(identifier.type)"
                                          class="mr-2"
                                        >
                                          {{ identifier.type }}
                                        </v-chip>
                                        <span class="text-caption flex-grow-1">{{ getDisplayContent(identifier) }}</span>
                                        <div class="action-buttons">
                                          <v-btn
                                            icon
                                            size="x-small"
                                            variant="text"
                                            @click="editIdentifierAdvanced(identifier, category, subCategory)"
                                          >
                                            <v-icon icon="mdi-pencil" size="small"></v-icon>
                                          </v-btn>
                                          <v-btn
                                            icon
                                            size="x-small"
                                            variant="text"
                                            color="error"
                                            @click="deleteIdentifierAdvanced(identifier, category, subCategory)"
                                          >
                                            <v-icon icon="mdi-delete" size="small"></v-icon>
                                          </v-btn>
                                        </div>
                                      </div>
                                    </v-card-text>
                                  </div>
                                </v-expand-transition>
                              </v-card>
                            </div>
                          </div>
                          
                          <!-- 主分类直接包含的识别词 -->
                          <div v-if="category.identifiers && category.identifiers.length > 0">
                            <div
                              v-for="(identifier, idx) in category.identifiers"
                              :key="idx"
                              class="identifier-item d-flex align-center py-2 px-2 mb-1 rounded border"
                            >
                              <v-icon
                                :icon="getTypeIcon(identifier.type)"
                                :color="getTypeColor(identifier.type)"
                                size="small"
                                class="mr-3"
                              ></v-icon>
                              <v-chip
                                size="x-small"
                                :color="getTypeColor(identifier.type)"
                                class="mr-2"
                              >
                                {{ identifier.type }}
                              </v-chip>
                              <span class="text-subtitle-2 flex-grow-1">{{ getDisplayContent(identifier) }}</span>
                              <div class="action-buttons">
                                <v-btn
                                  icon
                                  size="small"
                                  variant="text"
                                  @click="editIdentifierAdvanced(identifier, category)"
                                >
                                  <v-icon icon="mdi-pencil" size="small"></v-icon>
                                </v-btn>
                                <v-btn
                                  icon
                                  size="small"
                                  variant="text"
                                  color="error"
                                  @click="deleteIdentifierAdvanced(identifier, category)"
                                >
                                  <v-icon icon="mdi-delete" size="small"></v-icon>
                                </v-btn>
                              </div>
                            </div>
                          </div>
                          
                        </v-card-text>
                      </div>
                    </v-expand-transition>
                  </v-card>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8">
              <v-icon icon="mdi-emoticon-sad" size="large" color="grey" class="mb-2"></v-icon>
              <div class="text-subtitle-2 text-grey">暂无识别词</div>
              <div class="text-caption text-grey">点击"重新加载"获取数据或"添加分类"开始使用</div>
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>

    <!-- 添加分类对话框 -->
    <v-dialog v-model="showAddCategoryDialog" max-width="500">
      <v-card>
        <v-card-title class="text-subtitle-1">添加新分类</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newCategoryName"
            label="分类名称"
            variant="outlined"
            density="compact"
            placeholder="输入分类名称"
            :rules="[v => !!v || '分类名称不能为空']"
          ></v-text-field>
          <v-text-field
            v-model="newCategoryDescription"
            label="分类描述（可选）"
            variant="outlined"
            density="compact"
            placeholder="输入分类描述"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showAddCategoryDialog = false">取消</v-btn>
          <v-btn color="primary" @click="addNewCategory">确认</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 添加子分类对话框 -->
    <v-dialog v-model="showAddSubCategoryDialog" max-width="500">
      <v-card>
        <v-card-title class="text-subtitle-1">添加子分类到 {{ currentParentCategory?.name }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newSubCategoryName"
            label="子分类名称"
            variant="outlined"
            density="compact"
            placeholder="输入子分类名称"
            :rules="[v => !!v || '子分类名称不能为空']"
          ></v-text-field>
          <v-text-field
            v-model="newSubCategoryDescription"
            label="子分类描述（可选）"
            variant="outlined"
            density="compact"
            placeholder="输入子分类描述"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showAddSubCategoryDialog = false">取消</v-btn>
          <v-btn color="primary" @click="addNewSubCategory">确认</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 快速添加识别词对话框 -->
    <v-dialog v-model="showQuickAddDialog" max-width="700">
      <v-card>
        <v-card-title class="text-subtitle-1">快速添加识别词</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="quickAddForm.category"
                :items="categorySelectOptions"
                label="选择分类（可选）"
                variant="outlined"
                density="compact"
                class="mb-3"
                clearable
                hint="留空将自动分配到'未分类'"
                persistent-hint
              ></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="quickAddForm.subCategory"
                :items="subCategorySelectOptions"
                label="选择子分类（可选）"
                variant="outlined"
                density="compact"
                class="mb-3"
                :disabled="!quickAddForm.category"
              ></v-select>
            </v-col>
          </v-row>
          
          <v-select
            v-model="quickAddForm.type"
            :items="typeOptions"
            label="识别词类型"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          
          <!-- 动态表单区域 -->
          <div v-if="quickAddForm.type === '屏蔽'">
            <v-text-field
              v-model="quickAddForm.blockWord"
              label="屏蔽词"
              variant="outlined"
              density="compact"
              placeholder="输入要屏蔽的词语"
              hint="这个词语将在识别时被过滤掉"
              persistent-hint
            ></v-text-field>
          </div>
          
          <div v-else-if="quickAddForm.type === '替换'">
            <v-text-field
              v-model="quickAddForm.originalWord"
              label="原词"
              variant="outlined"
              density="compact"
              placeholder="输入原词"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="quickAddForm.replacementWord"
              label="替换词"
              variant="outlined"
              density="compact"
              placeholder="输入替换词"
              hint="原词将被替换为这个词"
              persistent-hint
            ></v-text-field>
          </div>
          
          <div v-else-if="quickAddForm.type === '集偏移'">
            <v-text-field
              v-model="quickAddForm.frontLocator"
              label="前定位词"
              variant="outlined"
              density="compact"
              placeholder="输入前定位词"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="quickAddForm.backLocator"
              label="后定位词"
              variant="outlined"
              density="compact"
              placeholder="输入后定位词"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="quickAddForm.offset"
              label="偏移量"
              variant="outlined"
              density="compact"
              placeholder="例如：EP+1、EP-2"
              hint="EP+数字表示向后偏移，EP-数字表示向前偏移"
              persistent-hint
            ></v-text-field>
          </div>
          
          <div v-else-if="quickAddForm.type === '替换和集偏移'">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="quickAddForm.originalWord"
                  label="原词"
                  variant="outlined"
                  density="compact"
                  placeholder="输入原词"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="quickAddForm.replacementWord"
                  label="替换词"
                  variant="outlined"
                  density="compact"
                  placeholder="输入替换词"
                ></v-text-field>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="quickAddForm.frontLocator"
                  label="前定位词"
                  variant="outlined"
                  density="compact"
                  placeholder="前定位词"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="quickAddForm.backLocator"
                  label="后定位词"
                  variant="outlined"
                  density="compact"
                  placeholder="后定位词"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="quickAddForm.offset"
                  label="偏移量"
                  variant="outlined"
                  density="compact"
                  placeholder="EP+1"
                ></v-text-field>
              </v-col>
            </v-row>
          </div>
          
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showQuickAddDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveQuickAdd" :disabled="!isQuickAddValid">添加</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 高级编辑识别词对话框 -->
    <v-dialog v-model="showAdvancedEditDialog" max-width="700">
      <v-card>
        <v-card-title class="text-subtitle-1">编辑识别词</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="editForm.category"
                :items="categorySelectOptions"
                label="选择分类（可选）"
                variant="outlined"
                density="compact"
                class="mb-3"
                clearable
                hint="留空将自动分配到'未分类'"
                persistent-hint
              ></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="editForm.subCategory"
                :items="subCategorySelectOptions"
                label="选择子分类（可选）"
                variant="outlined"
                density="compact"
                class="mb-3"
                :disabled="!editForm.category"
              ></v-select>
            </v-col>
          </v-row>
          
          <v-select
            v-model="editForm.type"
            :items="typeOptions"
            label="识别词类型"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          
          <!-- 动态表单区域（与快速添加相同的结构） -->
          <div v-if="editForm.type === '屏蔽'">
            <v-text-field
              v-model="editForm.blockWord"
              label="屏蔽词"
              variant="outlined"
              density="compact"
              placeholder="输入要屏蔽的词语"
            ></v-text-field>
          </div>
          
          <div v-else-if="editForm.type === '替换'">
            <v-text-field
              v-model="editForm.originalWord"
              label="原词"
              variant="outlined"
              density="compact"
              placeholder="输入原词"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="editForm.replacementWord"
              label="替换词"
              variant="outlined"
              density="compact"
              placeholder="输入替换词"
            ></v-text-field>
          </div>
          
          <div v-else-if="editForm.type === '集偏移'">
            <v-text-field
              v-model="editForm.frontLocator"
              label="前定位词"
              variant="outlined"
              density="compact"
              placeholder="输入前定位词"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="editForm.backLocator"
              label="后定位词"
              variant="outlined"
              density="compact"
              placeholder="输入后定位词"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="editForm.offset"
              label="偏移量"
              variant="outlined"
              density="compact"
              placeholder="例如：EP+1、EP-2"
            ></v-text-field>
          </div>
          
          <div v-else-if="editForm.type === '替换和集偏移'">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editForm.originalWord"
                  label="原词"
                  variant="outlined"
                  density="compact"
                  placeholder="输入原词"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editForm.replacementWord"
                  label="替换词"
                  variant="outlined"
                  density="compact"
                  placeholder="输入替换词"
                ></v-text-field>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="editForm.frontLocator"
                  label="前定位词"
                  variant="outlined"
                  density="compact"
                  placeholder="前定位词"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="editForm.backLocator"
                  label="后定位词"
                  variant="outlined"
                  density="compact"
                  placeholder="后定位词"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="editForm.offset"
                  label="偏移量"
                  variant="outlined"
                  density="compact"
                  placeholder="EP+1"
                ></v-text-field>
              </v-col>
            </v-row>
          </div>
          
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="showAdvancedEditDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveAdvancedEdit" :disabled="!isEditFormValid">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';

const props = defineProps({
  api: { 
    type: [Object, Function],
    required: true,
  }
});

const emit = defineEmits(['close', 'switch']);

// 响应式数据
const loading = ref(false);
const saving = ref(false);
const error = ref('');
const successMessage = ref('');

// 识别词数据
const identifiers = ref([]);
const hierarchicalData = ref([]);
const searchKeyword = ref('');
const selectedTag = ref('');

// 对话框控制
const showAddCategoryDialog = ref(false);
const showAddSubCategoryDialog = ref(false);
const showQuickAddDialog = ref(false);
const showAdvancedEditDialog = ref(false);

// 新分类相关
const newCategoryName = ref('');
const newCategoryDescription = ref('');
const newSubCategoryName = ref('');
const newSubCategoryDescription = ref('');
const currentParentCategory = ref(null);

// 快速添加表单
const quickAddForm = ref({
  category: '',
  subCategory: '',
  type: '屏蔽',
  blockWord: '',
  originalWord: '',
  replacementWord: '',
  frontLocator: '',
  backLocator: '',
  offset: ''
});

// 编辑表单
const editForm = ref({
  category: '',
  subCategory: '',
  type: '屏蔽',
  blockWord: '',
  originalWord: '',
  replacementWord: '',
  frontLocator: '',
  backLocator: '',
  offset: '',
  originalIdentifier: null,
  originalCategory: null,
  originalSubCategory: null
});

// 类型选项
const typeOptions = [
  { title: '屏蔽词', value: '屏蔽' },
  { title: '替换词', value: '替换' },
  { title: '集偏移', value: '集偏移' },
  { title: '替换和集偏移', value: '替换和集偏移' }
];

// 计算属性
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

const categorySelectOptions = computed(() => {
  return hierarchicalData.value.map(cat => ({ title: cat.name, value: cat.id }));
});

const subCategorySelectOptions = computed(() => {
  const currentCategoryId = quickAddForm.value.category || editForm.value.category;
  
  // 如果没有选择分类，则不显示子分类选项
  if (!currentCategoryId) return [];
  
  const category = hierarchicalData.value.find(cat => cat.id === currentCategoryId);
  
  if (!category || !category.subCategories) return [];
  
  return category.subCategories.map(subCat => ({ title: subCat.name, value: subCat.id }));
});

const isQuickAddValid = computed(() => {
  // 不再要求必须选择分类，如果没有选择分类将自动使用"未分类"
  if (!quickAddForm.value.type) return false;
  
  switch (quickAddForm.value.type) {
    case '屏蔽':
      return !!quickAddForm.value.blockWord;
    case '替换':
      return !!quickAddForm.value.originalWord && !!quickAddForm.value.replacementWord;
    case '集偏移':
      return !!quickAddForm.value.frontLocator && !!quickAddForm.value.backLocator && !!quickAddForm.value.offset;
    case '替换和集偏移':
      return !!quickAddForm.value.originalWord && !!quickAddForm.value.replacementWord && 
             !!quickAddForm.value.frontLocator && !!quickAddForm.value.backLocator && !!quickAddForm.value.offset;
    default:
      return false;
  }
});

const isEditFormValid = computed(() => {
  // 编辑时如果没有选择分类也允许，将自动使用"未分类"
  if (!editForm.value.type) return false;
  
  switch (editForm.value.type) {
    case '屏蔽':
      return !!editForm.value.blockWord;
    case '替换':
      return !!editForm.value.originalWord && !!editForm.value.replacementWord;
    case '集偏移':
      return !!editForm.value.frontLocator && !!editForm.value.backLocator && !!editForm.value.offset;
    case '替换和集偏移':
      return !!editForm.value.originalWord && !!editForm.value.replacementWord && 
             !!editForm.value.frontLocator && !!editForm.value.backLocator && !!editForm.value.offset;
    default:
      return false;
  }
});

// 监听分类变化清空子分类
watch(() => quickAddForm.value.category, () => {
  quickAddForm.value.subCategory = '';
});

watch(() => editForm.value.category, () => {
  editForm.value.subCategory = '';
});

// 方法
const switchToConfig = () => {
  emit('switch');
};

const loadIdentifiers = async () => {
  if (!props.api) {
    error.value = 'API 对象未初始化';
    return;
  }
  
  loading.value = true;
  error.value = '';
  
  try {
    console.log('正在调用 API:', 'plugin/IdentifierHelper/get_identifiers');
    const response = await props.api.get('plugin/IdentifierHelper/get_identifiers');
    console.log('API 响应:', response);
    
    if (response && response.code === 0) {
      identifiers.value = response.data || [];
      buildHierarchicalData();
      successMessage.value = '识别词加载成功';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    } else {
      error.value = response?.message || '未知错误';
    }
  } catch (err) {
    console.error('API 调用错误:', err);
    error.value = '加载识别词失败: ' + (err.message || '未知错误');
  } finally {
    loading.value = false;
  }
};

const buildHierarchicalData = () => {
  const categories = new Map();
  
  // 遍历所有识别词，构建层级结构
  identifiers.value.forEach(item => {
    const parts = item.tag.split('/');
    const categoryName = parts[0] || '未分类';
    const subCategoryName = parts[1];
    
    // 获取或创建主分类
    if (!categories.has(categoryName)) {
      categories.set(categoryName, {
        id: categoryName,
        name: categoryName,
        identifiers: [],
        subCategories: [],
        expanded: true
      });
    }
    
    const category = categories.get(categoryName);
    
    if (subCategoryName) {
      // 查找或创建子分类
      let subCategory = category.subCategories.find(sub => sub.name === subCategoryName);
      if (!subCategory) {
        subCategory = {
          id: `${categoryName}/${subCategoryName}`,
          name: subCategoryName,
          identifiers: [],
          expanded: true
        };
        category.subCategories.push(subCategory);
      }
      subCategory.identifiers.push(item);
    } else {
      // 直接属于主分类
      category.identifiers.push(item);
    }
  });
  
  hierarchicalData.value = Array.from(categories.values());
};

const saveIdentifiers = async () => {
  if (!props.api) {
    error.value = 'API 对象未初始化';
    return;
  }
  
  saving.value = true;
  error.value = '';
  
  try {
    console.log('正在保存识别词:', identifiers.value);
    console.log('保存的数据长度:', identifiers.value.length);
    
    // 确保数据格式正确
    const dataToSave = identifiers.value.map(item => ({
      tag: item.tag || '未分类',
      type: item.type || '屏蔽',
      content: item.content || ''
    }));
    
    console.log('格式化后的数据:', dataToSave);
    
    // 转换为原始文本格式
    const rawText = generateRawTextFromIdentifiers(dataToSave);
    console.log('生成的原始文本:', rawText);
    
    // 为长文本使用请求体，需要添加空的查询参数来满足FastAPI要求
    const response = await props.api.post('plugin/IdentifierHelper/save_raw_data?data=', {
      data: rawText
    });
    console.log('保存响应:', response);
    
    if (response && response.code === 0) {
      successMessage.value = response.message || '识别词保存成功';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    } else {
      error.value = response?.message || '保存失败';
    }
  } catch (err) {
    console.error('保存错误:', err);
    error.value = '保存识别词失败: ' + (err.message || '未知错误');
  } finally {
    saving.value = false;
  }
};

// 将结构化数据转换为原始文本格式
const generateRawTextFromIdentifiers = (identifierList) => {
  if (!identifierList || identifierList.length === 0) {
    return '';
  }
  
  // 按标签分组
  const grouped = {};
  identifierList.forEach(item => {
    const tag = item.tag || '未分类';
    if (!grouped[tag]) {
      grouped[tag] = [];
    }
    grouped[tag].push(item);
  });
  
  const lines = [];
  
  // 处理未分类的条目（放在最前面，不需要标签标记）
  if (grouped['未分类']) {
    grouped['未分类'].forEach(item => {
      lines.push(item.content);
    });
    lines.push(''); // 空行分隔
    delete grouped['未分类'];
  }
  
  // 处理其他标签
  Object.entries(grouped).forEach(([tag, items]) => {
    lines.push(`# ${tag}`);
    items.forEach(item => {
      lines.push(item.content);
    });
    lines.push(''); // 空行分隔
  });
  
  return lines.join('\n').trim();
};

const addNewCategory = () => {
  if (!newCategoryName.value.trim()) return;
  
  const categoryName = newCategoryName.value.trim();
  
  // 添加一个新分类
  hierarchicalData.value.push({
    id: categoryName,
    name: categoryName,
    identifiers: [],
    subCategories: [],
    expanded: true
  });
  
  newCategoryName.value = '';
  newCategoryDescription.value = '';
  showAddCategoryDialog.value = false;
  successMessage.value = `分类 "${categoryName}" 创建成功`;
  setTimeout(() => { successMessage.value = ''; }, 3000);
};

const addSubCategory = (parentCategory) => {
  currentParentCategory.value = parentCategory;
  showAddSubCategoryDialog.value = true;
};

const addNewSubCategory = () => {
  if (!newSubCategoryName.value.trim() || !currentParentCategory.value) return;
  
  const subCategoryName = newSubCategoryName.value.trim();
  
  currentParentCategory.value.subCategories.push({
    id: `${currentParentCategory.value.id}/${subCategoryName}`,
    name: subCategoryName,
    identifiers: [],
    expanded: true
  });
  
  newSubCategoryName.value = '';
  newSubCategoryDescription.value = '';
  showAddSubCategoryDialog.value = false;
  successMessage.value = `子分类 "${subCategoryName}" 创建成功`;
  setTimeout(() => { successMessage.value = ''; }, 3000);
};

const deleteCategory = (category) => {
  if (confirm(`确定要删除分类 "${category.name}" 及其下的所有内容吗？`)) {
    // 从identifiers中删除相关项
    identifiers.value = identifiers.value.filter(item => !item.tag.startsWith(category.name));
    
    // 从层级数据中删除
    const index = hierarchicalData.value.findIndex(cat => cat.id === category.id);
    if (index >= 0) {
      hierarchicalData.value.splice(index, 1);
    }
    
    successMessage.value = `分类 "${category.name}" 删除成功`;
    setTimeout(() => { successMessage.value = ''; }, 3000);
  }
};

const deleteSubCategory = (parentCategory, subCategory) => {
  if (confirm(`确定要删除子分类 "${subCategory.name}" 及其下的所有识别词吗？`)) {
    // 从identifiers中删除相关项
    identifiers.value = identifiers.value.filter(item => item.tag !== subCategory.id);
    
    // 从父分类中删除子分类
    const index = parentCategory.subCategories.findIndex(sub => sub.id === subCategory.id);
    if (index >= 0) {
      parentCategory.subCategories.splice(index, 1);
    }
    
    successMessage.value = `子分类 "${subCategory.name}" 删除成功`;
    setTimeout(() => { successMessage.value = ''; }, 3000);
  }
};

const toggleCategory = (category) => {
  category.expanded = !category.expanded;
};

const toggleSubCategory = (subCategory) => {
  subCategory.expanded = !subCategory.expanded;
};

const getTotalCount = (category) => {
  let count = category.identifiers.length;
  if (category.subCategories) {
    count += category.subCategories.reduce((sum, sub) => sum + sub.identifiers.length, 0);
  }
  return count;
};

const getDisplayContent = (identifier) => {
  // 根据类型生成友好的显示内容
  const content = identifier.content;
  
  if (identifier.type === '屏蔽') {
    return content;
  } else if (identifier.type === '替换') {
    return content;
  } else if (identifier.type === '集偏移') {
    return content;
  } else if (identifier.type === '替换和集偏移') {
    return content;
  }
  
  return content;
};

const addIdentifierToCategory = (category) => {
  quickAddForm.value.category = category.id;
  quickAddForm.value.subCategory = '';
  resetQuickAddForm();
  showQuickAddDialog.value = true;
};

const addIdentifierToSubCategory = (subCategory) => {
  const parts = subCategory.id.split('/');
  quickAddForm.value.category = parts[0];
  quickAddForm.value.subCategory = subCategory.id;
  resetQuickAddForm();
  showQuickAddDialog.value = true;
};

const resetQuickAddForm = () => {
  quickAddForm.value.type = '屏蔽';
  quickAddForm.value.blockWord = '';
  quickAddForm.value.originalWord = '';
  quickAddForm.value.replacementWord = '';
  quickAddForm.value.frontLocator = '';
  quickAddForm.value.backLocator = '';
  quickAddForm.value.offset = '';
};

const generateContentFromForm = (form) => {
  switch (form.type) {
    case '屏蔽':
      return form.blockWord || '';
    case '替换':
      return form.originalWord && form.replacementWord ? `${form.originalWord} => ${form.replacementWord}` : '';
    case '集偏移':
      return form.frontLocator && form.backLocator && form.offset ? 
        `${form.frontLocator} <> ${form.backLocator} >> ${form.offset}` : '';
    case '替换和集偏移':
      return form.originalWord && form.replacementWord && form.frontLocator && form.backLocator && form.offset ?
        `${form.originalWord} => ${form.replacementWord} && ${form.frontLocator} <> ${form.backLocator} >> ${form.offset}` : '';
    default:
      return '';
  }
};

const saveQuickAdd = () => {
  const content = generateContentFromForm(quickAddForm.value);
  if (!content) return;
  
  // 如果没有选择分类，使用"未分类"
  const tagName = quickAddForm.value.subCategory || quickAddForm.value.category || '未分类';
  
  identifiers.value.push({
    tag: tagName,
    type: quickAddForm.value.type,
    content: content
  });
  
  buildHierarchicalData();
  showQuickAddDialog.value = false;
  resetQuickAddForm();
  
  successMessage.value = '识别词添加成功';
  setTimeout(() => { successMessage.value = ''; }, 3000);
};

const editIdentifierAdvanced = (identifier, category, subCategory = null) => {
  editForm.value.category = category.id;
  editForm.value.subCategory = subCategory ? subCategory.id : '';
  editForm.value.type = identifier.type;
  editForm.value.originalIdentifier = identifier;
  editForm.value.originalCategory = category;
  editForm.value.originalSubCategory = subCategory;
  
  // 解析已有内容到表单
  parseContentToForm(identifier.content, identifier.type, editForm.value);
  
  showAdvancedEditDialog.value = true;
};

const parseContentToForm = (content, type, form) => {
  switch (type) {
    case '屏蔽':
      form.blockWord = content;
      break;
    case '替换':
      const replaceParts = content.split(' => ');
      form.originalWord = replaceParts[0] || '';
      form.replacementWord = replaceParts[1] || '';
      break;
    case '集偏移':
      const offsetMatch = content.match(/^(.*?)\s*<>\s*(.*?)\s*>>\s*(.*)$/);
      if (offsetMatch) {
        form.frontLocator = offsetMatch[1];
        form.backLocator = offsetMatch[2];
        form.offset = offsetMatch[3];
      }
      break;
    case '替换和集偏移':
      const complexMatch = content.match(/^(.*?)\s*=>\s*(.*?)\s*&&\s*(.*?)\s*<>\s*(.*?)\s*>>\s*(.*)$/);
      if (complexMatch) {
        form.originalWord = complexMatch[1];
        form.replacementWord = complexMatch[2];
        form.frontLocator = complexMatch[3];
        form.backLocator = complexMatch[4];
        form.offset = complexMatch[5];
      }
      break;
  }
};

const saveAdvancedEdit = () => {
  const newContent = generateContentFromForm(editForm.value);
  if (!newContent) return;
  
  // 如果没有选择分类，使用"未分类"
  const newTagName = editForm.value.subCategory || editForm.value.category || '未分类';
  
  // 找到原识别词并更新
  const index = identifiers.value.findIndex(item => item === editForm.value.originalIdentifier);
  if (index >= 0) {
    identifiers.value[index] = {
      tag: newTagName,
      type: editForm.value.type,
      content: newContent
    };
  }
  
  buildHierarchicalData();
  showAdvancedEditDialog.value = false;
  
  successMessage.value = '识别词修改成功';
  setTimeout(() => { successMessage.value = ''; }, 3000);
};

const deleteIdentifierAdvanced = (identifier, category, subCategory = null) => {
  if (confirm('确定要删除这个识别词吗？')) {
    const index = identifiers.value.findIndex(item => item === identifier);
    if (index >= 0) {
      identifiers.value.splice(index, 1);
      buildHierarchicalData();
      
      successMessage.value = '识别词删除成功';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    }
  }
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
  // 延迟加载，等待 API 对象初始化
  setTimeout(() => {
    loadIdentifiers();
  }, 500);
});
    
</script>

<style scoped>
.plugin-page {
  width: 100%;
  height: 100%;
}

.tree-container {
  max-height: 70vh;
  overflow-y: auto;
}

.category-node {
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.category-node:hover {
  border-left-color: rgba(var(--v-theme-primary), 0.5);
}

.category-header {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.category-header:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.sub-category-node {
  position: relative;
}

.sub-category-node::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: rgba(var(--v-theme-info), 0.3);
}

.sub-category-card {
  background-color: rgba(var(--v-theme-surface), 0.8);
  border-left: 2px solid rgba(var(--v-theme-info), 0.5);
}

.sub-category-card .v-card-title {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.sub-category-card .v-card-title:hover {
  background-color: rgba(var(--v-theme-info), 0.05);
}

.identifier-item {
  background-color: rgba(var(--v-theme-surface), 0.5);
  transition: all 0.2s ease;
  border-left: 2px solid transparent;
}

.identifier-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-left-color: rgba(var(--v-theme-primary), 0.5);
}

.action-buttons {
  display: flex;
  gap: 2px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.identifier-item:hover .action-buttons {
  opacity: 1;
}

.expanded {
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.1);
}

.cursor-pointer {
  cursor: pointer;
}


/* 滚动条样式 */
.tree-container::-webkit-scrollbar {
  width: 6px;
}

.tree-container::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface), 0.1);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.3);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.5);
}

/* 动画效果 */
.v-enter-active,
.v-leave-active {
  transition: all 0.3s ease;
}

.v-enter-from,
.v-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tree-container {
    max-height: 60vh;
  }
  
  .sub-category-node {
    margin-left: 0;
  }
  
  .sub-category-node::before {
    display: none;
  }
}
</style>