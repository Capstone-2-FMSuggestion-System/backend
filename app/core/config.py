import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Cấu hình logging sớm để thấy được output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tìm file .env
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    logger.info(f"Đang tải biến môi trường từ: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True) # override=True để đảm bảo .env ghi đè biến hệ thống
else:
    logger.warning(f"Không tìm thấy file .env tại: {env_path}")

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
CLOUDINARY_CLOUD_NAME_FROM_ENV = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY_FROM_ENV = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET_FROM_ENV = os.getenv("CLOUDINARY_API_SECRET")

logger.info(f"CLOUDINARY_CLOUD_NAME đọc từ env: {CLOUDINARY_CLOUD_NAME_FROM_ENV}")

CLOUDINARY_CLOUD_NAME = CLOUDINARY_CLOUD_NAME_FROM_ENV or "dkleeailh" # Fallback nếu env không có
CLOUDINARY_API_KEY = CLOUDINARY_API_KEY_FROM_ENV or "171326873511271"
CLOUDINARY_API_SECRET = CLOUDINARY_API_SECRET_FROM_ENV or "aIwwnuXsnlhQYM0VsavcR_l56kQ"

logger.info(f"CLOUDINARY_CLOUD_NAME sẽ sử dụng: {CLOUDINARY_CLOUD_NAME}")

# Không còn sử dụng upload_preset và folder
CLOUDINARY_UPLOAD_PRESET = None
CLOUDINARY_FOLDER = None 