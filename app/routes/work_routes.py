from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent
from app.utils.auth import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/work")
def get_my_work(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = (
        db.query(SavedContent)
        .filter(SavedContent.user_id == user.id)
        .order_by(SavedContent.id.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "content_type": item.content_type,
            "prompt": item.prompt,
            "result": item.result,
        }
        for item in items
    ]
