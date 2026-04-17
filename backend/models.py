#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, Boolean, BigInteger
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# ==================== 用户认证系统模型 ====================

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(255))
    gender = Column(SQLEnum('male', 'female', 'other', name='gender_enum'))
    shop_id = Column(String(36), ForeignKey('shops.id'))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    shop = relationship("Shop", foreign_keys=[shop_id])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    login_logs = relationship("LoginLog", back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="refresh_tokens")


class LoginLog(Base):
    __tablename__ = "login_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'))
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    login_status = Column(SQLEnum('success', 'failed', name='login_status_enum'), nullable=False)
    fail_reason = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="login_logs")

# ==================== 配方系统模型 ====================

class Shop(Base):
    __tablename__ = "shops"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    owner_name = Column(String(50))
    contact_phone = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    recipes = relationship("Recipe", back_populates="shop")


class RecipeCategory(Base):
    __tablename__ = "recipe_categories"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    recipes = relationship("Recipe", back_populates="category")


class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), ForeignKey('shops.id'), nullable=False)
    category_id = Column(String(36), ForeignKey('recipe_categories.id'), nullable=False)
    current_name = Column(String(100), nullable=False)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    shop = relationship("Shop", back_populates="recipes")
    category = relationship("RecipeCategory", back_populates="recipes")
    versions = relationship("RecipeVersion", back_populates="recipe", cascade="all, delete-orphan")


class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    
    id = Column(String(36), primary_key=True)
    recipe_id = Column(String(36), ForeignKey('recipes.id'), nullable=False)
    version = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    base_quantity = Column(DECIMAL(10, 2))
    base_weight = Column(DECIMAL(10, 2))
    total_calories = Column(DECIMAL(10, 2))
    notes = Column(Text)
    calculation_rule = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    
    recipe = relationship("Recipe", back_populates="versions")
    ingredients = relationship("RecipeVersionIngredient", back_populates="recipe_version", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="recipe_version", cascade="all, delete-orphan")


class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    unit = Column(String(10), default='g')
    calories_per_100g = Column(DECIMAL(10, 2))
    protein_per_100g = Column(DECIMAL(10, 2))
    fat_per_100g = Column(DECIMAL(10, 2))
    carbs_per_100g = Column(DECIMAL(10, 2))
    created_at = Column(DateTime, server_default=func.now())
    
    recipe_ingredients = relationship("RecipeVersionIngredient", back_populates="ingredient")


class RecipeVersionIngredient(Base):
    __tablename__ = "recipe_version_ingredients"
    
    id = Column(String(36), primary_key=True)
    recipe_version_id = Column(String(36), ForeignKey('recipe_versions.id'), nullable=False)
    ingredient_id = Column(String(36), ForeignKey('ingredients.id'), nullable=False)
    weight = Column(DECIMAL(10, 2), nullable=False)
    sort_order = Column(Integer, default=0)
    
    recipe_version = relationship("RecipeVersion", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")


class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    
    id = Column(String(36), primary_key=True)
    recipe_version_id = Column(String(36), ForeignKey('recipe_versions.id'), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    duration_minutes = Column(Integer)
    temperature = Column(Integer)
    
    recipe_version = relationship("RecipeVersion", back_populates="steps")


# ==================== 黑名单系统模型 ====================

# 风险等级枚举
class RiskLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# 黑名单类型枚举
class BlacklistType(str, enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"


# 推送申请状态枚举
class PushRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# 通知类型枚举
class NotificationType(str, enum.Enum):
    PUSH_APPROVED = "PUSH_APPROVED"
    PUSH_REJECTED = "PUSH_REJECTED"


class Blacklist(Base):
    __tablename__ = "blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(String(36), nullable=False, index=True)
    new_id = Column(String(20), unique=True, index=True)
    ktt_name = Column(String(100))
    wechat_name = Column(String(100))
    wechat_id = Column(String(100))
    order_name_phone = Column(String(200))
    phone_numbers = Column(JSON)
    order_address1 = Column(Text)
    order_address2 = Column(Text)
    blacklist_reason = Column(Text)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    created_by = Column(String(36))
    blacklist_type = Column(SQLEnum(BlacklistType), default=BlacklistType.USER, nullable=False)
    owner_id = Column(String(36), nullable=True)
    source_push_request_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PushRequest(Base):
    __tablename__ = "push_requests"

    id = Column(Integer, primary_key=True)
    blacklist_id = Column(Integer, ForeignKey('blacklist.id'), nullable=False)
    applicant_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    evidence = Column(Text, nullable=False)
    status = Column(SQLEnum(PushRequestStatus), default=PushRequestStatus.PENDING, nullable=False)
    reject_reason = Column(Text, nullable=True)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    blacklist_entry = relationship("Blacklist")
    applicant = relationship("User", foreign_keys=[applicant_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    push_request_id = Column(Integer, ForeignKey('push_requests.id'), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    push_request = relationship("PushRequest")


# ==================== 订单检查系统模型 ====================

class OrderScreeningRecord(Base):
    __tablename__ = "order_screening_records"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(String(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    total_orders = Column(Integer, default=0)
    matched_count = Column(Integer, default=0)
    screening_time = Column(DateTime, server_default=func.now(), index=True)
    created_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联详情
    details = relationship("OrderScreeningDetail", back_populates="record", cascade="all, delete-orphan")


class OrderScreeningDetail(Base):
    __tablename__ = "order_screening_details"
    
    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(Integer, ForeignKey('order_screening_records.id'), nullable=False, index=True)
    order_name = Column(String(100))
    order_phone = Column(String(20))
    order_address = Column(Text)
    order_data = Column(JSON)
    blacklist_id = Column(Integer, ForeignKey('blacklist.id'), nullable=False, index=True)
    match_type = Column(String(20), nullable=False)
    match_value = Column(String(255))
    risk_level = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联
    record = relationship("OrderScreeningRecord", back_populates="details")
    blacklist = relationship("Blacklist")


# ==================== 订单数据处理记录模型 ====================

class OrderProcessRecord(Base):
    __tablename__ = "order_process_records"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(String(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    group_nos = Column(JSON)           # 本次处理的跟团号列表
    total_orders = Column(Integer, default=0)   # 过滤后订单数
    product_types = Column(Integer, default=0)  # 商品种类数
    summary = Column(JSON)             # 数量汇总摘要（前10条）
    created_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), index=True)
