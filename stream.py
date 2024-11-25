from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import asyncio
import cv2
import numpy as np

app = FastAPI()

# 스트리밍 생성기를 위한 글로벌 변수
stream_queue = asyncio.Queue()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)