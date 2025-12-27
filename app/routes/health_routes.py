from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Project Backend Smart Presence dimulai"}
