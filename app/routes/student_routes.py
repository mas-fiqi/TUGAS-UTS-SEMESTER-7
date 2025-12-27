from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, schemas
from app.utils.ai_service import get_face_encoding
import shutil
import os

router = APIRouter(prefix="/students", tags=["students"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Student)
async def create_student(
    name: str = Form(...),
    nim: str = Form(...),
    class_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if student exists
    db_student = db.query(models.Student).filter(models.Student.nim == nim).first()
    if db_student:
        raise HTTPException(status_code=400, detail="NIM already registered")

    # Read image content
    content = await file.read()
    
    # Generate face encoding
    encoding = get_face_encoding(content)
    if encoding is None:
        raise HTTPException(status_code=400, detail="No face detected in the photo")

    # Create Student
    new_student = models.Student(
        name=name,
        nim=nim,
        class_id=class_id,
        face_encoding=encoding
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.get("/", response_model=list[schemas.Student])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    students = db.query(models.Student).offset(skip).limit(limit).all()
    return students

@router.post("/classes/", response_model=schemas.Class)
def create_class(name: str = Form(...), db: Session = Depends(get_db)):
    db_class = models.Class(name=name)
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@router.get("/classes/", response_model=list[schemas.Class])
def read_classes(db: Session = Depends(get_db)):
    return db.query(models.Class).all()
