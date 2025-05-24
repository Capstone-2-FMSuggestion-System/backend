from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user
from .models import Product, Category, Orders, OrderItems, Reviews
from ..user.models import User
from .schemas import (
    ProductBase, ProductCreate, ProductUpdate, ProductResponse, ProductImageCreate, 
    ProductImageResponse, CartItemCreate, CartItem, OrderItemBase, OrderItemCreate, 
    OrderCreate, OrderResponse, ReviewCreate, ReviewResponse, 
    CategoryResponse, CategoryWithSubcategories, ProductDiscountResponse, 
    MainCategoryResponse, ProductImageResponse, ProductDetailResponse, ProductSimpleResponse,
    RelatedProductResponse
)
from ..core.cache import get_cache, set_cache
from typing import List, Optional
import random
import json
import datetime
from pydantic import BaseModel
import logging
from sqlalchemy.sql import func

# Tạo logger
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

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
    await set_cache(cache_key, json.dumps([category.model_dump() for category in result], cls=DateTimeEncoder), expire=600)
    
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
    await set_cache(cache_key, json.dumps([subcategory.model_dump() for subcategory in result], cls=DateTimeEncoder), expire=600)
    
    return result

@router.get("/categories-tree", response_model=List[CategoryWithSubcategories])
async def get_categories_tree(force_refresh: bool = False, db: Session = Depends(get_db)):
    """
    Lấy cây danh mục
    """
    try:
        # Tạo cache key
        cache_key = "e_commerce:categories-tree"
        
        # Kiểm tra cache nếu không yêu cầu force refresh
        if not force_refresh:
            try:
                cached_data = await get_cache(cache_key)
                if cached_data:
                    print("Returning categories tree from cache")
                    return json.loads(cached_data)
            except Exception as cache_error:
                print(f"Cache error: {str(cache_error)}")
        else:
            print("Force refresh requested, skipping cache")
        
        # Lấy tất cả categories từ database
        all_categories = db.query(Category).all()
        
        # Tạo dictionary để mapping category_id với category object
        category_dict = {category.category_id: CategoryWithSubcategories.model_validate(category) for category in all_categories}
        
        # Tạo map để lưu tất cả ID của danh mục và subcategories
        category_subcategories_map = {}
        
        # Hàm đệ quy để lấy tất cả ID của subcategories
        def get_all_subcategory_ids(cat_id, subcategory_ids=None):
            if subcategory_ids is None:
                subcategory_ids = []
            
            # Lấy các subcategory trực tiếp
            direct_subcategories = [cat for cat in all_categories if cat.parent_id == cat_id]
            
            # Thêm vào danh sách
            for subcategory in direct_subcategories:
                sub_id = subcategory.category_id
                subcategory_ids.append(sub_id)
                # Đệ quy để lấy các subcategory của subcategory này
                get_all_subcategory_ids(sub_id, subcategory_ids)
            
            return subcategory_ids
        
        # Tính toán product_count cho mỗi category
        for category_id, category in category_dict.items():
            # Lấy tất cả ID của subcategories (bao gồm cả các subcategory lồng nhau)
            subcategory_ids = get_all_subcategory_ids(category_id)
            category_subcategories_map[category_id] = subcategory_ids
            
            # Đếm số lượng sản phẩm trực tiếp trong category này
            direct_product_count = db.query(Product).filter(Product.category_id == category_id).count()
            
            # Đếm số lượng sản phẩm trong tất cả subcategories
            subcategories_product_count = 0
            if subcategory_ids:
                subcategories_product_count = db.query(Product).filter(Product.category_id.in_(subcategory_ids)).count()
            
            # Tổng số lượng sản phẩm
            total_product_count = direct_product_count + subcategories_product_count
            
            # Cập nhật product_count
            category_dict[category_id].product_count = total_product_count
        
        # Danh sách chứa chỉ các category cấp cao nhất (parent_id is None hoặc 0)
        root_categories = []
        
        # Duyệt qua tất cả category để xây dựng cây phân cấp
        for category_id, category in category_dict.items():
            # Nếu là category con (có parent_id), thêm vào subcategories của parent
            if category.parent_id:
                if category.parent_id in category_dict:
                    parent_category = category_dict[category.parent_id]
                    parent_category.subcategories.append(CategoryResponse(
                        category_id=category.category_id,
                        name=category.name,
                        description=category.description,
                        level=category.level,
                        parent_id=category.parent_id,
                        product_count=category.product_count
                    ))
            # Nếu là category gốc (không có parent_id hoặc level=1), thêm vào danh sách root_categories
            else:
                root_categories.append(category)
        
        # Lọc ra chỉ các category cấp 1 nếu danh sách không có category nào
        if not root_categories:
            root_categories = [cat for cat in category_dict.values() if cat.level == 1]
            
        # Lưu vào cache với thời gian hết hạn là 15 phút
        try:
            await set_cache(cache_key, json.dumps([cat.model_dump() for cat in root_categories], cls=DateTimeEncoder), 900)
            print("Categories tree cached for 15 minutes")
        except Exception as cache_error:
            print(f"Failed to cache categories tree: {str(cache_error)}")
        
        return root_categories
    except Exception as e:
        print(f"Error in get_categories_tree: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

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

@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Tính giá gốc và giá sau giảm
    original_price = float(product.original_price)
    price =  float(product.price)
    
    # Lấy tất cả hình ảnh từ mối quan hệ images và sắp xếp theo display_order tăng dần
    images = []
    if product.images:
        # Sắp xếp hình ảnh theo display_order tăng dần
        sorted_images = sorted(product.images, key=lambda img: img.display_order)
        images = [img.image_url for img in sorted_images]
    
    # Lấy hình ảnh primary để gán vào trường image
    image_url = None
    if product.images:
        # Ưu tiên lấy hình ảnh được đánh dấu là primary
        primary_images = [img for img in product.images if img.is_primary]
        if primary_images:
            image_url = primary_images[0].image_url
        elif images:
            # Nếu không có hình ảnh primary, lấy hình ảnh đầu tiên sau khi sắp xếp
            image_url = images[0]
    
    # Tạo đối tượng response với các trường cần thiết
    return ProductDetailResponse(
        product_id=product.product_id,
        name=product.name,
        price=price,
        original_price=original_price,
        unit=product.unit,
        description=product.description,
        stock_quantity=product.stock_quantity,
        image=image_url,
        images=images
    )

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
    orders = db.query(Orders).options(joinedload(Orders.items).joinedload(OrderItems.product)).filter(Orders.user_id == current_user.user_id).order_by(Orders.created_at.desc()).all()
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
    try:
        # Try to get from cache first
        cache_key = "products:featured"
        cached_result = await get_cache(cache_key)
        if cached_result:
            try:
                # Parse JSON instead of using eval
                cached_data = json.loads(cached_result)
                return [ProductResponse.model_validate(item) for item in cached_data]
            except Exception as e:
                logger.error(f"Error parsing cached result: {str(e)}")
                # Continue to fetch from database if cache parsing fails
        
        # Get featured products with proper error handling
        featured_products = db.query(Product).filter(
            Product.is_featured == True
        ).limit(10).all()
        
        logger.info(f"Found {len(featured_products)} featured products")
        
        if not featured_products:
            # If no featured products found, get some random products
            featured_products = db.query(Product).order_by(
                func.random()
            ).limit(10).all()
            logger.info("No featured products found, using random products instead")
        
        # Convert to response model with proper error handling
        result = []
        for product in featured_products:
            try:
                # Ensure all required fields have valid values
                if not product.name or product.price is None or product.original_price is None or product.category_id is None:
                    logger.warning(f"Product {product.product_id} is missing required fields")
                    continue

                # Convert datetime to ISO format for JSON serialization
                product_dict = {
                    "product_id": product.product_id,
                    "name": product.name,
                    "description": product.description or "",
                    "price": float(product.price),
                    "original_price": float(product.original_price),
                    "category_id": product.category_id,
                    "unit": product.unit or "piece",
                    "stock_quantity": product.stock_quantity or 0,
                    "is_featured": product.is_featured or False,
                    "created_at": product.created_at if product.created_at else datetime.now(),
                    "images": [img.image_url for img in product.images] if product.images else []
                }
                
                # Log the processed product data
                logger.info(f"Processed product data: {json.dumps(product_dict, cls=DateTimeEncoder)}")
                
                # Validate the product data
                try:
                    product_response = ProductResponse.model_validate(product_dict)
                    result.append(product_response)
                except Exception as e:
                    logger.error(f"Validation error for product {product.product_id}: {str(e)}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error converting product {product.product_id} to response model: {str(e)}")
                logger.error(f"Product data that caused error: {product.__dict__}")
                continue
        
        if not result:
            logger.warning("No valid products found after processing")
            return []
            
        # Cache the result with proper JSON serialization
        try:
            serialized_result = json.dumps([item.model_dump() for item in result], cls=DateTimeEncoder)
            await set_cache(cache_key, serialized_result, expire=300)
        except Exception as e:
            logger.error(f"Error caching featured products: {str(e)}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_featured_products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching featured products"
        )

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
        serialized_data = json.dumps(result.model_dump(), cls=DateTimeEncoder)
        await set_cache(cache_key, serialized_data, expire=600)
    except Exception as e:
        # Trong trường hợp serialize gặp lỗi, chỉ log và bỏ qua việc cache
        print(f"Error serializing category tree: {str(e)}")
    
    return result

# Định nghĩa response model cho API get_products_by_subcategory
class ProductsByCategoryResponse(BaseModel):
    products: List[ProductSimpleResponse]
    pagination: dict
    category: CategoryResponse

@router.get("/categories/{category_id}/products", response_model=ProductsByCategoryResponse)
async def get_products_by_subcategory(
    category_id: int,
    include_subcategories: bool = True,
    page: int = 1,
    limit: int = 9,
    sort_by: Optional[str] = "name",  # name, price_asc, price_desc, newest
    db: Session = Depends(get_db)
):
    """
    Lấy sản phẩm theo danh mục, hỗ trợ phân trang
    - category_id: ID của danh mục
    - include_subcategories: Có lấy sản phẩm từ danh mục con hay không
    - page: Trang hiện tại
    - limit: Số sản phẩm trên mỗi trang (tối đa 9)
    - sort_by: Tiêu chí sắp xếp (name, price_asc, price_desc, newest)
    """
    # Giới hạn số lượng sản phẩm trên mỗi trang
    if limit > 9:
        limit = 9
    
    if page < 1:
        page = 1
    
    # Tính offset cho phân trang
    offset = (page - 1) * limit
    
    # Kiểm tra xem dữ liệu có trong cache không
    cache_key = f"subcategory:{category_id}:products_simple:{include_subcategories}:page:{page}:limit:{limit}:sort:{sort_by}"
    cached_result = await get_cache(cache_key)
    if cached_result:
        try:
            return json.loads(cached_result)
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
    
    # Tạo query cơ bản
    base_query = db.query(Product).filter(Product.category_id.in_(category_ids))
    
    # Đếm tổng số sản phẩm
    total_products = base_query.count()
    
    # Tính tổng số trang
    total_pages = (total_products + limit - 1) // limit
    
    # Áp dụng sắp xếp
    if sort_by == "price_asc":
        base_query = base_query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        base_query = base_query.order_by(Product.price.desc())
    elif sort_by == "newest":
        base_query = base_query.order_by(Product.created_at.desc())
    else:  # Mặc định sắp xếp theo tên
        base_query = base_query.order_by(Product.name.asc())
    
    # Áp dụng phân trang
    products = base_query.offset(offset).limit(limit).all()
    
    # Tạo response với thông tin giảm giá
    result_products = []
    for product in products:
        # Tìm hình ảnh có is_primary = 1
        image_url = None
        images = []
        if product.images:
            # Sắp xếp hình ảnh theo display_order tăng dần
            sorted_images = sorted(product.images, key=lambda img: img.display_order)
            images = [img.image_url for img in sorted_images]
            
            # Tìm hình ảnh primary
            primary_images = [img for img in product.images if img.is_primary]
            if primary_images:
                image_url = primary_images[0].image_url
            elif images:
                # Nếu không có hình ảnh primary, lấy hình ảnh đầu tiên sau khi sắp xếp
                image_url = images[0]
        
        # Tính giá gốc và giá sau giảm
        original_price = float(product.original_price if product.original_price else product.price)
        price = float(product.price)  # Giả sử được giảm 10% cho ví dụ
        
        # Tạo đối tượng sản phẩm đơn giản
        product_data = ProductSimpleResponse(
            product_id=product.product_id,
            name=product.name,
            price=price,
            original_price=original_price,
            unit=product.unit,
            image=image_url,
            images=images,
            category_id=product.category_id,
            created_at=product.created_at.isoformat() if product.created_at else datetime.datetime.now().isoformat(),
            description=product.description,
            stock_quantity=product.stock_quantity,
            is_featured=product.is_featured
        )
        result_products.append(product_data)
    
    # Tạo response model
    category_response = CategoryResponse(
        category_id=category.category_id,
        name=category.name,
        description=category.description,
        level=category.level,
        parent_id=category.parent_id
    )
    
    pagination = {
        "total_products": total_products,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    result = ProductsByCategoryResponse(
        products=result_products,
        pagination=pagination,
        category=category_response
    )
    
    # Lưu kết quả vào cache
    try:
        await set_cache(cache_key, json.dumps(result.model_dump(), cls=DateTimeEncoder), expire=600)
    except Exception as e:
        print(f"Error serializing products: {str(e)}")
    
    return result

@router.get("/products/{product_id}/related", response_model=List[RelatedProductResponse])
async def get_related_products(
    product_id: int, 
    limit: int = 4,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách sản phẩm liên quan dựa trên sản phẩm được chọn.
    Các tiêu chí:
    1. Cùng danh mục con (subcategory)
    2. Khoảng giá tương tự
    3. Các thuộc tính khác có liên quan
    """
    # Kiểm tra cache
    cache_key = f"products:{product_id}:related:limit:{limit}"
    cached_result = await get_cache(cache_key)
    if cached_result:
        try:
            cached_data = json.loads(cached_result)
            return [RelatedProductResponse.model_validate(item) for item in cached_data]
        except Exception as e:
            print(f"Lỗi khi đọc cache sản phẩm liên quan: {str(e)}")
    
    # Lấy thông tin sản phẩm hiện tại
    current_product = db.query(Product).filter(Product.product_id == product_id).first()
    if not current_product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    
    # Lấy thông tin về danh mục của sản phẩm
    category = db.query(Category).filter(Category.category_id == current_product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục của sản phẩm")
    
    related_products = []
    
    # Bước 1: Lấy sản phẩm cùng danh mục con (subcategory)
    if category.parent_id:
        # Lấy các sản phẩm cùng subcategory, ngoại trừ sản phẩm hiện tại
        same_subcategory_products = db.query(Product).filter(
            Product.category_id == current_product.category_id,
            Product.product_id != product_id
        ).limit(limit * 2).all()
        
        related_products.extend(same_subcategory_products)
    
    # Bước 2: Nếu không đủ sản phẩm từ cùng subcategory, lấy thêm sản phẩm từ parent category
    if len(related_products) < limit and category.parent_id:
        # Lấy tất cả subcategories cùng cấp (siblings)
        sibling_categories = db.query(Category).filter(
            Category.parent_id == category.parent_id,
            Category.category_id != category.category_id
        ).all()
        
        sibling_category_ids = [cat.category_id for cat in sibling_categories]
        
        # Lấy sản phẩm từ các danh mục cùng cấp
        if sibling_category_ids:
            sibling_products = db.query(Product).filter(
                Product.category_id.in_(sibling_category_ids),
                Product.product_id != product_id
            ).limit(limit - len(related_products)).all()
            
            related_products.extend(sibling_products)
    
    # Bước 3: Nếu vẫn không đủ, lấy sản phẩm cùng khoảng giá
    if len(related_products) < limit:
        # Khoảng giá ±30%
        min_price = float(current_product.price) * 0.7
        max_price = float(current_product.price) * 1.3
        
        # Lấy ID của các sản phẩm đã có để loại trừ
        existing_ids = [p.product_id for p in related_products] + [product_id]
        
        price_similar_products = db.query(Product).filter(
            Product.price.between(min_price, max_price),
            Product.product_id.notin_(existing_ids)
        ).limit(limit - len(related_products)).all()
        
        related_products.extend(price_similar_products)
    
    # Tính điểm liên quan cho từng sản phẩm
    scored_products = []
    for product in related_products:
        score = 0
        
        # Cùng danh mục con (điểm cao nhất)
        if product.category_id == current_product.category_id:
            score += 10
        # Danh mục cùng cấp (điểm cao thứ hai)
        elif category.parent_id and product.category_id in sibling_category_ids:
            score += 5
        
        # Khoảng giá tương tự (điểm trung bình)
        price_diff = abs(float(product.price) - float(current_product.price))
        if price_diff < float(current_product.price) * 0.1:  # Chênh lệch < 10%
            score += 5
        elif price_diff < float(current_product.price) * 0.2:  # Chênh lệch < 20%
            score += 3
        elif price_diff < float(current_product.price) * 0.3:  # Chênh lệch < 30%
            score += 1
        
        scored_products.append((product, score))
    
    # Sắp xếp theo điểm liên quan (cao đến thấp)
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    # Lấy các sản phẩm có điểm cao nhất và giới hạn số lượng
    final_products = [item[0] for item in scored_products[:limit]]
    
    # Chuyển đổi sang định dạng response - chỉ bao gồm các trường cần thiết
    result = []
    for product in final_products:
        # Tìm hình ảnh có is_primary = 1
        image_url = None
        images = []
        if product.images:
            # Sắp xếp hình ảnh theo display_order tăng dần
            sorted_images = sorted(product.images, key=lambda img: img.display_order)
            images = [img.image_url for img in sorted_images]
            
            # Tìm hình ảnh primary
            primary_images = [img for img in product.images if img.is_primary]
            if primary_images:
                image_url = primary_images[0].image_url
            elif images:
                # Nếu không có hình ảnh primary, lấy hình ảnh đầu tiên sau khi sắp xếp
                image_url = images[0]
        
        # Tính giá gốc và giá sau giảm
        original_price = float(product.original_price if product.original_price else product.price)
        price = float(product.price) * 0.9  # Giả sử được giảm 10% cho ví dụ
        
        # Tạo đối tượng sản phẩm đơn giản
        simple_product = {
            "product_id": product.product_id,
            "name": product.name,
            "price": price,
            "original_price": original_price,
            "unit": product.unit,
            "image": image_url,
            "images": images,
            "created_at": product.created_at.isoformat() if product.created_at else datetime.datetime.now().isoformat()
        }
        result.append(simple_product)
    
    # Lưu kết quả vào cache
    try:
        await set_cache(
            cache_key, 
            json.dumps(result, cls=DateTimeEncoder), 
            expire=600  # Cache 10 phút
        )
    except Exception as e:
        print(f"Lỗi khi lưu cache sản phẩm liên quan: {str(e)}")
    
    # Chuyển đổi các dict thành RelatedProductResponse
    response_objects = [RelatedProductResponse.model_validate(product) for product in result]
    
    # In ra log để kiểm tra dữ liệu trả về
    print("=== DEBUG RELATED PRODUCTS RESPONSE ===")
    for idx, obj in enumerate(response_objects):
        print(f"Product {idx + 1}: {obj.model_dump_json()}")
    print("======================================")
    
    return response_objects