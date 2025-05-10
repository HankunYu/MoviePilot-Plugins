import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass} = await importShared('vue');


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
  class: "directory-tree"
};
const _hoisted_15 = {
  key: 0,
  class: "directory-item"
};
const _hoisted_16 = ["onClick"];
const _hoisted_17 = { class: "text-subtitle-2" };
const _hoisted_18 = {
  key: 0,
  class: "pl-4"
};
const _hoisted_19 = {
  key: 0,
  class: "media-item d-flex align-center py-2"
};
const _hoisted_20 = { class: "flex-grow-1" };
const _hoisted_21 = { class: "d-flex align-center" };
const _hoisted_22 = { class: "text-subtitle-2" };
const _hoisted_23 = {
  key: 1,
  class: "directory-item"
};
const _hoisted_24 = ["onClick"];
const _hoisted_25 = { class: "text-subtitle-2" };
const _hoisted_26 = {
  key: 0,
  class: "pl-4"
};
const _hoisted_27 = {
  key: 0,
  class: "media-item d-flex align-center py-2"
};
const _hoisted_28 = { class: "flex-grow-1" };
const _hoisted_29 = { class: "d-flex align-center" };
const _hoisted_30 = { class: "text-subtitle-2" };
const _hoisted_31 = {
  key: 1,
  class: "text-center py-4"
};
const _hoisted_32 = {
  key: 2,
  class: "text-center py-4"
};

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
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_card_actions = _resolveComponent("v-card-actions");

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
            _cache[3] || (_cache[3] = _createElementVNode("span", null, "弹幕刮削", -1))
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
                    _cache[4] || (_cache[4] = _createElementVNode("span", null, "插件状态", -1))
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
                                _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-subtitle-2" }, "插件状态", -1)),
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
                        _cache[6] || (_cache[6] = _createElementVNode("span", null, "刮削进度", -1))
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
                                    _cache[7] || (_cache[7] = _createElementVNode("div", { class: "text-subtitle-2" }, "当前文件", -1)),
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
                                    _cache[8] || (_cache[8] = _createElementVNode("div", { class: "text-subtitle-2" }, "处理进度", -1)),
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
                                    _cache[9] || (_cache[9] = _createElementVNode("div", { class: "text-subtitle-2" }, "运行时间", -1)),
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
                    _cache[10] || (_cache[10] = _createElementVNode("span", null, "目录浏览", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_text_field, {
                      modelValue: searchKeyword.value,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((searchKeyword).value = $event)),
                      density: "compact",
                      variant: "outlined",
                      "hide-details": "",
                      placeholder: "仅过滤目录",
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
                            (directoryTree.value)
                              ? (_openBlock(), _createElementBlock("div", _hoisted_14, [
                                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(directoryTree.value.children, (item, index) => {
                                    return (_openBlock(), _createElementBlock("div", {
                                      key: index,
                                      class: _normalizeClass(["tree-item", { 'hidden': searchKeyword.value && item.type === 'directory' && !isDirectoryMatch(item, false) }])
                                    }, [
                                      (item.type === 'directory')
                                        ? (_openBlock(), _createElementBlock("div", _hoisted_15, [
                                            _createElementVNode("div", {
                                              class: "d-flex align-center py-2",
                                              onClick: $event => (toggleDirectory(item))
                                            }, [
                                              _createVNode(_component_v_icon, {
                                                icon: item.expanded ? 'mdi-folder-open' : 'mdi-folder',
                                                size: "small",
                                                color: "primary",
                                                class: "mr-2"
                                              }, null, 8, ["icon"]),
                                              _createElementVNode("span", _hoisted_17, _toDisplayString(item.name), 1)
                                            ], 8, _hoisted_16),
                                            (item.expanded)
                                              ? (_openBlock(), _createElementBlock("div", _hoisted_18, [
                                                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(item.children, (child, childIndex) => {
                                                    return (_openBlock(), _createElementBlock("div", {
                                                      key: childIndex,
                                                      class: _normalizeClass(["tree-item", { 'hidden': searchKeyword.value && child.type === 'directory' && !isDirectoryMatch(child, isDirectoryMatch(item, false)) }])
                                                    }, [
                                                      (child.type === 'media')
                                                        ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
                                                            _createVNode(_component_v_icon, {
                                                              icon: "mdi-video",
                                                              size: "small",
                                                              color: "info",
                                                              class: "mr-2"
                                                            }),
                                                            _createElementVNode("div", _hoisted_20, [
                                                              _createElementVNode("div", _hoisted_21, [
                                                                _createElementVNode("span", _hoisted_22, _toDisplayString(child.name), 1),
                                                                (child.danmu_count > 0)
                                                                  ? (_openBlock(), _createBlock(_component_v_chip, {
                                                                      key: 0,
                                                                      size: "small",
                                                                      color: "info",
                                                                      class: "ml-2"
                                                                    }, {
                                                                      default: _withCtx(() => [
                                                                        _createTextVNode(" 弹幕: " + _toDisplayString(child.danmu_count), 1)
                                                                      ]),
                                                                      _: 2
                                                                    }, 1024))
                                                                  : (_openBlock(), _createBlock(_component_v_chip, {
                                                                      key: 1,
                                                                      size: "small",
                                                                      color: "grey",
                                                                      class: "ml-2"
                                                                    }, {
                                                                      default: _withCtx(() => _cache[11] || (_cache[11] = [
                                                                        _createTextVNode(" 无弹幕 ")
                                                                      ])),
                                                                      _: 1
                                                                    }))
                                                              ])
                                                            ]),
                                                            _createVNode(_component_v_btn, {
                                                              color: "primary",
                                                              size: "small",
                                                              variant: "text",
                                                              loading: child.generating,
                                                              onClick: $event => (generateDanmu(child, item))
                                                            }, {
                                                              default: _withCtx(() => [
                                                                _createVNode(_component_v_icon, {
                                                                  icon: "mdi-download",
                                                                  size: "small",
                                                                  class: "mr-1"
                                                                }),
                                                                _cache[12] || (_cache[12] = _createTextVNode(" 刮削 "))
                                                              ]),
                                                              _: 2
                                                            }, 1032, ["loading", "onClick"])
                                                          ]))
                                                        : (child.type === 'directory')
                                                          ? (_openBlock(), _createElementBlock("div", _hoisted_23, [
                                                              _createElementVNode("div", {
                                                                class: "d-flex align-center py-2",
                                                                onClick: $event => (toggleDirectory(child))
                                                              }, [
                                                                _createVNode(_component_v_icon, {
                                                                  icon: child.expanded ? 'mdi-folder-open' : 'mdi-folder',
                                                                  size: "small",
                                                                  color: "primary",
                                                                  class: "mr-2"
                                                                }, null, 8, ["icon"]),
                                                                _createElementVNode("span", _hoisted_25, _toDisplayString(child.name), 1)
                                                              ], 8, _hoisted_24),
                                                              (child.expanded)
                                                                ? (_openBlock(), _createElementBlock("div", _hoisted_26, [
                                                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(child.children, (grandChild, grandChildIndex) => {
                                                                      return (_openBlock(), _createElementBlock("div", {
                                                                        key: grandChildIndex,
                                                                        class: "tree-item"
                                                                      }, [
                                                                        (grandChild.type === 'media')
                                                                          ? (_openBlock(), _createElementBlock("div", _hoisted_27, [
                                                                              _createVNode(_component_v_icon, {
                                                                                icon: "mdi-video",
                                                                                size: "small",
                                                                                color: "info",
                                                                                class: "mr-2"
                                                                              }),
                                                                              _createElementVNode("div", _hoisted_28, [
                                                                                _createElementVNode("div", _hoisted_29, [
                                                                                  _createElementVNode("span", _hoisted_30, _toDisplayString(grandChild.name), 1),
                                                                                  (grandChild.danmu_count > 0)
                                                                                    ? (_openBlock(), _createBlock(_component_v_chip, {
                                                                                        key: 0,
                                                                                        size: "small",
                                                                                        color: "info",
                                                                                        class: "ml-2"
                                                                                      }, {
                                                                                        default: _withCtx(() => [
                                                                                          _createTextVNode(" 弹幕: " + _toDisplayString(grandChild.danmu_count), 1)
                                                                                        ]),
                                                                                        _: 2
                                                                                      }, 1024))
                                                                                    : (_openBlock(), _createBlock(_component_v_chip, {
                                                                                        key: 1,
                                                                                        size: "small",
                                                                                        color: "grey",
                                                                                        class: "ml-2"
                                                                                      }, {
                                                                                        default: _withCtx(() => _cache[13] || (_cache[13] = [
                                                                                          _createTextVNode(" 无弹幕 ")
                                                                                        ])),
                                                                                        _: 1
                                                                                      }))
                                                                                ])
                                                                              ]),
                                                                              _createVNode(_component_v_btn, {
                                                                                color: "primary",
                                                                                size: "small",
                                                                                variant: "text",
                                                                                loading: grandChild.generating,
                                                                                onClick: $event => (generateDanmu(grandChild, child))
                                                                              }, {
                                                                                default: _withCtx(() => [
                                                                                  _createVNode(_component_v_icon, {
                                                                                    icon: "mdi-download",
                                                                                    size: "small",
                                                                                    class: "mr-1"
                                                                                  }),
                                                                                  _cache[14] || (_cache[14] = _createTextVNode(" 刮削 "))
                                                                                ]),
                                                                                _: 2
                                                                              }, 1032, ["loading", "onClick"])
                                                                            ]))
                                                                          : _createCommentVNode("", true)
                                                                      ]))
                                                                    }), 128))
                                                                  ]))
                                                                : _createCommentVNode("", true)
                                                            ]))
                                                          : _createCommentVNode("", true)
                                                    ], 2))
                                                  }), 128))
                                                ]))
                                              : _createCommentVNode("", true)
                                          ]))
                                        : _createCommentVNode("", true)
                                    ], 2))
                                  }), 128))
                                ]))
                              : (!directoryTree.value && error.value)
                                ? (_openBlock(), _createElementBlock("div", _hoisted_31, [
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
                                : (_openBlock(), _createElementBlock("div", _hoisted_32, [
                                    _createVNode(_component_v_alert, {
                                      type: "info",
                                      density: "compact",
                                      class: "mb-2 text-caption",
                                      variant: "tonal"
                                    }, {
                                      default: _withCtx(() => _cache[15] || (_cache[15] = [
                                        _createTextVNode("请先在配置中设置刮削路径")
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
              onClick: _cache[1] || (_cache[1] = $event => (emit('switch'))),
              "prepend-icon": "mdi-cog",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[16] || (_cache[16] = [
                _createTextVNode("配置")
              ])),
              _: 1
            }),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "grey",
              onClick: _cache[2] || (_cache[2] = $event => (emit('close'))),
              "prepend-icon": "mdi-close",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[17] || (_cache[17] = [
                _createTextVNode("关闭")
              ])),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    })
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-ec0497e3"]]);

export { Page as default };
