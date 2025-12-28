from app.database import SessionLocal
from app.models import Student, Class, ClassMember, AttendanceSession
from datetime import datetime, timedelta

db = SessionLocal()

print("--- MULAI SEEDING DATA ---")

# 1. Buat Kelas
kelas = db.query(Class).filter(Class.name == "Kelas Percobaan").first()
if not kelas:
    kelas = Class(name="Kelas Percobaan")
    db.add(kelas)
    db.commit()
    db.refresh(kelas)
    print(f"[OK] Kelas dibuat: {kelas.name} (ID: {kelas.id})")
else:
    print(f"[INFO] Kelas sudah ada: {kelas.name} (ID: {kelas.id})")

# 2. Masukkan Semua Siswa ke Kelas ini
students = db.query(Student).all()
if not students:
    print("[ERROR] Belum ada siswa! Silakan Create Student dulu via API.")
else:
    for s in students:
        # Update foreign key legacy
        s.class_id = kelas.id
        
        # Create Membership
        member = db.query(ClassMember).filter(ClassMember.student_id == s.id, ClassMember.class_id == kelas.id).first()
        if not member:
            member = ClassMember(student_id=s.id, class_id=kelas.id)
            db.add(member)
            print(f"[OK] Siswa {s.name} (NIM: {s.nim}) ditambahkan ke kelas.")
    db.commit()

# 3. Buat Sesi Aktif SEKARANG
now = datetime.now()
start_time = (now - timedelta(hours=1)).strftime("%H:%M")
end_time = (now + timedelta(hours=2)).strftime("%H:%M")
today_str = now.strftime("%Y-%m-%d")

session = db.query(AttendanceSession).filter(
    AttendanceSession.class_id == kelas.id,
    AttendanceSession.date == today_str,
    AttendanceSession.is_active == True
).first()

if not session:
    session = AttendanceSession(
        class_id=kelas.id,
        date=today_str,
        start_time=start_time,
        end_time=end_time,
        method="face",
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    print(f"[OK] Sesi Absensi DIBUKA untuk hari ini!")
    print(f"    - Waktu: {start_time} s/d {end_time}")
    print(f"    - Metode: FACE")
else:
    print(f"[INFO] Sesi Absensi sudah aktif.")

print("\n--- STATUS SIAP ---")
print(f"Sekarang coba hit API '/attendance/' dengan:")
print(f" - class_id: {kelas.id}")
print(f" - nim: <salah satu nim diatas>")
print(f" - method: face")
db.close()
