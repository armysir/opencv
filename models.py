from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

from sqlalchemy import Column, Integer, String, BLOB, DateTime

class Visitor(Base):
    __tablename__ = 'visitors'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    photo = Column(BLOB)  # BLOB 또는 LONGBLOB로 설정
    visit_date = Column(DateTime)

    def __repr__(self):
        return f"<Visitor(name={self.name}, visit_time={self.visit_time})>"