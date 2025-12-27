from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from typing import List
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/class/{class_id}", response_model=schemas.ClassReport)
def get_class_report(class_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    # 1. Hitung total sesi yang SUDAH BERLALU (Expired)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    # Query logic: date < today OR (date == today AND end_time < current_time)
    # Simplification for string comparison: filtering active sessions or just all sessions?
    # Report usually implies ALL scheduled sessions that have passed.
    
    # Let's count all sessions created for this class
    total_sessions_count = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.class_id == class_id
    ).count()

    # Get all students in the class via ClassMember (or direct foreign key for simplicity if legacy)
    # Using ClassMember is better as we migrated to it.
    members = db.query(models.ClassMember).filter(models.ClassMember.class_id == class_id).all()
    student_ids = [m.student_id for m in members]
    students = db.query(models.Student).filter(models.Student.id.in_(student_ids)).all()

    student_reports = []
    for student in students:
        # Count present
        total_present = db.query(models.Attendance).filter(
            models.Attendance.student_id == student.id,
            models.Attendance.status == "Hadir" # Ensure we only count 'Hadir'
        ).count()

        total_alpha = total_sessions_count - total_present
        if total_alpha < 0: total_alpha = 0 # Safety net

        percentage = 0.0
        if total_sessions_count > 0:
            percentage = (total_present / total_sessions_count) * 100

        student_reports.append(schemas.StudentReport(
            student_id=student.id,
            name=student.name,
            nim=student.nim,
            total_sessions=total_sessions_count,
            total_present=total_present,
            total_alpha=total_alpha,
            attendance_percentage=round(percentage, 2)
        ))

    return schemas.ClassReport(
        class_id=class_id,
        class_name=class_obj.name,
        total_sessions=total_sessions_count,
        students=student_reports
    )

@router.get("/student/{student_id}", response_model=schemas.StudentReport)
def get_student_report(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Determine class from membership (assuming single class for simplicity in report context)
    # Or use student.class_id if legacy field is still reliable/primary.
    # We'll rely on the student.class_id as primary class for now, or find the main class.
    # Let's check where the student is currently enrolled (Main Class)
    current_class_id = student.class_id 
    
    total_sessions_count = 0
    if current_class_id:
        total_sessions_count = db.query(models.AttendanceSession).filter(
            models.AttendanceSession.class_id == current_class_id
        ).count()

    total_present = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id,
        models.Attendance.status == "Hadir"
    ).count()

    total_alpha = total_sessions_count - total_present
    if total_alpha < 0: total_alpha = 0

    percentage = 0.0
    if total_sessions_count > 0:
        percentage = (total_present / total_sessions_count) * 100

    return schemas.StudentReport(
        student_id=student.id,
        name=student.name,
        nim=student.nim,
        total_sessions=total_sessions_count,
        total_present=total_present,
        total_alpha=total_alpha,
        attendance_percentage=round(percentage, 2)
    )
