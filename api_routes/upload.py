from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from core.dependencies import get_current_user
from schemas.user import DocumentResponse
from services.document_processor import extract_text_from_pdf, extract_text_from_docx, chunking_file
import os
from sqlalchemy.orm import Session
from db.session import get_db
from services.document_service import create_document

upload_router = APIRouter(tags=["upload"])


@upload_router.post("/upload", response_model=DocumentResponse)
async def upload_file(file: UploadFile = File(...), current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not file.content_type in ('text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    

    if file.content_type == 'application/pdf':
        temp_file_path, total_size = chunking_file(file)
        try:
            text = extract_text_from_pdf(temp_file_path)
        finally:
            os.remove(temp_file_path)

    elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        temp_file_path, total_size = chunking_file(file)
        try:
            text = extract_text_from_docx(temp_file_path)
        finally:
            os.remove(temp_file_path)


    elif file.content_type == 'text/plain':
        content = await file.read()
        text = content.decode('utf-8')
        total_size = len(content)
        
    word_count = len(text.split())

    FILE_TYPE_MAP = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "text",
}
    file_type = FILE_TYPE_MAP.get(file.content_type)

    document = create_document(current_user.id, file.filename or "Uploaded document", "upload", text, db)

    return DocumentResponse(
        document_id=document.id,
        title=document.title,
        source_type=document.source_type,
        extracted_text=document.extracted_text,
        file_name=file.filename,
        text=text,
        file_size=total_size,
        file_type=file_type,
        word_count=word_count
    )
