from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Visitor(Base):
    __tablename__ = 'visitors'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    photo_path = Column(String)  # 사진 파일 경로
    visit_time = Column(DateTime, default=datetime.utcnow)  # 방문 시간

    def __repr__(self):
        return f"<Visitor(name={self.name}, visit_time={self.visit_time})>"