import logging
from typing import List, Optional
from .cache import redis_client

logger = logging.getLogger(__name__)

async def invalidate_dashboard_cache():
    """
    Hàm này vô hiệu hóa (xóa) tất cả các cache liên quan đến dashboard
    để đảm bảo API dashboard luôn trả về dữ liệu mới nhất.
    """
    patterns = [
        "dashboard:stats",
        "dashboard:recent_orders:*",
        "dashboard:revenue:*"
    ]
    
    try:
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    logger.info(f"Invalidating {len(keys)} cache keys matching pattern: {pattern}")
                    await redis_client.delete(*keys)
                if cursor == 0:
                    break
        logger.info("Dashboard cache invalidated successfully")
        return True
    except Exception as e:
        logger.error(f"Error invalidating dashboard cache: {str(e)}")
        return False

async def invalidate_specific_cache(cache_keys: List[str]):
    """
    Hàm này vô hiệu hóa các cache key cụ thể được truyền vào.
    
    Args:
        cache_keys: Danh sách các cache key cần xóa
    """
    try:
        if cache_keys:
            await redis_client.delete(*cache_keys)
            logger.info(f"Invalidated specific cache keys: {cache_keys}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating specific cache keys: {str(e)}")
        return False