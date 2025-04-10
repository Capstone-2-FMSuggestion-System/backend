from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from .models import Inventory, InventoryTransactions

def create_inventory(db: Session, inventory_data: dict) -> Inventory:
    """
    Tên Function: create_inventory
    
    1. Mô tả ngắn gọn:
    Tạo bản ghi tồn kho mới.
    
    2. Mô tả công dụng:
    Tạo một bản ghi tồn kho mới cho một sản phẩm trong cơ sở dữ liệu.
    """
    new_inventory = Inventory(**inventory_data)
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    return new_inventory

def get_inventory(db: Session, inventory_id: int) -> Optional[Inventory]:
    """
    Tên Function: get_inventory
    
    1. Mô tả ngắn gọn:
    Lấy thông tin tồn kho theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin tồn kho dựa trên ID.
    """
    return db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()

def get_inventory_by_product(db: Session, product_id: int) -> Optional[Inventory]:
    """
    Tên Function: get_inventory_by_product
    
    1. Mô tả ngắn gọn:
    Lấy thông tin tồn kho theo ID sản phẩm.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin tồn kho của một sản phẩm cụ thể.
    """
    return db.query(Inventory).filter(Inventory.product_id == product_id).first()

def update_inventory(db: Session, inventory_id: int, quantity: int) -> Optional[Inventory]:
    """
    Tên Function: update_inventory
    
    1. Mô tả ngắn gọn:
    Cập nhật số lượng tồn kho.
    
    2. Mô tả công dụng:
    Cập nhật số lượng tồn kho của một sản phẩm trong cơ sở dữ liệu.
    """
    db_inventory = get_inventory(db, inventory_id)
    if not db_inventory:
        return None
    
    db_inventory.quantity = quantity
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def delete_inventory(db: Session, inventory_id: int) -> bool:
    """
    Tên Function: delete_inventory
    
    1. Mô tả ngắn gọn:
    Xóa bản ghi tồn kho.
    
    2. Mô tả công dụng:
    Xóa bản ghi tồn kho khỏi cơ sở dữ liệu.
    """
    db_inventory = get_inventory(db, inventory_id)
    if not db_inventory:
        return False
    
    db.delete(db_inventory)
    db.commit()
    return True

def create_inventory_transaction(db: Session, transaction_data: dict) -> InventoryTransactions:
    """
    Tên Function: create_inventory_transaction
    
    1. Mô tả ngắn gọn:
    Tạo giao dịch tồn kho mới.
    
    2. Mô tả công dụng:
    Tạo một bản ghi giao dịch tồn kho mới trong cơ sở dữ liệu để theo dõi
    các thay đổi về số lượng tồn kho (nhập, xuất, điều chỉnh).
    """
    new_transaction = InventoryTransactions(**transaction_data)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def get_inventory_transactions(db: Session, start_date: str = None, end_date: str = None) -> List[InventoryTransactions]:
    """
    Tên Function: get_inventory_transactions
    
    1. Mô tả ngắn gọn:
    Lấy danh sách các giao dịch tồn kho trong khoảng thời gian.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy danh sách các giao dịch tồn kho
    trong một khoảng thời gian cụ thể.
    """
    query = db.query(InventoryTransactions)
    if start_date:
        query = query.filter(InventoryTransactions.created_at >= start_date)
    if end_date:
        query = query.filter(InventoryTransactions.created_at <= end_date)
    return query.all() 