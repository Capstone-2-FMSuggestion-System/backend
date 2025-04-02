from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Product, Category, Orders, OrderItems, Reviews
from ..schemas import ProductResponse, OrderCreate, OrderResponse, ReviewCreate, ReviewResponse
from ..cache import get_cache, set_cache
from typing import List, Optional
import random

router = APIRouter(prefix="/api/e-commerce", tags=["E-Commerce"])

@router.get("/categories", response_model=List[dict])
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return [
        {
            "category_id": category.category_id,
            "name": category.name,
            "description": category.description,
            "parent_id": category.parent_id,
            "level": category.level
        }
        for category in categories
    ]

@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    name: Optional[str] = None,
    category_id: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    db: Session = Depends(get_db)
):
    # Try to get from cache first
    cache_key = f"products:{name}:{category_id}:{price_min}:{price_max}"
    cached_result = await get_cache(cache_key)
    if cached_result:
        return eval(cached_result)
    
    # Build query
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if price_min is not None:
        query = query.filter(Product.price >= price_min)
    if price_max is not None:
        query = query.filter(Product.price <= price_max)
    
    products = query.all()
    result = [ProductResponse.from_orm(p) for p in products]
    
    # Cache the result
    await set_cache(cache_key, str(result), expire=300)
    return result

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.from_orm(product)

@router.get("/products/{product_id}/reviews", response_model=List[ReviewResponse])
async def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Reviews).filter(Reviews.product_id == product_id).all()
    result = []
    for review in reviews:
        user = db.query(User).filter(User.user_id == review.user_id).first()
        result.append(
            ReviewResponse(
                review_id=review.review_id,
                user_id=review.user_id,
                product_id=review.product_id,
                rating=review.rating,
                comment=review.comment,
                created_at=str(review.created_at),
                user_name=user.username if user else "Unknown"
            )
        )
    return result

@router.post("/products/{product_id}/reviews", response_model=ReviewResponse)
async def create_product_review(
    product_id: int,
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if product exists
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has already reviewed this product
    existing_review = db.query(Reviews).filter(
        Reviews.user_id == current_user.user_id,
        Reviews.product_id == product_id
    ).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")
    
    # Create review
    new_review = Reviews(
        user_id=current_user.user_id,
        product_id=product_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return ReviewResponse(
        review_id=new_review.review_id,
        user_id=new_review.user_id,
        product_id=new_review.product_id,
        rating=new_review.rating,
        comment=new_review.comment,
        created_at=str(new_review.created_at),
        user_name=current_user.username
    )

@router.get("/orders", response_model=List[OrderResponse])
async def get_user_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Orders).filter(Orders.user_id == current_user.user_id).all()
    return [OrderResponse.from_orm(order) for order in orders]

@router.get("/orders/{order_id}", response_model=dict)
async def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Orders).filter(
        Orders.order_id == order_id,
        Orders.user_id == current_user.user_id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_items = db.query(OrderItems).filter(OrderItems.order_id == order_id).all()
    items = []
    for item in order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        items.append({
            "product_id": item.product_id,
            "product_name": product.name if product else "Unknown",
            "quantity": item.quantity,
            "price": float(item.price),
            "total": float(item.price * item.quantity)
        })
    
    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "total_amount": float(order.total_amount),
        "status": order.status,
        "payment_method": order.payment_method,
        "created_at": order.created_at,
        "items": items
    }

@router.get("/products/featured", response_model=List[ProductResponse])
async def get_featured_products(db: Session = Depends(get_db)):
    """
    Retrieve featured products based on criteria like high ratings or manual selection
    """
    # Try to get from cache first
    cache_key = "products:featured"
    cached_result = await get_cache(cache_key)
    if cached_result:
        return eval(cached_result)
    
    # Get products with rating >= 4.0 or randomly select 10 products
    # In a real scenario, this could be based on other business logic
    featured_products = db.query(Product).limit(10).all()
    
    result = [ProductResponse.from_orm(p) for p in featured_products]
    
    # Cache the result
    await set_cache(cache_key, str(result), expire=300)
    return result 