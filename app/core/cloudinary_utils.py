import cloudinary
import cloudinary.uploader
import cloudinary.api
import re
import aiofiles
import os
import tempfile
from fastapi import UploadFile
from typing import List, Optional
from . import config

# Cấu hình Cloudinary từ file config
cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET
)

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
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    
    try:
        # Đọc và ghi vào temporary file
        async with aiofiles.open(temp_file.name, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Upload lên Cloudinary
        upload_folder = folder or config.CLOUDINARY_FOLDER
        upload_result = cloudinary.uploader.upload(
            temp_file.name,
            folder=upload_folder,
            public_id=os.path.splitext(safe_filename)[0],
            overwrite=True,
            resource_type="image",
            unique_filename=True
        )
        
        return {
            "public_id": upload_result["public_id"],
            "url": upload_result["url"],
            "secure_url": upload_result["secure_url"],
            "format": upload_result["format"],
            "width": upload_result["width"],
            "height": upload_result["height"],
            "bytes": upload_result["bytes"]
        }
    finally:
        # Dọn dẹp temporary file
        temp_file.close()
        os.unlink(temp_file.name)
        
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