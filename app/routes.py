from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.models.product import Product
from backend.models.user import User
from backend.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from backend.database.database import get_db
from typing import Optional
import json

router = APIRouter()

@router.post("/manage/products", response_model=ProductResponse)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    original_price: float = Form(...),
    stock_quantity: int = Form(...),
    is_featured: bool = Form(False),
    category_id: int = Form(...),
    unit: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    try:
        # Create new product
        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "original_price": original_price,
            "stock_quantity": stock_quantity,
            "is_featured": is_featured,
            "category_id": category_id,
            "unit": unit
        }
        
        db_product = Product(**product_data)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # Handle file upload if present
        if file:
            # Save the file and update the product's image URL
            # This part depends on your file storage implementation
            pass

        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/manage/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    try:
        # Lấy sản phẩm hiện tại
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

        # Cập nhật thông tin sản phẩm
        for field, value in product_data.dict(exclude_unset=True).items():
            setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)

        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) 