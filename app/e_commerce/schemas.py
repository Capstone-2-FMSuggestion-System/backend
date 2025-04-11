# Đây là file schemas.py cho module e_commerce
# Định nghĩa trực tiếp các schema thay vì import từ schemas.py gốc

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: int
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int
    
    class Config:
        from_attributes = True

class CategoryWithSubcategories(CategoryResponse):
    subcategories: List['CategoryWithSubcategories'] = []
    
    class Config:
        from_attributes = True

class MainCategoryResponse(CategoryResponse):
    subcategories: List[CategoryResponse] = []
    
    class Config:
        from_attributes = True

class ProductImageBase(BaseModel):
    image_url: str
    is_primary: Optional[bool] = False
    display_order: Optional[int] = 0

class ProductImageCreate(ProductImageBase):
    product_id: int

class ProductImageUpdate(BaseModel):
    image_url: Optional[str] = None
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None

class ProductImageResponse(ProductImageBase):
    image_id: int
    product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    unit: Optional[str] = None
    stock_quantity: Optional[int] = 0
    is_featured: Optional[bool] = False

class ProductCreate(ProductBase):
    images: Optional[List[ProductImageBase]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    unit: Optional[str] = None
    stock_quantity: Optional[int] = None
    is_featured: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int
    created_at: datetime
    images: List[ProductImageResponse] = []
    
    class Config:
        from_attributes = True

class ProductDiscountResponse(ProductResponse):
    discount_price: Optional[float] = None
    
    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    user_id: int

class CartItem(CartItemBase):
    cart_item_id: int
    user_id: int
    added_at: datetime
    product: Optional[ProductResponse] = None
    
    class Config:
        from_attributes = True

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderBase(BaseModel):
    user_id: int
    total_amount: float
    payment_method: Optional[str] = None
    status: str = "pending"

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]
    cart_items: Optional[List[CartItemBase]] = []

class OrderItemResponse(OrderItemBase):
    order_item_id: int
    order_id: int
    product: Optional[ProductResponse] = None
    
    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    order_id: int
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True

class MenuBase(BaseModel):
    name: str
    description: Optional[str] = None

class MenuCreate(MenuBase):
    items: List[dict]  # List of product_id and quantity

class MenuResponse(MenuBase):
    menu_id: int
    created_at: datetime
    items: List[dict] = []
    
    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    product_id: int
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    user_id: int

class ReviewResponse(ReviewBase):
    review_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PromotionBase(BaseModel):
    name: str
    discount: float
    start_date: datetime
    end_date: datetime

class PromotionCreate(PromotionBase):
    pass

class PromotionResponse(PromotionBase):
    promotion_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
