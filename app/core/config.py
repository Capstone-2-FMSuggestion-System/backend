from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # PayOS settings
    PAYOS_CLIENT_ID: str = os.getenv("PAYOS_CLIENT_ID", "")
    PAYOS_API_KEY: str = os.getenv("PAYOS_API_KEY", "")
    PAYOS_CHECKSUM_KEY: str = os.getenv("PAYOS_CHECKSUM_KEY", "")
    PAYOS_CALLBACK_URL: str = os.getenv("PAYOS_CALLBACK_URL", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

# Tìm file .env
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Cấu hình cơ bản
SECRET_KEY = os.getenv("SECRET_KEY")
API_PREFIX = os.getenv("API_PREFIX", "/api")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Cấu hình database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fmshop")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Cấu hình Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = os.getenv("REDIS_URL", f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Cấu hình JWT
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Cấu hình Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "dgmdtzsya")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "396451297575275")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "ldDZdyY8Zo-xyWr9RuJ97OCqUl4")
# Không sử dụng upload_preset để tránh lỗi "Upload preset not found"
CLOUDINARY_UPLOAD_PRESET = None  # Không dùng upload_preset
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "fm_products") 