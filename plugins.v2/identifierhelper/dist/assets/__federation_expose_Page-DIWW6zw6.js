import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,withModifiers:_withModifiers,vShow:_vShow,withDirectives:_withDirectives,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "plugin-page" };
const _hoisted_2 = { class: "text-caption" };
const _hoisted_3 = { key: 1 };
const _hoisted_4 = { class: "tree-container pa-3" };
const _hoisted_5 = { class: "d-flex align-center w-100" };
const _hoisted_6 = { class: "font-weight-medium text-subtitle-2" };
const _hoisted_7 = {
  key: 0,
  class: "mb-3"
};
const _hoisted_8 = { class: "d-flex align-center w-100" };
const _hoisted_9 = { class: "font-weight-medium" };
const _hoisted_10 = { class: "text-caption flex-grow-1" };
const _hoisted_11 = { class: "action-buttons" };
const _hoisted_12 = { key: 1 };
const _hoisted_13 = { class: "text-subtitle-2 flex-grow-1" };
const _hoisted_14 = { class: "action-buttons" };
const _hoisted_15 = {
  key: 2,
  class: "text-center py-8"
};
const _hoisted_16 = { key: 0 };
const _hoisted_17 = { key: 1 };
const _hoisted_18 = { key: 2 };
const _hoisted_19 = { key: 3 };
const _hoisted_20 = { key: 0 };
const _hoisted_21 = { key: 1 };
const _hoisted_22 = { key: 2 };
const _hoisted_23 = { key: 3 };

const {ref,computed,onMounted,watch} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { 
    type: [Object, Function],
    required: true,
  }
},
  emits: ['close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

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
    

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_expand_transition = _resolveComponent("v-expand-transition");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              icon: "mdi-tag-text",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[45] || (_cache[45] = _createElementVNode("span", null, "自定义识别词管理", -1)),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "primary",
              size: "small",
              variant: "text",
              onClick: switchToConfig
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-cog",
                  size: "small",
                  class: "mr-1"
                }),
                _cache[44] || (_cache[44] = _createTextVNode(" 配置 "))
              ]),
              _: 1,
              __: [44]
            })
          ]),
          _: 1,
          __: [45]
        }),
        _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
          default: _withCtx(() => [
            (error.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "error",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(error.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (successMessage.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 1,
                  type: "success",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(successMessage.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card, {
              flat: "",
              class: "rounded mb-3 border"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-wrench",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[46] || (_cache[46] = _createElementVNode("span", null, "操作面板", -1))
                  ]),
                  _: 1,
                  __: [46]
                }),
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_row, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              block: "",
                              onClick: loadIdentifiers,
                              loading: loading.value
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-refresh",
                                  class: "mr-1"
                                }),
                                _cache[47] || (_cache[47] = _createTextVNode(" 重新加载 "))
                              ]),
                              _: 1,
                              __: [47]
                            }, 8, ["loading"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              color: "success",
                              block: "",
                              onClick: saveIdentifiers,
                              loading: saving.value
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-content-save",
                                  class: "mr-1"
                                }),
                                _cache[48] || (_cache[48] = _createTextVNode(" 保存修改 "))
                              ]),
                              _: 1,
                              __: [48]
                            }, 8, ["loading"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              color: "info",
                              block: "",
                              onClick: _cache[0] || (_cache[0] = $event => (showAddCategoryDialog.value = true))
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-folder-plus",
                                  class: "mr-1"
                                }),
                                _cache[49] || (_cache[49] = _createTextVNode(" 添加分类 "))
                              ]),
                              _: 1,
                              __: [49]
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              color: "warning",
                              block: "",
                              onClick: _cache[1] || (_cache[1] = $event => (showQuickAddDialog.value = true))
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-plus-circle",
                                  class: "mr-1"
                                }),
                                _cache[50] || (_cache[50] = _createTextVNode(" 快速添加 "))
                              ]),
                              _: 1,
                              __: [50]
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card, {
              flat: "",
              class: "rounded mb-3 border"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_row, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_text_field, {
                              modelValue: searchKeyword.value,
                              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((searchKeyword).value = $event)),
                              density: "compact",
                              variant: "outlined",
                              "hide-details": "",
                              placeholder: "搜索识别词...",
                              "prepend-inner-icon": "mdi-magnify",
                              clearable: ""
                            }, null, 8, ["modelValue"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_select, {
                              modelValue: selectedTag.value,
                              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((selectedTag).value = $event)),
                              items: _ctx.tagOptions,
                              density: "compact",
                              variant: "outlined",
                              "hide-details": "",
                              placeholder: "选择标签过滤...",
                              "prepend-inner-icon": "mdi-tag",
                              clearable: ""
                            }, null, 8, ["modelValue", "items"])
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card, {
              flat: "",
              class: "rounded border"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-file-tree",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[51] || (_cache[51] = _createElementVNode("span", null, "识别词树形管理", -1)),
                    _createVNode(_component_v_spacer),
                    _createElementVNode("span", _hoisted_2, "共 " + _toDisplayString(filteredIdentifiers.value.length) + " 条", 1)
                  ]),
                  _: 1,
                  __: [51]
                }),
                _createVNode(_component_v_card_text, { class: "px-0 py-0" }, {
                  default: _withCtx(() => [
                    (loading.value)
                      ? (_openBlock(), _createBlock(_component_v_progress_linear, {
                          key: 0,
                          indeterminate: "",
                          color: "primary"
                        }))
                      : _createCommentVNode("", true),
                    (hierarchicalData.value && hierarchicalData.value.length > 0)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_3, [
                          _createElementVNode("div", _hoisted_4, [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(hierarchicalData.value, (category) => {
                              return (_openBlock(), _createElementBlock("div", {
                                key: category.id,
                                class: "category-node mb-3"
                              }, [
                                _createVNode(_component_v_card, {
                                  class: _normalizeClass(["mb-2", {'expanded': category.expanded}])
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_card_title, {
                                      class: "py-2 px-3 category-header",
                                      onClick: $event => (toggleCategory(category))
                                    }, {
                                      default: _withCtx(() => [
                                        _createElementVNode("div", _hoisted_5, [
                                          _createVNode(_component_v_icon, {
                                            icon: category.expanded ? 'mdi-folder-open' : 'mdi-folder',
                                            class: "mr-2",
                                            size: "small",
                                            color: "primary"
                                          }, null, 8, ["icon"]),
                                          _createElementVNode("span", _hoisted_6, _toDisplayString(category.name), 1),
                                          _createVNode(_component_v_spacer),
                                          _createVNode(_component_v_chip, {
                                            size: "x-small",
                                            color: "primary",
                                            class: "mr-2"
                                          }, {
                                            default: _withCtx(() => [
                                              _createTextVNode(_toDisplayString(getTotalCount(category)), 1)
                                            ]),
                                            _: 2
                                          }, 1024),
                                          _createVNode(_component_v_btn, {
                                            icon: "",
                                            size: "x-small",
                                            variant: "text",
                                            onClick: _withModifiers($event => (addSubCategory(category)), ["stop"])
                                          }, {
                                            default: _withCtx(() => [
                                              _createVNode(_component_v_icon, {
                                                icon: "mdi-folder-plus",
                                                size: "small"
                                              })
                                            ]),
                                            _: 2
                                          }, 1032, ["onClick"]),
                                          _createVNode(_component_v_btn, {
                                            icon: "",
                                            size: "x-small",
                                            variant: "text",
                                            onClick: _withModifiers($event => (addIdentifierToCategory(category)), ["stop"])
                                          }, {
                                            default: _withCtx(() => [
                                              _createVNode(_component_v_icon, {
                                                icon: "mdi-plus",
                                                size: "small"
                                              })
                                            ]),
                                            _: 2
                                          }, 1032, ["onClick"]),
                                          (category.name !== '未分类')
                                            ? (_openBlock(), _createBlock(_component_v_btn, {
                                                key: 0,
                                                icon: "",
                                                size: "x-small",
                                                variant: "text",
                                                color: "error",
                                                onClick: _withModifiers($event => (deleteCategory(category)), ["stop"])
                                              }, {
                                                default: _withCtx(() => [
                                                  _createVNode(_component_v_icon, {
                                                    icon: "mdi-delete",
                                                    size: "small"
                                                  })
                                                ]),
                                                _: 2
                                              }, 1032, ["onClick"]))
                                            : _createCommentVNode("", true)
                                        ])
                                      ]),
                                      _: 2
                                    }, 1032, ["onClick"]),
                                    _createVNode(_component_v_expand_transition, null, {
                                      default: _withCtx(() => [
                                        _withDirectives(_createElementVNode("div", null, [
                                          _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                                            default: _withCtx(() => [
                                              (category.subCategories && category.subCategories.length > 0)
                                                ? (_openBlock(), _createElementBlock("div", _hoisted_7, [
                                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(category.subCategories, (subCategory) => {
                                                      return (_openBlock(), _createElementBlock("div", {
                                                        key: subCategory.id,
                                                        class: "sub-category-node mb-2 ml-4"
                                                      }, [
                                                        _createVNode(_component_v_card, {
                                                          variant: "outlined",
                                                          class: "sub-category-card"
                                                        }, {
                                                          default: _withCtx(() => [
                                                            _createVNode(_component_v_card_title, {
                                                              class: "py-1 px-2 text-caption",
                                                              onClick: $event => (toggleSubCategory(subCategory))
                                                            }, {
                                                              default: _withCtx(() => [
                                                                _createElementVNode("div", _hoisted_8, [
                                                                  _createVNode(_component_v_icon, {
                                                                    icon: subCategory.expanded ? 'mdi-folder-open-outline' : 'mdi-folder-outline',
                                                                    class: "mr-2",
                                                                    size: "small",
                                                                    color: "info"
                                                                  }, null, 8, ["icon"]),
                                                                  _createElementVNode("span", _hoisted_9, _toDisplayString(subCategory.name), 1),
                                                                  _createVNode(_component_v_spacer),
                                                                  _createVNode(_component_v_chip, {
                                                                    size: "x-small",
                                                                    color: "info",
                                                                    class: "mr-2"
                                                                  }, {
                                                                    default: _withCtx(() => [
                                                                      _createTextVNode(_toDisplayString(subCategory.identifiers.length), 1)
                                                                    ]),
                                                                    _: 2
                                                                  }, 1024),
                                                                  _createVNode(_component_v_btn, {
                                                                    icon: "",
                                                                    size: "x-small",
                                                                    variant: "text",
                                                                    onClick: _withModifiers($event => (addIdentifierToSubCategory(subCategory)), ["stop"])
                                                                  }, {
                                                                    default: _withCtx(() => [
                                                                      _createVNode(_component_v_icon, {
                                                                        icon: "mdi-plus",
                                                                        size: "small"
                                                                      })
                                                                    ]),
                                                                    _: 2
                                                                  }, 1032, ["onClick"]),
                                                                  _createVNode(_component_v_btn, {
                                                                    icon: "",
                                                                    size: "x-small",
                                                                    variant: "text",
                                                                    color: "error",
                                                                    onClick: _withModifiers($event => (deleteSubCategory(category, subCategory)), ["stop"])
                                                                  }, {
                                                                    default: _withCtx(() => [
                                                                      _createVNode(_component_v_icon, {
                                                                        icon: "mdi-delete",
                                                                        size: "small"
                                                                      })
                                                                    ]),
                                                                    _: 2
                                                                  }, 1032, ["onClick"])
                                                                ])
                                                              ]),
                                                              _: 2
                                                            }, 1032, ["onClick"]),
                                                            _createVNode(_component_v_expand_transition, null, {
                                                              default: _withCtx(() => [
                                                                _withDirectives(_createElementVNode("div", null, [
                                                                  _createVNode(_component_v_card_text, { class: "px-2 py-1" }, {
                                                                    default: _withCtx(() => [
                                                                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(subCategory.identifiers, (identifier, idx) => {
                                                                        return (_openBlock(), _createElementBlock("div", {
                                                                          key: idx,
                                                                          class: "identifier-item d-flex align-center py-1 px-2 mb-1 rounded"
                                                                        }, [
                                                                          _createVNode(_component_v_icon, {
                                                                            icon: getTypeIcon(identifier.type),
                                                                            color: getTypeColor(identifier.type),
                                                                            size: "small",
                                                                            class: "mr-2"
                                                                          }, null, 8, ["icon", "color"]),
                                                                          _createVNode(_component_v_chip, {
                                                                            size: "x-small",
                                                                            color: getTypeColor(identifier.type),
                                                                            class: "mr-2"
                                                                          }, {
                                                                            default: _withCtx(() => [
                                                                              _createTextVNode(_toDisplayString(identifier.type), 1)
                                                                            ]),
                                                                            _: 2
                                                                          }, 1032, ["color"]),
                                                                          _createElementVNode("span", _hoisted_10, _toDisplayString(getDisplayContent(identifier)), 1),
                                                                          _createElementVNode("div", _hoisted_11, [
                                                                            _createVNode(_component_v_btn, {
                                                                              icon: "",
                                                                              size: "x-small",
                                                                              variant: "text",
                                                                              onClick: $event => (editIdentifierAdvanced(identifier, category, subCategory))
                                                                            }, {
                                                                              default: _withCtx(() => [
                                                                                _createVNode(_component_v_icon, {
                                                                                  icon: "mdi-pencil",
                                                                                  size: "small"
                                                                                })
                                                                              ]),
                                                                              _: 2
                                                                            }, 1032, ["onClick"]),
                                                                            _createVNode(_component_v_btn, {
                                                                              icon: "",
                                                                              size: "x-small",
                                                                              variant: "text",
                                                                              color: "error",
                                                                              onClick: $event => (deleteIdentifierAdvanced(identifier, category, subCategory))
                                                                            }, {
                                                                              default: _withCtx(() => [
                                                                                _createVNode(_component_v_icon, {
                                                                                  icon: "mdi-delete",
                                                                                  size: "small"
                                                                                })
                                                                              ]),
                                                                              _: 2
                                                                            }, 1032, ["onClick"])
                                                                          ])
                                                                        ]))
                                                                      }), 128))
                                                                    ]),
                                                                    _: 2
                                                                  }, 1024)
                                                                ], 512), [
                                                                  [_vShow, subCategory.expanded]
                                                                ])
                                                              ]),
                                                              _: 2
                                                            }, 1024)
                                                          ]),
                                                          _: 2
                                                        }, 1024)
                                                      ]))
                                                    }), 128))
                                                  ]))
                                                : _createCommentVNode("", true),
                                              (category.identifiers && category.identifiers.length > 0)
                                                ? (_openBlock(), _createElementBlock("div", _hoisted_12, [
                                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(category.identifiers, (identifier, idx) => {
                                                      return (_openBlock(), _createElementBlock("div", {
                                                        key: idx,
                                                        class: "identifier-item d-flex align-center py-2 px-2 mb-1 rounded border"
                                                      }, [
                                                        _createVNode(_component_v_icon, {
                                                          icon: getTypeIcon(identifier.type),
                                                          color: getTypeColor(identifier.type),
                                                          size: "small",
                                                          class: "mr-3"
                                                        }, null, 8, ["icon", "color"]),
                                                        _createVNode(_component_v_chip, {
                                                          size: "x-small",
                                                          color: getTypeColor(identifier.type),
                                                          class: "mr-2"
                                                        }, {
                                                          default: _withCtx(() => [
                                                            _createTextVNode(_toDisplayString(identifier.type), 1)
                                                          ]),
                                                          _: 2
                                                        }, 1032, ["color"]),
                                                        _createElementVNode("span", _hoisted_13, _toDisplayString(getDisplayContent(identifier)), 1),
                                                        _createElementVNode("div", _hoisted_14, [
                                                          _createVNode(_component_v_btn, {
                                                            icon: "",
                                                            size: "small",
                                                            variant: "text",
                                                            onClick: $event => (editIdentifierAdvanced(identifier, category))
                                                          }, {
                                                            default: _withCtx(() => [
                                                              _createVNode(_component_v_icon, {
                                                                icon: "mdi-pencil",
                                                                size: "small"
                                                              })
                                                            ]),
                                                            _: 2
                                                          }, 1032, ["onClick"]),
                                                          _createVNode(_component_v_btn, {
                                                            icon: "",
                                                            size: "small",
                                                            variant: "text",
                                                            color: "error",
                                                            onClick: $event => (deleteIdentifierAdvanced(identifier))
                                                          }, {
                                                            default: _withCtx(() => [
                                                              _createVNode(_component_v_icon, {
                                                                icon: "mdi-delete",
                                                                size: "small"
                                                              })
                                                            ]),
                                                            _: 2
                                                          }, 1032, ["onClick"])
                                                        ])
                                                      ]))
                                                    }), 128))
                                                  ]))
                                                : _createCommentVNode("", true)
                                            ]),
                                            _: 2
                                          }, 1024)
                                        ], 512), [
                                          [_vShow, category.expanded]
                                        ])
                                      ]),
                                      _: 2
                                    }, 1024)
                                  ]),
                                  _: 2
                                }, 1032, ["class"])
                              ]))
                            }), 128))
                          ])
                        ]))
                      : (_openBlock(), _createElementBlock("div", _hoisted_15, [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-emoticon-sad",
                            size: "large",
                            color: "grey",
                            class: "mb-2"
                          }),
                          _cache[52] || (_cache[52] = _createElementVNode("div", { class: "text-subtitle-2 text-grey" }, "暂无识别词", -1)),
                          _cache[53] || (_cache[53] = _createElementVNode("div", { class: "text-caption text-grey" }, "点击\"重新加载\"获取数据或\"添加分类\"开始使用", -1))
                        ]))
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_dialog, {
      modelValue: showAddCategoryDialog.value,
      "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((showAddCategoryDialog).value = $event)),
      "max-width": "500"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => _cache[54] || (_cache[54] = [
                _createTextVNode("添加新分类")
              ])),
              _: 1,
              __: [54]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_text_field, {
                  modelValue: newCategoryName.value,
                  "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((newCategoryName).value = $event)),
                  label: "分类名称",
                  variant: "outlined",
                  density: "compact",
                  placeholder: "输入分类名称",
                  rules: [v => !!v || '分类名称不能为空']
                }, null, 8, ["modelValue", "rules"]),
                _createVNode(_component_v_text_field, {
                  modelValue: newCategoryDescription.value,
                  "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((newCategoryDescription).value = $event)),
                  label: "分类描述（可选）",
                  variant: "outlined",
                  density: "compact",
                  placeholder: "输入分类描述"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[6] || (_cache[6] = $event => (showAddCategoryDialog.value = false))
                }, {
                  default: _withCtx(() => _cache[55] || (_cache[55] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1,
                  __: [55]
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: addNewCategory
                }, {
                  default: _withCtx(() => _cache[56] || (_cache[56] = [
                    _createTextVNode("确认")
                  ])),
                  _: 1,
                  __: [56]
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showAddSubCategoryDialog.value,
      "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((showAddSubCategoryDialog).value = $event)),
      "max-width": "500"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [
                _createTextVNode("添加子分类到 " + _toDisplayString(currentParentCategory.value?.name), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_text_field, {
                  modelValue: newSubCategoryName.value,
                  "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((newSubCategoryName).value = $event)),
                  label: "子分类名称",
                  variant: "outlined",
                  density: "compact",
                  placeholder: "输入子分类名称",
                  rules: [v => !!v || '子分类名称不能为空']
                }, null, 8, ["modelValue", "rules"]),
                _createVNode(_component_v_text_field, {
                  modelValue: newSubCategoryDescription.value,
                  "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((newSubCategoryDescription).value = $event)),
                  label: "子分类描述（可选）",
                  variant: "outlined",
                  density: "compact",
                  placeholder: "输入子分类描述"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[10] || (_cache[10] = $event => (showAddSubCategoryDialog.value = false))
                }, {
                  default: _withCtx(() => _cache[57] || (_cache[57] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1,
                  __: [57]
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: addNewSubCategory
                }, {
                  default: _withCtx(() => _cache[58] || (_cache[58] = [
                    _createTextVNode("确认")
                  ])),
                  _: 1,
                  __: [58]
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showQuickAddDialog.value,
      "onUpdate:modelValue": _cache[27] || (_cache[27] = $event => ((showQuickAddDialog).value = $event)),
      "max-width": "700"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => _cache[59] || (_cache[59] = [
                _createTextVNode("快速添加识别词")
              ])),
              _: 1,
              __: [59]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: quickAddForm.value.category,
                          "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((quickAddForm.value.category) = $event)),
                          items: categorySelectOptions.value,
                          label: "选择分类（可选）",
                          variant: "outlined",
                          density: "compact",
                          class: "mb-3",
                          clearable: "",
                          hint: "留空将自动分配到'未分类'",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue", "items"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: quickAddForm.value.subCategory,
                          "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((quickAddForm.value.subCategory) = $event)),
                          items: subCategorySelectOptions.value,
                          label: "选择子分类（可选）",
                          variant: "outlined",
                          density: "compact",
                          class: "mb-3",
                          disabled: !quickAddForm.value.category
                        }, null, 8, ["modelValue", "items", "disabled"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_select, {
                  modelValue: quickAddForm.value.type,
                  "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((quickAddForm.value.type) = $event)),
                  items: typeOptions,
                  label: "识别词类型",
                  variant: "outlined",
                  density: "compact",
                  class: "mb-3"
                }, null, 8, ["modelValue"]),
                (quickAddForm.value.type === '屏蔽')
                  ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
                      _createVNode(_component_v_text_field, {
                        modelValue: quickAddForm.value.blockWord,
                        "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((quickAddForm.value.blockWord) = $event)),
                        label: "屏蔽词",
                        variant: "outlined",
                        density: "compact",
                        placeholder: "输入要屏蔽的词语",
                        hint: "这个词语将在识别时被过滤掉",
                        "persistent-hint": ""
                      }, null, 8, ["modelValue"])
                    ]))
                  : (quickAddForm.value.type === '替换')
                    ? (_openBlock(), _createElementBlock("div", _hoisted_17, [
                        _createVNode(_component_v_text_field, {
                          modelValue: quickAddForm.value.originalWord,
                          "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((quickAddForm.value.originalWord) = $event)),
                          label: "原词",
                          variant: "outlined",
                          density: "compact",
                          placeholder: "输入原词",
                          class: "mb-3"
                        }, null, 8, ["modelValue"]),
                        _createVNode(_component_v_text_field, {
                          modelValue: quickAddForm.value.replacementWord,
                          "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((quickAddForm.value.replacementWord) = $event)),
                          label: "替换词",
                          variant: "outlined",
                          density: "compact",
                          placeholder: "输入替换词",
                          hint: "原词将被替换为这个词",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue"])
                      ]))
                    : (quickAddForm.value.type === '集偏移')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_18, [
                          _createVNode(_component_v_text_field, {
                            modelValue: quickAddForm.value.frontLocator,
                            "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((quickAddForm.value.frontLocator) = $event)),
                            label: "前定位词",
                            variant: "outlined",
                            density: "compact",
                            placeholder: "输入前定位词",
                            class: "mb-3"
                          }, null, 8, ["modelValue"]),
                          _createVNode(_component_v_text_field, {
                            modelValue: quickAddForm.value.backLocator,
                            "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((quickAddForm.value.backLocator) = $event)),
                            label: "后定位词",
                            variant: "outlined",
                            density: "compact",
                            placeholder: "输入后定位词",
                            class: "mb-3"
                          }, null, 8, ["modelValue"]),
                          _createVNode(_component_v_text_field, {
                            modelValue: quickAddForm.value.offset,
                            "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((quickAddForm.value.offset) = $event)),
                            label: "偏移量",
                            variant: "outlined",
                            density: "compact",
                            placeholder: "例如：EP+1、EP-2",
                            hint: "EP+数字表示向后偏移，EP-数字表示向前偏移",
                            "persistent-hint": ""
                          }, null, 8, ["modelValue"])
                        ]))
                      : (quickAddForm.value.type === '替换和集偏移')
                        ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "6"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: quickAddForm.value.originalWord,
                                      "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((quickAddForm.value.originalWord) = $event)),
                                      label: "原词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "输入原词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "6"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: quickAddForm.value.replacementWord,
                                      "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((quickAddForm.value.replacementWord) = $event)),
                                      label: "替换词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "输入替换词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                })
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "4"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: quickAddForm.value.frontLocator,
                                      "onUpdate:modelValue": _cache[23] || (_cache[23] = $event => ((quickAddForm.value.frontLocator) = $event)),
                                      label: "前定位词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "前定位词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "4"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: quickAddForm.value.backLocator,
                                      "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => ((quickAddForm.value.backLocator) = $event)),
                                      label: "后定位词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "后定位词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "4"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: quickAddForm.value.offset,
                                      "onUpdate:modelValue": _cache[25] || (_cache[25] = $event => ((quickAddForm.value.offset) = $event)),
                                      label: "偏移量",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "EP+1"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                })
                              ]),
                              _: 1
                            })
                          ]))
                        : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[26] || (_cache[26] = $event => (showQuickAddDialog.value = false))
                }, {
                  default: _withCtx(() => _cache[60] || (_cache[60] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1,
                  __: [60]
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: saveQuickAdd,
                  disabled: !isQuickAddValid.value
                }, {
                  default: _withCtx(() => _cache[61] || (_cache[61] = [
                    _createTextVNode("添加")
                  ])),
                  _: 1,
                  __: [61]
                }, 8, ["disabled"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showAdvancedEditDialog.value,
      "onUpdate:modelValue": _cache[43] || (_cache[43] = $event => ((showAdvancedEditDialog).value = $event)),
      "max-width": "700"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => _cache[62] || (_cache[62] = [
                _createTextVNode("编辑识别词")
              ])),
              _: 1,
              __: [62]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: editForm.value.category,
                          "onUpdate:modelValue": _cache[28] || (_cache[28] = $event => ((editForm.value.category) = $event)),
                          items: categorySelectOptions.value,
                          label: "选择分类（可选）",
                          variant: "outlined",
                          density: "compact",
                          class: "mb-3",
                          clearable: "",
                          hint: "留空将自动分配到'未分类'",
                          "persistent-hint": ""
                        }, null, 8, ["modelValue", "items"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: editForm.value.subCategory,
                          "onUpdate:modelValue": _cache[29] || (_cache[29] = $event => ((editForm.value.subCategory) = $event)),
                          items: subCategorySelectOptions.value,
                          label: "选择子分类（可选）",
                          variant: "outlined",
                          density: "compact",
                          class: "mb-3",
                          disabled: !editForm.value.category
                        }, null, 8, ["modelValue", "items", "disabled"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_select, {
                  modelValue: editForm.value.type,
                  "onUpdate:modelValue": _cache[30] || (_cache[30] = $event => ((editForm.value.type) = $event)),
                  items: typeOptions,
                  label: "识别词类型",
                  variant: "outlined",
                  density: "compact",
                  class: "mb-3"
                }, null, 8, ["modelValue"]),
                (editForm.value.type === '屏蔽')
                  ? (_openBlock(), _createElementBlock("div", _hoisted_20, [
                      _createVNode(_component_v_text_field, {
                        modelValue: editForm.value.blockWord,
                        "onUpdate:modelValue": _cache[31] || (_cache[31] = $event => ((editForm.value.blockWord) = $event)),
                        label: "屏蔽词",
                        variant: "outlined",
                        density: "compact",
                        placeholder: "输入要屏蔽的词语"
                      }, null, 8, ["modelValue"])
                    ]))
                  : (editForm.value.type === '替换')
                    ? (_openBlock(), _createElementBlock("div", _hoisted_21, [
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.originalWord,
                          "onUpdate:modelValue": _cache[32] || (_cache[32] = $event => ((editForm.value.originalWord) = $event)),
                          label: "原词",
                          variant: "outlined",
                          density: "compact",
                          placeholder: "输入原词",
                          class: "mb-3"
                        }, null, 8, ["modelValue"]),
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.replacementWord,
                          "onUpdate:modelValue": _cache[33] || (_cache[33] = $event => ((editForm.value.replacementWord) = $event)),
                          label: "替换词",
                          variant: "outlined",
                          density: "compact",
                          placeholder: "输入替换词"
                        }, null, 8, ["modelValue"])
                      ]))
                    : (editForm.value.type === '集偏移')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_22, [
                          _createVNode(_component_v_text_field, {
                            modelValue: editForm.value.frontLocator,
                            "onUpdate:modelValue": _cache[34] || (_cache[34] = $event => ((editForm.value.frontLocator) = $event)),
                            label: "前定位词",
                            variant: "outlined",
                            density: "compact",
                            placeholder: "输入前定位词",
                            class: "mb-3"
                          }, null, 8, ["modelValue"]),
                          _createVNode(_component_v_text_field, {
                            modelValue: editForm.value.backLocator,
                            "onUpdate:modelValue": _cache[35] || (_cache[35] = $event => ((editForm.value.backLocator) = $event)),
                            label: "后定位词",
                            variant: "outlined",
                            density: "compact",
                            placeholder: "输入后定位词",
                            class: "mb-3"
                          }, null, 8, ["modelValue"]),
                          _createVNode(_component_v_text_field, {
                            modelValue: editForm.value.offset,
                            "onUpdate:modelValue": _cache[36] || (_cache[36] = $event => ((editForm.value.offset) = $event)),
                            label: "偏移量",
                            variant: "outlined",
                            density: "compact",
                            placeholder: "例如：EP+1、EP-2"
                          }, null, 8, ["modelValue"])
                        ]))
                      : (editForm.value.type === '替换和集偏移')
                        ? (_openBlock(), _createElementBlock("div", _hoisted_23, [
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "6"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: editForm.value.originalWord,
                                      "onUpdate:modelValue": _cache[37] || (_cache[37] = $event => ((editForm.value.originalWord) = $event)),
                                      label: "原词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "输入原词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "6"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: editForm.value.replacementWord,
                                      "onUpdate:modelValue": _cache[38] || (_cache[38] = $event => ((editForm.value.replacementWord) = $event)),
                                      label: "替换词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "输入替换词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                })
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_row, null, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "4"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: editForm.value.frontLocator,
                                      "onUpdate:modelValue": _cache[39] || (_cache[39] = $event => ((editForm.value.frontLocator) = $event)),
                                      label: "前定位词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "前定位词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "4"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: editForm.value.backLocator,
                                      "onUpdate:modelValue": _cache[40] || (_cache[40] = $event => ((editForm.value.backLocator) = $event)),
                                      label: "后定位词",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "后定位词"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                }),
                                _createVNode(_component_v_col, {
                                  cols: "12",
                                  md: "4"
                                }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_text_field, {
                                      modelValue: editForm.value.offset,
                                      "onUpdate:modelValue": _cache[41] || (_cache[41] = $event => ((editForm.value.offset) = $event)),
                                      label: "偏移量",
                                      variant: "outlined",
                                      density: "compact",
                                      placeholder: "EP+1"
                                    }, null, 8, ["modelValue"])
                                  ]),
                                  _: 1
                                })
                              ]),
                              _: 1
                            })
                          ]))
                        : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[42] || (_cache[42] = $event => (showAdvancedEditDialog.value = false))
                }, {
                  default: _withCtx(() => _cache[63] || (_cache[63] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1,
                  __: [63]
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: saveAdvancedEdit,
                  disabled: !isEditFormValid.value
                }, {
                  default: _withCtx(() => _cache[64] || (_cache[64] = [
                    _createTextVNode("保存")
                  ])),
                  _: 1,
                  __: [64]
                }, 8, ["disabled"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-d92b4dc5"]]);

export { Page as default };
