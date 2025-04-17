from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..e_commerce.models import Product, ProductImages
from ..e_commerce.schemas import ProductCreate, ProductUpdate
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def create_product(db: Session, product: ProductCreate) -> Product:
    """
    Tạo sản phẩm mới trong cơ sở dữ liệu.
    
    Args:
        db: Phiên database
        product: Thông tin sản phẩm cần tạo
        
    Returns:
        Product: Sản phẩm đã được tạo
    """
    try:
        # Tạo đối tượng Product từ ProductCreate
        db_product = Product(
            name=product.name,
            description=product.description,
            price=product.price,
            original_price=product.original_price,
            category_id=product.category_id,
            unit=product.unit,
            stock_quantity=product.stock_quantity,
            is_featured=product.is_featured
        )
        
        # Thêm sản phẩm vào database
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        return db_product
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {str(e)}")
        raise

def add_product_image(db: Session, product_id: int, image_url: str, is_primary: bool = False, display_order: int = 0) -> ProductImages:
    """
    Thêm hình ảnh cho sản phẩm.
    
    Args:
        db: Phiên database
        product_id: ID của sản phẩm
        image_url: URL của hình ảnh
        is_primary: Có phải là hình ảnh chính không
        display_order: Thứ tự hiển thị
        
    Returns:
        ProductImages: Đối tượng hình ảnh đã được tạo
    """
    try:
        # Kiểm tra product_id có tồn tại không
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm với ID {product_id}")
        
        # Nếu đây là ảnh primary, cập nhật tất cả các ảnh khác thành non-primary
        if is_primary:
            db.query(ProductImages).filter(
                ProductImages.product_id == product_id,
                ProductImages.is_primary == True
            ).update({"is_primary": False})
        
        # Tạo đối tượng ProductImages
        db_image = ProductImages(
            product_id=product_id,
            image_url=image_url,
            is_primary=is_primary,
            display_order=display_order
        )
        
        # Thêm hình ảnh vào database
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return db_image
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding product image: {str(e)}")
        raise

def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Product:
    """
    Cập nhật thông tin sản phẩm.
    
    Args:
        db: Phiên database
        product_id: ID của sản phẩm
        product_data: Dữ liệu cập nhật
        
    Returns:
        Product: Sản phẩm đã được cập nhật
    """
    try:
        # Lấy sản phẩm từ database
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm với ID {product_id}")
        
        # Cập nhật các trường
        update_data = product_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        
        # Lưu thay đổi
        db.commit()
        db.refresh(db_product)
        
        return db_product
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product: {str(e)}")
        raise

def delete_product(db: Session, product_id: int) -> bool:
    """
    Xóa sản phẩm.
    
    Args:
        db: Phiên database
        product_id: ID của sản phẩm
        
    Returns:
        bool: True nếu xóa thành công
    """
    try:
        # Lấy sản phẩm từ database
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm với ID {product_id}")
        
        # Xóa sản phẩm
        db.delete(db_product)
        db.commit()
        
        return True
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product: {str(e)}")
        raise

def delete_product_image(db: Session, image_id: int) -> bool:
    """
    Xóa hình ảnh của sản phẩm.
    
    Args:
        db: Phiên database
        image_id: ID của hình ảnh
        
    Returns:
        bool: True nếu xóa thành công
    """
    try:
        # Lấy hình ảnh từ database
        db_image = db.query(ProductImages).filter(ProductImages.image_id == image_id).first()
        if not db_image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy hình ảnh với ID {image_id}")
        
        # Lưu lại product_id và trạng thái is_primary để xử lý sau khi xóa
        product_id = db_image.product_id
        was_primary = db_image.is_primary
        
        # Xóa hình ảnh
        db.delete(db_image)
        
        # Nếu đây là hình ảnh chính, cập nhật một hình ảnh khác làm hình ảnh chính
        if was_primary:
            # Lấy hình ảnh đầu tiên của sản phẩm (nếu có)
            another_image = db.query(ProductImages).filter(
                ProductImages.product_id == product_id
            ).order_by(ProductImages.display_order).first()
            
            if another_image:
                another_image.is_primary = True
        
        db.commit()
        
        return True
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product image: {str(e)}")
        raise

def get_product_images(db: Session, product_id: int) -> List[Dict[str, Any]]:
    """
    Lấy danh sách hình ảnh của sản phẩm.
    
    Args:
        db: Phiên database
        product_id: ID của sản phẩm
        
    Returns:
        List[Dict[str, Any]]: Danh sách thông tin hình ảnh
    """
    try:
        # Kiểm tra product_id có tồn tại không
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm với ID {product_id}")
        
        # Lấy danh sách hình ảnh
        db_images = db.query(ProductImages).filter(
            ProductImages.product_id == product_id
        ).order_by(ProductImages.display_order).all()
        
        # Chuyển đổi thành định dạng response
        images = []
        for image in db_images:
            images.append({
                "image_id": image.image_id,
                "product_id": image.product_id,
                "image_url": image.image_url,
                "is_primary": image.is_primary,
                "display_order": image.display_order,
                "created_at": image.created_at
            })
        
        return images
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product images: {str(e)}")
        raise

def update_product_image(db: Session, image_id: int, image_url: Optional[str] = None, is_primary: Optional[bool] = None, display_order: Optional[int] = None) -> ProductImages:
    """
    Cập nhật thông tin hình ảnh của sản phẩm.
    
    Args:
        db: Phiên database
        image_id: ID của hình ảnh
        image_url: URL mới của hình ảnh (nếu cần cập nhật)
        is_primary: Trạng thái hình ảnh chính mới (nếu cần cập nhật)
        display_order: Thứ tự hiển thị mới (nếu cần cập nhật)
        
    Returns:
        ProductImages: Đối tượng hình ảnh đã được cập nhật
    """
    try:
        # Lấy hình ảnh từ database
        db_image = db.query(ProductImages).filter(ProductImages.image_id == image_id).first()
        if not db_image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy hình ảnh với ID {image_id}")
        
        # Nếu cập nhật is_primary thành True, cập nhật tất cả các hình ảnh khác của sản phẩm thành False
        if is_primary:
            db.query(ProductImages).filter(
                ProductImages.product_id == db_image.product_id,
                ProductImages.image_id != image_id,
                ProductImages.is_primary == True
            ).update({"is_primary": False})
        
        # Cập nhật các trường
        if image_url is not None:
            db_image.image_url = image_url
        if is_primary is not None:
            db_image.is_primary = is_primary
        if display_order is not None:
            db_image.display_order = display_order
        
        # Lưu thay đổi
        db.commit()
        db.refresh(db_image)
        
        return db_image
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product image: {str(e)}")
        raise 