try:
    import face_recognition
    import numpy as np
    import io
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False
    print("WARNING: 'face_recognition' library not found. Running in AI LITE mode (Face Detection Only).")
    import cv2
    import numpy as np
    import io

def validate_face(image_bytes: bytes, known_face_encoding_bytes: bytes) -> bool:
    """
    Validates if the face in the image matches the known face encoding.
    """
    if HAS_FACE_RECOGNITION:
        try:
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            face_encodings = face_recognition.face_encodings(image)
            
            if not face_encodings:
                print("No face found in the uploaded image.")
                return False

            unknown_face_encoding = face_encodings[0]
            known_face_encoding = np.frombuffer(known_face_encoding_bytes, dtype=np.float64)

            results = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding)
            
            if not results:
                return False
                
            return results[0]
        except Exception as e:
            print(f"Error in face validation: {e}")
            return False
    else:
        # Fallback: Use OpenCV just to detect IF there is a face, 
        # but skip strict comparison (mock validation as True if face exists)
        return _detect_face_opencv(image_bytes)

def get_face_encoding(image_bytes: bytes) -> bytes:
    """
    Generates face encoding bytes from an image.
    """
    if HAS_FACE_RECOGNITION:
        try:
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            face_encodings = face_recognition.face_encodings(image)
            
            if not face_encodings:
                return None
                
            return face_encodings[0].tobytes()
        except Exception as e:
            print(f"Error generating encoding: {e}")
            return None
    else:
        # Fallback: Return a dummy byte string if face detected
        if _detect_face_opencv(image_bytes):
            return b"dummy_encoding_opencv_lite"
        return None

def _detect_face_opencv(image_bytes: bytes) -> bool:
    """
    Simple face detection using OpenCV Haarcascades as fallback.
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load Haarcascade (included in opencv-python)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            print(f"AI LITE: Detected {len(faces)} face(s). Verification bypassed (Success).")
            return True
        else:
            print("AI LITE: No face detected.")
            return False
    except Exception as e:
        print(f"Error in OpenCV fallback: {e}")
        return False
