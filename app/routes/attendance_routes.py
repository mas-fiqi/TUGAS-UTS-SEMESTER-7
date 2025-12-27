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

@router.post("/", response_model=schemas.AttendanceResponse)
async def submit_attendance(
    nim: str = Form(...),
    class_id: int = Form(...), # Ditambahkan sesuai request: Identitas Kelas
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Cari Data Siswa (Identitas Siswa)
    student = db.query(models.Student).filter(models.Student.nim == nim).first()
    if not student:
        # Mengembalikan respon GAGAL yang rapi
        return {"status": "gagal", "message": "Siswa tidak ditemukan", "data": None}

    # 2. Validasi Kelas (Memastikan siswa mengirim identitas kelas yang benar)
    if student.class_id != class_id:
        return {"status": "gagal", "message": "Siswa tidak terdaftar di kelas ini", "data": None}

    # 3. Cek Absen Ganda (Anti-Double)
    today = datetime.now().strftime("%Y-%m-%d")
    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.student_id == student.id,
        models.Attendance.date == today
    ).first()

    if existing_attendance:
        return {"status": "gagal", "message": "Siswa sudah melakukan absensi hari ini", "data": None}

    # 4. Validasi Wajah dengan AI
    content = await file.read()
    if student.face_encoding:
        is_match = validate_face(content, student.face_encoding)
        if not is_match:
             return {"status": "gagal", "message": "Wajah tidak cocok! Absensi ditolak.", "data": None}
    else:
        return {"status": "gagal", "message": "Data wajah siswa belum terdaftar", "data": None}

    # 5. Simpan Bukti Foto
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    image_dir = "assets/attendance_images"
    os.makedirs(image_dir, exist_ok=True)
    file_path = os.path.join(image_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(content)

    # 6. Simpan Data Absensi ke Database
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
    
    return {"status": "berhasil", "message": "Absensi berhasil dicatat", "data": new_attendance}

from typing import Optional

@router.get("/", response_model=list[schemas.Attendance])
def read_attendance(
    skip: int = 0, 
    limit: int = 100, 
    student_id: Optional[int] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Attendance)

    # Filter by Student ID
    if student_id:
        query = query.filter(models.Attendance.student_id == student_id)
    
    # Filter by Class ID (Join with Student table)
    if class_id:
        query = query.join(models.Student).filter(models.Student.class_id == class_id)

    return query.offset(skip).limit(limit).all()
