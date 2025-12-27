from fastapi import FastAPI
from app.routes import health_routes, student_routes, attendance_routes
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Presence Backend")

app.include_router(health_routes.router)
app.include_router(student_routes.router)
app.include_router(attendance_routes.router)
