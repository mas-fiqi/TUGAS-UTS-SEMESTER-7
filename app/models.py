from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    students = relationship("Student", back_populates="student_class")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    nim = Column(String, unique=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    # Storing face encoding as bytes (numpy array dumped)
    face_encoding = Column(LargeBinary, nullable=True)

    student_class = relationship("Class", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")

class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint('student_id', 'date', name='_student_date_uc'),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    timestamp = Column(DateTime, default=datetime.now)
    date = Column(String, index=True) # Storing YYYY-MM-DD for easy querying
    status = Column(String, default="Hadir") # Hadir, Gagal
    image_path = Column(String, nullable=True)

    student = relationship("Student", back_populates="attendances")
