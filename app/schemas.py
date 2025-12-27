from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

class AttendanceResponse(BaseModel):
    status: str
    message: str
    data: Optional[Attendance] = None

class AttendanceSessionBase(BaseModel):
    class_id: int
    date: str
    start_time: str
    end_time: str
    method: str = "face"
    is_active: bool = True

class AttendanceSessionCreate(AttendanceSessionBase):
    pass

class AttendanceSession(AttendanceSessionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClassMemberBase(BaseModel):
    class_id: int
    student_id: int

class ClassMemberCreate(ClassMemberBase):
    pass

class ClassMember(ClassMemberBase):
    id: int
    
    class Config:
        from_attributes = True

class StudentReport(BaseModel):
    student_id: int
    name: str
    nim: str
    total_sessions: int
    total_present: int
    total_alpha: int
    attendance_percentage: float

class ClassReport(BaseModel):
    class_id: int
    class_name: str
    total_sessions: int
    students: List[StudentReport]
