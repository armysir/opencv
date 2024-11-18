from sqlalchemy.orm import Session
import models

# 방문자 생성 (DB에 저장)
def create_visitor(db: Session, name: str, photo: bytes):
    db_visitor = models.Visitor(name=name, photo=photo)
    db.add(db_visitor)
    db.commit()
    db.refresh(db_visitor)
    return db_visitor

# 모든 방문자 가져오기
def get_visitors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Visitor).offset(skip).limit(limit).all()