import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock,renderList:_renderList,Fragment:_Fragment,withModifiers:_withModifiers,withKeys:_withKeys} = await importShared('vue');


const _hoisted_1 = { class: "plugin-page" };
const _hoisted_2 = { class: "status-item d-flex align-center py-2" };
const _hoisted_3 = { class: "status-content flex-grow-1" };
const _hoisted_4 = { class: "text-caption text-grey" };
const _hoisted_5 = { class: "status-item d-flex align-center py-2" };
const _hoisted_6 = { class: "status-content flex-grow-1" };
const _hoisted_7 = { class: "text-caption text-grey" };
const _hoisted_8 = { class: "status-item d-flex align-center py-2" };
const _hoisted_9 = { class: "status-content flex-grow-1" };
const _hoisted_10 = { class: "text-caption text-grey" };
const _hoisted_11 = { class: "status-item d-flex align-center py-2" };
const _hoisted_12 = { class: "status-content flex-grow-1" };
const _hoisted_13 = { class: "text-caption text-grey" };
const _hoisted_14 = {
  key: 0,
  class: "directory-content"
};
const _hoisted_15 = { class: "text-subtitle-2 text-primary cursor-pointer" };
const _hoisted_16 = ["onClick"];
const _hoisted_17 = { class: "flex-grow-1 d-flex align-center" };
const _hoisted_18 = { class: "text-subtitle-2 cursor-pointer" };
const _hoisted_19 = {
  key: 1,
  class: "media-item d-flex align-center py-2"
};
const _hoisted_20 = { class: "flex-grow-1" };
const _hoisted_21 = { class: "d-flex align-center" };
const _hoisted_22 = { class: "text-subtitle-2" };
const _hoisted_23 = {
  key: 2,
  class: "text-center py-4"
};
const _hoisted_24 = {
  key: 1,
  class: "text-center py-4"
};
const _hoisted_25 = {
  key: 2,
  class: "text-center py-4"
};
const _hoisted_26 = { class: "text-caption text-grey mb-2" };
const _hoisted_27 = { key: 0 };
const _hoisted_28 = { key: 1 };
const _hoisted_29 = { key: 2 };

const {ref,reactive,onMounted,onUnmounted,computed} = await importShared('vue');



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

// 状态变量
const error = ref(null);
const successMessage = ref(null);
const running = ref(false);

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

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_radio = _resolveComponent("v-radio");
  const _component_v_radio_group = _resolveComponent("v-radio-group");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_list_item_subtitle = _resolveComponent("v-list-item-subtitle");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
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
              icon: "mdi-video",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[11] || (_cache[11] = _createElementVNode("span", null, "弹幕刮削", -1))
          ]),
          _: 1
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
              class: "rounded mb-3 border status-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-information",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[12] || (_cache[12] = _createElementVNode("span", null, "插件状态", -1))
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_row, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createElementVNode("div", _hoisted_2, [
                              _createVNode(_component_v_icon, {
                                icon: "mdi-power",
                                size: "small",
                                color: status.enabled ? 'success' : 'grey',
                                class: "mr-3"
                              }, null, 8, ["color"]),
                              _createElementVNode("div", _hoisted_3, [
                                _cache[13] || (_cache[13] = _createElementVNode("div", { class: "text-subtitle-2" }, "插件状态", -1)),
                                _createElementVNode("div", _hoisted_4, _toDisplayString(status.enabled ? '已启用' : '已禁用'), 1)
                              ])
                            ])
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
            (scrapingStatus.running)
              ? (_openBlock(), _createBlock(_component_v_card, {
                  key: 2,
                  flat: "",
                  class: "rounded mb-3 border status-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-progress-clock",
                          class: "mr-2",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[14] || (_cache[14] = _createElementVNode("span", null, "刮削进度", -1))
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_5, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-file-document",
                                    size: "small",
                                    color: "primary",
                                    class: "mr-3"
                                  }),
                                  _createElementVNode("div", _hoisted_6, [
                                    _cache[15] || (_cache[15] = _createElementVNode("div", { class: "text-subtitle-2" }, "当前文件", -1)),
                                    _createElementVNode("div", _hoisted_7, _toDisplayString(scrapingStatus.current_file || '等待中...'), 1)
                                  ])
                                ])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_8, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-counter",
                                    size: "small",
                                    color: "primary",
                                    class: "mr-3"
                                  }),
                                  _createElementVNode("div", _hoisted_9, [
                                    _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-subtitle-2" }, "处理进度", -1)),
                                    _createElementVNode("div", _hoisted_10, _toDisplayString(scrapingStatus.processed) + "/" + _toDisplayString(scrapingStatus.total) + " 个文件 (" + _toDisplayString(scrapingStatus.success) + " 成功, " + _toDisplayString(scrapingStatus.failed) + " 失败) ", 1)
                                  ])
                                ])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_11, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-clock-outline",
                                    size: "small",
                                    color: "primary",
                                    class: "mr-3"
                                  }),
                                  _createElementVNode("div", _hoisted_12, [
                                    _cache[17] || (_cache[17] = _createElementVNode("div", { class: "text-subtitle-2" }, "运行时间", -1)),
                                    _createElementVNode("div", _hoisted_13, _toDisplayString(formatDuration(scrapingStatus.duration)), 1)
                                  ])
                                ])
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
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card, {
              flat: "",
              class: "rounded mb-3 border status-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-folder",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[18] || (_cache[18] = _createElementVNode("span", null, "目录浏览", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_text_field, {
                      modelValue: searchKeyword.value,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((searchKeyword).value = $event)),
                      density: "compact",
                      variant: "outlined",
                      "hide-details": "",
                      placeholder: "搜索文件/目录",
                      "prepend-inner-icon": "mdi-magnify",
                      class: "search-field",
                      style: {"max-width":"200px"}
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_row, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, { cols: "12" }, {
                          default: _withCtx(() => [
                            (directoryContent.value)
                              ? (_openBlock(), _createElementBlock("div", _hoisted_14, [
                                  (loading.value)
                                    ? (_openBlock(), _createBlock(_component_v_progress_linear, {
                                        key: 0,
                                        indeterminate: "",
                                        color: "primary",
                                        class: "mb-2"
                                      }))
                                    : _createCommentVNode("", true),
                                  (currentPath.value)
                                    ? (_openBlock(), _createElementBlock("div", {
                                        key: 1,
                                        class: "back-item d-flex align-center py-2 mb-2",
                                        onClick: _cache[1] || (_cache[1] = $event => (goBack()))
                                      }, [
                                        _createVNode(_component_v_icon, {
                                          icon: "mdi-keyboard-backspace",
                                          size: "small",
                                          color: "primary",
                                          class: "mr-2"
                                        }),
                                        _createElementVNode("span", _hoisted_15, _toDisplayString(directoryContent.value.is_root ? '返回目录列表' : '返回上级目录'), 1)
                                      ]))
                                    : _createCommentVNode("", true),
                                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(filteredItems.value, (item, index) => {
                                    return (_openBlock(), _createElementBlock(_Fragment, { key: index }, [
                                      (item.type === 'directory')
                                        ? (_openBlock(), _createElementBlock("div", {
                                            key: 0,
                                            class: "directory-item d-flex align-center py-2",
                                            onClick: $event => (navigateToPath(item.path))
                                          }, [
                                            _createVNode(_component_v_icon, {
                                              icon: "mdi-folder",
                                              size: "small",
                                              color: "primary",
                                              class: "mr-2"
                                            }),
                                            _createElementVNode("div", _hoisted_17, [
                                              _createElementVNode("span", _hoisted_18, _toDisplayString(item.name), 1),
                                              (item.manual_match)
                                                ? (_openBlock(), _createBlock(_component_v_chip, {
                                                    key: 0,
                                                    size: "small",
                                                    color: "secondary",
                                                    class: "ml-2",
                                                    closable: "",
                                                    onClick: _cache[2] || (_cache[2] = _withModifiers(() => {}, ["stop"])),
                                                    "onClick:close": _withModifiers($event => (clearManualMatch(item, item.manual_scope)), ["stop"])
                                                  }, {
                                                    default: _withCtx(() => [
                                                      _createTextVNode(_toDisplayString(manualChipText(item)), 1)
                                                    ]),
                                                    _: 2
                                                  }, 1032, ["onClick:close"]))
                                                : _createCommentVNode("", true)
                                            ]),
                                            _createVNode(_component_v_btn, {
                                              icon: "mdi-magnify",
                                              size: "small",
                                              variant: "text",
                                              color: "secondary",
                                              class: "mr-1",
                                              onClick: _withModifiers($event => (openManualMatch(item)), ["stop"])
                                            }, null, 8, ["onClick"]),
                                            _createVNode(_component_v_icon, {
                                              icon: "mdi-chevron-right",
                                              size: "small",
                                              color: "grey"
                                            })
                                          ], 8, _hoisted_16))
                                        : (item.type === 'media')
                                          ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
                                              _createVNode(_component_v_icon, {
                                                icon: "mdi-video",
                                                size: "small",
                                                color: "info",
                                                class: "mr-2"
                                              }),
                                              _createElementVNode("div", _hoisted_20, [
                                                _createElementVNode("div", _hoisted_21, [
                                                  _createElementVNode("span", _hoisted_22, _toDisplayString(item.name), 1),
                                                  (item.danmu_count > 0)
                                                    ? (_openBlock(), _createBlock(_component_v_chip, {
                                                        key: 0,
                                                        size: "small",
                                                        color: "info",
                                                        class: "ml-2"
                                                      }, {
                                                        default: _withCtx(() => [
                                                          _createTextVNode(" 弹幕: " + _toDisplayString(item.danmu_count), 1)
                                                        ]),
                                                        _: 2
                                                      }, 1024))
                                                    : (_openBlock(), _createBlock(_component_v_chip, {
                                                        key: 1,
                                                        size: "small",
                                                        color: "grey",
                                                        class: "ml-2"
                                                      }, {
                                                        default: _withCtx(() => _cache[19] || (_cache[19] = [
                                                          _createTextVNode(" 无弹幕 ")
                                                        ])),
                                                        _: 1
                                                      })),
                                                  (item.manual_match)
                                                    ? (_openBlock(), _createBlock(_component_v_chip, {
                                                        key: 2,
                                                        size: "small",
                                                        color: "secondary",
                                                        class: "ml-2",
                                                        closable: "",
                                                        "onClick:close": _withModifiers($event => (clearManualMatch(item, item.manual_scope)), ["stop"])
                                                      }, {
                                                        default: _withCtx(() => [
                                                          _createTextVNode(_toDisplayString(manualChipText(item)), 1)
                                                        ]),
                                                        _: 2
                                                      }, 1032, ["onClick:close"]))
                                                    : _createCommentVNode("", true)
                                                ])
                                              ]),
                                              _createVNode(_component_v_btn, {
                                                color: "secondary",
                                                size: "small",
                                                variant: "text",
                                                class: "mr-1",
                                                onClick: $event => (openManualMatch(item))
                                              }, {
                                                default: _withCtx(() => [
                                                  _createVNode(_component_v_icon, {
                                                    icon: "mdi-magnify",
                                                    size: "small",
                                                    class: "mr-1"
                                                  }),
                                                  _cache[20] || (_cache[20] = _createTextVNode(" 手动匹配 "))
                                                ]),
                                                _: 2
                                              }, 1032, ["onClick"]),
                                              _createVNode(_component_v_btn, {
                                                color: "primary",
                                                size: "small",
                                                variant: "text",
                                                loading: item.generating,
                                                onClick: $event => (generateDanmu(item))
                                              }, {
                                                default: _withCtx(() => [
                                                  _createVNode(_component_v_icon, {
                                                    icon: "mdi-download",
                                                    size: "small",
                                                    class: "mr-1"
                                                  }),
                                                  _cache[21] || (_cache[21] = _createTextVNode(" 刮削 "))
                                                ]),
                                                _: 2
                                              }, 1032, ["loading", "onClick"])
                                            ]))
                                          : _createCommentVNode("", true)
                                    ], 64))
                                  }), 128)),
                                  (directoryContent.value.children && directoryContent.value.children.length === 0)
                                    ? (_openBlock(), _createElementBlock("div", _hoisted_23, [
                                        _createVNode(_component_v_alert, {
                                          type: "info",
                                          density: "compact",
                                          class: "mb-2 text-caption",
                                          variant: "tonal"
                                        }, {
                                          default: _withCtx(() => _cache[22] || (_cache[22] = [
                                            _createTextVNode(" 该目录为空或没有支持的媒体文件 ")
                                          ])),
                                          _: 1
                                        })
                                      ]))
                                    : _createCommentVNode("", true)
                                ]))
                              : (!directoryContent.value && error.value)
                                ? (_openBlock(), _createElementBlock("div", _hoisted_24, [
                                    _createVNode(_component_v_alert, {
                                      type: "error",
                                      density: "compact",
                                      class: "mb-2 text-caption",
                                      variant: "tonal"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(error.value), 1)
                                      ]),
                                      _: 1
                                    })
                                  ]))
                                : (_openBlock(), _createElementBlock("div", _hoisted_25, [
                                    _createVNode(_component_v_alert, {
                                      type: "info",
                                      density: "compact",
                                      class: "mb-2 text-caption",
                                      variant: "tonal"
                                    }, {
                                      default: _withCtx(() => _cache[23] || (_cache[23] = [
                                        _createTextVNode(" 请先在配置中设置刮削路径 ")
                                      ])),
                                      _: 1
                                    })
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
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_divider),
        _createVNode(_component_v_card_actions, { class: "px-2 py-1" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "info",
              onClick: _cache[3] || (_cache[3] = $event => (emit('switch'))),
              "prepend-icon": "mdi-cog",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[24] || (_cache[24] = [
                _createTextVNode("配置")
              ])),
              _: 1
            }),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "grey",
              onClick: _cache[4] || (_cache[4] = $event => (emit('close'))),
              "prepend-icon": "mdi-close",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[25] || (_cache[25] = [
                _createTextVNode("关闭")
              ])),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_dialog, {
      modelValue: manualDialog.value,
      "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((manualDialog).value = $event)),
      "max-width": "720"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => _cache[26] || (_cache[26] = [
                _createTextVNode(" 手动匹配弹幕 ")
              ])),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_26, " 当前选择：" + _toDisplayString(manualTargetItem.value?.name || '未选择文件'), 1),
                (manualExistingMatch.value)
                  ? (_openBlock(), _createBlock(_component_v_alert, {
                      key: 0,
                      type: "info",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-2 text-caption"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(" 已匹配（" + _toDisplayString(scopeLabel(manualExistingScope.value)) + "）：" + _toDisplayString(manualExistingMatch.value.animeTitle || `ID ${manualExistingMatch.value.animeId}`), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                (manualSearchError.value)
                  ? (_openBlock(), _createBlock(_component_v_alert, {
                      key: 1,
                      type: "error",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-2 text-caption",
                      closable: "",
                      "onClick:close": _cache[5] || (_cache[5] = $event => (manualSearchError.value = null))
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(manualSearchError.value), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: manualSearchKeyword.value,
                          "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((manualSearchKeyword).value = $event)),
                          label: "搜索关键字",
                          density: "compact",
                          variant: "outlined",
                          clearable: "",
                          "hide-details": "",
                          onKeyup: _withKeys(performManualSearch, ["enter"])
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: manualSearchType.value,
                          "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((manualSearchType).value = $event)),
                          items: manualTypeOptions,
                          "item-title": "title",
                          "item-value": "value",
                          density: "compact",
                          variant: "outlined",
                          "hide-details": "",
                          label: "类型"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "2",
                      class: "d-flex align-center"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_btn, {
                          color: "primary",
                          block: "",
                          loading: manualSearchLoading.value,
                          onClick: performManualSearch
                        }, {
                          default: _withCtx(() => _cache[27] || (_cache[27] = [
                            _createTextVNode(" 搜索 ")
                          ])),
                          _: 1
                        }, 8, ["loading"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (manualSearchLoading.value)
                  ? (_openBlock(), _createBlock(_component_v_progress_linear, {
                      key: 2,
                      indeterminate: "",
                      color: "primary",
                      class: "mb-2"
                    }))
                  : _createCommentVNode("", true),
                (manualTargetItem.value && manualTargetItem.value.type === 'media')
                  ? (_openBlock(), _createBlock(_component_v_row, { key: 3 }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, { cols: "12" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_radio_group, {
                              modelValue: manualScope.value,
                              "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((manualScope).value = $event)),
                              inline: "",
                              density: "compact",
                              "hide-details": ""
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_radio, {
                                  label: "仅当前文件",
                                  value: "file"
                                }),
                                _createVNode(_component_v_radio, {
                                  label: "整目录",
                                  value: "directory"
                                })
                              ]),
                              _: 1
                            }, 8, ["modelValue"])
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                (!manualSearchLoading.value && manualSearchPerformed.value && manualSearchResults.value.length === 0)
                  ? (_openBlock(), _createBlock(_component_v_alert, {
                      key: 4,
                      type: "info",
                      density: "compact",
                      variant: "tonal",
                      class: "mb-2 text-caption"
                    }, {
                      default: _withCtx(() => _cache[28] || (_cache[28] = [
                        _createTextVNode(" 未找到匹配结果，请调整关键字后再试。 ")
                      ])),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                (manualSearchResults.value.length > 0)
                  ? (_openBlock(), _createBlock(_component_v_list, {
                      key: 5,
                      lines: "two",
                      density: "comfortable"
                    }, {
                      default: _withCtx(() => [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(manualSearchResults.value, (anime) => {
                          return (_openBlock(), _createBlock(_component_v_list_item, {
                            key: anime.animeId,
                            active: manualSelected.value && manualSelected.value.animeId === anime.animeId,
                            onClick: $event => (selectManualResult(anime))
                          }, {
                            append: _withCtx(() => [
                              _createVNode(_component_v_btn, {
                                icon: "mdi-check",
                                size: "small",
                                variant: "text",
                                color: manualSelected.value && manualSelected.value.animeId === anime.animeId ? 'primary' : 'grey'
                              }, null, 8, ["color"])
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_title, null, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(anime.animeTitle), 1)
                                ]),
                                _: 2
                              }, 1024),
                              _createVNode(_component_v_list_item_subtitle, null, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(anime.typeDescription || '未知类型') + " ", 1),
                                  (anime.episodeCount)
                                    ? (_openBlock(), _createElementBlock("span", _hoisted_27, " · " + _toDisplayString(anime.episodeCount) + " 集", 1))
                                    : _createCommentVNode("", true),
                                  (anime.rating)
                                    ? (_openBlock(), _createElementBlock("span", _hoisted_28, " · 评分 " + _toDisplayString(anime.rating), 1))
                                    : _createCommentVNode("", true),
                                  (anime.startDate)
                                    ? (_openBlock(), _createElementBlock("span", _hoisted_29, " · " + _toDisplayString(formatDate(anime.startDate)), 1))
                                    : _createCommentVNode("", true)
                                ]),
                                _: 2
                              }, 1024)
                            ]),
                            _: 2
                          }, 1032, ["active", "onClick"]))
                        }), 128))
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                (manualExistingMatch.value)
                  ? (_openBlock(), _createBlock(_component_v_btn, {
                      key: 0,
                      color: "grey",
                      variant: "text",
                      onClick: _cache[9] || (_cache[9] = $event => (clearManualMatch(manualTargetItem.value, manualExistingScope.value || (manualTargetItem.value?.type === 'directory' ? 'directory' : 'file'), true)))
                    }, {
                      default: _withCtx(() => _cache[29] || (_cache[29] = [
                        _createTextVNode(" 清除匹配 ")
                      ])),
                      _: 1
                    }))
                  : _createCommentVNode("", true),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: closeManualDialog
                }, {
                  default: _withCtx(() => _cache[30] || (_cache[30] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  disabled: !manualSelected.value,
                  loading: manualSaving.value,
                  onClick: confirmManualMatch
                }, {
                  default: _withCtx(() => _cache[31] || (_cache[31] = [
                    _createTextVNode(" 保存 ")
                  ])),
                  _: 1
                }, 8, ["disabled", "loading"])
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-3bacb9fc"]]);

export { Page as default };
