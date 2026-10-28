from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal, Optional


class AdminUserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    is_banned: bool
    total_conversions: int

    model_config = ConfigDict(from_attributes=True)


class AdminUsersListResponse(BaseModel):
    users: list[AdminUserResponse]


class AdminUserUpdate(BaseModel):
    role: Optional[Literal["user", "admin"]] = None
    is_banned: Optional[bool] = None


class ConversionsByDay(BaseModel):
    date: str
    count: int


class AdminStatsResponse(BaseModel):
    total_users: int
    total_conversions: int
    conversions_today: int
    conversions_by_language: dict[str, int]
    conversions_by_day: list[ConversionsByDay]


class AdminLogEntry(BaseModel):
    id: int
    user_id: int | None
    action: str
    details: str | None
    created_at: datetime
    timestamp: str
    level: str
    message: str
    user_email: str


class AdminLogsResponse(BaseModel):
    logs: list[AdminLogEntry]
    limit: int
    offset: int
