from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

# --------------------------
# USER MODEL
# --------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    # Subscription fields
    subscription_plan = Column(String, default="basic")
    monthly_limit = Column(Integer, nullable=True, default=50)
    used_generations = Column(Integer, default=0)

    last_reset = Column(DateTime, default=datetime.utcnow)

    # 🔐 PASSWORD RESET FIELDS
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    saved_content = relationship("SavedContent", back_populates="user")
    saved_images = relationship("SavedImage", back_populates="user")  # <-- NEW


# --------------------------
# PROFILE MODEL
# --------------------------
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    full_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    title = Column(String, nullable=True)
    brand_tone = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    brand_description = Column(String, nullable=True)
    target_audience = Column(String, nullable=True)
    signature = Column(String, nullable=True)
    writing_style = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")


# --------------------------
# SAVED CONTENT
# --------------------------
class SavedContent(Base):
    __tablename__ = "saved_content"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_type = Column(String)
    prompt = Column(String)
    result = Column(String)

    user = relationship("User", back_populates="saved_content")


# --------------------------
# SAVED IMAGES  (NEW)
# --------------------------
class SavedImage(Base):
    __tablename__ = "saved_images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text_content = Column(Text, nullable=True)  # text associated with image
    image_url = Column(Text, nullable=False)    # OpenAI image URL
    image_style = Column(String, nullable=True) # style user selected

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_images")


# --------------------------
# DASHBOARD SETTINGS
# --------------------------
class DashboardSettings(Base):
    __tablename__ = "dashboard_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    stocks_json = Column(Text, default="[]")
    cryptos_json = Column(Text, default='["BTC","ETH","SOL"]')
    currency_pairs_json = Column(Text, default='["USD:THB","EUR:THB","NOK:THB","BTC:USD"]')
    city = Column(String, nullable=True)

    widgets_order_json = Column(Text, default="[]")
    widgets_collapsed_json = Column(Text, default="{}")

    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="dashboard_settings")


# --------------------------
# TASKS
# --------------------------
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="tasks")
