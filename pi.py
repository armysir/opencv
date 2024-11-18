import requests

# 서버 URL 설정
register_url = "http://localhost:8000/register-face/"
identify_url = "http://localhost:8000/identify-face/"

# 얼굴 등록 함수
def register_face(image_path, name):
    with open(image_path, "rb") as image_file:
        files = {"file": image_file}
        data = {"name": name}
        response = requests.post(register_url, files=files, data=data)
        print(response.json())

# 얼굴 인식 함수
def identify_face(image_path):
    with open(image_path, "rb") as image_file:
        files = {"file": image_file}
        response = requests.post(identify_url, files=files)
        print(response.json())

# 예시 사용법
register_face("image/image.png", "조아름")  # 얼굴 등록
identify_face("image/image.png")        # 얼굴 인식
