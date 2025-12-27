from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    students = relationship("Student", back_populates="student_class")
    sessions = relationship("AttendanceSession", back_populates="session_class")
    members = relationship("ClassMember", back_populates="member_class")

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
    memberships = relationship("ClassMember", back_populates="member_student")

class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint('student_id', 'session_id', name='_student_session_uc'),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=True) # Link to session
    timestamp = Column(DateTime, default=datetime.now)
    date = Column(String, index=True) # Storing YYYY-MM-DD for easy querying
    status = Column(String, default="Hadir") # Hadir, Gagal
    method = Column(String, default="face") # face, qr, pin
    confidence_score = Column(Float, default=0.0)
    image_path = Column(String, nullable=True)

    student = relationship("Student", back_populates="attendances")
    session = relationship("AttendanceSession") # Relationship to access session details if needed

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    date = Column(String, index=True) # YYYY-MM-DD
    start_time = Column(String) # HH:MM
    end_time = Column(String) # HH:MM
    method = Column(String, default="face") # face, qr, pin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    session_class = relationship("Class", back_populates="sessions")

class ClassMember(Base):
    __tablename__ = "class_members"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    student_id = Column(Integer, ForeignKey("students.id"))

    member_class = relationship("Class", back_populates="members")
    member_student = relationship("Student", back_populates="memberships")
