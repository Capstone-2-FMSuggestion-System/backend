import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình Cloudinary từ biến môi trường
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dgmdtzsya"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "396451297575275"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "ldDZdyY8Zo-xyWr9RuJ97OCqUl4"),
    secure=True
)

async def upload_image(file: UploadFile, folder: str = "data_fm") -> dict:
    """
    Tải lên hình ảnh lên Cloudinary
    
    Args:
        file (UploadFile): File hình ảnh cần tải lên
        folder (str): Thư mục lưu trữ trên Cloudinary
    
    Returns:
        dict: Thông tin về hình ảnh đã tải lên
    """
    # Đọc nội dung file
    contents = await file.read()
    
    # Tải lên Cloudinary
    upload_result = cloudinary.uploader.upload(
        contents,
        folder=folder,
        resource_type="image"
    )
    
    # Trả về kết quả
    return {
        "url": upload_result["secure_url"],
        "public_id": upload_result["public_id"],
        "width": upload_result["width"],
        "height": upload_result["height"],
        "format": upload_result["format"]
    }

async def delete_image(public_id: str) -> dict:
    """
    Xóa hình ảnh từ Cloudinary dựa trên public_id
    
    Args:
        public_id (str): Public ID của hình ảnh trên Cloudinary
    
    Returns:
        dict: Kết quả của việc xóa
    """
    # Xóa hình ảnh từ Cloudinary
    result = cloudinary.uploader.destroy(public_id)
    
    return result 