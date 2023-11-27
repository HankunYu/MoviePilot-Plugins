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
            # 优先按名称查
            item = BangumiInfo.exists_by_title(self._db, tmdbid=kwargs.get("title"))
        else:
            return None
        if not item:
            return None
        return item

    def get_item_id(self, **kwargs) -> Optional[str]:
        """
        获取 Bangumi ID
        """
        item = self.exists(**kwargs)
        if not item:
            return None
        return str(item.subject_id)
