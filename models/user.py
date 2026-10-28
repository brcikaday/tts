from sqlalchemy import Column, Integer, String
from sqlalchemy.sql import func
from db.base import Base
import enum
from sqlalchemy import Enum
from sqlalchemy import Boolean,DateTime
from sqlalchemy.orm import relationship


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True , nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_banned = Column(Boolean, default=False)  # False for not banned, True for banned
    dark_mode = Column(Boolean, nullable=False, default=False, server_default="false")
    auto_play = Column(Boolean, nullable=False, default=True, server_default="true")
    high_quality = Column(Boolean, nullable=False, default=True, server_default="true")

    documents = relationship("Document", back_populates="user")
    conversions = relationship("ConversionHistory", back_populates="user")
    system_logs = relationship("SystemLog", back_populates="user", passive_deletes=True)


    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, created_at={self.created_at}, is_banned={self.is_banned})>"
