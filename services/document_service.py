from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.document import Document
from services.system_log_service import log_system_event


def get_document(user_id: int, document_id: int, db: Session) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not authorized")
    return document


def list_documents(user_id: int, db: Session, limit: int = 50, offset: int = 0) -> list:
    return (db.query(Document).filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc(), Document.id.desc()).offset(offset).limit(limit).all())


def create_document(user_id: int, title: str, source_type: str, extracted_text: str,
                    db: Session, source_url: str | None = None) -> Document:
    if not extracted_text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No readable content found")
    document = Document(user_id=user_id, title=title.strip() or "Untitled document",
                        source_type=source_type, source_url=source_url,
                        file_url=None, extracted_text=extracted_text)
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save document")
    action = "DOCUMENT_UPLOADED" if source_type == "upload" else "DOCUMENT_SCRAPED"
    log_system_event(db, user_id, action, f"Created document {document.id} from {source_type}")
    return document


def delete_document(user_id: int, document_id: int, db: Session) -> None:
    document = get_document(user_id, document_id, db)
    try:
        db.delete(document)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete document")
    log_system_event(db, user_id, "DOCUMENT_DELETED", f"Deleted document {document_id}")
