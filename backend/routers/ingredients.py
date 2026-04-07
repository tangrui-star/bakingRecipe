from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from database import get_db
from models import Ingredient
from schemas import Ingredient as IngredientSchema, IngredientCreate

router = APIRouter()

@router.post("/", response_model=IngredientSchema)
def create_ingredient(ingredient: IngredientCreate, db: Session = Depends(get_db)):
    """创建原料"""
    db_ingredient = Ingredient(
        id=str(uuid.uuid4()),
        **ingredient.model_dump()
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@router.get("/", response_model=List[IngredientSchema])
def get_ingredients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取所有原料"""
    ingredients = db.query(Ingredient).offset(skip).limit(limit).all()
    return ingredients

@router.get("/{ingredient_id}", response_model=IngredientSchema)
def get_ingredient(ingredient_id: str, db: Session = Depends(get_db)):
    """获取单个原料"""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="原料不存在")
    return ingredient

@router.put("/{ingredient_id}", response_model=IngredientSchema)
def update_ingredient(ingredient_id: str, ingredient: IngredientCreate, db: Session = Depends(get_db)):
    """更新原料"""
    db_ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(status_code=404, detail="原料不存在")
    
    for key, value in ingredient.model_dump().items():
        setattr(db_ingredient, key, value)
    
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@router.delete("/{ingredient_id}")
def delete_ingredient(ingredient_id: str, db: Session = Depends(get_db)):
    """删除原料"""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="原料不存在")
    
    db.delete(ingredient)
    db.commit()
    return {"message": "原料已删除"}
