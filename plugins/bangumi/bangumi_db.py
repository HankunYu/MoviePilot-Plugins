from app.db.models.mediaserver import MediaServerItem
from app.db import db_query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db import Engine, DbOper

class BangumiDbOper(DbOper):
    def __init__(self, db: Session = None):
        super().__init__(db)

    @db_query
    def get_media_in_library(self, media_server: list,):
        media_in_library = self._db.query(MediaServerItem).filter(
            MediaServerItem.server.in_(media_server),
            MediaServerItem.item_type.in_(["电影","电视剧"])
        ).all()
        return media_in_library