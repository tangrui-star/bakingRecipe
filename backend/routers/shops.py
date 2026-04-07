from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from database import get_db
from models import Shop
from schemas import Shop as ShopSchema, ShopCreate

router = APIRouter()

@router.post("/", response_model=ShopSchema)
def create_shop(shop: ShopCreate, db: Session = Depends(get_db)):
    """创建店铺"""
    db_shop = Shop(
        id=str(uuid.uuid4()),
        **shop.model_dump()
    )
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    return db_shop

@router.get("/", response_model=List[ShopSchema])
def get_shops(db: Session = Depends(get_db)):
    """获取所有店铺"""
    shops = db.query(Shop).all()
    return shops

@router.get("/{shop_id}", response_model=ShopSchema)
def get_shop(shop_id: str, db: Session = Depends(get_db)):
    """获取单个店铺"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="店铺不存在")
    return shop
