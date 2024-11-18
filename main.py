from fastapi import FastAPI
from .database import Base, engine
from .routers import register, identify

app = FastAPI()

# �����ͺ��̽� ���̺� ����
Base.metadata.create_all(bind=engine)

# ����� ���
app.include_router(register.router)
app.include_router(identify.router)
