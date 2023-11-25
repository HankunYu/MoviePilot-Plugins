from app.log import logger
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple

from app.db.systemconfig_oper import SystemConfigOper
from app.helper.plugin import PluginHelper
from app.core.plugin import PluginManager
from app.schemas.types import SystemConfigKey

import threading
class CheckUpdate(_PluginBase):
    # 插件名称
    plugin_name = "插件更新检查"
    # 插件描述
    plugin_desc = "手动检查一次所有插件是否有更新"
    # 插件图标
    plugin_icon = "download.png"
    # 主题色
    plugin_color = "#66778E"
    # 插件版本
    plugin_version = "0.3"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "check_update_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
        if self._enabled:
            threading.Thread(target=self.plugin_update).start()
            self.update_config({
                "enabled": False
            })

    # from https://github.com/thsrite/MoviePilot-Plugins/blob/main/plugins/pluginautoupdate/__init__.py
    def plugin_update(self):
        """
        插件自动更新
        """
        # 已安装插件
        install_plugins = SystemConfigOper().get(SystemConfigKey.UserInstalledPlugins) or []
        # 在线插件
        online_plugins = PluginManager().get_online_plugins()
        if not online_plugins:
            logger.error("未获取到在线插件，停止运行")
            return

        plugin_reload = False
        # 支持更新的插件自动更新
        for plugin in online_plugins:
            # 只处理已安装的插件
            if str(plugin.get("id")) in install_plugins:
                # 有更新 或者 本地未安装的
                if plugin.get("has_update") or not plugin.get("installed"):
                    # 下载安装
                    state, msg = PluginHelper().install(pid=plugin.get("id"),
                                                        repo_url=plugin.get("repo_url"))
                    # 安装失败
                    if not state:
                        logger.error(
                            f"插件 {plugin.get('plugin_name')} 更新失败，最新版本 {plugin.get('plugin_version')}")
                        continue

                    logger.info(f"插件 {plugin.get('plugin_name')} 更新成功，最新版本 {plugin.get('plugin_version')}")
                    plugin_reload = True

        # 重载插件管理器
        if plugin_reload:
            logger.info("开始插件重载")
            PluginManager().init_config()
        else:
            logger.info("所有插件已是最新版本")

    def get_state(self) -> bool:
        return self._enabled
    
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass
    
    # 插件配置页面
    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '检查更新',
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
        }

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        pass

