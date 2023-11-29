from datetime import datetime

from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import Session

from app.db import db_query
from app.db.models import Base, db_update


class BangumiInfo(Base):
    plugin_version = "1.0.7"
    """
    Bangumi 数据表
    """
    id = Column(Integer, Sequence('id'), primary_key=True, index=True)
    # 标题
    title = Column(String, index=True)
    # 原标题
    original_title = Column(String)
    # bangumi 项目 ID
    subject_id = Column(String, index=True)
    # 评分
    rating = Column(String)
    # 收藏状态 1:想看 2:看过 3:在看 4:搁置 5:抛弃
    status = Column(String, index=True)
    # 是否同步过
    synced = Column(String, index=True)
    # poster
    poster = Column(String)

    @staticmethod
    @db_query
    def get_by_title(db: Session, title: str):
        return db.query(BangumiInfo).filter(BangumiInfo.title == title).first()

    @staticmethod
    @db_update
    def empty(db: Session):
        db.query(BangumiInfo).delete()

    @staticmethod
    @db_query
    def exists_by_title(db: Session, title: str):
        return db.query(BangumiInfo).filter(BangumiInfo.title == title).first()

    @staticmethod
    @db_query
    def get_amount(db: Session):
        return db.query(BangumiInfo).count()
    
    @staticmethod
    @db_query
    def get_all(db: Session):
        return db.query(BangumiInfo).all()
    
    @staticmethod
    @db_query
    def get_all_bangumi(db: Session):
        return db.query(BangumiInfo).filter(BangumiInfo.subject_id != None).all()
    
    @staticmethod
    @db_update
    def update_info(db: Session, title: str, original_title: str ,subject_id: str, rating: str, status: str, synced: bool, poster: str):
        db.query(BangumiInfo).filter(BangumiInfo.title == title).update({
            "original_title": original_title,
            "subject_id": subject_id,
            "rating": rating,
            "status": status,
            "synced": synced,
            "poster": poster,
        })
        
    @staticmethod
    @db_query
    def get_wish(db: Session):
        return db.query(BangumiInfo).filter(BangumiInfo.status == 1).all()
    
    @staticmethod
    @db_query
    def get_watched(db: Session):
        return db.query(BangumiInfo).filter(BangumiInfo.status == 2).all()
    
    @staticmethod
    @db_query
    def get_watching(db: Session):
        return db.query(BangumiInfo).filter(BangumiInfo.status == 3).all()
    
    @staticmethod
    @db_query
    def get_dropped(db: Session):
        return db.query(BangumiInfo).filter(BangumiInfo.status == 4).all()
    
    @staticmethod
    @db_query
    def exists_by_subject_id(db: Session, subject_id: str):
        return db.query(BangumiInfo).filter(BangumiInfo.subject_id == subject_id).first()