import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,withModifiers:_withModifiers,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "setting-item d-flex align-center py-2" };
const _hoisted_3 = { class: "setting-content flex-grow-1" };
const _hoisted_4 = { class: "d-flex justify-space-between align-center" };
const _hoisted_5 = { class: "setting-item d-flex align-center py-2" };
const _hoisted_6 = { class: "setting-content flex-grow-1" };
const _hoisted_7 = { class: "d-flex justify-space-between align-center" };
const _hoisted_8 = { class: "setting-item d-flex align-center py-2" };
const _hoisted_9 = { class: "setting-content flex-grow-1" };
const _hoisted_10 = { class: "d-flex justify-space-between align-center" };
const _hoisted_11 = { class: "setting-item d-flex align-center py-2" };
const _hoisted_12 = { class: "setting-content flex-grow-1" };
const _hoisted_13 = { class: "d-flex justify-space-between align-center" };
const _hoisted_14 = { class: "setting-item d-flex align-center py-2" };
const _hoisted_15 = { class: "setting-content flex-grow-1" };
const _hoisted_16 = { class: "d-flex justify-space-between align-center" };

const {ref,reactive,onMounted} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { 
    type: [Object, Function],
    required: true,
  },
  initialConfig: {
    type: Object,
    default: () => ({}),
  }
},
  emits: ['close', 'switch', 'config-updated-on-server', 'save'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

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
  auto_scrape: true,
  enable_retry_task: true
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
    if (!pluginId) ;
    
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
        auto_scrape: data.auto_scrape,
        enable_retry_task: data.enable_retry_task
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
        auto_scrape: props.initialConfig.auto_scrape,
        enable_retry_task: props.initialConfig.enable_retry_task
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
    if (!pluginId) ;

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
      auto_scrape: editableConfig.auto_scrape,
      enable_retry_task: editableConfig.enable_retry_task
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
      auto_scrape: serverFetchedConfig.auto_scrape,
      enable_retry_task: serverFetchedConfig.enable_retry_task
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
      auto_scrape: props.initialConfig.auto_scrape,
      enable_retry_task: props.initialConfig.enable_retry_task
    });
  }
  loadInitialData();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_textarea = _resolveComponent("v-textarea");
  const _component_v_form = _resolveComponent("v-form");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_spacer = _resolveComponent("v-spacer");
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
              icon: "mdi-cog",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[14] || (_cache[14] = _createElementVNode("span", null, "弹幕刮削配置", -1))
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
            _createVNode(_component_v_form, {
              ref_key: "form",
              ref: form,
              modelValue: isFormValid.value,
              "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((isFormValid).value = $event)),
              onSubmit: _withModifiers(saveFullConfig, ["prevent"])
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card, {
                  flat: "",
                  class: "rounded mb-3 border config-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-tune",
                          class: "mr-2",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[15] || (_cache[15] = _createElementVNode("span", null, "基本设置", -1))
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
                                    color: editableConfig.enable ? 'success' : 'grey',
                                    class: "mr-3"
                                  }, null, 8, ["color"]),
                                  _createElementVNode("div", _hoisted_3, [
                                    _createElementVNode("div", _hoisted_4, [
                                      _cache[16] || (_cache[16] = _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "text-subtitle-2" }, "启用插件"),
                                        _createElementVNode("div", { class: "text-caption text-grey" }, "是否启用弹幕刮削功能")
                                      ], -1)),
                                      _createVNode(_component_v_switch, {
                                        modelValue: editableConfig.enable,
                                        "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((editableConfig.enable) = $event)),
                                        color: "primary",
                                        inset: "",
                                        disabled: saving.value,
                                        density: "compact",
                                        "hide-details": "",
                                        class: "small-switch"
                                      }, null, 8, ["modelValue", "disabled"])
                                    ])
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
                                _createElementVNode("div", _hoisted_5, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-bilibili",
                                    size: "small",
                                    color: editableConfig.onlyFromBili ? 'info' : 'grey',
                                    class: "mr-3"
                                  }, null, 8, ["color"]),
                                  _createElementVNode("div", _hoisted_6, [
                                    _createElementVNode("div", _hoisted_7, [
                                      _cache[17] || (_cache[17] = _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "text-subtitle-2" }, "仅从B站获取"),
                                        _createElementVNode("div", { class: "text-caption text-grey" }, "是否仅从B站获取弹幕")
                                      ], -1)),
                                      _createVNode(_component_v_switch, {
                                        modelValue: editableConfig.onlyFromBili,
                                        "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((editableConfig.onlyFromBili) = $event)),
                                        color: "info",
                                        inset: "",
                                        disabled: saving.value,
                                        density: "compact",
                                        "hide-details": "",
                                        class: "small-switch"
                                      }, null, 8, ["modelValue", "disabled"])
                                    ])
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
                                    icon: "mdi-database",
                                    size: "small",
                                    color: editableConfig.useTmdbID ? 'info' : 'grey',
                                    class: "mr-3"
                                  }, null, 8, ["color"]),
                                  _createElementVNode("div", _hoisted_9, [
                                    _createElementVNode("div", _hoisted_10, [
                                      _cache[18] || (_cache[18] = _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "text-subtitle-2" }, "使用TMDB ID"),
                                        _createElementVNode("div", { class: "text-caption text-grey" }, "是否使用TMDB ID进行匹配")
                                      ], -1)),
                                      _createVNode(_component_v_switch, {
                                        modelValue: editableConfig.useTmdbID,
                                        "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((editableConfig.useTmdbID) = $event)),
                                        color: "info",
                                        inset: "",
                                        disabled: saving.value,
                                        density: "compact",
                                        "hide-details": "",
                                        class: "small-switch"
                                      }, null, 8, ["modelValue", "disabled"])
                                    ])
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
                                    icon: "mdi-auto-fix",
                                    size: "small",
                                    color: editableConfig.auto_scrape ? 'success' : 'grey',
                                    class: "mr-3"
                                  }, null, 8, ["color"]),
                                  _createElementVNode("div", _hoisted_12, [
                                    _createElementVNode("div", _hoisted_13, [
                                      _cache[19] || (_cache[19] = _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "text-subtitle-2" }, "入库自动刮削"),
                                        _createElementVNode("div", { class: "text-caption text-grey" }, "是否在媒体入库时自动刮削弹幕")
                                      ], -1)),
                                      _createVNode(_component_v_switch, {
                                        modelValue: editableConfig.auto_scrape,
                                        "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((editableConfig.auto_scrape) = $event)),
                                        color: "success",
                                        inset: "",
                                        disabled: saving.value,
                                        density: "compact",
                                        "hide-details": "",
                                        class: "small-switch"
                                      }, null, 8, ["modelValue", "disabled"])
                                    ])
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
                                _createElementVNode("div", _hoisted_14, [
                                  _createVNode(_component_v_icon, {
                                    icon: "mdi-repeat",
                                    size: "small",
                                    color: editableConfig.enable_retry_task ? 'warning' : 'grey',
                                    class: "mr-3"
                                  }, null, 8, ["color"]),
                                  _createElementVNode("div", _hoisted_15, [
                                    _createElementVNode("div", _hoisted_16, [
                                      _cache[20] || (_cache[20] = _createElementVNode("div", null, [
                                        _createElementVNode("div", { class: "text-subtitle-2" }, "启用重试任务"),
                                        _createElementVNode("div", { class: "text-caption text-grey" }, "弹幕数量不足时自动加入重试列表")
                                      ], -1)),
                                      _createVNode(_component_v_switch, {
                                        modelValue: editableConfig.enable_retry_task,
                                        "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((editableConfig.enable_retry_task) = $event)),
                                        color: "warning",
                                        inset: "",
                                        disabled: saving.value,
                                        density: "compact",
                                        "hide-details": "",
                                        class: "small-switch"
                                      }, null, 8, ["modelValue", "disabled"])
                                    ])
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
                _createVNode(_component_v_card, {
                  flat: "",
                  class: "rounded mb-3 border config-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-video",
                          class: "mr-2",
                          color: "primary",
                          size: "small"
                        }),
                        _cache[21] || (_cache[21] = _createElementVNode("span", null, "弹幕参数设置", -1))
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
                                _createVNode(_component_v_text_field, {
                                  modelValue: editableConfig.width,
                                  "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((editableConfig.width) = $event)),
                                  modelModifiers: { number: true },
                                  label: "视频宽度",
                                  type: "number",
                                  variant: "outlined",
                                  min: 1,
                                  rules: [v => v > 0 || '宽度必须大于0'],
                                  hint: "弹幕视频的宽度",
                                  "persistent-hint": "",
                                  "prepend-inner-icon": "mdi-arrow-expand-horizontal",
                                  disabled: saving.value,
                                  density: "compact",
                                  class: "text-caption"
                                }, null, 8, ["modelValue", "rules", "disabled"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_text_field, {
                                  modelValue: editableConfig.height,
                                  "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((editableConfig.height) = $event)),
                                  modelModifiers: { number: true },
                                  label: "视频高度",
                                  type: "number",
                                  variant: "outlined",
                                  min: 1,
                                  rules: [v => v > 0 || '高度必须大于0'],
                                  hint: "弹幕视频的高度",
                                  "persistent-hint": "",
                                  "prepend-inner-icon": "mdi-arrow-expand-vertical",
                                  disabled: saving.value,
                                  density: "compact",
                                  class: "text-caption"
                                }, null, 8, ["modelValue", "rules", "disabled"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_text_field, {
                                  modelValue: editableConfig.fontsize,
                                  "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((editableConfig.fontsize) = $event)),
                                  modelModifiers: { number: true },
                                  label: "字体大小",
                                  type: "number",
                                  variant: "outlined",
                                  min: 1,
                                  rules: [v => v > 0 || '字体大小必须大于0'],
                                  hint: "弹幕字体大小",
                                  "persistent-hint": "",
                                  "prepend-inner-icon": "mdi-format-font-size-increase",
                                  disabled: saving.value,
                                  density: "compact",
                                  class: "text-caption"
                                }, null, 8, ["modelValue", "rules", "disabled"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_text_field, {
                                  modelValue: editableConfig.alpha,
                                  "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((editableConfig.alpha) = $event)),
                                  modelModifiers: { number: true },
                                  label: "透明度",
                                  type: "number",
                                  variant: "outlined",
                                  min: 0,
                                  max: 1,
                                  step: 0.1,
                                  rules: [v => v >= 0 && v <= 1 || '透明度必须在0-1之间'],
                                  hint: "弹幕透明度(0-1)",
                                  "persistent-hint": "",
                                  "prepend-inner-icon": "mdi-opacity",
                                  disabled: saving.value,
                                  density: "compact",
                                  class: "text-caption"
                                }, null, 8, ["modelValue", "rules", "disabled"])
                              ]),
                              _: 1
                            }),
                            _createVNode(_component_v_col, {
                              cols: "12",
                              md: "6"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_text_field, {
                                  modelValue: editableConfig.duration,
                                  "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((editableConfig.duration) = $event)),
                                  modelModifiers: { number: true },
                                  label: "持续时间",
                                  type: "number",
                                  variant: "outlined",
                                  min: 1,
                                  rules: [v => v > 0 || '持续时间必须大于0'],
                                  hint: "弹幕显示持续时间(秒)",
                                  "persistent-hint": "",
                                  "prepend-inner-icon": "mdi-clock-outline",
                                  disabled: saving.value,
                                  density: "compact",
                                  class: "text-caption"
                                }, null, 8, ["modelValue", "rules", "disabled"])
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
                  class: "rounded mb-3 border config-card"
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
                        _cache[22] || (_cache[22] = _createElementVNode("span", null, "手动控制媒体库路径", -1))
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_textarea, {
                          modelValue: editableConfig.path,
                          "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((editableConfig.path) = $event)),
                          label: "/",
                          variant: "outlined",
                          hint: "每行一个路径,在状态页手动控制刮削",
                          "persistent-hint": "",
                          "prepend-inner-icon": "mdi-folder-multiple",
                          disabled: saving.value,
                          density: "compact",
                          class: "text-caption",
                          rows: "3"
                        }, null, 8, ["modelValue", "disabled"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card, {
                  flat: "",
                  class: "rounded mb-3 border config-card"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_text, { class: "d-flex align-center px-3 py-2" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-information",
                          color: "info",
                          class: "mr-2",
                          size: "small"
                        }),
                        _cache[23] || (_cache[23] = _createElementVNode("span", { class: "text-caption" }, " 此插件用于生成视频的弹幕字幕文件.弹幕来源为弹弹play平台. ", -1))
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_divider),
        _createVNode(_component_v_card_actions, { class: "px-2 py-1" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "info",
              onClick: _cache[12] || (_cache[12] = $event => (emit('switch'))),
              "prepend-icon": "mdi-view-dashboard",
              disabled: saving.value,
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[24] || (_cache[24] = [
                _createTextVNode("状态页")
              ])),
              _: 1
            }, 8, ["disabled"]),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "secondary",
              variant: "text",
              onClick: resetConfigToFetched,
              disabled: !initialConfigLoaded.value || saving.value,
              "prepend-icon": "mdi-restore",
              size: "small"
            }, {
              default: _withCtx(() => _cache[25] || (_cache[25] = [
                _createTextVNode("重置")
              ])),
              _: 1
            }, 8, ["disabled"]),
            _createVNode(_component_v_btn, {
              color: "primary",
              disabled: !isFormValid.value || saving.value,
              onClick: saveFullConfig,
              loading: saving.value,
              "prepend-icon": "mdi-content-save",
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[26] || (_cache[26] = [
                _createTextVNode("保存配置")
              ])),
              _: 1
            }, 8, ["disabled", "loading"]),
            _createVNode(_component_v_btn, {
              color: "grey",
              onClick: _cache[13] || (_cache[13] = $event => (emit('close'))),
              "prepend-icon": "mdi-close",
              disabled: saving.value,
              variant: "text",
              size: "small"
            }, {
              default: _withCtx(() => _cache[27] || (_cache[27] = [
                _createTextVNode("关闭")
              ])),
              _: 1
            }, 8, ["disabled"])
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-2b6e1a1e"]]);

export { Config as default };
