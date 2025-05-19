from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user
from .models import User, Product, Inventory, InventoryTransactions
from .schemas import InventoryCreate, InventoryTransactionCreate
from typing import List

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.get("/", response_model=List[dict])
async def get_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to view inventory")
    
    inventory = db.query(Inventory).all()
    result = []
    for item in inventory:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        result.append({
            "inventory_id": item.inventory_id,
            "product_id": item.product_id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "last_updated": item.last_updated
        })
    return result

@router.post("/", response_model=dict)
async def create_inventory(
    inventory: InventoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to create inventory")
    
    product = db.query(Product).filter(Product.product_id == inventory.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_inventory = Inventory(
        product_id=inventory.product_id,
        quantity=inventory.quantity,
        unit=inventory.unit
    )
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    
    # Create initial transaction
    transaction = InventoryTransactions(
        inventory_id=new_inventory.inventory_id,
        type="initial",
        quantity=inventory.quantity
    )
    db.add(transaction)
    db.commit()
    
    return {"message": "Inventory created successfully", "inventory_id": new_inventory.inventory_id}

@router.put("/{inventory_id}", response_model=dict)
async def update_inventory(
    inventory_id: int,
    transaction: InventoryTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to update inventory")
    
    inventory = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    # Update inventory quantity
    if transaction.type == "add":
        inventory.quantity += transaction.quantity
    elif transaction.type == "remove":
        if inventory.quantity < transaction.quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        inventory.quantity -= transaction.quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid transaction type")
    
    # Create transaction record
    new_transaction = InventoryTransactions(
        inventory_id=inventory_id,
        type=transaction.type,
        quantity=transaction.quantity
    )
    db.add(new_transaction)
    db.commit()
    
    return {"message": "Inventory updated successfully", "new_quantity": inventory.quantity}

@router.get("/transactions", response_model=List[dict])
async def get_inventory_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to view transactions")
    
    transactions = db.query(InventoryTransactions).all()
    result = []
    for transaction in transactions:
        inventory = db.query(Inventory).filter(Inventory.inventory_id == transaction.inventory_id).first()
        product = db.query(Product).filter(Product.product_id == inventory.product_id).first()
        result.append({
            "transaction_id": transaction.transaction_id,
            "inventory_id": transaction.inventory_id,
            "product_name": product.name,
            "type": transaction.type,
            "quantity": transaction.quantity,
            "created_at": transaction.created_at
        })
    return result 