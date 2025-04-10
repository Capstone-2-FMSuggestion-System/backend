# Import models và schemas trước
from .models import Inventory, InventoryTransactions
from .schemas import InventoryCreate, InventoryUpdate

# Export crud functions
from .crud import (
    create_inventory,
    get_inventory,
    get_inventory_by_product,
    update_inventory,
    delete_inventory,
    create_inventory_transaction,
    get_inventory_transactions
)

# Import router sau các import khác để tránh circular import
from .routes import router
