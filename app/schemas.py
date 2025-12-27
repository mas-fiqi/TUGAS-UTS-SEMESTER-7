from pydantic import BaseModel
from typing import List, Optional

class ClassBase(BaseModel):
    name: str

class ClassCreate(ClassBase):
    pass

class Class(ClassBase):
    id: int

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    name: str
    nim: str
    class_id: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int

    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    student_id: int

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    date: str
    timestamp: str
    status: str
    
    class Config:
        from_attributes = True
