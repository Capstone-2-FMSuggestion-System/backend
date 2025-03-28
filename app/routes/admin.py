from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Product, Category, Orders, Payments, Promotions
from ..schemas import ProductCreate, UserCreate, PromotionCreate
from typing import List

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def check_admin(user: User):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )

@router.get("/users", response_model=List[dict])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    users = db.query(User).all()
    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at
        }
        for user in users
    ]

@router.post("/users", response_model=dict)
async def create_admin_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.user_id}

@router.get("/products", response_model=List[dict])
async def get_all_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    products = db.query(Product).all()
    return [
        {
            "product_id": product.product_id,
            "name": product.name,
            "category_id": product.category_id,
            "price": float(product.price),
            "stock_quantity": product.stock_quantity,
            "is_featured": product.is_featured
        }
        for product in products
    ]

@router.post("/products", response_model=dict)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    category = db.query(Category).filter(Category.category_id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Product created successfully", "product_id": new_product.product_id}

@router.get("/orders", response_model=List[dict])
async def get_all_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    orders = db.query(Orders).all()
    return [
        {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_method": order.payment_method,
            "created_at": order.created_at
        }
        for order in orders
    ]

@router.get("/payments", response_model=List[dict])
async def get_all_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    payments = db.query(Payments).all()
    return [
        {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "amount": float(payment.amount),
            "method": payment.method,
            "status": payment.status,
            "created_at": payment.created_at
        }
        for payment in payments
    ]

@router.post("/promotions", response_model=dict)
async def create_promotion(
    promotion: PromotionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    new_promotion = Promotions(**promotion.dict())
    db.add(new_promotion)
    db.commit()
    db.refresh(new_promotion)
    return {"message": "Promotion created successfully", "promotion_id": new_promotion.promotion_id}

@router.get("/dashboard", response_model=dict)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    total_users = db.query(User).count()
    total_orders = db.query(Orders).count()
    total_products = db.query(Product).count()
    total_revenue = db.query(Orders).filter(Orders.status == "completed").with_entities(
        func.sum(Orders.total_amount)
    ).scalar() or 0
    
    recent_orders = db.query(Orders).order_by(Orders.created_at.desc()).limit(5).all()
    
    return {
        "stats": {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_products": total_products,
            "total_revenue": float(total_revenue)
        },
        "recent_orders": [
            {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "created_at": order.created_at
            }
            for order in recent_orders
        ]
    } 