from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from app.utils.ai_service import validate_face
from datetime import datetime
import os
import shutil
import uuid

router = APIRouter(prefix="/attendance", tags=["attendance"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Attendance)
async def submit_attendance(
    nim: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Find Student
    student = db.query(models.Student).filter(models.Student.nim == nim).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 2. Check for duplicate attendance today
    today = datetime.now().strftime("%Y-%m-%d")
    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.student_id == student.id,
        models.Attendance.date == today
    ).first()

    if existing_attendance:
        raise HTTPException(status_code=400, detail="Student already attended today")

    # 3. Validate Face (AI)
    content = await file.read()
    if student.face_encoding:
        is_match = validate_face(content, student.face_encoding)
        if not is_match:
             raise HTTPException(status_code=400, detail="Face mismatch! Attendance rejected.")
    else:
        # Fallback if no encoding (shouldn't happen if registered correctly)
        raise HTTPException(status_code=400, detail="Student has no registered face data")

    # 4. Save Image (Evidence)
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    image_dir = "assets/attendance_images"
    os.makedirs(image_dir, exist_ok=True)
    file_path = os.path.join(image_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(content)

    # 5. Record Attendance
    new_attendance = models.Attendance(
        student_id=student.id,
        date=today,
        timestamp=datetime.now(),
        status="Hadir",
        image_path=file_path
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return new_attendance

@router.get("/", response_model=list[schemas.Attendance])
def read_attendance(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Attendance).offset(skip).limit(limit).all()
