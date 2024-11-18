from sqlalchemy.orm import Session
from . import models, schemas
import json

def create_face_data(db: Session, name: str, encoding: list):
    encoding_json = json.dumps(encoding)  # JSON 형식으로 변환
    face_data = models.FaceData(name=name, encoding=encoding_json)
    db.add(face_data)
    db.commit()
    db.refresh(face_data)
    return face_data

def get_all_faces(db: Session):
    return db.query(models.FaceData).all()
