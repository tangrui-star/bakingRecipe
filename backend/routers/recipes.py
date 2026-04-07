from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List
from decimal import Decimal
import uuid
import json
from datetime import datetime

from database import get_db
from models import Recipe, RecipeVersion, RecipeVersionIngredient, Ingredient, RecipeStep, RecipeCategory
from schemas import (
    Recipe as RecipeSchema,
    RecipeCreate,
    RecipeDetail,
    RecipeVersion as RecipeVersionSchema,
    RecipeVersionCreate,
    RecipeCalculateRequest,
    RecipeCalculateResponse
)

router = APIRouter()

@router.post("/", response_model=RecipeSchema)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    """创建新配方"""
    recipe_id = str(uuid.uuid4())
    
    db_recipe = Recipe(
        id=recipe_id,
        shop_id=recipe.shop_id,
        category_id=recipe.category_id,
        current_name=recipe.version_data.name,
        current_version=1
    )
    db.add(db_recipe)
    
    # 创建第一个版本
    version_id = str(uuid.uuid4())
    db_version = RecipeVersion(
        id=version_id,
        recipe_id=recipe_id,
        version=1,
        name=recipe.version_data.name,
        base_quantity=recipe.version_data.base_quantity,
        base_weight=recipe.version_data.base_weight,
        notes=recipe.version_data.notes,
        calculation_rule=recipe.version_data.calculation_rule,
        created_by=recipe.version_data.created_by
    )
    db.add(db_version)
    
    # 添加原料并计算热量
    total_calories = Decimal(0)
    for idx, ing in enumerate(recipe.version_data.ingredients):
        ingredient = db.query(Ingredient).filter(Ingredient.id == ing.ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail=f"原料 {ing.ingredient_id} 不存在")
        
        db_recipe_ing = RecipeVersionIngredient(
            id=str(uuid.uuid4()),
            recipe_version_id=version_id,
            ingredient_id=ing.ingredient_id,
            weight=ing.weight,
            sort_order=ing.sort_order or idx
        )
        db.add(db_recipe_ing)
        
        # 计算热量
        if ingredient.calories_per_100g:
            total_calories += (ingredient.calories_per_100g * ing.weight / 100)
    
    db_version.total_calories = total_calories
    
    # 添加制作步骤
    for step in recipe.version_data.steps:
        db_step = RecipeStep(
            id=str(uuid.uuid4()),
            recipe_version_id=version_id,
            step_number=step.step_number,
            description=step.description,
            duration_minutes=step.duration_minutes,
            temperature=step.temperature
        )
        db.add(db_step)
    
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@router.get("/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """获取配方详情（包含所有版本及关联数据）"""
    recipe = db.query(Recipe).options(
        selectinload(Recipe.versions).selectinload(RecipeVersion.ingredients).joinedload(RecipeVersionIngredient.ingredient),
        selectinload(Recipe.versions).selectinload(RecipeVersion.steps)
    ).filter(Recipe.id == recipe_id).first()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="配方不存在")
    return recipe

@router.get("/shop/{shop_id}", response_model=List[RecipeSchema])
def get_shop_recipes(shop_id: str, category_id: str = None, db: Session = Depends(get_db)):
    """获取店铺的所有配方"""
    query = db.query(Recipe).filter(Recipe.shop_id == shop_id)
    if category_id:
        query = query.filter(Recipe.category_id == category_id)
    return query.all()

@router.put("/{recipe_id}", response_model=RecipeSchema)
def update_recipe(recipe_id: str, version_data: RecipeVersionCreate, db: Session = Depends(get_db)):
    """更新配方（创建新版本）"""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="配方不存在")
    
    new_version = recipe.current_version + 1
    version_id = str(uuid.uuid4())
    
    db_version = RecipeVersion(
        id=version_id,
        recipe_id=recipe_id,
        version=new_version,
        name=version_data.name,
        base_quantity=version_data.base_quantity,
        base_weight=version_data.base_weight,
        notes=version_data.notes,
        calculation_rule=version_data.calculation_rule,
        created_by=version_data.created_by
    )
    db.add(db_version)
    
    # 添加原料并计算热量
    total_calories = Decimal(0)
    for idx, ing in enumerate(version_data.ingredients):
        ingredient = db.query(Ingredient).filter(Ingredient.id == ing.ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail=f"原料 {ing.ingredient_id} 不存在")
        
        db_recipe_ing = RecipeVersionIngredient(
            id=str(uuid.uuid4()),
            recipe_version_id=version_id,
            ingredient_id=ing.ingredient_id,
            weight=ing.weight,
            sort_order=ing.sort_order or idx
        )
        db.add(db_recipe_ing)
        
        if ingredient.calories_per_100g:
            total_calories += (ingredient.calories_per_100g * ing.weight / 100)
    
    db_version.total_calories = total_calories
    
    # 添加制作步骤
    for step in version_data.steps:
        db_step = RecipeStep(
            id=str(uuid.uuid4()),
            recipe_version_id=version_id,
            step_number=step.step_number,
            description=step.description,
            duration_minutes=step.duration_minutes,
            temperature=step.temperature
        )
        db.add(db_step)
    
    # 更新配方主表
    recipe.current_version = new_version
    recipe.current_name = version_data.name
    
    db.commit()
    db.refresh(recipe)
    return recipe

@router.post("/calculate", response_model=RecipeCalculateResponse)
def calculate_recipe(request: RecipeCalculateRequest, db: Session = Depends(get_db)):
    """配方计算器：根据目标数量计算所需原料"""
    recipe = db.query(Recipe).filter(Recipe.id == request.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="配方不存在")
    
    # 获取最新版本（预加载原料信息）
    latest_version = db.query(RecipeVersion).options(
        selectinload(RecipeVersion.ingredients).joinedload(RecipeVersionIngredient.ingredient)
    ).filter(
        RecipeVersion.recipe_id == request.recipe_id,
        RecipeVersion.version == recipe.current_version
    ).first()
    
    if not latest_version or not latest_version.base_quantity:
        raise HTTPException(status_code=400, detail="配方缺少基础数量信息")
    
    # 计算比例
    ratio = Decimal(request.target_quantity) / latest_version.base_quantity
    
    # 计算每个原料的用量
    ingredients_result = []
    total_calories = Decimal(0)
    
    for recipe_ing in latest_version.ingredients:
        calculated_weight = recipe_ing.weight * ratio
        ingredient_data = {
            "name": recipe_ing.ingredient.name,
            "base_weight": float(recipe_ing.weight),
            "calculated_weight": float(calculated_weight),
            "unit": recipe_ing.ingredient.unit
        }
        ingredients_result.append(ingredient_data)
        
        if recipe_ing.ingredient.calories_per_100g:
            total_calories += (recipe_ing.ingredient.calories_per_100g * calculated_weight / 100)
    
    return RecipeCalculateResponse(
        recipe_name=latest_version.name,
        target_quantity=request.target_quantity,
        ingredients=ingredients_result,
        total_calories=total_calories
    )

@router.get("/{recipe_id}/versions", response_model=List[RecipeVersionSchema])
def get_recipe_versions(recipe_id: str, db: Session = Depends(get_db)):
    """获取配方的所有历史版本（包含原料和步骤）"""
    versions = db.query(RecipeVersion).options(
        selectinload(RecipeVersion.ingredients).joinedload(RecipeVersionIngredient.ingredient),
        selectinload(RecipeVersion.steps)
    ).filter(
        RecipeVersion.recipe_id == recipe_id
    ).order_by(RecipeVersion.version.desc()).all()
    return versions

@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """删除配方"""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="配方不存在")
    
    db.delete(recipe)
    db.commit()
    return {"message": "配方已删除"}

@router.get("/export/{shop_id}")
def export_recipes(shop_id: str, db: Session = Depends(get_db)):
    """导出店铺的所有配方数据（JSON格式）"""
    # 获取店铺的所有配方
    recipes = db.query(Recipe).options(
        selectinload(Recipe.versions).selectinload(RecipeVersion.ingredients).joinedload(RecipeVersionIngredient.ingredient),
        selectinload(Recipe.versions).selectinload(RecipeVersion.steps),
        joinedload(Recipe.category)
    ).filter(Recipe.shop_id == shop_id).all()
    
    if not recipes:
        raise HTTPException(status_code=404, detail="没有找到配方数据")
    
    # 构建导出数据
    export_data = {
        "export_time": datetime.now().isoformat(),
        "shop_id": shop_id,
        "total_recipes": len(recipes),
        "recipes": []
    }
    
    for recipe in recipes:
        recipe_data = {
            "id": recipe.id,
            "name": recipe.current_name,
            "category": recipe.category.name if recipe.category else "未分类",
            "current_version": recipe.current_version,
            "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
            "updated_at": recipe.updated_at.isoformat() if recipe.updated_at else None,
            "versions": []
        }
        
        for version in recipe.versions:
            version_data = {
                "version": version.version,
                "name": version.name,
                "base_quantity": float(version.base_quantity) if version.base_quantity else None,
                "base_weight": float(version.base_weight) if version.base_weight else None,
                "total_calories": float(version.total_calories) if version.total_calories else None,
                "notes": version.notes,
                "calculation_rule": version.calculation_rule,
                "created_by": version.created_by,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "ingredients": [],
                "steps": []
            }
            
            # 添加原料
            for ing in version.ingredients:
                version_data["ingredients"].append({
                    "name": ing.ingredient.name,
                    "weight": float(ing.weight),
                    "unit": ing.ingredient.unit,
                    "calories_per_100g": float(ing.ingredient.calories_per_100g) if ing.ingredient.calories_per_100g else None,
                    "sort_order": ing.sort_order
                })
            
            # 添加步骤
            for step in version.steps:
                version_data["steps"].append({
                    "step_number": step.step_number,
                    "description": step.description,
                    "duration_minutes": step.duration_minutes,
                    "temperature": step.temperature
                })
            
            recipe_data["versions"].append(version_data)
        
        export_data["recipes"].append(recipe_data)
    
    # 返回JSON文件
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=recipes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )
