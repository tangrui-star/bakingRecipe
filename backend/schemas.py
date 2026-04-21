from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# 原料相关
class IngredientBase(BaseModel):
    name: str
    unit: str = "g"
    calories_per_100g: Optional[Decimal] = None
    protein_per_100g: Optional[Decimal] = None
    fat_per_100g: Optional[Decimal] = None
    carbs_per_100g: Optional[Decimal] = None

class IngredientCreate(IngredientBase):
    pass

class Ingredient(IngredientBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 配方版本原料
class RecipeIngredientBase(BaseModel):
    ingredient_id: str
    weight: Decimal
    sort_order: Optional[int] = 0

class RecipeIngredientCreate(RecipeIngredientBase):
    pass

class RecipeIngredient(RecipeIngredientBase):
    id: str
    ingredient: Ingredient
    
    class Config:
        from_attributes = True

# 制作步骤
class RecipeStepBase(BaseModel):
    step_number: int
    description: str
    duration_minutes: Optional[int] = None
    temperature: Optional[int] = None

class RecipeStepCreate(RecipeStepBase):
    pass

class RecipeStep(RecipeStepBase):
    id: str
    
    class Config:
        from_attributes = True

# 配方版本
class RecipeVersionBase(BaseModel):
    name: str
    base_quantity: Optional[Decimal] = None
    base_weight: Optional[Decimal] = None
    notes: Optional[str] = None
    calculation_rule: Optional[str] = None
    created_by: Optional[str] = None

class RecipeVersionCreate(RecipeVersionBase):
    ingredients: List[RecipeIngredientCreate] = []
    steps: List[RecipeStepCreate] = []

class RecipeVersion(RecipeVersionBase):
    id: str
    recipe_id: str
    version: int
    total_calories: Optional[Decimal] = None
    created_at: datetime
    ingredients: List[RecipeIngredient] = []
    steps: List[RecipeStep] = []
    
    class Config:
        from_attributes = True

# 配方
class RecipeBase(BaseModel):
    category_id: str
    current_name: str

class RecipeCreate(RecipeBase):
    shop_id: str
    version_data: RecipeVersionCreate

class Recipe(RecipeBase):
    id: str
    shop_id: str
    current_version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RecipeDetail(Recipe):
    versions: List[RecipeVersion] = []

# 品类
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 店铺
class ShopBase(BaseModel):
    name: str
    owner_name: Optional[str] = None
    contact_phone: Optional[str] = None

class ShopCreate(ShopBase):
    pass

class Shop(ShopBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 配方计算请求
class RecipeCalculateRequest(BaseModel):
    recipe_id: str
    target_quantity: int = Field(..., description="目标数量")

class RecipeCalculateResponse(BaseModel):
    recipe_name: str
    target_quantity: int
    ingredients: List[dict]
    total_calories: Decimal


# 用户认证相关
class UserBase(BaseModel):
    username: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    gender: Optional[str] = None
    shop_name: Optional[str] = None
    email_code: str = Field(..., min_length=6, max_length=6)
    captcha_id: str
    captcha_code: str = Field(..., min_length=4, max_length=4)

class UserLogin(BaseModel):
    username_or_email: str
    password: str
    captcha_id: str
    captcha_code: str = Field(..., min_length=4)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    shop_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class EmailCodeRequest(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    captcha_id: str
    captcha_code: str = Field(..., min_length=4, max_length=4)

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class PasswordResetRequest(BaseModel):
    email: str
    email_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
    captcha_id: str
    captcha_code: str = Field(..., min_length=4, max_length=4)


# 黑名单相关
class BlacklistBase(BaseModel):
    ktt_name: Optional[str] = None
    wechat_name: Optional[str] = None
    wechat_id: Optional[str] = None
    order_name_phone: Optional[str] = None
    phone_numbers: Optional[List[str]] = None
    order_address1: Optional[str] = None
    order_address2: Optional[str] = None
    blacklist_reason: Optional[str] = None
    risk_level: str = "MEDIUM"  # HIGH, MEDIUM, LOW

class BlacklistCreate(BlacklistBase):
    shop_id: str

class BlacklistUpdate(BlacklistBase):
    pass

class BlacklistResponse(BlacklistBase):
    id: int
    shop_id: str
    new_id: Optional[str] = None
    phone_numbers: Optional[List[str]] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BlacklistListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BlacklistResponse]
