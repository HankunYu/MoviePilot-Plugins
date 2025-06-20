from typing import List, Tuple, Dict, Any, Optional
import datetime, re, json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Request

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
    plugin_version = "1.0.1"
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
        """Vue mode doesn't use Vuetify page definitions."""
        return None
    
    # --- V2 Vue Interface Method ---
    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """Declare Vue rendering mode and assets path."""
        return "vue", "dist/assets"

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
                "path": "/save_raw_data",
                "endpoint": self.save_raw_data,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存原始文本数据",
                "description": "直接保存原始文本到数据库"
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
                "path": "/parse_identifiers",
                "endpoint": self.parse_identifiers,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "解析识别词数据",
                "description": "解析原始文本为结构化数据"
            },
            {
                "path": "/get_hierarchical_data",
                "endpoint": self.get_hierarchical_data,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取层级结构数据",
                "description": "获取按分类和子分类组织的层级数据"
            },
            {
                "path": "/validate_identifier",
                "endpoint": self.validate_identifier,
                "methods": ["POST"],
                "auth": "bear", 
                "summary": "验证识别词格式",
                "description": "验证识别词的格式是否正确"
            },
            {
                "path": "/auto_categorize",
                "endpoint": self.auto_categorize,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "自动添加分类",
                "description": "为没有分类的识别词自动添加'未分类'标记"
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
            raw_data = self.systemconfig.get(SystemConfigKey.CustomIdentifiers)
            logger.debug(f"从数据库获取的原始数据类型: {type(raw_data)}")
            
            # 增强类型处理，确保 text 是字符串类型
            if raw_data is None:
                text = ""
                logger.debug("原始数据为None，设置为空字符串")
            elif isinstance(raw_data, str):
                text = raw_data
                logger.debug(f"原始数据是字符串，长度: {len(text)}")
            elif isinstance(raw_data, list):
                # 处理列表类型的数据
                text_parts = []
                for item in raw_data:
                    if isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                text = '\n'.join(text_parts) if text_parts else ""
                logger.debug(f"列表转换为字符串，长度: {len(text)}")
            elif isinstance(raw_data, dict):
                # 处理字典类型的数据（可能的JSON格式）
                text = str(raw_data)
                logger.debug(f"字典转换为字符串，长度: {len(text)}")
            else:
                text = str(raw_data)
                logger.debug(f"其他类型({type(raw_data)})转换为字符串，长度: {len(text)}")
        
        # 确保 text 是字符串类型
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        # 初始化结果
        entries = []
        current_tag = '未分类'
        
        # 按行分割文本，增加错误处理
        try:
            lines = text.strip().split('\n') if text else []
        except AttributeError as e:
            logger.error(f"文本分割错误: {e}, text类型: {type(text)}, text内容: {text}")
            return []
    
        # 遍历每一行
        for line_num, line in enumerate(lines, 1):
            try:
                # 确保line是字符串类型
                if not isinstance(line, str):
                    line = str(line) if line is not None else ""
                
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
            except Exception as e:
                logger.error(f"处理第{line_num}行时出错: {e}, line类型: {type(line)}, line内容: {line}")
                continue
        
        logger.info(f"成功提取了 {len(entries)} 条识别词")
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
    
    async def save_raw_data(self, request: Request) -> Dict[str, Any]:
        """保存原始文本数据到数据库"""
        try:
            logger.info(f"save_raw_data被调用")
            
            final_data = None
            
            # 从请求体获取数据
            try:
                body = await request.body()
                if body:
                    logger.info(f"从请求体获取数据，原始长度: {len(body)}")
                    # 尝试解析JSON
                    try:
                        body_text = body.decode('utf-8')
                        logger.info(f"请求体文本: {body_text}")
                        body_data = json.loads(body_text)
                        logger.info(f"解析后的JSON数据: {body_data}")
                        if isinstance(body_data, dict):
                            final_data = body_data.get('data') or body_data.get('content')
                            logger.info(f"从JSON.data获取数据，长度: {len(final_data) if final_data else 0}")
                        else:
                            final_data = str(body_data)
                            logger.info(f"JSON数据转字符串，长度: {len(final_data)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败: {e}")
                        final_data = body.decode('utf-8')
                        logger.info(f"从请求体纯文本获取数据，长度: {len(final_data)}")
                else:
                    logger.warning("请求体为空")
            except Exception as e:
                logger.error(f"读取请求体失败: {e}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
            
            # 从查询参数获取（备选）
            if not final_data:
                query_data = request.query_params.get('data')
                if query_data:
                    final_data = query_data
                    logger.info(f"从查询参数获取数据，长度: {len(final_data)}")
            
            # 验证数据
            if not final_data:
                logger.warning("所有方式都无法获取到数据")
                logger.info(f"查询参数: {dict(request.query_params)}")
                return {
                    "code": 1,
                    "message": "没有接收到任何数据，请检查请求格式"
                }
            
            # 确保final_data是字符串类型
            if not isinstance(final_data, str):
                final_data = str(final_data) if final_data is not None else ""
            
            # 自动添加未分类标记
            final_data = self._auto_add_uncategorized_tag(final_data)
            
            logger.info(f"最终获取的数据长度: {len(final_data)}")
            logger.debug(f"保存的数据前200字符: {final_data[:200]}...")
            
            # 保存到数据库
            try:
                result = self.systemconfig.set(SystemConfigKey.CustomIdentifiers, final_data)
                logger.info(f"数据库保存操作结果: {result}")
                
                # 验证保存是否成功
                saved_data = self.systemconfig.get(SystemConfigKey.CustomIdentifiers)
                if saved_data == final_data:
                    logger.info(f"数据保存验证成功，共{len(final_data)}个字符")
                    return {
                        "code": 0,
                        "message": f"数据保存成功，共{len(final_data)}个字符"
                    }
                else:
                    logger.error(f"数据保存验证失败，期望长度: {len(final_data)}, 实际长度: {len(str(saved_data)) if saved_data else 0}")
                    return {
                        "code": 1,
                        "message": "数据保存验证失败"
                    }
                    
            except Exception as e:
                logger.error(f"数据库保存失败: {e}")
                import traceback
                logger.error(f"数据库保存错误详情: {traceback.format_exc()}")
                return {
                    "code": 1,
                    "message": f"数据库保存失败: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"保存原始数据失败: {e}")
            import traceback
            logger.error(f"总体错误详情: {traceback.format_exc()}")
            return {
                "code": 1,
                "message": f"保存数据失败: {str(e)}"
            }
    
    def get_raw_identifiers(self) -> Dict[str, Any]:
        """获取原始识别词数据"""
        try:
            raw_data = self.systemconfig.get(SystemConfigKey.CustomIdentifiers) or ""
            # 确保返回字符串类型
            if isinstance(raw_data, list):
                data = '\n'.join(raw_data) if raw_data else ""
            else:
                data = str(raw_data) if raw_data else ""
            
            return {
                "code": 0,
                "message": "success",
                "data": data
            }
        except Exception as e:
            logger.error(f"获取原始识别词失败: {e}")
            return {
                "code": 1,
                "message": f"获取原始识别词失败: {str(e)}",
                "data": ""
            }
    
    async def parse_identifiers(self, request: Request) -> Dict[str, Any]:
        """解析识别词数据"""
        try:
            logger.info(f"parse_identifiers被调用")
            
            final_data = None
            
            # 从请求体获取
            try:
                body = await request.body()
                if body:
                    logger.info(f"从请求体获取数据，长度: {len(body)}")
                    # 尝试解析JSON
                    try:
                        body_text = body.decode('utf-8')
                        body_data = json.loads(body_text)
                        if isinstance(body_data, dict):
                            final_data = body_data.get('data') or body_data.get('content')
                        else:
                            final_data = str(body_data)
                        logger.info(f"从请求体JSON解析获取数据，长度: {len(final_data) if final_data else 0}")
                    except json.JSONDecodeError:
                        final_data = body.decode('utf-8')
                        logger.info(f"从请求体纯文本获取数据，长度: {len(final_data)}")
            except Exception as e:
                logger.error(f"读取请求体失败: {e}")
            
            logger.info(f"parse_identifiers最终数据长度: {len(final_data) if final_data else 0}")
            
            # 确保final_data是字符串类型
            if not isinstance(final_data, str):
                final_data = str(final_data) if final_data is not None else ""
            
            # 自动添加未分类标记
            final_data = self._auto_add_uncategorized_tag(final_data)
            
            identifiers = self.extract_identifier(final_data)
            return {
                "code": 0,
                "message": f"解析成功，共解析出 {len(identifiers)} 条识别词",
                "data": identifiers
            }
        except Exception as e:
            logger.error(f"解析识别词失败: {e}")
            return {
                "code": 1,
                "message": f"解析识别词失败: {str(e)}",
                "data": []
            }
    
    def get_hierarchical_data(self) -> Dict[str, Any]:
        """获取层级结构数据"""
        try:
            identifiers = self.extract_identifier()
            hierarchical_data = self._build_hierarchical_structure(identifiers)
            return {
                "code": 0,
                "message": "success",
                "data": hierarchical_data
            }
        except Exception as e:
            logger.error(f"获取层级数据失败: {e}")
            return {
                "code": 1,
                "message": f"获取层级数据失败: {str(e)}",
                "data": []
            }
    
    async def validate_identifier(self, request: Request) -> Dict[str, Any]:
        """验证识别词格式"""
        try:
            logger.info(f"validate_identifier被调用")
            
            final_type = None
            final_content = None
            
            # 从请求体获取
            try:
                body = await request.body()
                if body:
                    try:
                        body_text = body.decode('utf-8')
                        body_data = json.loads(body_text)
                        if isinstance(body_data, dict):
                            final_type = body_data.get('identifier_type') or body_data.get('type')
                            final_content = body_data.get('content') or body_data.get('data')
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logger.error(f"读取请求体失败: {e}")
            
            logger.info(f"validate_identifier - 类型: {final_type}, 内容长度: {len(final_content) if final_content else 0}")
            
            if not final_content:
                return {
                    "code": 1,
                    "message": "没有接收到内容数据",
                    "data": {"valid": False, "errors": ["没有接收到内容数据"]}
                }
            
            # 验证不同类型的格式
            validation_result = self._validate_identifier_format(final_type, final_content)
            
            return {
                "code": 0,
                "message": "验证完成",
                "data": validation_result
            }
        except Exception as e:
            logger.error(f"验证识别词失败: {e}")
            return {
                "code": 1,
                "message": f"验证识别词失败: {str(e)}",
                "data": {"valid": False, "errors": [str(e)]}
            }
    
    def _build_hierarchical_structure(self, identifiers: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """构建层级结构数据"""
        categories = {}
        
        for item in identifiers:
            # 解析标签层级
            parts = item['tag'].split('/')
            category_name = parts[0] if parts else '未分类'
            sub_category_name = parts[1] if len(parts) > 1 else None
            
            # 创建或获取主分类
            if category_name not in categories:
                categories[category_name] = {
                    'id': category_name,
                    'name': category_name,
                    'identifiers': [],
                    'subCategories': [],
                    'expanded': True
                }
            
            category = categories[category_name]
            
            if sub_category_name:
                # 查找或创建子分类
                sub_category = None
                for sub in category['subCategories']:
                    if sub['name'] == sub_category_name:
                        sub_category = sub
                        break
                
                if not sub_category:
                    sub_category = {
                        'id': f"{category_name}/{sub_category_name}",
                        'name': sub_category_name,
                        'identifiers': [],
                        'expanded': True
                    }
                    category['subCategories'].append(sub_category)
                
                sub_category['identifiers'].append(item)
            else:
                # 直接添加到主分类
                category['identifiers'].append(item)
        
        return list(categories.values())
    
    def _validate_identifier_format(self, identifier_type: str, content: str) -> Dict[str, Any]:
        """验证识别词格式"""
        errors = []
        suggestions = []
        
        if not content.strip():
            errors.append("内容不能为空")
            return {"valid": False, "errors": errors, "suggestions": suggestions}
        
        if identifier_type == '屏蔽':
            # 屏蔽词验证 - 简单验证非空即可
            if len(content.strip()) < 1:
                errors.append("屏蔽词长度至少为1个字符")
        
        elif identifier_type == '替换':
            # 替换词验证 - 必须包含 =>
            if ' => ' not in content:
                errors.append("替换词必须包含 ' => ' 分隔符")
                suggestions.append("格式应为：原词 => 替换词")
            else:
                parts = content.split(' => ')
                if len(parts) != 2:
                    errors.append("替换词格式错误，只能包含一个 ' => ' 分隔符")
                elif not parts[0].strip() or not parts[1].strip():
                    errors.append("原词和替换词都不能为空")
        
        elif identifier_type == '集偏移':
            # 集偏移验证 - 必须包含 <> 和 >>
            if ' <> ' not in content or ' >> ' not in content:
                errors.append("集偏移必须包含 ' <> ' 和 ' >> ' 分隔符")
                suggestions.append("格式应为：前定位词 <> 后定位词 >> 偏移量")
            else:
                # 验证格式
                pattern = r'^(.+?)\s*<>\s*(.+?)\s*>>\s*(.+)$'
                if not re.match(pattern, content):
                    errors.append("集偏移格式错误")
                else:
                    match = re.match(pattern, content)
                    front, back, offset = match.groups()
                    if not front.strip() or not back.strip() or not offset.strip():
                        errors.append("前定位词、后定位词和偏移量都不能为空")
        
        elif identifier_type == '替换和集偏移':
            # 复合类型验证
            if ' => ' not in content or ' && ' not in content or ' <> ' not in content or ' >> ' not in content:
                errors.append("替换和集偏移必须包含所有分隔符：' => '、' && '、' <> '、' >> '")
                suggestions.append("格式应为：原词 => 替换词 && 前定位词 <> 后定位词 >> 偏移量")
            else:
                pattern = r'^(.+?)\s*=>\s*(.+?)\s*&&\s*(.+?)\s*<>\s*(.+?)\s*>>\s*(.+)$'
                if not re.match(pattern, content):
                    errors.append("替换和集偏移格式错误")
                else:
                    match = re.match(pattern, content)
                    original, replacement, front, back, offset = match.groups()
                    if not all(part.strip() for part in [original, replacement, front, back, offset]):
                        errors.append("所有字段都不能为空")
        
        else:
            errors.append(f"未知的识别词类型: {identifier_type}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "suggestions": suggestions
        }

    def _auto_add_uncategorized_tag(self, text: str) -> str:
        """自动添加未分类标记"""
        if not text or not text.strip():
            return text
        
        lines = text.strip().split('\n')
        has_category = False
        has_content = False
        content_lines = 0
        
        # 检查是否已经有分类标记和是否有实际内容
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否有分类标记（以#开头的行）
            if re.match(r'^#\s*(.+)$', line):
                has_category = True
            else:
                # 检查是否有实际的识别词内容
                entry_type = self._determine_entry_type(line)
                if entry_type:
                    has_content = True
                    content_lines += 1
        
        # 如果有内容但没有分类，则添加"未分类"标记
        if has_content and not has_category:
            logger.info(f"检测到{content_lines}条没有分类的识别词，自动添加'未分类'标记")
            return f"# 未分类\n{text}"
        elif has_content and has_category:
            logger.info(f"检测到{content_lines}条已分类的识别词，无需添加分类标记")
        elif not has_content:
            logger.info("未检测到有效的识别词内容")
        
        return text

    async def auto_categorize(self, request: Request) -> Dict[str, Any]:
        """自动为识别词添加分类"""
        try:
            logger.info(f"auto_categorize被调用")
            
            final_data = None
            
            # 从请求体获取数据
            try:
                body = await request.body()
                if body:
                    try:
                        body_text = body.decode('utf-8')
                        body_data = json.loads(body_text)
                        if isinstance(body_data, dict):
                            final_data = body_data.get('data') or body_data.get('content')
                        else:
                            final_data = str(body_data)
                    except json.JSONDecodeError:
                        final_data = body.decode('utf-8')
            except Exception as e:
                logger.error(f"读取请求体失败: {e}")
                return {
                    "code": 1,
                    "message": f"读取请求数据失败: {str(e)}",
                    "data": ""
                }
            
            if not final_data:
                return {
                    "code": 1,
                    "message": "没有接收到数据",
                    "data": ""
                }
            
            # 确保是字符串类型
            if not isinstance(final_data, str):
                final_data = str(final_data) if final_data is not None else ""
            
            # 应用自动分类
            categorized_data = self._auto_add_uncategorized_tag(final_data)
            
            # 检查是否有变化
            has_changes = categorized_data != final_data
            
            return {
                "code": 0,
                "message": "自动分类处理完成" + ("，已添加未分类标记" if has_changes else "，无需修改"),
                "data": categorized_data,
                "changed": has_changes
            }
            
        except Exception as e:
            logger.error(f"自动分类失败: {e}")
            return {
                "code": 1,
                "message": f"自动分类失败: {str(e)}",
                "data": ""
            }