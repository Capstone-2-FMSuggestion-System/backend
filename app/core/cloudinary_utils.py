import cloudinary
import cloudinary.uploader
import cloudinary.api
import re
import aiofiles
import os
import tempfile
import logging
from fastapi import UploadFile
from typing import List, Optional
from . import config

# Cấu hình logging
logger = logging.getLogger(__name__)

# Hàm để tạo cấu hình Cloudinary mỗi khi cần thiết
def get_cloudinary_config():
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET
    )
    return cloudinary.config()

# Đảm bảo cấu hình ban đầu được thiết lập
get_cloudinary_config()

async def upload_image(file: UploadFile, folder: Optional[str] = None) -> dict:
    """
    Upload một hình ảnh lên Cloudinary
    
    Args:
        file (UploadFile): File ảnh cần upload
        folder (str, optional): Thư mục lưu trữ
        
    Returns:
        dict: Kết quả từ Cloudinary
    """
    # Kiểm tra kiểu file
    if not file.content_type.startswith('image/'):
        raise ValueError("Chỉ chấp nhận file hình ảnh (image/*)")
    
    # Tạo tên file an toàn
    filename = file.filename
    safe_filename = re.sub(r'[^\w\-\.]', '-', filename)
    
    # Tạo temporary file
    temp_file = None
    
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        # Đọc và ghi vào temporary file
        try:
            content = await file.read()
            with open(temp_file.name, 'wb') as out_file:
                out_file.write(content)
        except Exception as e:
            raise ValueError(f"Lỗi khi đọc/ghi file tạm: {str(e)}")
        
        # Tạo lại cấu hình Cloudinary mỗi khi upload để đảm bảo kết nối
        cloud_config = get_cloudinary_config()
        
        # Upload lên Cloudinary
        try:
            logger.info(f"Uploading image to Cloudinary: {safe_filename} to folder {folder}")
            # Log cấu hình Cloudinary để debug
            logger.info(f"Cloudinary config: cloud_name={cloud_config.cloud_name}, api_key={cloud_config.api_key[:6]}...")
            
            # Không dùng upload_preset vì gây lỗi "Upload preset not found"
            upload_result = cloudinary.uploader.upload(
                temp_file.name,
                folder=folder,  # Sử dụng folder trực tiếp từ tham số
                public_id=os.path.splitext(safe_filename)[0],
                overwrite=True,
                resource_type="image",
                unique_filename=True
            )
            
            logger.info(f"Upload successful: {upload_result.get('public_id', 'unknown')}")
            return {
                "public_id": upload_result["public_id"],
                "url": upload_result["url"],
                "secure_url": upload_result["secure_url"],
                "format": upload_result["format"],
                "width": upload_result["width"],
                "height": upload_result["height"],
                "bytes": upload_result["bytes"]
            }
        except Exception as e:
            logger.error(f"Error uploading to Cloudinary: {str(e)}")
            raise ValueError(f"Lỗi khi upload lên Cloudinary: {str(e)}")
    finally:
        # Dọn dẹp temporary file
        if temp_file:
            temp_file.close()
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
async def upload_multiple_images(files: List[UploadFile], folder: Optional[str] = None) -> List[dict]:
    """
    Upload nhiều hình ảnh lên Cloudinary
    
    Args:
        files (List[UploadFile]): Danh sách file cần upload
        folder (str, optional): Thư mục lưu trữ
        
    Returns:
        List[dict]: Danh sách kết quả upload
    """
    results = []
    for file in files:
        result = await upload_image(file, folder)
        results.append(result)
    return results

async def delete_image(public_id: str) -> dict:
    """
    Xóa một hình ảnh từ Cloudinary bằng public_id
    
    Args:
        public_id (str): Public ID của hình ảnh cần xóa
        
    Returns:
        dict: Kết quả từ Cloudinary
    """
    result = cloudinary.uploader.destroy(public_id)
    return {
        "public_id": public_id,
        "result": result.get("result", "unknown"),
        "status": "success" if result.get("result") == "ok" else "error"
    }

def extract_public_id_from_url(url: str) -> Optional[str]:
    """
    Trích xuất public_id từ URL của Cloudinary
    
    Args:
        url (str): URL của hình ảnh Cloudinary
        
    Returns:
        Optional[str]: Public ID hoặc None nếu không tìm thấy
    """
    # URL mẫu: https://res.cloudinary.com/{cloud_name}/image/upload/v{version}/{folder}/{public_id}.{format}
    if not url or "cloudinary.com" not in url:
        return None
    
    # Sử dụng regex để tìm public_id
    match = re.search(r'upload/v\d+/(.+?)(?:\.[a-zA-Z0-9]+)?$', url)
    if match:
        return match.group(1)
    
    return None 