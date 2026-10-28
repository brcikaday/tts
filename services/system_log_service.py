import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.system_log import SystemLog

logger = logging.getLogger(__name__)


def log_system_event(db: Session, user_id: int | None, action: str, details: str | None = None) -> bool:
    """Call after successful work (and any business commit).

    A separate transaction cannot roll back the completed business operation.

    Only controlled event descriptions belong here, never request bodies or secrets.
    """
    try:
        with Session(bind=db.get_bind()) as log_db:
            log_db.add(SystemLog(user_id=user_id, action=action, details=details))
            log_db.commit()
        return True
    except SQLAlchemyError:
        # Do not include SQL parameters or connection credentials in diagnostics.
        logger.warning("Could not persist system audit event %s", action)
        return False
