from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.session import SessionLocal
from app.database.models import SavedImage
from app.utils.auth import get_current_user

router = APIRouter(prefix="/images", tags=["Images"])


class SaveImageRequest(BaseModel):
    image_url: str
    text_content: str | None = None
    image_style: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/save")
def save_image(
    data: SaveImageRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not data.image_url:
        raise HTTPException(422, "Image URL missing")

    image = SavedImage(
        user_id=user.id,
        text_content=data.text_content,
        image_url=data.image_url,
        image_style=data.image_style
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return {"message": "Image saved", "id": image.id}


@router.get("/history")
def get_history(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    images = (
        db.query(SavedImage)
        .filter(SavedImage.user_id == user.id)
        .order_by(SavedImage.created_at.desc())
        .all()
    )

    return images
