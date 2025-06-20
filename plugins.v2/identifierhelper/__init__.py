from typing import List, Tuple, Dict, Any, Optional

import datetime, re, json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.utils.http import RequestUtils
from app.log import logger

from app.plugins import _PluginBase
from app.db.systemconfig_oper import SystemConfigOper
from app.schemas.types import SystemConfigKey, EventType
from app.utils.common import retry


class IdentifierHelper(_PluginBase):
    # 插件名称
    plugin_name = "自定义识别词助手"
    # 插件描述
    plugin_desc = "帮助管理自定义识别词，支持标签分类和可视化编辑"
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
    _categories = []
    
    # SystemConfig操作器
    systemconfig = None
    
    def init_plugin(self, config: dict = None):
        # 初始化SystemConfig操作器
        self.systemconfig = SystemConfigOper()
        
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
                                    "type": "info",
                                    "variant": "tonal",
                                    "text": "自定义识别词管理插件，支持标签分类和可视化编辑。请注意备份原始数据。"
                                }
                            }
                        ]
                    }
                ]
            }
        ], {}

    def __update_config(self):
        self.update_config({
        })

    def stop_service(self):
        pass

    def get_page(self) -> List[dict]:
        return [
            {
                "component": "div",
                "text": "自定义识别词管理",
                "props": {
                    "class": "text-center"
                }
            },
            {
                "component": "VBtn",
                "text": "打开管理界面",
                "props": {
                    "class": "mt-3",
                    "block": True,
                    "color": "primary",
                    "@click": "openIdentifierManager"
                }
            }
        ]

    def get_state(self) -> bool:
        return False

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [
            {
                "cmd": "/identifier_reload",
                "event": EventType.PluginAction,
                "desc": "重新加载自定义识别词",
                "category": "识别词管理",
                "data": {
                    "action": "reload_identifiers"
                }
            },
            {
                "cmd": "/identifier_backup",
                "event": EventType.PluginAction,
                "desc": "备份当前识别词配置",
                "category": "识别词管理",
                "data": {
                    "action": "backup_identifiers"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/get_identifiers",
                "endpoint": self.get_identifiers,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取解析后的识别词列表",
                "description": "获取按标签分类的识别词列表"
            },
            {
                "path": "/save_identifiers",
                "endpoint": self.save_identifiers,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存识别词列表",
                "description": "将识别词列表保存到系统配置"
            },
            {
                "path": "/get_raw_identifiers",
                "endpoint": self.get_raw_identifiers,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取原始识别词数据",
                "description": "获取未解析的原始识别词文本"
            },
            {
                "path": "/save_raw_identifiers",
                "endpoint": self.save_raw_identifiers,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存原始识别词数据",
                "description": "直接保存原始识别词文本"
            },
            {
                "path": "/parse_identifiers",
                "endpoint": self.parse_identifiers,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "解析识别词数据",
                "description": "解析原始文本为结构化数据"
            }
        ]
    
    def add_entry(self, category, entry_type, content):
        # 创建一个字典表示条目
        entry = {
            "Category": category,
            "Type": entry_type,
            "Content": content
        }
        # 将条目添加到列表中
        self._entries.append(entry)
        
    def extract_identifier(self, text: str = None) -> List[Dict[str, str]]:
        """提取识别词并返回结构化数据"""
        if text is None:
            text = self.systemconfig.get(SystemConfigKey.CustomIdentifiers) or ""
        
        # 初始化结果
        entries = []
        current_tag = '未分类'
        
        # 按行分割文本
        lines = text.strip().split('\n') if text else []
    
        # 遍历每一行
        for line in lines:
            line = line.strip()  # 去除行首尾空白
            
            if not line:  # 跳过空行
                continue
            
            # 匹配标签开始（# 标签名）
            tag_match = re.match(r'^#\s*(.+)$', line)
            if tag_match:
                current_tag = tag_match.group(1).strip()
                continue
            
            # 开始匹配条目
            entry_type = self._determine_entry_type(line)
            if entry_type:
                entries.append({
                    'tag': current_tag,
                    'type': entry_type,
                    'content': line
                })
        
        return entries
    
    def _determine_entry_type(self, line: str) -> Optional[str]:
        """确定识别词条目的类型"""
        # 匹配结合替换和集偏移量的格式
        if re.match(r'^.*?\s*=>\s*.*\s*&&\s*.*?\s*<>\s*.*?\s*>>\s*.*$', line):
            return '替换和集偏移'
        
        # 匹配被替换词 => 替换词
        if re.match(r'^.*?\s*=>\s*.*$', line):
            return '替换'
        
        # 匹配前定位词 <> 后定位词 >> 集偏移量（EP）
        if re.match(r'^.*?\s*<>\s*.*?\s*>>\s*.*$', line):
            return '集偏移'
        
        # 匹配屏蔽词（简单的非空单词）
        if re.match(r'^\S+.*$', line):
            return '屏蔽'
        
        return None
    
    def _generate_raw_data(self, identifiers: List[Dict[str, str]]) -> str:
        """将结构化数据转换为原始文本格式"""
        if not identifiers:
            return ""
        
        # 按标签分组
        grouped = {}
        for item in identifiers:
            tag = item['tag']
            if tag not in grouped:
                grouped[tag] = []
            grouped[tag].append(item)
        
        # 生成文本
        lines = []
        
        # 处理未分类的条目（放在最前面，不需要标签标记）
        if '未分类' in grouped:
            for item in grouped['未分类']:
                lines.append(item['content'])
            lines.append('')  # 空行分隔
            del grouped['未分类']
        
        # 处理其他标签
        for tag, items in grouped.items():
            lines.append(f'# {tag}')
            for item in items:
                lines.append(item['content'])
            lines.append('')  # 空行分隔
        
        return '\n'.join(lines).strip()
    
    # API端点实现
    def get_identifiers(self) -> Dict[str, Any]:
        """获取解析后的识别词列表"""
        try:
            identifiers = self.extract_identifier()
            return {
                "code": 0,
                "message": "success",
                "data": identifiers
            }
        except Exception as e:
            logger.error(f"获取识别词失败: {e}")
            return {
                "code": 1,
                "message": f"获取识别词失败: {str(e)}",
                "data": []
            }
    
    def save_identifiers(self, identifiers: List[Dict[str, str]]) -> Dict[str, Any]:
        """保存识别词列表"""
        try:
            raw_data = self._generate_raw_data(identifiers)
            self.systemconfig.set(SystemConfigKey.CustomIdentifiers, raw_data)
            logger.info(f"保存了 {len(identifiers)} 条识别词")
            return {
                "code": 0,
                "message": "识别词保存成功"
            }
        except Exception as e:
            logger.error(f"保存识别词失败: {e}")
            return {
                "code": 1,
                "message": f"保存识别词失败: {str(e)}"
            }
    
    def get_raw_identifiers(self) -> Dict[str, Any]:
        """获取原始识别词数据"""
        try:
            raw_data = self.systemconfig.get(SystemConfigKey.CustomIdentifiers) or ""
            return {
                "code": 0,
                "message": "success",
                "data": raw_data
            }
        except Exception as e:
            logger.error(f"获取原始识别词失败: {e}")
            return {
                "code": 1,
                "message": f"获取原始识别词失败: {str(e)}",
                "data": ""
            }
    
    def save_raw_identifiers(self, data: str) -> Dict[str, Any]:
        """保存原始识别词数据"""
        try:
            self.systemconfig.set(SystemConfigKey.CustomIdentifiers, data)
            logger.info("原始识别词数据保存成功")
            return {
                "code": 0,
                "message": "原始识别词数据保存成功"
            }
        except Exception as e:
            logger.error(f"保存原始识别词失败: {e}")
            return {
                "code": 1,
                "message": f"保存原始识别词失败: {str(e)}"
            }
    
    def parse_identifiers(self, data: str) -> Dict[str, Any]:
        """解析识别词数据"""
        try:
            identifiers = self.extract_identifier(data)
            return {
                "code": 0,
                "message": "解析成功",
                "data": identifiers
            }
        except Exception as e:
            logger.error(f"解析识别词失败: {e}")
            return {
                "code": 1,
                "message": f"解析识别词失败: {str(e)}",
                "data": []
            }