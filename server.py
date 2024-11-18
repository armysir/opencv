from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import face_recognition
import numpy as np
import json

# MySQL 데이터베이스 설정 (pymysql을 사용해 MySQL에 연결)
DATABASE_URL = "mysql+pymysql://root:0908@localhost:3306/test"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# 등록된 얼굴 데이터를 저장할 리스트
known_face_encodings = []
known_face_names = []



# 얼굴 등록 API
@app.post("/register-face/")
async def register_face(file: UploadFile = File(...), name: str = Form("Unknown")):
    image = face_recognition.load_image_file(file.file)
    face_encodings = face_recognition.face_encodings(image)
    
    if face_encodings:
        face_encoding = face_encodings[0]  # 첫 번째 얼굴만 사용
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)
        return JSONResponse(content={"message": f"{name} 얼굴이 등록되었습니다."})
    else:
        return JSONResponse(content={"message": "얼굴을 인식할 수 없습니다."}, status_code=400)

# 얼굴 인식 API
@app.post("/identify-face/")
async def identify_face(file: UploadFile = File(...)):
    unknown_image = face_recognition.load_image_file(file.file)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_face_encodings:
        return JSONResponse(content={"message": "사진에서 얼굴을 인식할 수 없습니다."}, status_code=400)
    
    response_data = {"recognized_faces": []}
    for unknown_face_encoding in unknown_face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, unknown_face_encoding)
        
        best_match_index = np.argmin(face_distances) if matches else None
        
        if matches and matches[best_match_index]:
            name = known_face_names[best_match_index]
            response_data["recognized_faces"].append(name)
            print(response_data)
        else:
            response_data["recognized_faces"].append("등록되지 않은 얼굴")
            print(response_data)

    
    return JSONResponse(content=response_data)

# 서버 실행: `uvicorn server:app --reload`
