import os
import sys
import logging
import shutil
import re
from pathlib import Path

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def remove_zalopay_references():
    """Xóa các tham chiếu đến ZaloPay trong mã nguồn"""
    # Xóa file ZaloPay
    zalopay_file = Path('app/payment/zalopay.py')
    if zalopay_file.exists():
        zalopay_file.unlink()
        logger.info(f"Đã xóa file: {zalopay_file}")
    
    # Tìm và xóa các biến môi trường ZaloPay
    env_file = Path('.env')
    env_example_file = Path('.env.example')
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Xóa các dòng ZaloPay
        new_env_content = re.sub(r'# ZaloPay Integration.*?(?=\n\n|\n#|$)', '', env_content, flags=re.DOTALL)
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(new_env_content)
        logger.info("Đã xóa biến môi trường ZaloPay từ .env")
    
    if env_example_file.exists():
        with open(env_example_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Xóa các dòng ZaloPay
        new_env_content = re.sub(r'# ZaloPay Integration.*?(?=\n\n|\n#|$)', '', env_content, flags=re.DOTALL)
        
        with open(env_example_file, 'w', encoding='utf-8') as f:
            f.write(new_env_content)
        logger.info("Đã xóa biến môi trường ZaloPay từ .env.example")
    
    # Cập nhật routes.py để xóa code ZaloPay
    update_payment_routes()
    
    # Cập nhật __init__.py để xóa import liên quan đến ZaloPay
    update_payment_init()
    
    logger.info("Đã hoàn thành việc xóa các tham chiếu đến ZaloPay")

def update_payment_routes():
    """Cập nhật file routes.py để xóa code ZaloPay và chỉ sử dụng PayOS"""
    routes_file = Path('app/payment/routes.py')
    
    if not routes_file.exists():
        logger.error(f"Không tìm thấy file {routes_file}")
        return
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Xóa các import zalopay
    content = re.sub(r'from \. import zalopay.*?\n', '', content)
    content = re.sub(r'import zalopay.*?\n', '', content)
    
    # Xóa các route zalopay
    content = re.sub(r'@router\.post\("/zalopay/create"\).*?(?=@router|$)', '', content, flags=re.DOTALL)
    content = re.sub(r'@router\.post\("/zalopay/callback"\).*?(?=@router|$)', '', content, flags=re.DOTALL)
    content = re.sub(r'@router\.get\("/zalopay/status.*?(?=@router|$)', '', content, flags=re.DOTALL)
    
    # Cập nhật payment methods để loại bỏ ZaloPay
    content = re.sub(r'\{\s*"id":\s*"zalopay".*?\},', '', content, flags=re.DOTALL)
    
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Đã cập nhật {routes_file} để xóa code ZaloPay")

def update_payment_init():
    """Cập nhật file __init__.py để xóa import liên quan đến ZaloPay"""
    init_file = Path('app/payment/__init__.py')
    
    if not init_file.exists():
        logger.error(f"Không tìm thấy file {init_file}")
        return
    
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Xóa các import zalopay
    content = re.sub(r'from \. import zalopay.*?\n', '', content)
    content = re.sub(r'import zalopay.*?\n', '', content)
    
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Đã cập nhật {init_file} để xóa import liên quan đến ZaloPay")

def run_migration():
    """Chạy quy trình di chuyển từ ZaloPay sang PayOS"""
    logger.info("Bắt đầu quy trình chuyển đổi từ ZaloPay sang PayOS...")
    
    # Xóa các tham chiếu đến ZaloPay
    remove_zalopay_references()
    
    # Tạo backup của .env
    try:
        shutil.copy('.env', '.env.backup')
        logger.info("Đã tạo backup .env -> .env.backup")
    except Exception as e:
        logger.error(f"Không thể tạo backup .env: {e}")
    
    logger.info("Quá trình chuyển đổi sang PayOS đã hoàn tất!")

if __name__ == "__main__":
    run_migration() 