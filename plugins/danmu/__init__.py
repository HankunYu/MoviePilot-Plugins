
# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.system import SystemUtils
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from typing import Any, List, Dict, Tuple
import subprocess
import os
import threading
from plugins.danmu import danmu_generator as generator
    

class Danmu(_PluginBase):
    # 插件名称
    plugin_name = "弹幕刮削"
    # 插件描述
    plugin_desc = "使用弹弹play平台生成弹幕的字幕文件，实现弹幕播放。"
    # 插件图标
    plugin_icon =  "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/icons/danmu.png"
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "1.0.7"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "danmu_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _width = 1920
    _height = 1080
    # 搞字体太复杂 以后再说
    # _fontface = 'Arial'
    _fontsize = 50
    _alpha = 0.8
    _duration = 6
    _cron = '0 23 * * 3'
    _path = ''

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._width = config.get("width")
            self._height = config.get("height")
            # self._fontface = config.get("fontface")
            self._fontsize = config.get("fontsize")
            self._alpha = config.get("alpha")
            self._duration = config.get("duration")
            self._path = config.get("path")
            self._cron = config.get("cron")
        if self._enabled:
            logger.info("弹幕加载插件已启用")
            

    def get_state(self) -> bool:
        return self._enabled
    
    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        [{
            "id": "服务ID",
            "name": "服务名称",
            "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数
        }]
        """
        if self.get_state() and self._path and self._cron:
            return [{
                "id": "Danmu",
                "name": "弹幕全局刮削服务",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.generate_danmu_global,
                "kwargs": {}
            }]
        return []
        
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
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 6,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'width',
                                            'label': '宽度，默认1920',
                                            'type': 'number',
                                        
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 6,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'height',
                                            'label': '高度，默认1080',
                                            'type': 'number',
                                       
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
                                    'cols': 6,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'fontsize',
                                            'label': '字体大小，默认50',
                                            'type': 'number',
                                        
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 6,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'alpha',
                                            'label': '弹幕透明度，默认0.8',
                                            'type': 'number',
                                            
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
                                    'cols': 6,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'duration',
                                            'label': '弹幕持续时间 默认6秒',
                                            'type': 'number',
                                     
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 6,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '自定义 cron 参数，默认每周三晚上十一点运行一次',
                                            'type': 'text',
                                     
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
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'path',
                                            'label': '刮削媒体库路径，一行一个',
                                            'placeholder': '留空不启用',
                                            'rows': 2,
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
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'flat',
                                            'text': '此插件会根据情况生成两种弹幕字幕文件，均为ass格式。.danmu为刮削出来的纯弹幕，.withDanmu为原生字幕与弹幕合并后的文件。自动刮削新入库文件。如果没有外挂字幕只有内嵌字幕会自动提取内嵌字幕生成.withDanmu文件。弹幕来源为 弹弹play 提供的多站合并资源以及 https://github.com/m13253/danmaku2ass 提供的思路。第一次使用可以去 设置->服务 手动启动全局刮削',
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "width": 1920,
            "height": 1080,
            "fontsize": 50,
            "alpha": 0.8,
            "duration": 6,
            "cron": "0 23 * * 3",
        }

    def get_page(self) -> List[dict]:
        pass
    
    def generate_danmu(self, file_path: str):
        generator.danmu_generator(file_path, self._width, self._height,'Arial', self._fontsize, self._alpha, self._duration)

    def generate_danmu_global(self):
        # 同时最多开启10个线程
        threading_list = []
        max_thread = 10
        if self._path:
            logger.info("开始全局弹幕刮削")
            # 按行切割并去除前后空白
            paths = [path.strip() for path in self._path.split('\n') if path.strip()]
            for path in paths:
                logger.info(f"刮削路径：{path}")
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.endswith('.mp4') or file.endswith('.mkv'):
                                if len(threading_list) >= max_thread:
                                    threading_list[0].join()  # 只等待第一个线程
                                    threading_list.pop(0)
                                target_file = os.path.join(root, file)
                                print(f"开始生成弹幕文件：{target_file}")
                                thread = threading.Thread(target=self.generate_danmu, args=(target_file,))
                                thread.start()
                                threading_list.append(thread)
        
        for thread in threading_list:
            thread.join()
        logger.info("全局弹幕刮削完成")
    
    @eventmanager.register(EventType.TransferComplete)
    def generate_danmu_after_transfer(self, event):
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
        target_file = raw_data.get("transferinfo").get("file_list_new")[0]
        logger.info(f"开始生成弹幕文件：{target_file}")
        thread = threading.Thread(target=self.generate_danmu, args=(target_file,))
        thread.start()
        



    def stop_service(self):
        """
        退出插件
        """
        pass
