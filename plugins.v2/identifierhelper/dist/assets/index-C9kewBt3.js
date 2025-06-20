import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import Page from './__federation_expose_Page-DIWW6zw6.js';
import Config from './__federation_expose_Config-Bh2z7GYr.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

true&&(function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) {
    return;
  }
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) {
    processPreload(link);
  }
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") {
        continue;
      }
      for (const node of mutation.addedNodes) {
        if (node.tagName === "LINK" && node.rel === "modulepreload")
          processPreload(node);
      }
    }
  }).observe(document, { childList: true, subtree: true });
  function getFetchOpts(link) {
    const fetchOpts = {};
    if (link.integrity) fetchOpts.integrity = link.integrity;
    if (link.referrerPolicy) fetchOpts.referrerPolicy = link.referrerPolicy;
    if (link.crossOrigin === "use-credentials")
      fetchOpts.credentials = "include";
    else if (link.crossOrigin === "anonymous") fetchOpts.credentials = "omit";
    else fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep)
      return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
}());

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
      console.log('收到父窗口消息:', event.data);
      
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
      console.log('插件组件已挂载');
      window.addEventListener('message', handleMessage);
      
      // 通知父窗口已准备好接收API
      if (window.parent && window.parent.postMessage) {
        console.log('向父窗口发送ready消息');
        window.parent.postMessage({ type: 'ready' }, '*');
      }
      
      // 延迟检查API状态
      setTimeout(() => {
        console.log('当前API状态:', api.value);
      }, 1000);
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

const {createApp} = await importShared('vue');

const app = createApp(App);
app.mount('#app');
