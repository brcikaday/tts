"""Legacy table mapping retained for Alembic and existing data only.

No application route or service reads these retired settings.
"""
from sqlalchemy import Column, Integer, String, Boolean
from db.base import Base


class AdminConfig(Base):
    __tablename__ = "admin_config"

    id = Column(Integer, primary_key=True, index=True)
    tts_primary = Column(String, nullable=False, default="ghana_nlp", server_default="ghana_nlp")
    tts_fallback_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
