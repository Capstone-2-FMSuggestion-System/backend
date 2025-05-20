import os
import sys
import importlib
import logging
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from dotenv import load_dotenv

# Thiết lập logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Đặt PYTHONPATH để script có thể tìm thấy các module trong 'app'
# Điều này quan trọng khi chạy script từ thư mục gốc của project
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Tải biến môi trường từ file .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    logger.error("Một hoặc nhiều biến môi trường cho database chưa được cấu hình.")
    sys.exit(1)

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Sử dụng một engine thực sự để compile DDL cho MySQL
# Engine này không cần kết nối tới DB, chỉ cần dialect
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", echo=False)

def get_all_metadata():
    """Import tất cả models và trả về Base.metadata."""
    try:
        # Import Base từ app.core.database
        core_database_module = importlib.import_module("app.core.database")
        Base = getattr(core_database_module, "Base")
    except ImportError as e:
        logger.error(f"Không thể import Base từ app.core.database: {e}")
        sys.exit(1)
    except AttributeError:
        logger.error("Không tìm thấy 'Base' trong app.core.database.")
        sys.exit(1)

    # Danh sách các module chứa model
    # (Dựa trên cấu trúc thư mục bạn cung cấp)
    model_modules_paths = [
        'app.user.models',
        'app.auth.models', # auth.models có thể chỉ import từ user.models
        'app.payment.models',
        'app.e_commerce.models',
        'app.inventory.models',
        'app.admin.models' # admin.models có thể chỉ import từ các models khác
    ]

    for module_path in model_modules_paths:
        try:
            importlib.import_module(module_path)
            logger.info(f"Đã import thành công models từ: {module_path}")
        except ImportError as e:
            # Một số module model có thể không tồn tại hoặc chỉ là re-export, nên cảnh báo thay vì thoát
            logger.warning(f"Không thể import models từ {module_path}: {e}. Có thể module này không chứa model trực tiếp.")
        except Exception as e:
            logger.error(f"Lỗi không xác định khi import {module_path}: {e}")


    return Base.metadata

def generate_sql_schema(output_file="database_schema.sql"):
    """Tạo file SQL schema từ metadata."""
    metadata = get_all_metadata()
    
    if not metadata.tables:
        logger.error("Không tìm thấy bảng nào trong metadata. Kiểm tra lại việc import models.")
        return

    sql_statements = []

    # Câu lệnh tạo database và sử dụng database
    sql_statements.append(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    sql_statements.append(f"USE `{DB_NAME}`;")
    sql_statements.append("\n-- Disable foreign key checks for initial table creation")
    sql_statements.append("SET FOREIGN_KEY_CHECKS=0;")
    sql_statements.append("\n")


    # Câu lệnh tạo bảng
    logger.info(f"Tổng số bảng tìm thấy trong metadata: {len(metadata.tables)}")
    
    # Sắp xếp bảng để đảm bảo các bảng tham chiếu được tạo trước
    # metadata.sorted_tables đã tự động xử lý việc này
    for table in metadata.sorted_tables:
        try:
            logger.info(f"Đang tạo DDL cho bảng: {table.name}")
            create_table_sql = str(CreateTable(table).compile(engine)).strip()
            sql_statements.append(f"{create_table_sql};\n")
        except Exception as e:
            logger.error(f"Lỗi khi tạo DDL cho bảng {table.name}: {e}")
            
    sql_statements.append("\n-- Enable foreign key checks")
    sql_statements.append("SET FOREIGN_KEY_CHECKS=1;")


    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for stmt in sql_statements:
                f.write(stmt + "\n")
        logger.info(f"Đã tạo thành công file schema SQL: {output_file}")
    except IOError as e:
        logger.error(f"Không thể ghi vào file {output_file}: {e}")

if __name__ == "__main__":
    logger.info("Bắt đầu quá trình tạo SQL schema...")
    generate_sql_schema()
    logger.info("Hoàn tất quá trình tạo SQL schema.") 