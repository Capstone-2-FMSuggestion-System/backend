import redis.asyncio as redis
from dotenv import load_dotenv
import os

load_dotenv()
redis_client = redis.from_url(os.getenv("REDIS_URL"))

async def set_cache(key: str, value, expire: int = 300):
    """
    Tên Function: set_cache
    
    1. Mô tả ngắn gọn:
    Lưu giá trị vào Redis cache với thời gian hết hạn.
    
    2. Mô tả công dụng:
    Lưu trữ dữ liệu vào Redis cache với một khóa xác định và thời gian tồn tại.
    Hữu ích cho việc cache tạm thời các dữ liệu thường xuyên truy cập.
    
    3. Các tham số đầu vào:
    - key (str): Khóa để lưu trữ giá trị trong cache
    - value (any): Giá trị cần lưu trữ (sẽ được chuyển đổi thành chuỗi)
    - expire (int, optional): Thời gian hết hạn tính bằng giây (mặc định: 300 giây)
    
    4. Giá trị trả về:
    - None: Function này không trả về giá trị
    
    5. Ví dụ sử dụng:
    >>> await set_cache("user_123", user_data, 600)  # Cache trong 10 phút
    """
    await redis_client.setex(key, expire, str(value))

async def get_cache(key: str):
    """
    Tên Function: get_cache
    
    1. Mô tả ngắn gọn:
    Lấy giá trị từ Redis cache theo khóa.
    
    2. Mô tả công dụng:
    Truy xuất dữ liệu đã được lưu trữ trong Redis cache bằng khóa.
    Giúp tối ưu hiệu suất bằng cách lấy dữ liệu từ cache thay vì truy vấn database.
    
    3. Các tham số đầu vào:
    - key (str): Khóa để tìm kiếm giá trị trong cache
    
    4. Giá trị trả về:
    - str/None: Giá trị được lưu trữ dưới dạng chuỗi nếu tồn tại, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> cached_data = await get_cache("user_123")
    >>> if cached_data:
    >>>     return json.loads(cached_data)
    """
    return await redis_client.get(key)