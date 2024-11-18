import cv2
import face_recognition
import os

# 이미 등록된 얼굴 데이터를 저장할 리스트
known_face_encodings = []
known_face_names = []

# 얼굴 등록 함수
def register_face(image_path, name):
    """ 얼굴을 등록합니다. """
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)
    
    if face_encodings:
        face_encoding = face_encodings[0]  # 첫 번째 얼굴만 사용
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)
        print(f"{name} 얼굴이 등록되었습니다.")
    else:
        print("얼굴을 인식할 수 없습니다.")

# 사진 파일에서 얼굴 구별하기
def identify_face(image_path):
    """ 지정된 사진 파일에서 얼굴을 인식하고 등록된 얼굴인지 구별합니다. """
    unknown_image = face_recognition.load_image_file(image_path)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_face_encodings:
        print("사진에서 얼굴을 인식할 수 없습니다.")
        return
    
    for unknown_face_encoding in unknown_face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, unknown_face_encoding)

        best_match_index = face_distances.argmin() if matches else None

        if matches and matches[best_match_index]:
            name = known_face_names[best_match_index]
            print(f"이 사람은 등록된 사람입니다: {name}")
        else:
            print("등록되지 않은 얼굴입니다.")

# 예시 사용법
if __name__ == "__main__":
    # 얼굴 등록
    register_face("image copy.png", "조아름")

    # 등록된 사람인지 확인
    identify_face("image copy.png")
