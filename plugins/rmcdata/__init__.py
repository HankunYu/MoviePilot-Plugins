import os

# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from typing import Any, List, Dict, Tuple

class RmCdata(_PluginBase):
    # 插件名称
    plugin_name = "Infuse nfo 简介修复"
    # 插件描述
    plugin_desc = "去除nfo文件中的cdata标签以修复Infuse简介内容显示"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins-discord/main/icons/Infuse.png"
    # 主题色
    plugin_color = "#32699D"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "rmcdata_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _rm_all = False
    _all_path = ""


    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._rm_all = config.get("rm_all")
            self._all_path = config.get("all_path")
        if self._rm_all:
            for path in self._all_path.split('\n'):
                if not path: 
                    continue
                self.process_all_nfo_files(path)
            self._rm_all = False
            self.update_config({
                    "enabled": self._enabled,
                    "rm_all": False,
                    "all_path": self._all_path,
                })

        
        if self._enabled:
            logger.info(f"nfo 文件监控开始, version: {self.plugin_version}")

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
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'rm_all',
                                            'label': '运行一次全媒体库nfo修复',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'all_path',
                                            'label': '全媒体库nfo修复目录',
                                            'rows': 5,
                                            'placeholder': '每一行一个目录，需配置到媒体文件的上级目录'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            "rm_all": False,
            "all_path": "",
        }

    def get_page(self) -> List[dict]:
        pass
    @staticmethod
    def replace_cdata_tags(file_path):
        logger.info(f'正在处理 {file_path}...')
        with open(file_path, 'r') as file:
            content = file.read()
        # 替换 CDATA 标签
        content = content.replace('<![CDATA[', '').replace(']]>', '')
        with open(file_path, 'w') as file:
            file.write(content)
            logger.info(f'{file_path} 处理完成')

    def process_all_nfo_files(self,directory):
        logger.info(f'正在处理 {directory} 下的所有 nfo 文件...')
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.nfo'):
                    file_path = os.path.join(root, file)
                    self.replace_cdata_tags(file_path)
                    logger.info(f'{file_path} 处理完成')
                        
        logger.info(f'{directory} - 处理完成')

    @eventmanager.register(EventType.TransferComplete)
    def rmcdata(self, event):
        
        if not self._enabled:
            return

        def __to_dict(_event):
            """
            递归将对象转换为字典
            """
            if isinstance(_event, dict):
                for k, v in _event.items():
                    _event[k] = __to_dict(v)
                return _event
            elif isinstance(_event, list):
                for i in range(len(_event)):
                    _event[i] = __to_dict(_event[i])
                return _event
            elif isinstance(_event, tuple):
                return tuple(__to_dict(list(_event)))
            elif isinstance(_event, set):
                return set(__to_dict(list(_event)))
            elif hasattr(_event, 'to_dict'):
                return __to_dict(_event.to_dict())
            elif hasattr(_event, '__dict__'):
                return __to_dict(_event.__dict__)
            elif isinstance(_event, (int, float, str, bool, type(None))):
                return _event
            else:
                return str(_event)


        raw_data = __to_dict(event.event_data)
        targets = raw_data.get("transferinfo").get("file_list_new")

        for media in targets:
            logger.info(f'test {media}...')
            file_name, file_ext = os.path.splitext(media)
            nfo_file = file_name + ".nfo"
            if os.path.exists(nfo_file):
                logger.info(f'准备处理 {nfo_file}...')
                self.replace_cdata_tags(nfo_file)
            else:
                logger.error(f'{nfo_file} 不存在')


        

    def stop_service(self):
        """
        退出插件
        """
        pass
