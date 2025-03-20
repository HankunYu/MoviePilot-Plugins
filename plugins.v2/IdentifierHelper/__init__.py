from typing import List, Tuple, Dict, Any

import datetime, re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.utils.http import RequestUtils
from app.log import logger

from app.plugins import _PluginBase
from ...db.systemconfig_oper import SystemConfigOper
from ...schemas.types import SystemConfigKey
from app.utils.common import retry


class IdentifierHelper(_PluginBase):
    # 插件名称
    plugin_name = "自定义识别词助手"
    # 插件描述
    plugin_desc = "帮助管理自定义识别词"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/icons/Identifier.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "identifierHelper_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1  
    # 条目的类型
    _type = ['屏蔽', '替换', '集偏移', '替换和集偏移']
    _entries = []
    _catgroies = []
    
    def init_plugin(self, config: dict = None):
        if not config:
            return
        
        # config操作
        self.__update_config()



    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {
                            "cols": 12,
                        },
                        "content": [
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "warning",
                                    "variant": "tonal",
                                    "text": "注意备份"
                                }
                            }
                        ]
                    }
                ]
            },               
            "component": "VTabs",
                "props": {
                    "model": "_tabs",
                    "height": 72,
                    "fixed-tabs": True,
                    "style": {
                        "margin-top": "8px",
                        "margin-bottom": "10px",
                    }
                },
        ], {
            
        }

    def __update_config(self):
        self.update_config({
        })

    def stop_service(self):
        pass

    def get_page(self) -> List[dict]:
        pass

    def get_state(self) -> bool:
        return False

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass
    
    def add_entry(self, catgory, entry_type, content):
        # 创建一个字典表示条目
        entry = {
            "Catgory": catgory,
            "Type": entry_type,
            "Content": content
        }
        # 将条目添加到列表中
        self._entries.append(entry)
        
    def extract_identifier(self):
        text = SystemConfigOper.get(SystemConfigKey.CustomIdentifiers)
        
        # 初始化结果
        self._categories = []
        current_category = '未分类'
        self._categories.append(current_category)
        
        # 按行分割文本
        lines = text.strip().split('\n')
    
        # 遍历每一行
        for line in lines:
            line = line.strip()  # 去除行首尾空白
            
            # 匹配分类开始
            category_start_match = re.match(r'^##\s*Catgory\s*(.*)$', line)
            if category_start_match:
                current_category = category_start_match.group(1).strip()
                self._categories.append(current_category)
                continue
            
            # 匹配分类结束
            if line.startswith('## Catgory End'):
                current_category = '未分类'  # 结束当前分类
                continue
            
            # 开始匹配条目
            # 匹配屏蔽词
            if re.match(r'^\S+$', line):
                self.add_entry(current_category, '屏蔽', line)
                continue
            
            # 匹配结合替换和集偏移量的格式
            complex_match = re.match(r'^(.*?)\s*=>\s*(.*)\s*&&\s*(.*?)\s*<>\s*(.*?)\s*>>\s*(.*)$', line)
            if complex_match:
                self.add_entry(current_category, '替换和集偏移', line)
                continue
            
            # 匹配被替换词 => 替换词
            simple_replace_match = re.match(r'^(.*?)\s*=>\s*(.*)$', line)
            if simple_replace_match:
                self.add_entry(current_category, '替换', line)
                continue
            
            # 匹配前定位词 <> 后定位词 >> 集偏移量（EP）
            offset_match = re.match(r'^(.*?)\s*<>\s*(.*?)\s*>>\s*(.*)$', line)
            if offset_match:
                self.add_entry(current_category, '集偏移', line)
                continue
            
            

