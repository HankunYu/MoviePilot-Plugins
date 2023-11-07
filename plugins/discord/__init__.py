#import discord
import requests

# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from typing import Any, List, Dict, Tuple
from app.utils.http import RequestUtils

class Discord(_PluginBase):
    # 插件名称
    plugin_name = "discord"
    # 插件描述
    plugin_desc = "Discord 消息推送"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins-discord/main/icons/discord.png"
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "0.13"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "discord_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _webhook_url = None
    _enabled = False
    _debug_enabled = False
    _site_url = None

    # 消息类型
    _download: str = "资源下载"
    _subscribe: str = "订阅"
    _organize: str = "整理入库"
    _site_message: str = "站点消息"
    _media_server: str = "媒体服务器通知"
    _manual: str = "手动处理通知"
    _all_types: List[str] = [_download, _subscribe, _organize, _site_message, _media_server, _manual]
    _select_types: List[str] = []


    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._webhook_url = config.get("webhook_url")
            self._debug_enabled = config.get("debug_enabled")
            self._site_url = config.get("site_url")
            self._select_types = config.get("select_types")
        
        logger.info(f"Discord插件初始化完成")

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
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'debug_enabled',
                                            'label': 'debug模式',
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
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'webhook_url',
                                            'label': 'Discord webhook URL'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'site_url',
                                            'label': '站点地址或IP（可选）'
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
                                        'component': 'VSelect',
                                        'props': {
                                            'chips': True,
                                            'multiple': True,
                                            'model': 'select_types',
                                            'label': '选择通知类型',
                                            'items': self._all_types
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
            "debug_enabled": False,
            "webhook_url": "",
            "site_url": "",
            "select_types": []
        }

    def get_page(self) -> List[dict]:
        pass
    """
    Example:
    资源下载通知
    {
        'channel': None, 
        'type': {
            '_value_': '资源下载', 
            '_name_': 'Download', 
            '__objclass__': "{
                '_generate_next_value_': <function Enum._generate_next_value_ at 0x7f4950e3cb80>, 
                '__module__': 'app.schemas.types', 
                '_new_member_': <built-in method __new__ of type object at 0x7f495180b0c0>, 
                '_use_args_': False, 
                '_member_names_': ['Download', 'Organize', 'Subscribe', 'SiteMessage', 'MediaServer', 'Manual'], 
                '_member_map_': {'Download': <NotificationType.Download: '资源下载'>, 
                'Organize': <NotificationType.Organize: '整理入库'>, 
                'Subscribe': <NotificationType.Subscribe: '订阅'>, 
                'SiteMessage': <NotificationType.SiteMessage: '站点消息'>, 
                'MediaServer': <NotificationType.MediaServer: '媒体服务器通知'>, 
                'Manual': <NotificationType.Manual: '手动处理通知'>
                }, 
            '_value2member_map_': {
                '资源下载': <NotificationType.Download: '资源下载'>, 
                '整理入库': <NotificationType.Organize: '整理入库'>, 
                '订阅': <NotificationType.Subscribe: '订阅'>, 
                '站点消息': <NotificationType.SiteMessage: '站点消息'>, 
                '媒体服务器通知': <NotificationType.MediaServer: '媒体服务器通知'>, 
                '手动处理通知': <NotificationType.Manual: '手动处理通知'>
                }, 
            '_unhashable_values_': [], 
            '_member_type_': <class 'object'>, 
            '_value_repr_': None, 
            '__doc__': None, 
            'Download': <NotificationType.Download: '资源下载'>, 
            'Organize': <NotificationType.Organize: '整理入库'>, 
            'Subscribe': <NotificationType.Subscribe: '订阅'>, 
            'SiteMessage': <NotificationType.SiteMessage: '站点消息'>, 
            'MediaServer': <NotificationType.MediaServer: '媒体服务器通知'>, 
            'Manual': <NotificationType.Manual: '手动处理通知'>, 
            '__new__': <function Enum.__new__ at 0x7f4950e3ca40>}", 
            '_sort_order_': 0
        }, 
        'title': '猪肝记得煮熟再吃 (2023) S01 E05 开始下载', 
        'text': '\n站点：Nyaa\n质量： 1080p\n大小：268.7M\n种子：[LoliHouse] 猪肝记得煮熟再吃 / Buta no Liver wa Kanetsu Shiro - 05 [WebRip 1080p HEVC-10bit AAC][简繁内封字幕]\n发布时间：2023-11-05 02:59\n做种数：74', 
        'image': 'https://image.tmdb.org/t/p/w500/b4fZ0Ez3ngJhbG2cPmVHwOObgVO.jpg', 
        'userid': None
    }
    数据统计通知
    {
        'channel': None, 
        'type': {
            '_value_': '站点消息', 
            '_name_': 'SiteMessage', 
            '__objclass__': "{
                '_generate_next_value_': <function Enum._generate_next_value_ at 0x7f4950e3cb80>, 
                '__module__': 'app.schemas.types', 
                '_new_member_': <built-in method __new__ of type object at 0x7f495180b0c0>, 
                '_use_args_': False, 
                '_member_names_': ['Download', 'Organize', 'Subscribe', 'SiteMessage', 'MediaServer', 'Manual'], 
                '_member_map_': {
                    'Download': <NotificationType.Download: '资源下载'>, 
                    'Organize': <NotificationType.Organize: '整理入库'>, 
                    'Subscribe': <NotificationType.Subscribe: '订阅'>, 
                    'SiteMessage': <NotificationType.SiteMessage: '站点消息'>, 
                    'MediaServer': <NotificationType.MediaServer: '媒体服务器通知'>, 
                    'Manual': <NotificationType.Manual: '手动处理通知'>
                }, 
                '_value2member_map_': {
                    '资源下载': <NotificationType.Download: '资源下载'>, 
                    '整理入库': <NotificationType.Organize: '整理入库'>, 
                    '订阅': <NotificationType.Subscribe: '订阅'>, 
                    '站点消息': <NotificationType.SiteMessage: '站点消息'>, 
                    '媒体服务器通知': <NotificationType.MediaServer: '媒体服务器通知'>, 
                    '手动处理通知': <NotificationType.Manual: '手动处理通知'>}, 
                    '_unhashable_values_': [], 
                    '_member_type_': <class 'object'>, 
                    '_value_repr_': None, '__doc__': None, 
                    'Download': <NotificationType.Download: '资源下载'>, 
                    'Organize': <NotificationType.Organize: '整理入库'>, 
                    'Subscribe': <NotificationType.Subscribe: '订阅'>, 
                    'SiteMessage': <NotificationType.SiteMessage: '站点消息'>, 
                    'MediaServer': <NotificationType.MediaServer: '媒体服务器通知'>, 
                    'Manual': <NotificationType.Manual: '手动处理通知'>, 
                    '__new__': <function Enum.__new__ at 0x7f4950e3ca40>
                },
            '_sort_order_': 3
        }, 
        'title': '【站点自动签到】', 
        'text': '全部签到数量: 7 \n本次签到数量: 7 \n下次签到数量: 0 \n【梓喵】签到成功\n【2xFree】签到成功\n【红豆饭】签到成功\n【聆音】签到成功\n【馒头】签到成功\n【我堡】签到成功\n【幼儿园】今日已签到', 
        'image': None, 
        'userid': None
    }
    """
    def convert_data_to_embed(self,data,type):
        msg = data.get('text')
        title = msg.get('title')
        converted_text = ''
        fields = []
        url = self._site_url

        # 处理站点数据统计事件===================================================
        if(type == self._site_message):
            lines = msg.get('text').split('\n')
            converted_text = '  '
            for i in range(0, len(lines), 4):
                # 提取站点和上传下载量
                site = lines[i][1:].strip('】')
                upload = lines[i + 1].split('：')[1]
                download = lines[i + 2].split('：')[1]
                if(site == '汇总'):
                    converted_text = f'**汇总**\n上传量:`{upload}`\n下载量:`{download}`'
                    continue
                # 创建一个字典表示一个field
                field = {
                    "name": "**"+site+"**",
                    "value": f"上传量:`{upload}`\n下载量:`{download}`",
                    "inline": True
                }
                # 将field添加到fields列表中
                fields.append(field)

        # 处理开始下载事件===================================================
        elif(type == self._download):
            lines =  msg.get('text').split('\n')
            if(url != None):
                url += '/downloading'
            converted_text = '  '
            # 遍历每行内容
            for line in lines:
                print(line)
                # 将每行内容按冒号分割为字段名称和值
                if '：' not in line:
                    continue
                name, value = line.split('：', 1)
                
                # 创建一个字典表示一个 field
                if(name == '种子'):
                    continue
                field = {
                    "name": name.strip(),
                    "value": value.strip(),
                    "inline": True
                }
                
                # 将 field 添加到 fields 列表中
                fields.append(field)
    
        # 处理入库事件===================================================
        elif(type == self._organize):
            lines =  msg.get('text').split('，')
            converted_text = '  '
            # 遍历每行内容
            for line in lines:
                # 将每行内容按冒号分割为字段名称和值
                print(line)
                if '：' not in line:
                    converted_text = line
                else: 
                    name, value = line.split('：', 1)
                
                    # 创建一个字典表示一个 field
                    field = {
                        "name": name.strip(),
                        "value": value.strip(),
                        "inline": True
                    }
                    
                    # 将 field 添加到 fields 列表中
                    fields.append(field)
        # # 处理 一般事件===================================================
        else:
            lines =  msg.get('text').split('，')
            converted_text = '  '
            # 遍历每行内容
            for line in lines:
                # 将每行内容按冒号分割为字段名称和值
                print(line)
                if '：' not in line:
                    converted_text += line + '\n'
                else: 
                    name, value = line.split('：', 1)
                
                    # 创建一个字典表示一个 field
                    field = {
                        "name": name.strip(),
                        "value": value.strip(),
                        "inline": True
                    }
                    
                    # 将 field 添加到 fields 列表中
                    fields.append(field)
        
        # 构造 Webhook 请求的 JSON 数据
        if(self._debug_enabled):
            logger.info(f"尝试构造 Webhook 请求的 JSON 数据:" + str(data))
        data_json = {
            "embeds": [
                {
                    "author": {
                        "name": "Movie Pilot",
                        "url": url if url else "https://github.com/jxxghp/MoviePilot",
                        "icon_url": "https://cdn5.telegram-cdn.org/file/EKiDxdgUGOAW_YodOwWymqXoHrQKnY9v8YG_Id2unx6mQ2N-k_cdpVGigj7kBm2V78-dmu1w_-4g1rkHS_dUOZzajThES4XPLzUAanPON5KXxQnjVkmb2PJJI0zWMXKFUbhiHOdVS5n014LAgCUQ5OBvwQHNIgDDWznIEfa5-4bJdE2NDM3aN61-5tsT4zqm7caqfe-ERpyR49pLpe4w_W6ZhCPUiVCqDAMQpVqF-JP4ifVL5Z9KfV6X5_B0Pjy-hZlQFPC-RHZ8K-RGu4OhSYyaGs7hijOFzOZfoB-wuX99yttxAZqZ3uwvxD2qBMdltiWREUsg2fqPkRsLwDhkAQ.jpg"
                    },
                    "title": title,
                    "url": url if url else "https://github.com/jxxghp/MoviePilot",
                    "color": 15258703,
                    "description": converted_text if converted_text else msg.get('text'),
                    "fields": fields,
                    "image": {
                        "url": "http://none.png" if msg.get('image') is None else msg.get('image')
                    }
                }
            ]
            
        }

        return data_json
    
    @eventmanager.register(EventType)
    def send(self, event):
        """
        向discord Webhook发送请求
        """
        if not self._enabled or not self._webhook_url:
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

        # event_info = {
        #     "type": event.event_type,
        #     "data": __to_dict(event.event_data)
        # }
        raw_data = __to_dict(event.event_data)
        type = raw_data.get('type').get('_value_')
        if(self._debug_enabled):
            logger.info(f"raw data: " + str(raw_data))
            logger.info(f"event type: " + str(type))
        
        # 只发送已选择的通知消息
        if(type not in self._select_types):
            return
        event_info = self.convert_data_to_embed(self,raw_data,type)
        ret = RequestUtils(content_type="application/json").post_res(self._webhook_url, json=event_info)
        
        if ret:
            logger.info("发送成功：%s" % self._webhook_url)
        elif ret is not None:
            logger.error(f"发送失败，状态码：{ret.status_code}，返回信息：{ret.text} {ret.reason}")
        else:
            logger.error("发送失败，未获取到返回信息")

    def stop_service(self):
        """
        退出插件
        """
        pass