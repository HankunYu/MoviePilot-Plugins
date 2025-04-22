# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.system import SystemUtils
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.chain.media import MediaChain
from app.core.metainfo import MetaInfo
from app.core.config import settings
from app import schemas
from app.schemas.types import MediaType, EventType, SystemConfigKey
from datetime import datetime

from typing import Any, List, Dict, Tuple, Optional
import subprocess
import os
import threading
from app.plugins.danmu import danmu_generator as generator
    

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
    plugin_version = "1.2.0"
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
    _cron = '0 0 1 1 *'
    _path = ''
    _max_threads = 10
    _onlyFromBili = False
    _useTmdbID = True
    
    media_chain = MediaChain()
    
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._width = config.get("width", 1920)
            self._height = config.get("height", 1080)
            # self._fontface = config.get("fontface")
            self._fontsize = config.get("fontsize", 50)
            self._alpha = config.get("alpha", 0.8)
            self._duration = config.get("duration", 10)
            self._path = config.get("path", "")
            self._cron = config.get("cron", "0 0 1 1 *")
            self._onlyFromBili = config.get("onlyFromBili", False)
            self._useTmdbID = config.get("useTmdbID", True)
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
        return []
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
        """
        获取插件API
        [{
            "path": "/xx",
            "endpoint": self.xxx,
            "methods": ["GET", "POST"],
            "summary": "API说明"
        }]
        """
        return [{
            "path": "/generate_danmu_with_path",
            "endpoint": self.generate_danmu_global,
            "methods": ["GET"],
            "summary": "刮削弹幕",
            "description": "根据设定的路径刮削弹幕"
        },{
            "path": "/update_path",
            "endpoint": self.update_path,
            "methods": ["GET"],
            "summary": "更新路径",
            "description": "更新刮削路径"
        }]
    
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
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'onlyFromBili',
                                            'label': '仅使用B站弹幕，建议关闭',
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
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'useTmdbID',
                                            'label': '使用TMDB ID作为预备匹配方案，当无法匹配文件hash时尝试使用TMDB ID',
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
                                            'label': '弹幕持续时间 默认10秒',
                                            'type': 'number',
                                     
                                        }
                                    }
                                ]
                            },
                            # {
                            #     'component': 'VCol',
                            #     'props': {
                            #         'cols': 6,
                            #     },
                            #     'content': [
                            #         {
                            #             'component': 'VTextField',
                            #             'props': {
                            #                 'model': 'cron',
                            #                 'label': '取消定期刮削，需要全局刮削请去 设置->服务 手动启动',
                            #                 'type': 'text',
                                     
                            #             }
                            #         }
                            #     ]
                            # }
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
                    # {
                    #     'component': 'VRow',
                    #     'content': [
                    #         {
                    #             'component': 'VCol',
                    #             'props': {
                    #                 'cols': 6
                    #             },
                    #             'content': [
                    #                 {
                    #                     'component': 'VBtn',
                    #                     'props': {
                    #                         'color': 'primary',
                    #                         'block': True
                    #                     },
                    #                     'content': [
                    #                         {
                    #                             'component': 'text',
                    #                             'text': '手动刮削指定路径',
                    #                             "onClick": "function(e) { fetch('http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/plugin/Danmu/generate_danmu_with_path?apikey=' + {settings.API_TOKEN}).then(response => response.json()).then(data => { console.log('刮削完成:', data); }).catch(error => { console.error('刮削失败:', error); }); }",
                    #                         }
                    #                     ]
                    #                 }
                    #             ]
                    #         },
                    #     ]
                    # },
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
                                            'text': '此插件会根据情况生成两种弹幕字幕文件，均为ass格式。.danmu为刮削出来的纯弹幕，.withDanmu为原生字幕与弹幕合并后的文件。自动刮削新入库文件。如果没有外挂字幕只有内嵌字幕会自动提取内嵌字幕生成.withDanmu文件。弹幕来源为 弹弹play 提供的多站合并资源以及 https://github.com/m13253/danmaku2ass 提供的思路。',
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
            "cron": "0 0 1 1 *",
            "path": "",
            "onlyFromBili": False,
            "useTmdbID": True
        }

    def get_page(self) -> List[dict]:
        pass
            
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'div',
                        'content': [
                            {
                                'component': 'div',
                                'text': '刮削的媒体库路径',
                                'props': {
                                    'class': 'text-subtitle-1 text-medium-emphasis mb-2'
                                }
                            },
                            {
                                'component': 'VTextarea',
                                'props': {
                                    'model': 'current_path',
                                    'value': self._path,
                                    'variant': 'outlined',
                                    'bg-color': 'surface',
                                    'rows': 2,
                                    'readonly': True,
                                    'disabled': True
                                }
                            }
                        ]
                    },
                    # {
                    #     'component': 'div',
                    #     'props': {
                    #         'class': 'mt-4'
                    #     },
                    #     'content': [
                    #         {
                    #             'component': 'div',
                    #             'text': '新的媒体库路径',
                    #             'props': {
                    #                 'class': 'text-subtitle-1 text-medium-emphasis mb-2'
                    #             }
                    #         },
                    #         {
                    #             'component': 'VTextarea',
                    #             'props': {
                    #                 'model': 'path',
                    #                 'id': 'path-input',
                    #                 'placeholder': '请输入新的媒体库路径，一行一个',
                    #                 'variant': 'outlined',
                    #                 'bg-color': 'surface',
                    #                 'rows': 2
                    #             }
                    #         }
                    #     ]
                    # },
                    {
                        'component': 'VRow',
                        'props': {
                            'class': 'mt-2'
                        },
                        'content': [
                            # {
                            #     'component': 'VCol',
                            #     'props': {
                            #         'cols': 6
                            #     },
                            #     'content': [
                            #         {
                            #             'component': 'VBtn',
                            #             'props': {
                            #                 'color': 'primary',
                            #                 'block': True
                            #             },
                            #             'content': [
                            #                 {
                            #                     'component': 'text',
                            #                     'text': '保存路径'
                            #                 }
                            #             ],
                            #             'events': {
                            #                 'click': {
                            #                     'api': 'plugin/Danmu/update_path',
                            #                     'method': 'GET',
                            #                     'params': {
                            #                         'apikey': settings.API_TOKEN,
                            #                         'path': ''
                            #                     }
                            #                 }
                            #             }
                            #         }
                            #     ]
                            # },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 3,
                                    'offset': 9
                                },
                                'content': [
                                    {
                                        'component': 'VBtn',
                                        'props': {
                                            'color': 'primary',
                                            'block': True
                                        },
                                        'content': [
                                            {
                                                'component': 'text',
                                                'text': '开始刮削'
                                            }
                                        ],
                                        'events': {
                                            'click': {
                                                'api': 'plugin/Danmu/generate_danmu_with_path',
                                                'method': 'GET',
                                                'params': {
                                                    'apikey': settings.API_TOKEN
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'props': {
                            'class': 'mt-8 mb-8'
                        }
                    }
                ]
            }
        ]
    
    def generate_danmu(self, file_path: str) -> Optional[str]:
        """
        生成弹幕文件
        :param file_path: 视频文件路径
        :return: 生成的弹幕文件路径，如果失败则返回None
        """
        meta = MetaInfo(file_path)
        tmdb_id = None
        episode = None
        release_date = None
        use_short_cache_ttl = False
        if self._useTmdbID:
            media_info = self.media_chain.recognize_media(meta=meta)
            if media_info:
                tmdb_id = media_info.tmdb_id
                episode = meta.episode.split('E')[1] if meta.episode else None
                release_date = media_info.release_date
                # 检查发布日期是否在最近90天内
                if release_date:
                    try:
                        release_datetime = datetime.strptime(release_date, '%Y-%m-%d')
                        is_recent = (datetime.now() - release_datetime).days < 90
                        if is_recent:
                            logger.info(f"媒体 {tmdb_id} 是最近90天内发布的内容,使用短缓存")
                            use_short_cache_ttl = True
                    except ValueError:
                        logger.warning(f"无效的发布日期格式: {release_date},使用默认缓存时间")
                    
    
        try:
            return generator.danmu_generator(
                file_path,
                self._width,
                self._height,
                'Arial',
                self._fontsize,
                self._alpha,
                self._duration,
                self._onlyFromBili,
                self._useTmdbID,
                tmdb_id,
                episode,
                60 if use_short_cache_ttl else None
            )
        except Exception as e:
            logger.error(f"生成弹幕失败: {e}")
            return None

    def update_path(self, path: str):
        """
        更新路径
        """
        self._path = path
        logger.info(f"更新路径: {self._path}")
        
    def generate_danmu_global(self):
        """
        全局刮削弹幕
        """
        if not self._path:
            logger.warning("未设置刮削路径，跳过刮削")
            return schemas.Response(success=False, message="没有设定路径")

        logger.info("开始弹幕刮削")
        threading_list = []
        paths = [path.strip() for path in self._path.split('\n') if path.strip()]

        for path in paths:
            if not os.path.exists(path):
                logger.warning(f"路径不存在: {path}")
                return schemas.Response(success=False, message=f"路径不存在: {path}")
                continue

            # 检查是否是单个文件
            if os.path.isfile(path) and path.endswith(('.mp4', '.mkv')):
                logger.info(f"刮削单个文件：{path}")
                if len(threading_list) >= self._max_threads:
                    threading_list[0].join()
                    threading_list.pop(0)

                thread = threading.Thread(
                    target=self.generate_danmu,
                    args=(path,)
                )
                thread.start()
                threading_list.append(thread)
                continue

            # 处理目录
            logger.info(f"刮削路径：{path}")
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(('.mp4', '.mkv')):
                        if len(threading_list) >= self._max_threads:
                            threading_list[0].join()
                            threading_list.pop(0)

                        target_file = os.path.join(root, file)
                        logger.info(f"开始生成弹幕文件：{target_file}")
                        thread = threading.Thread(
                            target=self.generate_danmu,
                            args=(target_file,)
                        )
                        thread.start()
                        threading_list.append(thread)

        for thread in threading_list:
            thread.join()

        logger.info("弹幕刮削完成")
        return schemas.Response(success=True, message="弹幕刮削完成 ")
    
    @eventmanager.register(EventType.TransferComplete)
    def generate_danmu_after_transfer(self, event):
        """
        传输完成后生成弹幕
        """
        if not self._enabled:
            return

        def __to_dict(_event):
            """
            递归将对象转换为字典
            """
            if isinstance(_event, dict):
                return {k: __to_dict(v) for k, v in _event.items()}
            elif isinstance(_event, list):
                return [__to_dict(item) for item in _event]
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

        try:
            raw_data = __to_dict(event.event_data)
            target_file = raw_data.get("transferinfo", {}).get("file_list_new", [None])[0]
            
            if not target_file:
                logger.warning("未找到目标文件")
                return

            logger.info(f"开始生成弹幕文件：{target_file}")
            thread = threading.Thread(
                target=self.generate_danmu,
                args=(target_file,)
            )
            thread.start()
        except Exception as e:
            logger.error(f"处理传输完成事件失败: {e}")

    def stop_service(self):
        """
        退出插件
        """
        pass
