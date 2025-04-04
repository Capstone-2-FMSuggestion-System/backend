from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class PaymentMethod(str, Enum):
    ZALOPAY_APP = "zalopayapp"
    ATM = "ATM"
    CREDIT_CARD = "CC"
    QR_CODE = "QR"

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None

class Login(BaseModel):
    username: str
    password: str

class User(UserBase):
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    unit: Optional[str] = None
    stock_quantity: int = 0
    is_featured: bool = False

class ProductResponse(BaseModel):
    product_id: int
    category_id: int
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    unit: Optional[str]
    stock_quantity: int
    is_featured: bool
    created_at: str

    class Config:
        from_attributes = True

class CartItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    cart_items: List[CartItem]
    payment_method: str

class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    total_amount: float
    status: str
    payment_method: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: float

class InventoryCreate(BaseModel):
    product_id: int
    quantity: int
    unit: str

class InventoryTransactionCreate(BaseModel):
    inventory_id: int
    type: str
    quantity: int

class MenuCreate(BaseModel):
    name: str
    description: Optional[str] = None
    items: Optional[List[CartItem]] = None

class ReviewCreate(BaseModel):
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    review_id: int
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str]
    created_at: str
    user_name: str

    class Config:
        from_attributes = True

class PromotionCreate(BaseModel):
    name: str
    discount: float
    start_date: str
    end_date: str

class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    method: str

class ZaloPayOrderResponse(BaseModel):
    order_url: str
    zp_trans_id: Optional[str] = None
    app_trans_id: Optional[str] = None
    payment_method: PaymentMethod

class ZaloPayCallback(BaseModel):
    data: str
    mac: str
    type: int

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: int
    parent_id: Optional[int] = None

class CategoryResponse(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True

class CategoryWithSubcategories(CategoryResponse):
    subcategories: List["CategoryWithSubcategories"] = []

    class Config:
        from_attributes = True

CategoryWithSubcategories.model_rebuild()

class ProductDiscountResponse(BaseModel):
    product_id: int
    name: str
    original_price: float
    discount_price: float
    discount_percent: float
    image_url: Optional[str]
    category_id: int

    class Config:
        from_attributes = True

class MainCategoryResponse(BaseModel):
    category_id: int
    name: str
    level: int
    
    class Config:
        from_attributes = True 