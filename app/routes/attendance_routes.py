from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from app.utils.ai_service import validate_face
from datetime import datetime
import os
import shutil
import uuid
from typing import Optional

router = APIRouter(prefix="/attendance", tags=["attendance"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sessions/", response_model=schemas.AttendanceSession)
def create_session(session: schemas.AttendanceSessionCreate, db: Session = Depends(get_db)):
    # Create new session
    # Access fields by attribute name (snake_case) thanks to populate_by_name=True
    new_session = models.AttendanceSession(
        class_id=session.class_id,
        date=session.date,
        start_time=session.start_time,
        end_time=session.end_time,
        method=session.method,
        is_active=session.is_active
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions/", response_model=list[schemas.AttendanceSession])
def get_sessions(
    class_id: Optional[int] = None, 
    date: Optional[str] = None, 
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.AttendanceSession)
    if class_id:
        query = query.filter(models.AttendanceSession.class_id == class_id)
    if date:
        query = query.filter(models.AttendanceSession.date == date)
    if is_active is not None:
        query = query.filter(models.AttendanceSession.is_active == is_active)
    return query.all()

@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.AttendanceSession).filter(models.AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Soft delete: Just set is_active to False
    session.is_active = False
    db.commit()
    return {"status": "success", "message": "Session deactivated"}

@router.post("/", response_model=schemas.AttendanceResponse)
async def submit_attendance(
    nim: str = Form(...),
    class_id: int = Form(...), # Ditambahkan sesuai request: Identitas Kelas
    method: str = Form(...), # Ditambahkan sesuai request: Metode Absensi (face, qr, pin)
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Cari Data Siswa (Identitas Siswa)
    student = db.query(models.Student).filter(models.Student.nim == nim).first()
    if not student:
        return {"status": "gagal", "message": "Siswa tidak ditemukan", "data": None}

    # 2. Validasi Kelas (Memastikan siswa mengirim identitas kelas yang benar)
    if student.class_id != class_id:
        return {"status": "gagal", "message": "Siswa tidak terdaftar di kelas ini", "data": None}

    # 2.5 CEK MEMBERSHIP (New Feature)
    # Pastikan student benar-benar terdaftar sebagai member di kelas tersebut
    is_member = db.query(models.ClassMember).filter(
        models.ClassMember.class_id == class_id, 
        models.ClassMember.student_id == student.id
    ).first()
    
    # Optional strict check: if membership table is populated, enforce it.
    if not is_member:
         return {"status": "gagal", "message": "Validasi Gagal: Mahasiswa bukan anggota kelas ini.", "data": None}

    # 2.6 CEK SESI AKTIF (New Feature)
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")

    active_session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.class_id == class_id,
        models.AttendanceSession.date == today_str,
        models.AttendanceSession.is_active == True,
        models.AttendanceSession.start_time <= current_time_str,
        models.AttendanceSession.end_time >= current_time_str
    ).first()

    if not active_session:
         # Mengembalikan HTTP 403 sesuai request
        return JSONResponse(
            status_code=403,
            content={"status": "gagal", "message": "Tidak ada sesi absensi aktif saat ini (Di luar jam sesi).", "data": None}
        )

    # 2.7 VALIDASI METODE (New Feature)
    # Pastikan metode yang dikirim siswa (misal: 'face') SAMA dengan metode sesi (misal: 'face')
    if active_session.method != method:
         return {"status": "gagal", "message": f"Metode absensi salah! Sesi ini mengharuskan metode: {active_session.method}", "data": None}

    # 3. Cek Absen Ganda (Anti-Double)
    # Gunakan session_id untuk pengecekan yang lebih akurat (Per Sesi, bukan Per Hari)
    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.student_id == student.id,
        models.Attendance.session_id == active_session.id
    ).first()

    if existing_attendance:
        return {"status": "gagal", "message": "Siswa sudah melakukan absensi di sesi ini.", "data": None}

    # 4. Validasi Wajah dengan AI
    content = await file.read()
    confidence_score = 0.0

    if method == "face":
        if student.face_encoding:
            is_match, score = validate_face(content, student.face_encoding)
            confidence_score = score
            
            if not is_match:
                 return {"status": "gagal", "message": f"Wajah tidak cocok! (Skor: {score:.2f})", "data": None}
            
            # Additional strict check requested by user
            if score < 0.8:
                 return {"status": "gagal", "message": f"Akurasi Wajah Kurang (Skor: {score:.2f} < 0.8). Coba foto lebih jelas.", "data": None}
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
        date=today_str,
        timestamp=now,
        status="Hadir",
        session_id=active_session.id, # Link ke sesi aktif
        method=method,
        confidence_score=confidence_score,
        image_path=file_path
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return {"status": "berhasil", "message": "Absensi berhasil dicatat", "data": new_attendance}


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
