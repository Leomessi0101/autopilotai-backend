from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import SavedContent, User

router = APIRouter()

@router.get("/history")
def get_history(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    items = db.query(SavedContent).filter_by(user_id=current_user.id).all()
    db.close()
    return items
