from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.sql import func
from db.base import Base
from sqlalchemy import Boolean,DateTime
from sqlalchemy.orm import relationship

class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False)
    text = Column(String, nullable=False)
    language = Column(String, nullable=False)
    voice = Column(String, nullable=False)
    audio_url = Column(String, nullable=True)
    source_type = Column(String, nullable=False)  # e.g., "text-to-speech"
    bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="conversions")
    document = relationship("Document", back_populates="conversions")

    def __repr__(self):
        return f"<ConversionHistory(id={self.id}, user_id={self.user_id}, title={self.title}, text={self.text}, language={self.language}, voice={self.voice}, audio_url={self.audio_url}, source_type={self.source_type}, bookmarked={self.bookmarked}, created_at={self.created_at}, updated_at={self.updated_at})>"
