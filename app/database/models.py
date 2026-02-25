from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    subscription_plan = Column(String, default="free")
    can_publish = Column(Boolean, default=False)
    max_pages = Column(Integer, default=1)

    monthly_limit = Column(Integer, nullable=True, default=50)
    used_generations = Column(Integer, default=0)
    last_reset = Column(DateTime, default=datetime.utcnow)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    profile = relationship("Profile", back_populates="user", uselist=False)
    saved_content = relationship("SavedContent", back_populates="user")
    saved_images = relationship("SavedImage", back_populates="user")
    websites = relationship("Website", back_populates="user")


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

    use_emojis = Column(Boolean, default=True)
    use_hashtags = Column(Boolean, default=True)
    length_pref = Column(String, default="medium")
    creativity_level = Column(Integer, default=5)
    cta_style = Column(String, default="soft")

    user = relationship("User", back_populates="profile")


class SavedContent(Base):
    __tablename__ = "saved_content"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    content_type = Column(String)
    prompt = Column(String)
    result = Column(String)

    user = relationship("User", back_populates="saved_content")


class SavedImage(Base):
    __tablename__ = "saved_images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text_content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=False)
    image_style = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_images")


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


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="tasks")


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    template = Column(String, nullable=False, default="master_architect_v1")

    html_content = Column(Text, nullable=True)
    content_json = Column(Text, nullable=False)

    ai_structure_json = Column(Text, nullable=True)
    ai_version = Column(Integer, default=1)

    publish_status = Column(String, default="draft")
    last_published_at = Column(DateTime, nullable=True)

    custom_domain = Column(String, unique=True, nullable=True)
    domain_verified = Column(Boolean, default=False)

    # Tracks how many times user has regenerated this site (enforced per plan)
    regen_count = Column(Integer, default=0, nullable=False, server_default="0")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="websites")