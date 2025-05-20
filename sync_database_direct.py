import os
import sys
import logging
import pymysql
from dotenv import load_dotenv

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load biến môi trường
load_dotenv()

# Lấy biến môi trường kết nối cơ sở dữ liệu
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306")) 
DB_NAME = os.getenv("DB_NAME", "family_menu_db")

def execute_sql(sql):
    """Thực thi câu lệnh SQL."""
    connection = None
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            connection.commit()
            
        return True, None
    except Exception as e:
        if connection:
            connection.rollback()
        return False, str(e)
    finally:
        if connection:
            connection.close()

def get_column_info(table_name):
    """Lấy thông tin cột của bảng."""
    connection = None
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
        return [col['Field'] for col in columns]
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin cột: {e}")
        return []
    finally:
        if connection:
            connection.close()

def add_columns_to_orders():
    """Thêm cột vào bảng orders nếu chưa tồn tại."""
    # Định nghĩa các cột cần thêm
    columns_to_add = [
        {"name": "shipping_address", "type": "VARCHAR(256)"},
        {"name": "shipping_city", "type": "VARCHAR(64)"},
        {"name": "shipping_province", "type": "VARCHAR(64)"},
        {"name": "shipping_postal_code", "type": "VARCHAR(16)"},
        {"name": "recipient_name", "type": "VARCHAR(128)"},
        {"name": "recipient_phone", "type": "VARCHAR(32)"}
    ]
    
    # Lấy danh sách cột hiện tại
    existing_columns = get_column_info("orders")
    logger.info(f"Các cột hiện có trong bảng orders: {existing_columns}")
    
    # Đếm số cột đã thêm
    columns_added = 0
    
    # Thêm từng cột nếu chưa tồn tại
    for column in columns_to_add:
        if column["name"] not in existing_columns:
            sql = f"ALTER TABLE orders ADD COLUMN {column['name']} {column['type']}"
            logger.info(f"Thêm cột {column['name']} với SQL: {sql}")
            
            success, error = execute_sql(sql)
            if success:
                columns_added += 1
                logger.info(f"Đã thêm cột {column['name']} vào bảng orders")
            else:
                logger.error(f"Lỗi khi thêm cột {column['name']}: {error}")
        else:
            logger.info(f"Cột {column['name']} đã tồn tại trong bảng orders")
    
    logger.info(f"Đã thêm {columns_added} cột mới vào bảng orders")

if __name__ == "__main__":
    logger.info("Bắt đầu cập nhật cấu trúc bảng orders...")
    add_columns_to_orders()
    logger.info("Hoàn tất cập nhật cấu trúc bảng orders") 