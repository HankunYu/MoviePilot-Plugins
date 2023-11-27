import json
from typing import Optional

from sqlalchemy.orm import Session

from app.db import DbOper
from plugins.bangumi.bangumi_db import BangumiInfo


class BangumiOper(DbOper):
    """
    媒体服务器数据管理
    """

    def __init__(self, db: Session = None):
        super().__init__(db)

    def add(self, **kwargs) -> bool:
        """
        新增媒体服务器数据
        """
        item = BangumiInfo(**kwargs)
        if not item.get_by_title(self._db, kwargs.get("title")):
            item.create(self._db)
            return True
        return False

    def empty(self):
        """
        清空 Bangumi 数据
        """
        BangumiInfo.empty(self._db)

    def exists(self, **kwargs) -> Optional[BangumiInfo]:
        """
        判断媒体服务器数据是否存在
        """
        if kwargs.get("title"):
            item = BangumiInfo.exists_by_title(self._db, title=kwargs.get("title"))
        else:
            return None
        if not item:
            return None
        return item

    def get_subject_id(self, **kwargs) -> Optional[str]:
        """
        获取 Bangumi ID
        """
        item = self.exists(**kwargs)
        if not item:
            return None
        return str(item.subject_id)
    
    def get_amount(self) -> int:
        """
        获取 Bangumi 数据量
        """
        return BangumiInfo.get_amount(self._db)
    
    def get_all(self) -> list:
        """
        获取所有 Bangumi 数据
        """
        return BangumiInfo.get_all(self._db)
    
    def update_info(self, **kwargs) -> bool:
        """
        更新 Bangumi 数据
        """
        item = self.exists(title = kwargs.get("title"))
        if not item:
            return False
        item.update_info(self._db, **kwargs)
        return True

    def get_original_title(self, **kwargs) -> Optional[str]:
        """
        获取原标题
        """
        item = self.exists(**kwargs)
        if not item:
            return None
        return str(item.original_title)