from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from database import get_db
from models import RecipeCategory
from schemas import Category, CategoryCreate

router = APIRouter()

@router.post("/", response_model=Category)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """创建品类"""
    db_category = RecipeCategory(
        id=str(uuid.uuid4()),
        **category.model_dump()
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[Category])
def get_categories(db: Session = Depends(get_db)):
    """获取所有品类"""
    categories = db.query(RecipeCategory).all()
    return categories

@router.get("/{category_id}", response_model=Category)
def get_category(category_id: str, db: Session = Depends(get_db)):
    """获取单个品类"""
    category = db.query(RecipeCategory).filter(RecipeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="品类不存在")
    return category

@router.delete("/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db)):
    """删除品类"""
    category = db.query(RecipeCategory).filter(RecipeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="品类不存在")
    
    db.delete(category)
    db.commit()
    return {"message": "品类已删除"}
