from fastapi import FastAPI
from .database import Base, engine
from .routers import register, identify

app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(register.router)
app.include_router(identify.router)
