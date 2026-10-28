from models.user import User
from models.conversion import ConversionHistory
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from schemas.conversion import ConversionHistoryCreate
from services.document_service import get_document
from services.system_log_service import log_system_event





def save_conversion(user_id, conversion: ConversionHistoryCreate, session: Session):
    """
    Save a new conversion to the database.
    """
    if conversion.document_id is not None:
        get_document(user_id, conversion.document_id, session)
    try:
        new_conversion = ConversionHistory(
            user_id=user_id,
            document_id=conversion.document_id,
            title=conversion.title,
            text=conversion.text,
            voice=conversion.voice,
            language=conversion.language,
            source_type=conversion.source_type,
            audio_url=conversion.audio_url
        )
        session.add(new_conversion)
        session.commit()
        session.refresh(new_conversion)
        log_system_event(session, user_id, "CONVERSION_CREATED", f"Saved conversion {new_conversion.id}")
        return new_conversion
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def load_library(user_id, session: Session):
    """
    Load the library of documents for the current user.
    """
    try:
        documents = session.query(ConversionHistory).filter(ConversionHistory.user_id == user_id).order_by(ConversionHistory.created_at.desc()).all()
        return documents
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

def delete_conversion(user_id,conversion_id,session:Session):
    conversion = session.query(ConversionHistory).filter(ConversionHistory.id == conversion_id).first()
    if not conversion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "conversion not found")
    if conversion.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "not authorized")
    
    session.delete(conversion)
    session.commit()
    log_system_event(session, user_id, "CONVERSION_DELETED", f"Deleted conversion {conversion_id}")

def bookmark_conversion(user_id, conversion_id, session: Session):
    conversion = session.query(ConversionHistory).filter(ConversionHistory.id == conversion_id).first()
    if not conversion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "conversion not found")
    if conversion.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "not authorized")
    
    conversion.bookmarked = not conversion.bookmarked
    session.commit()
    session.refresh(conversion)

    action = "CONVERSION_BOOKMARKED" if conversion.bookmarked else "CONVERSION_UNBOOKMARKED"
    log_system_event(session, user_id, action, f"Updated bookmark for conversion {conversion_id}")

    return conversion.bookmarked
