from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Product, CartItems, Orders, OrderItems, Menus, MenuItems, FavoriteMenus, Reviews
from ..schemas import ProductResponse, CartItem, OrderCreate, OrderResponse, ReviewCreate, ReviewResponse, UserUpdate
from ..crud import get_products, get_product, create_cart_item, get_cart_item, update_cart_item, delete_cart_item
from ..cache import get_cache, set_cache
from typing import List

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

@router.put("/me", response_model=dict)
async def update_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    return {"message": "User information updated successfully"}

@router.get("/cart", response_model=List[dict])
async def get_cart_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItems).filter(CartItems.user_id == current_user.user_id).all()
    result = []
    for item in cart_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        result.append({
            "cart_item_id": item.cart_item_id,
            "product_id": item.product_id,
            "product_name": product.name,
            "quantity": item.quantity,
            "price": float(product.price),
            "total": float(product.price * item.quantity)
        })
    return result

@router.post("/cart", response_model=dict)
async def add_to_cart(
    item: CartItem,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = get_product(db, item.product_id)
    if not product or item.quantity <= 0 or item.quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity or product")
    
    cart_item = create_cart_item(db, current_user.user_id, item.product_id, item.quantity)
    return {"message": "Item added to cart", "cart_item_id": cart_item.cart_item_id}

@router.put("/cart/{cart_item_id}", response_model=dict)
async def update_cart_item(
    cart_item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = get_cart_item(db, cart_item_id, current_user.user_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    product = get_product(db, cart_item.product_id)
    if not product or quantity <= 0 or quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    
    update_cart_item(db, cart_item_id, quantity)
    return {"message": "Cart item updated successfully"}

@router.delete("/cart/{cart_item_id}", response_model=dict)
async def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = get_cart_item(db, cart_item_id, current_user.user_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    delete_cart_item(db, cart_item_id)
    return {"message": "Item removed from cart"} 