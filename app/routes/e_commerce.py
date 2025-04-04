from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Product, Category, Orders, OrderItems, Reviews
from ..schemas import (
    ProductResponse, OrderCreate, OrderResponse, ReviewCreate, ReviewResponse, 
    CategoryResponse, CategoryWithSubcategories, ProductDiscountResponse, 
    MainCategoryResponse
)
from ..cache import get_cache, set_cache
from typing import List, Optional
import random
import json

router = APIRouter(prefix="/api/e-commerce", tags=["E-Commerce"])

@router.get("/categories", response_model=List[MainCategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    # Kiểm tra xem dữ liệu có trong cache không
    cache_key = "main:categories"
    cached_result = await get_cache(cache_key)
    if cached_result:
        # Chuyển đổi từ JSON string sang danh sách MainCategoryResponse
        cached_data = json.loads(cached_result)
        return [MainCategoryResponse.model_validate(item) for item in cached_data]
    
    # Lấy chỉ các categories cấp cao nhất (parent_id is None)
    main_categories = db.query(Category).filter(Category.parent_id == None).all()
    
    # Chuyển đổi sang định dạng response không bao gồm description
    result = [MainCategoryResponse.model_validate(category) for category in main_categories]
    
    # Lưu dữ liệu vào cache
    await set_cache(cache_key, json.dumps([category.model_dump() for category in result]), expire=600)
    
    return result

@router.get("/categories/{category_id}/subcategories", response_model=List[CategoryResponse])
async def get_subcategories_by_category(category_id: int, db: Session = Depends(get_db)):
    # Kiểm tra xem dữ liệu có trong cache không
    cache_key = f"categories:{category_id}:subcategories"
    cached_result = await get_cache(cache_key)
    if cached_result:
        # Chuyển đổi từ JSON string sang danh sách CategoryResponse
        cached_data = json.loads(cached_result)
        return [CategoryResponse.model_validate(item) for item in cached_data]
    
    # Kiểm tra xem category có tồn tại không
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Lấy tất cả subcategories trực tiếp của category này
    subcategories = db.query(Category).filter(Category.parent_id == category_id).all()
    
    # Chuyển đổi sang định dạng response
    result = [CategoryResponse.model_validate(subcategory) for subcategory in subcategories]
    
    # Lưu dữ liệu vào cache
    await set_cache(cache_key, json.dumps([subcategory.model_dump() for subcategory in result]), expire=600)
    
    return result

@router.get("/categories-tree", response_model=List[CategoryWithSubcategories])
async def get_categories_with_subcategories(db: Session = Depends(get_db)):
    # Kiểm tra xem dữ liệu có trong cache không
    cache_key = "categories:tree"
    cached_result = await get_cache(cache_key)
    if cached_result:
        # Chuyển đổi từ JSON string sang danh sách CategoryWithSubcategories
        try:
            cached_data = json.loads(cached_result)
            return [CategoryWithSubcategories.model_validate(item) for item in cached_data]
        except Exception as e:
            # Xử lý lỗi khi chuyển đổi từ cache
            print(f"Error deserializing cached categories tree: {str(e)}")
            # Không throw exception, tiếp tục xử lý dưới đây
    
    # Lấy tất cả categories từ database
    all_categories = db.query(Category).all()
    
    # Tạo dictionary để mapping category_id với category object
    category_dict = {category.category_id: CategoryWithSubcategories.model_validate(category) for category in all_categories}
    
    # Danh sách chứa chỉ các category cấp cao nhất (parent_id is None hoặc 0)
    root_categories = []
    
    # Duyệt qua tất cả category để xây dựng cây phân cấp
    for category_id, category in category_dict.items():
        # Nếu là category con (có parent_id), thêm vào subcategories của parent
        if category.parent_id:
            if category.parent_id in category_dict:
                category_dict[category.parent_id].subcategories.append(category)
        # Nếu là category gốc (không có parent_id), thêm vào danh sách root_categories
        else:
            root_categories.append(category)
    
    # Lưu kết quả vào cache - cần xử lý đặc biệt vì cấu trúc phức tạp
    try:
        serialized_data = json.dumps([cat.model_dump() for cat in root_categories])
        await set_cache(cache_key, serialized_data, expire=600)
    except Exception as e:
        # Trong trường hợp serialize gặp lỗi, chỉ log và bỏ qua việc cache
        print(f"Error serializing categories tree: {str(e)}")
    
    return root_categories

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

@router.get("/categories/{category_id}/subcategories-tree", response_model=CategoryWithSubcategories)
async def get_category_with_all_subcategories(category_id: int, db: Session = Depends(get_db)):
    # Kiểm tra xem dữ liệu có trong cache không
    cache_key = f"categories:{category_id}:subcategories-tree"
    cached_result = await get_cache(cache_key)
    if cached_result:
        # Chuyển đổi từ JSON string sang CategoryWithSubcategories
        try:
            cached_data = json.loads(cached_result)
            return CategoryWithSubcategories.model_validate(cached_data)
        except Exception as e:
            # Xử lý lỗi khi chuyển đổi từ cache
            print(f"Error deserializing cached category tree: {str(e)}")
            # Không throw exception, tiếp tục xử lý dưới đây
    
    # Kiểm tra xem category có tồn tại không
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Lấy tất cả categories từ database
    all_categories = db.query(Category).all()
    
    # Tạo dictionary để mapping category_id với category object
    category_dict = {cat.category_id: CategoryWithSubcategories.model_validate(cat) for cat in all_categories}
    
    # Xây dựng cây phân cấp
    for cat_id, cat in category_dict.items():
        if cat.parent_id and cat.parent_id in category_dict:
            category_dict[cat.parent_id].subcategories.append(cat)
    
    # Lấy category chính với toàn bộ subcategories của nó
    result = category_dict[category_id]
    
    # Lưu kết quả vào cache
    try:
        serialized_data = json.dumps(result.model_dump())
        await set_cache(cache_key, serialized_data, expire=600)
    except Exception as e:
        # Trong trường hợp serialize gặp lỗi, chỉ log và bỏ qua việc cache
        print(f"Error serializing category tree: {str(e)}")
    
    return result

@router.get("/categories/{category_id}/products", response_model=List[ProductDiscountResponse])
async def get_products_by_subcategory(
    category_id: int,
    include_subcategories: bool = True,
    db: Session = Depends(get_db)
):
    # Kiểm tra xem dữ liệu có trong cache không
    cache_key = f"subcategory:{category_id}:products:{include_subcategories}"
    cached_result = await get_cache(cache_key)
    if cached_result:
        try:
            cached_data = json.loads(cached_result)
            return [ProductDiscountResponse.model_validate(item) for item in cached_data]
        except Exception as e:
            print(f"Error deserializing cached products: {str(e)}")
            # Tiếp tục xử lý nếu có lỗi khi parse cache
    
    # Kiểm tra xem category có tồn tại không
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Lấy tất cả category_ids, bao gồm subcategories nếu được yêu cầu
    category_ids = [category_id]
    
    if include_subcategories:
        # Lấy tất cả subcategories (trực tiếp và gián tiếp)
        all_subcategories = []
        
        def get_subcategories(parent_id):
            subcats = db.query(Category).filter(Category.parent_id == parent_id).all()
            for subcat in subcats:
                all_subcategories.append(subcat.category_id)
                get_subcategories(subcat.category_id)  # Tìm tiếp các cấp con
        
        get_subcategories(category_id)
        category_ids.extend(all_subcategories)
    
    # Lấy sản phẩm theo list category_id
    products = db.query(Product).filter(Product.category_id.in_(category_ids)).all()
    
    # Tạo response với thông tin giảm giá
    result = []
    for product in products:
        # Lấy giá gốc từ sản phẩm
        original_price = float(product.price)
        
        # Trong thực tế, giá sau giảm có thể lấy từ bảng promotions hoặc bảng riêng
        # Ở đây, chúng ta tạm tính giá sau giảm, có thể thay đổi theo logic thực tế
        discount_price = original_price * 0.9  # Giả sử được giảm 10% cho ví dụ
        
        # Tính phần trăm giảm giá dựa trên giá gốc và giá sau giảm
        discount_percent = 0
        if original_price > 0 and discount_price is not None:
            discount_percent = round(((original_price - discount_price) / original_price) * 100, 2)
            discount_price = round(discount_price, 2)
        else:
            discount_price = original_price
            
        product_data = {
            "product_id": product.product_id,
            "name": product.name,
            "original_price": original_price,
            "discount_price": discount_price,
            "discount_percent": discount_percent,
            "image_url": product.image_url,
            "category_id": product.category_id
        }
        result.append(ProductDiscountResponse.model_validate(product_data))
    
    # Lưu kết quả vào cache
    try:
        serialized_data = json.dumps([product.model_dump() for product in result])
        await set_cache(cache_key, serialized_data, expire=600)
    except Exception as e:
        print(f"Error serializing products: {str(e)}")
    
    return result 