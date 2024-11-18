from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from .. import crud, database
import face_recognition

router = APIRouter()

@router.post("/register-face/")
async def register_face(file: UploadFile = File(...), name: str = Form("Unknown"), db: Session = Depends(database.get_db)):
    image = face_recognition.load_image_file(file.file)
    face_encodings = face_recognition.face_encodings(image)

    if face_encodings:
        face_encoding = face_encodings[0].tolist()  # 리스트로 변환 후 저장
        crud.create_face_data(db, name, face_encoding)
        return {"message": f"{name} 얼굴이 등록되었습니다."}
    else:
        return {"message": "얼굴을 인식할 수 없습니다."}
