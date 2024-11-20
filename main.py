from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session
from io import BytesIO
import face_recognition
import os
from database import get_db, Visitor  # database.py에서 필요한 내용 가져오기
import logging
from fastapi import Form


logger = logging.getLogger(__name__)
app = FastAPI()

# 메모리에서 사용할 전역 변수
known_face_encodings = []
known_face_names = []

# 얼굴 데이터를 로드하는 함수
def load_known_faces(db: Session):
    """데이터베이스에서 저장된 얼굴 데이터를 로드합니다."""
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []
    
    
    visitors = db.query(Visitor).all()
    for visitor in visitors:
        if visitor.photo:
            face_image = face_recognition.load_image_file(BytesIO(visitor.photo))
            face_encodings = face_recognition.face_encodings(face_image)
            if face_encodings:
                known_face_encodings.append(face_encodings[0])
                known_face_names.append(visitor.name)
                print(known_face_encodings)
                print(known_face_names)

# 애플리케이션 시작 시 얼굴 데이터 로드
@app.on_event("startup")
def startup_event():
    print("on_event Starting----------")
    db = next(get_db())
    load_known_faces(db)
@app.post("/register-face/")
async def register_face_api(file: UploadFile = File(...), name: str = Form("Unknown"), db: Session = Depends(get_db)):
    print(f"Received name: {name}")  # 디버깅을 위한 출력
    print(f"Received file: {file.filename}")
    
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    image = face_recognition.load_image_file(temp_file_path)
    face_encodings = face_recognition.face_encodings(image)

    if face_encodings:
        face_encoding = face_encodings[0]
        with open(temp_file_path, "rb") as img_file:
            photo = img_file.read()

        new_visitor = Visitor(name=name, photo=photo)
        db.add(new_visitor)
        db.commit()
        db.refresh(new_visitor)

        # 메모리 데이터 업데이트
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)

        os.remove(temp_file_path)
        return {"message": f"{name} 얼굴이 등록되었습니다."}
    else:
        os.remove(temp_file_path)
        return {"message": "얼굴을 인식할 수 없습니다."}

@app.post("/identify-face/")
async def identify_face_api(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    unknown_image = face_recognition.load_image_file(temp_file_path)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_face_encodings:
        os.remove(temp_file_path)
        return {"message": "사진에서 얼굴을 인식할 수 없습니다."}

    for unknown_face_encoding in unknown_face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, unknown_face_encoding)

        if any(matches):  # 매칭된 얼굴이 있으면
            best_match_index = face_distances.argmin()  # 가장 가까운 매칭을 찾음
            if matches[best_match_index]:  # 매칭된 얼굴이 존재하면
                name = known_face_names[best_match_index]
                os.remove(temp_file_path)
                return { f"{name}님이 방문하였습니다."}
            
    os.remove(temp_file_path)
    return {"외부인이 방문하였습니다."}