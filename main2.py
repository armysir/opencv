from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session
from io import BytesIO
import face_recognition
import os
from database import get_db, Visitor,Guestbook  # database.py에서 필요한 내용 가져오기
import logging
from fastapi import Form
from firebase_admin import credentials, messaging
from fastapi.responses import StreamingResponse
import asyncio
import cv2
import numpy as np
import base64
from fastapi.responses import JSONResponse
from firebase_admin import credentials, messaging, initialize_app
# Firebase Admin SDK 초기화
cred = credentials.Certificate("auth.json")  # Firebase 서비스 계정 키 경로
initialize_app(cred)

stream_queue = asyncio.Queue()



logger = logging.getLogger(__name__)
app = FastAPI()

# 스트리밍할 이미지를 실시간으로 받아서 클라이언트로 전송
async def generate_stream():
    while True:
        # 스트림 큐에서 이미지를 가져옴
        img = await stream_queue.get()
        if img is None:
            break  # 종료 조건
        nparr = np.frombuffer(img, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            continue

        # 프레임을 JPEG 형식으로 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # 실시간으로 클라이언트에 전송
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')




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


@app.post("/upload")
async def upload_frame(file: UploadFile = File(...)):
    # 업로드된 이미지를 읽어서 스트림 큐에 추가
    frame_data = await file.read()
    await stream_queue.put(frame_data)  # 큐에 프레임 추가
    return {"message": "Frame uploaded"}


@app.get("/stream")
async def stream_video():
    # 스트리밍 응답 생성
    return StreamingResponse(generate_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/list")
async def database_list(db: Session = Depends(get_db)):
    guestbook_entries = db.query(Guestbook).all()
    results = [
        {
            "id": entry.id,
            "visitor_name": entry.visitor_name,
            "photo": base64.b64encode(entry.photo).decode("utf-8") if entry.photo else None,
            "visit_date": entry.visit_date.isoformat() if entry.visit_date else None,
        }
        for entry in guestbook_entries
    ]
    return JSONResponse(content={"guestbook_entries": results})
     

    
@app.post("/register-face")
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

@app.post("/identify-face")
async def identify_face_api(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    unknown_image = face_recognition.load_image_file(temp_file_path)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)
    
    if not unknown_face_encodings:
        with open(temp_file_path, "rb") as img_file:
            photo = img_file.read()
        new_guest = Guestbook(visitor_name="알 수 없는 방문자", photo=photo)
        db.add(new_guest)
        db.commit()
        db.refresh(new_guest)
        os.remove(temp_file_path)

        # 푸시 알림 전송
        send_push_notification("알 수 없는 방문자", "새로운 방문자가 확인되었습니다.")

        print("등록되지 않은 사람")
        return {"message": "사진에서 얼굴을 인식할 수 없습니다."}

    for unknown_face_encoding in unknown_face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, unknown_face_encoding)

        if any(matches):  # 매칭된 얼굴이 있으면
            best_match_index = face_distances.argmin()  # 가장 가까운 매칭을 찾음
            if matches[best_match_index]:  # 매칭된 얼굴이 존재하면
                name = known_face_names[best_match_index]

                # 방명록에 기록
                with open(temp_file_path, "rb") as img_file:
                    photo = img_file.read()

                new_guest = Guestbook(visitor_name=name, photo=photo)
                db.add(new_guest)
                db.commit()
                db.refresh(new_guest)

                # 푸시 알림 전송
                send_push_notification(name, f"{name}님이 방문하셨습니다.")

                os.remove(temp_file_path)
                print("등록된 사람")
                return {"message": f"이 사람은 등록된 사람입니다: {name}"}
    
    with open(temp_file_path, "rb") as img_file:
        photo = img_file.read()
    new_guest = Guestbook(visitor_name="알 수 없는 방문자", photo=photo)
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)

    # 푸시 알림 전송
    send_push_notification("알 수 없는 방문자", "새로운 방문자가 확인되었습니다.")

    os.remove(temp_file_path)
    print("등록되지 않은 사람")
    return {"message": "등록되지 않은 얼굴입니다."}

# Firebase 푸시 알림 함수
def send_push_notification(title: str, body: str):
    """푸시 알림을 보내는 함수"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic="general",  # 알림을 보낼 대상 토픽
        )
        response = messaging.send(message)
        print(f"푸시 알림 전송 성공: {response}")
    except Exception as e:
        logger.error(f"푸시 알림 전송 실패: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)