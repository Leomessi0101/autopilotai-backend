from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.database.models import RestaurantWebsite

router = APIRouter(prefix="/api/websites", tags=["Websites"])


@router.post("/restaurant")
def create_restaurant_website(
    user_id: int,
    username: str,
    content_json: str,
    db: Session = Depends(get_db),
):
    existing = db.query(RestaurantWebsite).filter_by(username=username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    website = RestaurantWebsite(
        user_id=user_id,
        username=username,
        content_json=content_json,
    )

    db.add(website)
    db.commit()
    db.refresh(website)

    return {
        "id": website.id,
        "username": website.username,
        "template": website.template,
    }


@router.get("/restaurant/{username}")
def get_restaurant_website(username: str, db: Session = Depends(get_db)):
    website = db.query(RestaurantWebsite).filter_by(username=username).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return {
        "username": website.username,
        "template": website.template,
        "content_json": website.content_json,
    }


@router.get("/restaurant-create-test")
def create_test_restaurant(db: Session = Depends(get_db)):
    website = RestaurantWebsite(
        user_id=1,
        username="testrestaurant",
        content_json='{"hero":{"headline":"Test Restaurant","subheadline":"Best food in town"}}'
    )
    db.add(website)
    db.commit()
    db.refresh(website)

    return {
        "status": "created",
        "username": website.username
    }
