import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "d-flex gap-2 mt-3" };

const {ref,onMounted} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
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

const rawData = ref('');
const importFile = ref(null);

// 方法
const switchToPage = () => {
  emit('switch');
};

const loadRawData = async () => {
  if (!props.api) {
    error.value = 'API 对象未初始化';
    return;
  }
  
  loading.value = true;
  error.value = '';
  
  try {
    console.log('正在调用 API:', 'plugin/IdentifierHelper/get_raw_identifiers');
    const response = await props.api.get('plugin/IdentifierHelper/get_raw_identifiers');
    console.log('API 响应:', response);
    
    if (response && response.code === 0) {
      rawData.value = response.data || '';
      successMessage.value = '原始数据加载成功';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    } else {
      error.value = response?.message || '未知错误';
    }
  } catch (err) {
    console.error('API 调用错误:', err);
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
    console.log('正在保存原始数据，长度:', rawData.value.length);
    
    // 为长文本使用请求体，需要添加空的查询参数来满足FastAPI要求
    const response = await props.api.post('plugin/IdentifierHelper/save_raw_data?data=', {
      data: rawData.value
    });
    console.log('保存响应:', response);
    
    if (response && response.code === 0) {
      successMessage.value = response.message || '数据保存成功';
      setTimeout(() => { successMessage.value = ''; }, 3000);
    } else {
      error.value = response?.message || '保存失败';
    }
  } catch (err) {
    console.error('保存错误:', err);
    error.value = '保存数据失败: ' + (err.message || '未知错误');
  } finally {
    saving.value = false;
  }
};


const formatData = () => {
  if (!rawData.value) return;
  
  const lines = rawData.value.split('\n');
  const formatted = [];
  
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


// 生命周期
onMounted(() => {
  // 延迟加载，等待 API 对象初始化
  setTimeout(() => {
    loadRawData();
  }, 500);
});
    

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_textarea = _resolveComponent("v-textarea");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_file_input = _resolveComponent("v-file-input");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              icon: "mdi-cog",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[3] || (_cache[3] = _createElementVNode("span", null, "识别词配置", -1)),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "primary",
              size: "small",
              variant: "text",
              onClick: switchToPage
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-arrow-left",
                  size: "small",
                  class: "mr-1"
                }),
                _cache[2] || (_cache[2] = _createTextVNode(" 返回 "))
              ]),
              _: 1,
              __: [2]
            })
          ]),
          _: 1,
          __: [3]
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
                      icon: "mdi-code-tags",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[5] || (_cache[5] = _createElementVNode("span", null, "原始数据编辑", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      size: "small",
                      variant: "text",
                      onClick: loadRawData,
                      loading: loading.value
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-refresh",
                          size: "small",
                          class: "mr-1"
                        }),
                        _cache[4] || (_cache[4] = _createTextVNode(" 重新加载 "))
                      ]),
                      _: 1,
                      __: [4]
                    }, 8, ["loading"])
                  ]),
                  _: 1,
                  __: [5]
                }),
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_textarea, {
                      modelValue: rawData.value,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((rawData).value = $event)),
                      label: "识别词原始数据",
                      variant: "outlined",
                      rows: "20",
                      density: "compact",
                      placeholder: "输入识别词数据...",
                      loading: loading.value
                    }, null, 8, ["modelValue", "loading"]),
                    _createVNode(_component_v_alert, {
                      type: "info",
                      density: "compact",
                      variant: "tonal",
                      class: "mt-3"
                    }, {
                      default: _withCtx(() => _cache[6] || (_cache[6] = [
                        _createElementVNode("div", { class: "text-caption" }, [
                          _createElementVNode("strong", null, "标签格式说明："),
                          _createElementVNode("br"),
                          _createTextVNode(" • 使用 "),
                          _createElementVNode("code", null, "# 标签名"),
                          _createTextVNode(" 开始一个新标签"),
                          _createElementVNode("br"),
                          _createTextVNode(" • 标签下的所有识别词都属于该标签"),
                          _createElementVNode("br"),
                          _createTextVNode(" • 未在任何标签下的识别词归为\"未分类\""),
                          _createElementVNode("br"),
                          _createElementVNode("br"),
                          _createElementVNode("strong", null, "识别词格式："),
                          _createElementVNode("br"),
                          _createTextVNode(" • 屏蔽词："),
                          _createElementVNode("code", null, "要屏蔽的词"),
                          _createElementVNode("br"),
                          _createTextVNode(" • 替换词："),
                          _createElementVNode("code", null, "原词 => 新词"),
                          _createElementVNode("br"),
                          _createTextVNode(" • 集偏移："),
                          _createElementVNode("code", null, "前定位词 <> 后定位词 >> 偏移量"),
                          _createElementVNode("br"),
                          _createTextVNode(" • 复合格式："),
                          _createElementVNode("code", null, "原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量")
                        ], -1)
                      ])),
                      _: 1,
                      __: [6]
                    }),
                    _createElementVNode("div", _hoisted_2, [
                      _createVNode(_component_v_btn, {
                        color: "success",
                        onClick: saveRawData,
                        loading: saving.value
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-content-save",
                            class: "mr-1"
                          }),
                          _cache[7] || (_cache[7] = _createTextVNode(" 保存数据 "))
                        ]),
                        _: 1,
                        __: [7]
                      }, 8, ["loading"]),
                      _createVNode(_component_v_btn, {
                        color: "warning",
                        onClick: formatData
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-format-align-left",
                            class: "mr-1"
                          }),
                          _cache[8] || (_cache[8] = _createTextVNode(" 格式化 "))
                        ]),
                        _: 1,
                        __: [8]
                      })
                    ])
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
                      icon: "mdi-import",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[9] || (_cache[9] = _createElementVNode("span", null, "导入导出", -1))
                  ]),
                  _: 1,
                  __: [9]
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
                            _createVNode(_component_v_file_input, {
                              modelValue: importFile.value,
                              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((importFile).value = $event)),
                              label: "导入文件",
                              variant: "outlined",
                              density: "compact",
                              accept: ".txt,.json",
                              "prepend-icon": "mdi-file-upload",
                              onChange: handleFileImport
                            }, null, 8, ["modelValue"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              block: "",
                              onClick: exportData
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-download",
                                  class: "mr-1"
                                }),
                                _cache[10] || (_cache[10] = _createTextVNode(" 导出数据 "))
                              ]),
                              _: 1,
                              __: [10]
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-1f06656b"]]);

export { Config as default };
