from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from services import scrape_service
from schemas.scrape import ScrapeRequest, ScrapeResponse
from sqlalchemy.orm import Session
from db.session import get_db
from services.document_service import create_document


scrape_router = APIRouter(prefix="/scrape", tags=["scrape"])

@scrape_router.post("/", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):

    scrapped_data = scrape_service.scrape_article(str(request.url))
    
    document = create_document(current_user.id, scrapped_data["title"] or "Web article", "url",
                               scrapped_data["text"], db, source_url=str(request.url))
    return ScrapeResponse(**scrapped_data, document_id=document.id,
                          source_type=document.source_type, extracted_text=document.extracted_text)
