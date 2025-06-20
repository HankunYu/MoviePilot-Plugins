import { importShared } from './__federation_fn_import-BLov4B95.js';

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {defineComponent: defineComponent$2,ref: ref$2,computed,onMounted: onMounted$2} = await importShared('vue');


const _sfc_main$2 = defineComponent$2({
  name: 'IdentifierPage',
  props: {
    api: Object
  },
  emits: ['switch', 'close'],
  
  setup(props, { emit }) {
    // 响应式数据
    const loading = ref$2(false);
    const saving = ref$2(false);
    const error = ref$2('');
    const successMessage = ref$2('');
    
    // 识别词数据
    const identifiers = ref$2([]);
    const searchKeyword = ref$2('');
    const selectedTag = ref$2('');
    const expandedPanels = ref$2([]);
    
    // 对话框控制
    const showAddDialog = ref$2(false);
    const showEditDialog = ref$2(false);
    const showAddToTagDialog = ref$2(false);
    const newTagName = ref$2('');
    const currentTag = ref$2('');
    
    // 编辑相关
    const editingItem = ref$2({
      type: '屏蔽',
      tag: '未分类',
      content: '',
      originalTag: '',
      originalIndex: -1
    });
    
    const newItem = ref$2({
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
    onMounted$2(() => {
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

const {resolveComponent:_resolveComponent$2,createVNode:_createVNode$1,createElementVNode:_createElementVNode$2,createTextVNode:_createTextVNode$1,withCtx:_withCtx$2,toDisplayString:_toDisplayString$1,openBlock:_openBlock$2,createBlock:_createBlock$2,createCommentVNode:_createCommentVNode$1,renderList:_renderList$1,Fragment:_Fragment$1,createElementBlock:_createElementBlock$1,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1$2 = { class: "plugin-page" };
const _hoisted_2$1 = { class: "text-caption" };
const _hoisted_3$1 = { key: 1 };
const _hoisted_4$1 = { class: "d-flex align-center w-100" };
const _hoisted_5$1 = { class: "font-weight-medium" };
const _hoisted_6 = { class: "identifier-list" };
const _hoisted_7 = { class: "flex-grow-1" };
const _hoisted_8 = { class: "d-flex align-center" };
const _hoisted_9 = { class: "text-subtitle-2" };
const _hoisted_10 = { class: "action-buttons" };
const _hoisted_11 = {
  key: 2,
  class: "text-center py-8"
};

function _sfc_render$2(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_v_icon = _resolveComponent$2("v-icon");
  const _component_v_spacer = _resolveComponent$2("v-spacer");
  const _component_v_btn = _resolveComponent$2("v-btn");
  const _component_v_card_title = _resolveComponent$2("v-card-title");
  const _component_v_alert = _resolveComponent$2("v-alert");
  const _component_v_col = _resolveComponent$2("v-col");
  const _component_v_row = _resolveComponent$2("v-row");
  const _component_v_card_text = _resolveComponent$2("v-card-text");
  const _component_v_card = _resolveComponent$2("v-card");
  const _component_v_text_field = _resolveComponent$2("v-text-field");
  const _component_v_select = _resolveComponent$2("v-select");
  const _component_v_progress_linear = _resolveComponent$2("v-progress-linear");
  const _component_v_chip = _resolveComponent$2("v-chip");
  const _component_v_expansion_panel_title = _resolveComponent$2("v-expansion-panel-title");
  const _component_v_expansion_panel_text = _resolveComponent$2("v-expansion-panel-text");
  const _component_v_expansion_panel = _resolveComponent$2("v-expansion-panel");
  const _component_v_expansion_panels = _resolveComponent$2("v-expansion-panels");
  const _component_v_card_actions = _resolveComponent$2("v-card-actions");
  const _component_v_dialog = _resolveComponent$2("v-dialog");
  const _component_v_textarea = _resolveComponent$2("v-textarea");

  return (_openBlock$2(), _createElementBlock$1("div", _hoisted_1$2, [
    _createVNode$1(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx$2(() => [
        _createVNode$1(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
          default: _withCtx$2(() => [
            _createVNode$1(_component_v_icon, {
              icon: "mdi-tag-text",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[17] || (_cache[17] = _createElementVNode$2("span", null, "自定义识别词管理", -1)),
            _createVNode$1(_component_v_spacer),
            _createVNode$1(_component_v_btn, {
              color: "primary",
              size: "small",
              variant: "text",
              onClick: _ctx.switchToConfig
            }, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_icon, {
                  icon: "mdi-cog",
                  size: "small",
                  class: "mr-1"
                }),
                _cache[16] || (_cache[16] = _createTextVNode$1(" 配置 "))
              ]),
              _: 1,
              __: [16]
            }, 8, ["onClick"])
          ]),
          _: 1,
          __: [17]
        }),
        _createVNode$1(_component_v_card_text, { class: "px-3 py-2" }, {
          default: _withCtx$2(() => [
            (_ctx.error)
              ? (_openBlock$2(), _createBlock$2(_component_v_alert, {
                  key: 0,
                  type: "error",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx$2(() => [
                    _createTextVNode$1(_toDisplayString$1(_ctx.error), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode$1("", true),
            (_ctx.successMessage)
              ? (_openBlock$2(), _createBlock$2(_component_v_alert, {
                  key: 1,
                  type: "success",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx$2(() => [
                    _createTextVNode$1(_toDisplayString$1(_ctx.successMessage), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode$1("", true),
            _createVNode$1(_component_v_card, {
              flat: "",
              class: "rounded mb-3 border"
            }, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx$2(() => [
                    _createVNode$1(_component_v_icon, {
                      icon: "mdi-wrench",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[18] || (_cache[18] = _createElementVNode$2("span", null, "操作面板", -1))
                  ]),
                  _: 1,
                  __: [18]
                }),
                _createVNode$1(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx$2(() => [
                    _createVNode$1(_component_v_row, null, {
                      default: _withCtx$2(() => [
                        _createVNode$1(_component_v_col, {
                          cols: "12",
                          md: "4"
                        }, {
                          default: _withCtx$2(() => [
                            _createVNode$1(_component_v_btn, {
                              color: "primary",
                              block: "",
                              onClick: _ctx.loadIdentifiers,
                              loading: _ctx.loading
                            }, {
                              default: _withCtx$2(() => [
                                _createVNode$1(_component_v_icon, {
                                  icon: "mdi-refresh",
                                  class: "mr-1"
                                }),
                                _cache[19] || (_cache[19] = _createTextVNode$1(" 重新加载 "))
                              ]),
                              _: 1,
                              __: [19]
                            }, 8, ["onClick", "loading"])
                          ]),
                          _: 1
                        }),
                        _createVNode$1(_component_v_col, {
                          cols: "12",
                          md: "4"
                        }, {
                          default: _withCtx$2(() => [
                            _createVNode$1(_component_v_btn, {
                              color: "success",
                              block: "",
                              onClick: _ctx.saveIdentifiers,
                              loading: _ctx.saving
                            }, {
                              default: _withCtx$2(() => [
                                _createVNode$1(_component_v_icon, {
                                  icon: "mdi-content-save",
                                  class: "mr-1"
                                }),
                                _cache[20] || (_cache[20] = _createTextVNode$1(" 保存修改 "))
                              ]),
                              _: 1,
                              __: [20]
                            }, 8, ["onClick", "loading"])
                          ]),
                          _: 1
                        }),
                        _createVNode$1(_component_v_col, {
                          cols: "12",
                          md: "4"
                        }, {
                          default: _withCtx$2(() => [
                            _createVNode$1(_component_v_btn, {
                              color: "warning",
                              block: "",
                              onClick: _cache[0] || (_cache[0] = $event => (_ctx.showAddDialog = true))
                            }, {
                              default: _withCtx$2(() => [
                                _createVNode$1(_component_v_icon, {
                                  icon: "mdi-plus",
                                  class: "mr-1"
                                }),
                                _cache[21] || (_cache[21] = _createTextVNode$1(" 添加标签 "))
                              ]),
                              _: 1,
                              __: [21]
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
            _createVNode$1(_component_v_card, {
              flat: "",
              class: "rounded mb-3 border"
            }, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx$2(() => [
                    _createVNode$1(_component_v_row, null, {
                      default: _withCtx$2(() => [
                        _createVNode$1(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx$2(() => [
                            _createVNode$1(_component_v_text_field, {
                              modelValue: _ctx.searchKeyword,
                              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((_ctx.searchKeyword) = $event)),
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
                        _createVNode$1(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx$2(() => [
                            _createVNode$1(_component_v_select, {
                              modelValue: _ctx.selectedTag,
                              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((_ctx.selectedTag) = $event)),
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
            _createVNode$1(_component_v_card, {
              flat: "",
              class: "rounded border"
            }, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx$2(() => [
                    _createVNode$1(_component_v_icon, {
                      icon: "mdi-format-list-bulleted",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[22] || (_cache[22] = _createElementVNode$2("span", null, "识别词列表", -1)),
                    _createVNode$1(_component_v_spacer),
                    _createElementVNode$2("span", _hoisted_2$1, "共 " + _toDisplayString$1(_ctx.filteredIdentifiers.length) + " 条", 1)
                  ]),
                  _: 1,
                  __: [22]
                }),
                _createVNode$1(_component_v_card_text, { class: "px-0 py-0" }, {
                  default: _withCtx$2(() => [
                    (_ctx.loading)
                      ? (_openBlock$2(), _createBlock$2(_component_v_progress_linear, {
                          key: 0,
                          indeterminate: "",
                          color: "primary"
                        }))
                      : _createCommentVNode$1("", true),
                    (_ctx.groupedIdentifiers && Object.keys(_ctx.groupedIdentifiers).length > 0)
                      ? (_openBlock$2(), _createElementBlock$1("div", _hoisted_3$1, [
                          _createVNode$1(_component_v_expansion_panels, {
                            modelValue: _ctx.expandedPanels,
                            "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((_ctx.expandedPanels) = $event)),
                            multiple: ""
                          }, {
                            default: _withCtx$2(() => [
                              (_openBlock$2(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(_ctx.groupedIdentifiers, (items, tag) => {
                                return (_openBlock$2(), _createBlock$2(_component_v_expansion_panel, {
                                  key: tag,
                                  value: tag
                                }, {
                                  default: _withCtx$2(() => [
                                    _createVNode$1(_component_v_expansion_panel_title, null, {
                                      default: _withCtx$2(() => [
                                        _createElementVNode$2("div", _hoisted_4$1, [
                                          _createVNode$1(_component_v_icon, {
                                            icon: _ctx.getTagIcon(tag),
                                            class: "mr-2",
                                            size: "small"
                                          }, null, 8, ["icon"]),
                                          _createElementVNode$2("span", _hoisted_5$1, _toDisplayString$1(tag), 1),
                                          _createVNode$1(_component_v_spacer),
                                          _createVNode$1(_component_v_chip, {
                                            size: "small",
                                            color: "primary",
                                            class: "mr-2"
                                          }, {
                                            default: _withCtx$2(() => [
                                              _createTextVNode$1(_toDisplayString$1(items.length), 1)
                                            ]),
                                            _: 2
                                          }, 1024),
                                          (tag !== '未分类')
                                            ? (_openBlock$2(), _createBlock$2(_component_v_btn, {
                                                key: 0,
                                                icon: "",
                                                size: "small",
                                                variant: "text",
                                                onClick: _withModifiers($event => (_ctx.deleteTag(tag)), ["stop"])
                                              }, {
                                                default: _withCtx$2(() => [
                                                  _createVNode$1(_component_v_icon, {
                                                    icon: "mdi-delete",
                                                    size: "small"
                                                  })
                                                ]),
                                                _: 2
                                              }, 1032, ["onClick"]))
                                            : _createCommentVNode$1("", true)
                                        ])
                                      ]),
                                      _: 2
                                    }, 1024),
                                    _createVNode$1(_component_v_expansion_panel_text, null, {
                                      default: _withCtx$2(() => [
                                        _createElementVNode$2("div", _hoisted_6, [
                                          (_openBlock$2(true), _createElementBlock$1(_Fragment$1, null, _renderList$1(items, (item, index) => {
                                            return (_openBlock$2(), _createElementBlock$1("div", {
                                              key: index,
                                              class: "identifier-item d-flex align-center py-2 px-2 mb-2 rounded border"
                                            }, [
                                              _createVNode$1(_component_v_icon, {
                                                icon: _ctx.getTypeIcon(item.type),
                                                color: _ctx.getTypeColor(item.type),
                                                size: "small",
                                                class: "mr-3"
                                              }, null, 8, ["icon", "color"]),
                                              _createElementVNode$2("div", _hoisted_7, [
                                                _createElementVNode$2("div", _hoisted_8, [
                                                  _createVNode$1(_component_v_chip, {
                                                    size: "x-small",
                                                    color: _ctx.getTypeColor(item.type),
                                                    class: "mr-2"
                                                  }, {
                                                    default: _withCtx$2(() => [
                                                      _createTextVNode$1(_toDisplayString$1(item.type), 1)
                                                    ]),
                                                    _: 2
                                                  }, 1032, ["color"]),
                                                  _createElementVNode$2("span", _hoisted_9, _toDisplayString$1(item.content), 1)
                                                ])
                                              ]),
                                              _createElementVNode$2("div", _hoisted_10, [
                                                _createVNode$1(_component_v_btn, {
                                                  icon: "",
                                                  size: "small",
                                                  variant: "text",
                                                  onClick: $event => (_ctx.editIdentifier(item, tag))
                                                }, {
                                                  default: _withCtx$2(() => [
                                                    _createVNode$1(_component_v_icon, {
                                                      icon: "mdi-pencil",
                                                      size: "small"
                                                    })
                                                  ]),
                                                  _: 2
                                                }, 1032, ["onClick"]),
                                                _createVNode$1(_component_v_btn, {
                                                  icon: "",
                                                  size: "small",
                                                  variant: "text",
                                                  color: "error",
                                                  onClick: $event => (_ctx.deleteIdentifier(item, tag))
                                                }, {
                                                  default: _withCtx$2(() => [
                                                    _createVNode$1(_component_v_icon, {
                                                      icon: "mdi-delete",
                                                      size: "small"
                                                    })
                                                  ]),
                                                  _: 2
                                                }, 1032, ["onClick"])
                                              ])
                                            ]))
                                          }), 128)),
                                          _createVNode$1(_component_v_btn, {
                                            color: "primary",
                                            size: "small",
                                            variant: "outlined",
                                            block: "",
                                            onClick: $event => (_ctx.addToTag(tag))
                                          }, {
                                            default: _withCtx$2(() => [
                                              _createVNode$1(_component_v_icon, {
                                                icon: "mdi-plus",
                                                size: "small",
                                                class: "mr-1"
                                              }),
                                              _createTextVNode$1(" 添加到 " + _toDisplayString$1(tag), 1)
                                            ]),
                                            _: 2
                                          }, 1032, ["onClick"])
                                        ])
                                      ]),
                                      _: 2
                                    }, 1024)
                                  ]),
                                  _: 2
                                }, 1032, ["value"]))
                              }), 128))
                            ]),
                            _: 1
                          }, 8, ["modelValue"])
                        ]))
                      : (_openBlock$2(), _createElementBlock$1("div", _hoisted_11, [
                          _createVNode$1(_component_v_icon, {
                            icon: "mdi-emoticon-sad",
                            size: "large",
                            color: "grey",
                            class: "mb-2"
                          }),
                          _cache[23] || (_cache[23] = _createElementVNode$2("div", { class: "text-subtitle-2 text-grey" }, "暂无识别词", -1)),
                          _cache[24] || (_cache[24] = _createElementVNode$2("div", { class: "text-caption text-grey" }, "点击\"重新加载\"获取数据", -1))
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
    _createVNode$1(_component_v_dialog, {
      modelValue: _ctx.showAddDialog,
      "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((_ctx.showAddDialog) = $event)),
      "max-width": "500"
    }, {
      default: _withCtx$2(() => [
        _createVNode$1(_component_v_card, null, {
          default: _withCtx$2(() => [
            _createVNode$1(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx$2(() => _cache[25] || (_cache[25] = [
                _createTextVNode$1("添加新标签")
              ])),
              _: 1,
              __: [25]
            }),
            _createVNode$1(_component_v_card_text, null, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_text_field, {
                  modelValue: _ctx.newTagName,
                  "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((_ctx.newTagName) = $event)),
                  label: "标签名称",
                  variant: "outlined",
                  density: "compact",
                  placeholder: "输入标签名称（不需要#前缀）",
                  rules: [v => !!v || '标签名称不能为空']
                }, null, 8, ["modelValue", "rules"])
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_actions, null, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_spacer),
                _createVNode$1(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[5] || (_cache[5] = $event => (_ctx.showAddDialog = false))
                }, {
                  default: _withCtx$2(() => _cache[26] || (_cache[26] = [
                    _createTextVNode$1("取消")
                  ])),
                  _: 1,
                  __: [26]
                }),
                _createVNode$1(_component_v_btn, {
                  color: "primary",
                  onClick: _ctx.addNewTag
                }, {
                  default: _withCtx$2(() => _cache[27] || (_cache[27] = [
                    _createTextVNode$1("确认")
                  ])),
                  _: 1,
                  __: [27]
                }, 8, ["onClick"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode$1(_component_v_dialog, {
      modelValue: _ctx.showEditDialog,
      "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((_ctx.showEditDialog) = $event)),
      "max-width": "600"
    }, {
      default: _withCtx$2(() => [
        _createVNode$1(_component_v_card, null, {
          default: _withCtx$2(() => [
            _createVNode$1(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx$2(() => _cache[28] || (_cache[28] = [
                _createTextVNode$1("编辑识别词")
              ])),
              _: 1,
              __: [28]
            }),
            _createVNode$1(_component_v_card_text, null, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_select, {
                  modelValue: _ctx.editingItem.type,
                  "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((_ctx.editingItem.type) = $event)),
                  items: _ctx.typeOptions,
                  label: "类型",
                  variant: "outlined",
                  density: "compact",
                  class: "mb-3"
                }, null, 8, ["modelValue", "items"]),
                _createVNode$1(_component_v_select, {
                  modelValue: _ctx.editingItem.tag,
                  "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((_ctx.editingItem.tag) = $event)),
                  items: _ctx.tagOptions,
                  label: "标签",
                  variant: "outlined",
                  density: "compact",
                  class: "mb-3"
                }, null, 8, ["modelValue", "items"]),
                _createVNode$1(_component_v_textarea, {
                  modelValue: _ctx.editingItem.content,
                  "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((_ctx.editingItem.content) = $event)),
                  label: "内容",
                  variant: "outlined",
                  density: "compact",
                  rows: "3",
                  placeholder: "输入识别词内容..."
                }, null, 8, ["modelValue"]),
                _createVNode$1(_component_v_alert, {
                  type: "info",
                  density: "compact",
                  variant: "tonal",
                  class: "mt-3"
                }, {
                  default: _withCtx$2(() => _cache[29] || (_cache[29] = [
                    _createElementVNode$2("div", { class: "text-caption" }, [
                      _createElementVNode$2("strong", null, "格式说明："),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 屏蔽词：直接输入要屏蔽的词"),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 替换词：原词 => 新词"),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 集偏移：前定位词 <> 后定位词 >> 偏移量"),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 替换和集偏移：原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量 ")
                    ], -1)
                  ])),
                  _: 1,
                  __: [29]
                })
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_actions, null, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_spacer),
                _createVNode$1(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[10] || (_cache[10] = $event => (_ctx.showEditDialog = false))
                }, {
                  default: _withCtx$2(() => _cache[30] || (_cache[30] = [
                    _createTextVNode$1("取消")
                  ])),
                  _: 1,
                  __: [30]
                }),
                _createVNode$1(_component_v_btn, {
                  color: "primary",
                  onClick: _ctx.saveEdit
                }, {
                  default: _withCtx$2(() => _cache[31] || (_cache[31] = [
                    _createTextVNode$1("保存")
                  ])),
                  _: 1,
                  __: [31]
                }, 8, ["onClick"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode$1(_component_v_dialog, {
      modelValue: _ctx.showAddToTagDialog,
      "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((_ctx.showAddToTagDialog) = $event)),
      "max-width": "600"
    }, {
      default: _withCtx$2(() => [
        _createVNode$1(_component_v_card, null, {
          default: _withCtx$2(() => [
            _createVNode$1(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx$2(() => [
                _createTextVNode$1("添加识别词到 " + _toDisplayString$1(_ctx.currentTag), 1)
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_text, null, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_select, {
                  modelValue: _ctx.newItem.type,
                  "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((_ctx.newItem.type) = $event)),
                  items: _ctx.typeOptions,
                  label: "类型",
                  variant: "outlined",
                  density: "compact",
                  class: "mb-3"
                }, null, 8, ["modelValue", "items"]),
                _createVNode$1(_component_v_textarea, {
                  modelValue: _ctx.newItem.content,
                  "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((_ctx.newItem.content) = $event)),
                  label: "内容",
                  variant: "outlined",
                  density: "compact",
                  rows: "3",
                  placeholder: "输入识别词内容..."
                }, null, 8, ["modelValue"]),
                _createVNode$1(_component_v_alert, {
                  type: "info",
                  density: "compact",
                  variant: "tonal",
                  class: "mt-3"
                }, {
                  default: _withCtx$2(() => _cache[32] || (_cache[32] = [
                    _createElementVNode$2("div", { class: "text-caption" }, [
                      _createElementVNode$2("strong", null, "格式说明："),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 屏蔽词：直接输入要屏蔽的词"),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 替换词：原词 => 新词"),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 集偏移：前定位词 <> 后定位词 >> 偏移量"),
                      _createElementVNode$2("br"),
                      _createTextVNode$1(" • 替换和集偏移：原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量 ")
                    ], -1)
                  ])),
                  _: 1,
                  __: [32]
                })
              ]),
              _: 1
            }),
            _createVNode$1(_component_v_card_actions, null, {
              default: _withCtx$2(() => [
                _createVNode$1(_component_v_spacer),
                _createVNode$1(_component_v_btn, {
                  color: "grey",
                  onClick: _cache[14] || (_cache[14] = $event => (_ctx.showAddToTagDialog = false))
                }, {
                  default: _withCtx$2(() => _cache[33] || (_cache[33] = [
                    _createTextVNode$1("取消")
                  ])),
                  _: 1,
                  __: [33]
                }),
                _createVNode$1(_component_v_btn, {
                  color: "primary",
                  onClick: _ctx.saveNewItem
                }, {
                  default: _withCtx$2(() => _cache[34] || (_cache[34] = [
                    _createTextVNode$1("添加")
                  ])),
                  _: 1,
                  __: [34]
                }, 8, ["onClick"])
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
const Page = /*#__PURE__*/_export_sfc(_sfc_main$2, [['render',_sfc_render$2],['__scopeId',"data-v-0fbf6ad0"]]);

const {defineComponent: defineComponent$1,ref: ref$1,onMounted: onMounted$1} = await importShared('vue');


const _sfc_main$1 = defineComponent$1({
  name: 'IdentifierConfig',
  props: {
    api: Object
  },
  emits: ['switch', 'close'],
  
  setup(props, { emit }) {
    // 响应式数据
    const loading = ref$1(false);
    const saving = ref$1(false);
    const parsing = ref$1(false);
    const error = ref$1('');
    const successMessage = ref$1('');
    
    const rawData = ref$1('');
    const parsedData = ref$1([]);
    const importFile = ref$1(null);
    
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
    onMounted$1(() => {
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

const {resolveComponent:_resolveComponent$1,createVNode:_createVNode,createElementVNode:_createElementVNode$1,createTextVNode:_createTextVNode,withCtx:_withCtx$1,toDisplayString:_toDisplayString,openBlock:_openBlock$1,createBlock:_createBlock$1,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1$1 = { class: "plugin-config" };
const _hoisted_2 = { class: "d-flex gap-2 mt-3" };
const _hoisted_3 = { class: "text-caption" };
const _hoisted_4 = {
  class: "preview-container",
  style: {"max-height":"300px","overflow-y":"auto"}
};
const _hoisted_5 = { class: "text-caption font-mono" };

function _sfc_render$1(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_v_icon = _resolveComponent$1("v-icon");
  const _component_v_spacer = _resolveComponent$1("v-spacer");
  const _component_v_btn = _resolveComponent$1("v-btn");
  const _component_v_card_title = _resolveComponent$1("v-card-title");
  const _component_v_alert = _resolveComponent$1("v-alert");
  const _component_v_textarea = _resolveComponent$1("v-textarea");
  const _component_v_card_text = _resolveComponent$1("v-card-text");
  const _component_v_card = _resolveComponent$1("v-card");
  const _component_v_chip = _resolveComponent$1("v-chip");
  const _component_v_file_input = _resolveComponent$1("v-file-input");
  const _component_v_col = _resolveComponent$1("v-col");
  const _component_v_row = _resolveComponent$1("v-row");

  return (_openBlock$1(), _createElementBlock("div", _hoisted_1$1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx$1(() => [
        _createVNode(_component_v_card_title, { class: "text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
          default: _withCtx$1(() => [
            _createVNode(_component_v_icon, {
              icon: "mdi-cog",
              class: "mr-2",
              color: "primary",
              size: "small"
            }),
            _cache[3] || (_cache[3] = _createElementVNode$1("span", null, "识别词配置", -1)),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              color: "primary",
              size: "small",
              variant: "text",
              onClick: _ctx.switchToPage
            }, {
              default: _withCtx$1(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-arrow-left",
                  size: "small",
                  class: "mr-1"
                }),
                _cache[2] || (_cache[2] = _createTextVNode(" 返回 "))
              ]),
              _: 1,
              __: [2]
            }, 8, ["onClick"])
          ]),
          _: 1,
          __: [3]
        }),
        _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
          default: _withCtx$1(() => [
            (_ctx.error)
              ? (_openBlock$1(), _createBlock$1(_component_v_alert, {
                  key: 0,
                  type: "error",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode(_toDisplayString(_ctx.error), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (_ctx.successMessage)
              ? (_openBlock$1(), _createBlock$1(_component_v_alert, {
                  key: 1,
                  type: "success",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx$1(() => [
                    _createTextVNode(_toDisplayString(_ctx.successMessage), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card, {
              flat: "",
              class: "rounded mb-3 border"
            }, {
              default: _withCtx$1(() => [
                _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx$1(() => [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-code-tags",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[5] || (_cache[5] = _createElementVNode$1("span", null, "原始数据编辑", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      size: "small",
                      variant: "text",
                      onClick: _ctx.loadRawData,
                      loading: _ctx.loading
                    }, {
                      default: _withCtx$1(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-refresh",
                          size: "small",
                          class: "mr-1"
                        }),
                        _cache[4] || (_cache[4] = _createTextVNode(" 重新加载 "))
                      ]),
                      _: 1,
                      __: [4]
                    }, 8, ["onClick", "loading"])
                  ]),
                  _: 1,
                  __: [5]
                }),
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx$1(() => [
                    _createVNode(_component_v_textarea, {
                      modelValue: _ctx.rawData,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((_ctx.rawData) = $event)),
                      label: "识别词原始数据",
                      variant: "outlined",
                      rows: "20",
                      density: "compact",
                      placeholder: "输入识别词数据...",
                      loading: _ctx.loading
                    }, null, 8, ["modelValue", "loading"]),
                    _createVNode(_component_v_alert, {
                      type: "info",
                      density: "compact",
                      variant: "tonal",
                      class: "mt-3"
                    }, {
                      default: _withCtx$1(() => _cache[6] || (_cache[6] = [
                        _createElementVNode$1("div", { class: "text-caption" }, [
                          _createElementVNode$1("strong", null, "标签格式说明："),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 使用 "),
                          _createElementVNode$1("code", null, "# 标签名"),
                          _createTextVNode(" 开始一个新标签"),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 标签下的所有识别词都属于该标签"),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 未在任何标签下的识别词归为\"未分类\""),
                          _createElementVNode$1("br"),
                          _createElementVNode$1("br"),
                          _createElementVNode$1("strong", null, "识别词格式："),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 屏蔽词："),
                          _createElementVNode$1("code", null, "要屏蔽的词"),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 替换词："),
                          _createElementVNode$1("code", null, "原词 => 新词"),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 集偏移："),
                          _createElementVNode$1("code", null, "前定位词 <> 后定位词 >> 偏移量"),
                          _createElementVNode$1("br"),
                          _createTextVNode(" • 复合格式："),
                          _createElementVNode$1("code", null, "原词 => 新词 && 前定位词 <> 后定位词 >> 偏移量")
                        ], -1)
                      ])),
                      _: 1,
                      __: [6]
                    }),
                    _createElementVNode$1("div", _hoisted_2, [
                      _createVNode(_component_v_btn, {
                        color: "success",
                        onClick: _ctx.saveRawData,
                        loading: _ctx.saving
                      }, {
                        default: _withCtx$1(() => [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-content-save",
                            class: "mr-1"
                          }),
                          _cache[7] || (_cache[7] = _createTextVNode(" 保存数据 "))
                        ]),
                        _: 1,
                        __: [7]
                      }, 8, ["onClick", "loading"]),
                      _createVNode(_component_v_btn, {
                        color: "info",
                        onClick: _ctx.previewParsedData,
                        loading: _ctx.parsing
                      }, {
                        default: _withCtx$1(() => [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-eye",
                            class: "mr-1"
                          }),
                          _cache[8] || (_cache[8] = _createTextVNode(" 预览解析 "))
                        ]),
                        _: 1,
                        __: [8]
                      }, 8, ["onClick", "loading"]),
                      _createVNode(_component_v_btn, {
                        color: "warning",
                        onClick: _ctx.formatData
                      }, {
                        default: _withCtx$1(() => [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-format-align-left",
                            class: "mr-1"
                          }),
                          _cache[9] || (_cache[9] = _createTextVNode(" 格式化 "))
                        ]),
                        _: 1,
                        __: [9]
                      }, 8, ["onClick"])
                    ])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            (_ctx.parsedData.length > 0)
              ? (_openBlock$1(), _createBlock$1(_component_v_card, {
                  key: 2,
                  flat: "",
                  class: "rounded mb-3 border"
                }, {
                  default: _withCtx$1(() => [
                    _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-success-lighten-5" }, {
                      default: _withCtx$1(() => [
                        _createVNode(_component_v_icon, {
                          icon: "mdi-eye-check",
                          class: "mr-2",
                          color: "success",
                          size: "small"
                        }),
                        _cache[10] || (_cache[10] = _createElementVNode$1("span", null, "解析预览", -1)),
                        _createVNode(_component_v_spacer),
                        _createElementVNode$1("span", _hoisted_3, "共 " + _toDisplayString(_ctx.parsedData.length) + " 条", 1)
                      ]),
                      _: 1,
                      __: [10]
                    }),
                    _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                      default: _withCtx$1(() => [
                        _createElementVNode$1("div", _hoisted_4, [
                          (_openBlock$1(true), _createElementBlock(_Fragment, null, _renderList(_ctx.parsedData, (item, index) => {
                            return (_openBlock$1(), _createElementBlock("div", {
                              key: index,
                              class: _normalizeClass(["preview-item d-flex align-center py-1 px-2 mb-1 rounded", _ctx.getPreviewItemClass(item.type)])
                            }, [
                              _createVNode(_component_v_icon, {
                                icon: _ctx.getTypeIcon(item.type),
                                color: _ctx.getTypeColor(item.type),
                                size: "small",
                                class: "mr-2"
                              }, null, 8, ["icon", "color"]),
                              _createVNode(_component_v_chip, {
                                size: "x-small",
                                color: _ctx.getTypeColor(item.type),
                                class: "mr-2"
                              }, {
                                default: _withCtx$1(() => [
                                  _createTextVNode(_toDisplayString(item.type), 1)
                                ]),
                                _: 2
                              }, 1032, ["color"]),
                              _createVNode(_component_v_chip, {
                                size: "x-small",
                                color: "primary",
                                variant: "outlined",
                                class: "mr-2"
                              }, {
                                default: _withCtx$1(() => [
                                  _createTextVNode(_toDisplayString(item.tag), 1)
                                ]),
                                _: 2
                              }, 1024),
                              _createElementVNode$1("span", _hoisted_5, _toDisplayString(item.content), 1)
                            ], 2))
                          }), 128))
                        ])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card, {
              flat: "",
              class: "rounded border"
            }, {
              default: _withCtx$1(() => [
                _createVNode(_component_v_card_title, { class: "text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5" }, {
                  default: _withCtx$1(() => [
                    _createVNode(_component_v_icon, {
                      icon: "mdi-import",
                      class: "mr-2",
                      color: "primary",
                      size: "small"
                    }),
                    _cache[11] || (_cache[11] = _createElementVNode$1("span", null, "导入导出", -1))
                  ]),
                  _: 1,
                  __: [11]
                }),
                _createVNode(_component_v_card_text, { class: "px-3 py-2" }, {
                  default: _withCtx$1(() => [
                    _createVNode(_component_v_row, null, {
                      default: _withCtx$1(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx$1(() => [
                            _createVNode(_component_v_file_input, {
                              modelValue: _ctx.importFile,
                              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((_ctx.importFile) = $event)),
                              label: "导入文件",
                              variant: "outlined",
                              density: "compact",
                              accept: ".txt,.json",
                              "prepend-icon": "mdi-file-upload",
                              onChange: _ctx.handleFileImport
                            }, null, 8, ["modelValue", "onChange"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          md: "6"
                        }, {
                          default: _withCtx$1(() => [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              block: "",
                              onClick: _ctx.exportData
                            }, {
                              default: _withCtx$1(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-download",
                                  class: "mr-1"
                                }),
                                _cache[12] || (_cache[12] = _createTextVNode(" 导出数据 "))
                              ]),
                              _: 1,
                              __: [12]
                            }, 8, ["onClick"])
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main$1, [['render',_sfc_render$1],['__scopeId',"data-v-581d6900"]]);

const {defineComponent,ref,shallowRef,onMounted,onBeforeUnmount} = await importShared('vue');

const _sfc_main = defineComponent({
  name: 'App',
  
  setup() {
    // 当前显示的组件
    const currentComponent = shallowRef(Page);
    // API对象，用于传递给子组件
    const api = ref(null);
    
    // 处理窗口消息
    const handleMessage = (event) => {
      // 接收来自父窗口的消息，获取API对象
      if (event.data && event.data.type === 'api') {
        api.value = event.data.data;
        console.log('收到API:', api.value);
      }
      
      // 处理显示配置页面的消息
      if (event.data && event.data.type === 'showConfig') {
        currentComponent.value = Config;
      }
    };
    
    // 切换组件
    const switchComponent = () => {
      currentComponent.value = currentComponent.value === Page ? Config : Page;
    };
    
    // 关闭模态框
    const closeModal = () => {
      if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({ type: 'close' }, '*');
      }
    };
    
    // 挂载时添加消息监听
    onMounted(() => {
      window.addEventListener('message', handleMessage);
      
      // 通知父窗口已准备好接收API
      if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({ type: 'ready' }, '*');
      }
    });
    
    // 卸载前移除消息监听
    onBeforeUnmount(() => {
      window.removeEventListener('message', handleMessage);
    });
    
    return {
      currentComponent,
      api,
      switchComponent,
      closeModal
    };
  }
});

const {resolveDynamicComponent:_resolveDynamicComponent,openBlock:_openBlock,createBlock:_createBlock,createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,withCtx:_withCtx} = await importShared('vue');


const _hoisted_1 = { class: "plugin-app" };

function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_v_app = _resolveComponent("v-app");

  return (_openBlock(), _createBlock(_component_v_app, null, {
    default: _withCtx(() => [
      _createElementVNode("div", _hoisted_1, [
        (_openBlock(), _createBlock(_resolveDynamicComponent(_ctx.currentComponent), {
          api: _ctx.api,
          onSwitch: _ctx.switchComponent,
          onClose: _ctx.closeModal
        }, null, 40, ["api", "onSwitch", "onClose"]))
      ])
    ]),
    _: 1
  }))
}
const App = /*#__PURE__*/_export_sfc(_sfc_main, [['render',_sfc_render]]);

export { App as default };
