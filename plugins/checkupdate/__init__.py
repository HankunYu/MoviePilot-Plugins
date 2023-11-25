from app.log import logger
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple

from from app.core.plugin import PluginManager

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
    plugin_version = "0.1"
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
            PluginManager().init_config()
        
        config.update({
            "enabled": False
        })


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

