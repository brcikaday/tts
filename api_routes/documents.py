from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.dependencies import get_current_user
from db.session import get_db
from schemas.document import DocumentListItem, DocumentResponse
from services import document_service

documents_router = APIRouter(prefix="/documents", tags=["documents"])


@documents_router.get("", response_model=list[DocumentListItem])
def list_documents(current_user=Depends(get_current_user), db: Session = Depends(get_db),
                   limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return document_service.list_documents(current_user.id, db, limit, offset)


@documents_router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return document_service.get_document(current_user.id, document_id, db)


@documents_router.delete("/{document_id}")
def delete_document(document_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    document_service.delete_document(current_user.id, document_id, db)
    return {"message": "Deleted successfully"}
