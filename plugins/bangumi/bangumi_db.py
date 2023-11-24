from app.db.models.mediaserver import MediaServerItem
from app.db import db_query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db import Engine, DbOper
from app.db.mediaserver_oper import MediaServerOper

class BangumiDbOper():
    db_oper = MediaServerOper()
    db = db_oper._db

    @db_query
    def get_media_in_library(self, media_server: list):
        media_in_library = self.db.query(MediaServerItem).filter(
            MediaServerItem.server.in_(media_server)
        ).all()
        return media_in_library