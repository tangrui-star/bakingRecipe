"""用户认证路由"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import uuid

from database import get_db
from models import User, Shop, RefreshToken, LoginLog
from schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    EmailCodeRequest, PasswordChangeRequest, PasswordResetRequest,
    UserUpdate
)
from auth_utils import (
    get_password_hash, verify_password, validate_password_strength,
    validate_email, validate_phone, validate_username,
    create_access_token, create_refresh_token, decode_token
)
from captcha_utils import captcha_manager, email_code_manager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get('type') != 'access':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌数据"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

@router.get("/captcha")
def get_captcha():
    """获取图片验证码"""
    captcha_id, image_bytes = captcha_manager.generate_captcha()
    
    return StreamingResponse(
        image_bytes,
        media_type="image/png",
        headers={"X-Captcha-ID": captcha_id}
    )

@router.post("/email-code")
def send_email_code(request: EmailCodeRequest, db: Session = Depends(get_db)):
    """发送邮箱验证码"""
    # 验证图片验证码（不删除，允许后续注册时再次验证）
    success, message = captcha_manager.verify_captcha(request.captcha_id, request.captcha_code, delete_after_verify=False)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    # 验证邮箱格式
    if not validate_email(request.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    # 检查邮箱是否已注册
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    # 生成验证码
    from captcha_utils import email_code_manager
    from email_utils import send_verification_email
    code = email_code_manager.generate_code(request.email)

    # 发送邮件
    ok, err = send_verification_email(request.email, code, expire_minutes=5)
    if not ok:
        raise HTTPException(status_code=500, detail=err)

    return {
        "message": "验证码已发送到您的邮箱，请注意查收",
        "email": request.email,
        "expires_in": 300
    }

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """用户注册"""
    # 1. 验证图片验证码（验证成功后删除）
    success, message = captcha_manager.verify_captcha(user_data.captcha_id, user_data.captcha_code, delete_after_verify=True)
    if not success:
        raise HTTPException(status_code=400, detail=f"图片验证码错误: {message}")
    
    # 2. 验证邮箱验证码
    success, message = email_code_manager.verify_code(user_data.email, user_data.email_code)
    if not success:
        raise HTTPException(status_code=400, detail=f"邮箱验证码错误: {message}")
    
    # 3. 验证用户名
    valid, msg = validate_username(user_data.username)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    # 4. 验证邮箱格式
    if not validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 5. 验证手机号格式
    if user_data.phone and not validate_phone(user_data.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 6. 验证密码强度
    valid, msg = validate_password_strength(user_data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    # 7. 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已被使用")
    
    # 8. 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 9. 自动创建店铺（每个用户都有自己的店铺）
    shop_name = user_data.shop_name if user_data.shop_name else f"{user_data.username}的烘焙店"
    shop = Shop(
        id=str(uuid.uuid4()),
        name=shop_name,
        owner_name=user_data.username
    )
    db.add(shop)
    db.flush()
    shop_id = shop.id
    
    # 10. 创建用户
    user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        gender=user_data.gender,
        shop_id=shop_id,
        is_active=True,
        is_verified=True,  # 邮箱验证码验证通过即认为已验证
        last_login=datetime.utcnow()
    )
    db.add(user)
    
    # 11. 创建刷新令牌
    refresh_token_str = create_refresh_token({"sub": user.id})
    refresh_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(refresh_token)
    
    # 12. 记录登录日志
    login_log = LoginLog(
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent', ''),
        login_status='success'
    )
    db.add(login_log)
    
    db.commit()
    db.refresh(user)
    
    # 13. 生成访问令牌
    access_token = create_access_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """用户登录"""
    import logging
    logger = logging.getLogger("auth.login")

    client_ip = request.client.host if request.client else "unknown"
    logger.warning(f"[LOGIN] ===== 登录请求开始 =====")
    logger.warning(f"[LOGIN] 来源IP: {client_ip}")
    logger.warning(f"[LOGIN] 用户名/邮箱: {login_data.username_or_email}")
    logger.warning(f"[LOGIN] captcha_id: {login_data.captcha_id}")
    logger.warning(f"[LOGIN] captcha_code: {login_data.captcha_code}")
    logger.warning(f"[LOGIN] password长度: {len(login_data.password) if login_data.password else 0}")

    # 1. 验证图片验证码（验证成功后删除）
    # 如果是滑动验证通过的登录，captcha_id='slider'，直接跳过图片验证码校验
    if login_data.captcha_id != 'slider':
        success, message = captcha_manager.verify_captcha(login_data.captcha_id, login_data.captcha_code, delete_after_verify=True)
        logger.warning(f"[LOGIN] 步骤1 验证码校验: success={success}, message={message}")
        if not success:
            raise HTTPException(status_code=400, detail=f"验证码错误: {message}")
    else:
        logger.warning(f"[LOGIN] 步骤1 滑动验证通过，跳过图片验证码")

    # 2. 查找用户（支持用户名或邮箱登录）
    user = db.query(User).filter(
        (User.username == login_data.username_or_email) |
        (User.email == login_data.username_or_email)
    ).first()
    logger.warning(f"[LOGIN] 步骤2 查找用户: {'找到' if user else '未找到'}")

    # 记录登录日志
    def log_login(user_id: Optional[str], status: str, reason: Optional[str] = None):
        log = LoginLog(
            user_id=user_id,
            ip_address=client_ip,
            user_agent=request.headers.get('user-agent', ''),
            login_status=status,
            fail_reason=reason
        )
        db.add(log)
        db.commit()

    if not user:
        logger.warning(f"[LOGIN] 失败原因: 用户不存在 - {login_data.username_or_email}")
        log_login(None, 'failed', '用户不存在')
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 3. 验证密码
    pwd_ok = verify_password(login_data.password, user.password_hash)
    logger.warning(f"[LOGIN] 步骤3 密码校验: {'通过' if pwd_ok else '失败'}")
    if not pwd_ok:
        log_login(user.id, 'failed', '密码错误')
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 4. 检查用户状态
    logger.warning(f"[LOGIN] 步骤4 用户状态: is_active={user.is_active}")
    if not user.is_active:
        log_login(user.id, 'failed', '用户已被禁用')
        raise HTTPException(status_code=403, detail="用户已被禁用")
    
    # 5. 更新最后登录时间
    user.last_login = datetime.utcnow()
    
    # 6. 创建刷新令牌
    refresh_token_str = create_refresh_token({"sub": user.id})
    refresh_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(refresh_token)
    
    # 7. 记录成功登录
    log_login(user.id, 'success')
    
    db.commit()
    db.refresh(user)
    
    # 8. 生成访问令牌
    access_token = create_access_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """用户登出"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload and payload.get('sub'):
        user_id = payload['sub']
        # 删除该用户的所有刷新令牌
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
        db.commit()
    
    return {"message": "登出成功"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 验证用户名
    if user_update.username:
        valid, msg = validate_username(user_update.username)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)
        
        # 检查用户名是否已被使用
        existing = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已被使用")
        
        current_user.username = user_update.username
    
    # 验证手机号
    if user_update.phone:
        if not validate_phone(user_update.phone):
            raise HTTPException(status_code=400, detail="手机号格式不正确")
        current_user.phone = user_update.phone
    
    # 更新其他字段
    if user_update.gender:
        current_user.gender = user_update.gender
    
    if user_update.avatar:
        current_user.avatar = user_update.avatar
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    # 验证新密码强度
    valid, msg = validate_password_strength(password_data.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    
    # 删除所有刷新令牌（强制重新登录）
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    
    db.commit()
    
    return {"message": "密码修改成功，请重新登录"}

@router.post("/refresh-token", response_model=TokenResponse)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    # 验证刷新令牌
    payload = decode_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌数据")
    
    # 检查刷新令牌是否存在且未过期
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not token_record:
        raise HTTPException(status_code=401, detail="刷新令牌已过期或不存在")
    
    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    
    # 生成新的访问令牌
    access_token = create_access_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )
