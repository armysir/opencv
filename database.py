from sqlalchemy import create_engine, Column, Integer, String, DateTime, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "mysql+pymysql://root:0908@localhost:3306/iot"
# SQLAlchemy Base
Base = declarative_base()

# MySQL 연결 엔진
engine = create_engine(DATABASE_URL)

# 세션 만들기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 방문자 모델 정의
class Visitor(Base):
    __tablename__ = 'visitors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    photo = Column(BLOB)  # 사진을 BLOB 형식으로 저장
    visit_date = Column(DateTime, default=datetime.utcnow)  # 방문 날짜
    
# 데이터베이스 생성
Base.metadata.create_all(bind=engine)

# 세션을 가져오는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()