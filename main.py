from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import face_recognition
import os
from io import BytesIO
import crud, database

app = FastAPI()

# 얼굴 등록 함수
def register_face(image_path: str, name: str, db: Session):
    """ 얼굴을 등록하고 DB에 저장합니다. """
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)
    
    if face_encodings:
        face_encoding = face_encodings[0]  # 첫 번째 얼굴만 사용
        # 얼굴을 BLOB으로 저장하기 위해 BytesIO 사용
        with open(image_path, "rb") as img_file:
            photo = img_file.read()
        
        # DB에 방문자 정보 저장
        crud.create_visitor(db, name, photo)
        print(f"{name} 얼굴이 등록되었습니다.")
    else:
        print("얼굴을 인식할 수 없습니다.")

# 얼굴 식별 함수
def identify_face(image_path: str, db: Session):
    """ 지정된 사진 파일에서 얼굴을 인식하고 DB에 저장된 얼굴을 구별합니다. """
    unknown_image = face_recognition.load_image_file(image_path)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_face_encodings:
        return "사진에서 얼굴을 인식할 수 없습니다."
    
    for unknown_face_encoding in unknown_face_encodings:
        matches = face_recognition.compare_faces(database.known_face_encodings, unknown_face_encoding)
        face_distances = face_recognition.face_distance(database.known_face_encodings, unknown_face_encoding)

        best_match_index = face_distances.argmin() if matches else None

        if matches and matches[best_match_index]:
            name = database.known_face_names[best_match_index]
            return f"이 사람은 등록된 사람입니다: {name}"
        else:
            return "등록되지 않은 얼굴입니다."

# 얼굴 등록 API 엔드포인트
@app.post("/register-face/")
async def register_face_api(file: UploadFile = File(...), name: str = "Unknown", db: Session = Depends(database.get_db)):
    # 업로드된 파일을 임시로 저장
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # 얼굴 등록 및 DB에 저장
    register_face(temp_file_path, name, db)

    # 임시 파일 삭제
    os.remove(temp_file_path)

    return {"message": f"{name} 얼굴이 등록되었습니다."}

# 얼굴 식별 API 엔드포인트
@app.post("/identify-face/")
async def identify_face_api(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    # 업로드된 파일을 임시로 저장
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # 얼굴 식별
    result = identify_face(temp_file_path, db)

    # 임시 파일 삭제
    os.remove(temp_file_path)

    return {"message": result}