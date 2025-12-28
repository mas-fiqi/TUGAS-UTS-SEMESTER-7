from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from typing import List

router = APIRouter(prefix="/classes", tags=["classes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Class])
def read_classes(db: Session = Depends(get_db)):
    return db.query(models.Class).all()

@router.post("/", response_model=schemas.Class)
def create_class(class_data: schemas.ClassCreate, db: Session = Depends(get_db)):
    # Check if class with same name exists
    existing_class = db.query(models.Class).filter(models.Class.name == class_data.name).first()
    if existing_class:
        raise HTTPException(status_code=400, detail="Class with this name already exists")
    
    db_class = models.Class(name=class_data.name)
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@router.post("/{class_id}/students/{student_id}", response_model=schemas.ClassMember)
def add_student_to_class(class_id: int, student_id: int, db: Session = Depends(get_db)):
    # Check if student exists
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if class exists
    class_obj = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if already a member
    existing_member = db.query(models.ClassMember).filter(
        models.ClassMember.class_id == class_id,
        models.ClassMember.student_id == student_id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Student is already a member of this class")

    new_member = models.ClassMember(class_id=class_id, student_id=student_id)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

@router.get("/{class_id}/students", response_model=List[schemas.Student])
def get_class_students(class_id: int, db: Session = Depends(get_db)):
    # Get all student IDs in this class
    members = db.query(models.ClassMember).filter(models.ClassMember.class_id == class_id).all()
    student_ids = [m.student_id for m in members]
    
    students = db.query(models.Student).filter(models.Student.id.in_(student_ids)).all()
    return students
