from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'
    )
    
    # 数据库配置
    db_host: str = "47.109.97.153"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "Root@2025!"
    db_name: str = "baking_recipe_system"
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-this"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # 验证码配置
    captcha_expire_minutes: int = 5
    email_code_expire_minutes: int = 5
    email_code_length: int = 6
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # 文件上传配置
    upload_dir: str = "uploads"
    max_upload_size: int = 5242880  # 5MB

settings = Settings()
