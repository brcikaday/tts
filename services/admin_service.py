from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user import User, UserRole
from models.conversion import ConversionHistory
from schemas.admin import AdminUserUpdate
from models.system_log import SystemLog
from services.system_log_service import log_system_event


def list_users(session: Session) -> list:
    counts_subq = (
        session.query(
            ConversionHistory.user_id,
            func.count(ConversionHistory.id).label("total"),
        )
        .group_by(ConversionHistory.user_id)
        .subquery()
    )

    rows = (
        session.query(User, func.coalesce(counts_subq.c.total, 0))
        .outerjoin(counts_subq, User.id == counts_subq.c.user_id)
        .order_by(User.id)
        .all()
    )

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "is_banned": bool(user.is_banned),
            "total_conversions": total,
        }
        for user, total in rows
    ]


def update_user(user_id: int, update_data: AdminUserUpdate, session: Session, actor_id: int | None = None) -> User:
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    events = []
    if update_data.role is not None and user.role != UserRole(update_data.role):
        events.append(("ROLE_CHANGED", f"Changed user {user_id} role from {user.role.value} to {update_data.role}"))
        user.role = UserRole(update_data.role)
    if update_data.is_banned is not None and bool(user.is_banned) != update_data.is_banned:
        events.append(("USER_BANNED" if update_data.is_banned else "USER_UNBANNED", f"Updated ban status for user {user_id}"))
        user.is_banned = update_data.is_banned

    session.commit()
    for action, details in events:
        log_system_event(session, actor_id, action, details)
    return user


def get_stats(session: Session) -> dict:
    total_users = session.query(func.count(User.id)).scalar()
    total_conversions = session.query(func.count(ConversionHistory.id)).scalar()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    conversions_today = (
        session.query(func.count(ConversionHistory.id))
        .filter(ConversionHistory.created_at >= today_start)
        .scalar()
    )

    by_language_rows = (
        session.query(ConversionHistory.language, func.count(ConversionHistory.id))
        .group_by(ConversionHistory.language)
        .all()
    )
    conversions_by_language = {language: count for language, count in by_language_rows}

    day_col = func.date(ConversionHistory.created_at)
    by_day_rows = (
        session.query(day_col, func.count(ConversionHistory.id))
        .group_by(day_col)
        .order_by(day_col)
        .all()
    )
    conversions_by_day = [{"date": str(day), "count": count} for day, count in by_day_rows]

    return {
        "total_users": total_users,
        "total_conversions": total_conversions,
        "conversions_today": conversions_today,
        "conversions_by_language": conversions_by_language,
        "conversions_by_day": conversions_by_day,
    }


def get_logs(session: Session, limit: int = 50, offset: int = 0) -> list:
    rows = (session.query(SystemLog, User.email)
            .outerjoin(User, SystemLog.user_id == User.id)
            .order_by(SystemLog.created_at.desc(), SystemLog.id.desc())
            .offset(offset).limit(limit).all())
    return [{"id": entry.id, "user_id": entry.user_id, "action": entry.action,
             "details": entry.details, "created_at": entry.created_at,
             "timestamp": entry.created_at.isoformat(), "level": "info",
             "message": entry.details or entry.action, "user_email": email or "system"}
            for entry, email in rows]
