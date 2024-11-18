from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from .. import crud, database
import face_recognition
import numpy as np
import json

router = APIRouter()

@router.post("/identify-face/")
async def identify_face(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    unknown_image = face_recognition.load_image_file(file.file)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_face_encodings:
        return {"message": "사진에서 얼굴을 인식할 수 없습니다."}
    
    response_data = {"recognized_faces": []}
    for unknown_face_encoding in unknown_face_encodings:
        all_faces = crud.get_all_faces(db)
        for face_data in all_faces:
            known_encoding = np.array(json.loads(face_data.encoding))
            matches = face_recognition.compare_faces([known_encoding], unknown_face_encoding)
            face_distance = face_recognition.face_distance([known_encoding], unknown_face_encoding)[0]
            
            if matches[0]:
                response_data["recognized_faces"].append(face_data.name)
                break
        else:
            response_data["recognized_faces"].append("등록되지 않은 얼굴")

    return response_data
