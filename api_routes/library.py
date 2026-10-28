from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from schemas.conversion import ConversionHistoryResponse, ConversionHistoryCreate
from models.conversion import ConversionHistory
from services import library_service
from sqlalchemy.orm import Session
from db.session import get_db


library_router = APIRouter(prefix="/library", tags=["library"])


@library_router.post("/", response_model=ConversionHistoryResponse, status_code=201)
async def create_conversion(conversion: ConversionHistoryCreate, current_user = Depends(get_current_user),db:Session=Depends(get_db)):
    new_conversion = library_service.save_conversion(
        user_id=current_user.id,
        conversion=conversion,
        session=db
    )
    return new_conversion


@library_router.get("/", response_model=list[ConversionHistoryResponse])
async def library(current_user = Depends(get_current_user),db:Session=Depends(get_db)):

    all_conversions = library_service.load_library(current_user.id,db)

    return all_conversions


@library_router.delete("/{id}")
async def delete_library(id:int ,current_user = Depends(get_current_user),db:Session=Depends(get_db)):
        
    library_service.delete_conversion(current_user.id,id,db)
    
    return {"message": "Deleted successfully"}


@library_router.post("/{id}/bookmark")
async def bookmark(id:int ,current_user = Depends(get_current_user),db:Session=Depends(get_db)):

    bookmarked_state = library_service.bookmark_conversion(current_user.id,id,db)

    
    return {"bookmarked": bookmarked_state}