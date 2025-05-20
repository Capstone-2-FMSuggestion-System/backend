from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv
import os

# Tải biến môi trường
load_dotenv()

# Lấy biến môi trường kết nối cơ sở dữ liệu
DB_USER = os.getenv("DB_USER", "family_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456789")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306") 
DB_NAME = os.getenv("DB_NAME", "family_menu_db")

# Tạo chuỗi kết nối
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Đặt URL kết nối vào config
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import các model để lấy metadata
from app.core.database import Base
from app.user.models import User
from app.e_commerce.models import Category, Product, CartItems, Orders, OrderItems, Menus, MenuItems, FavoriteMenus, Reviews, Promotions, CategoryPromotion, ProductImages
from app.inventory.models import Inventory, InventoryTransactions
from app.payment.models import Payments
from app.auth.models import User

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Các tùy chọn bổ sung cho việc so sánh schema
            compare_type=True,  # So sánh kiểu dữ liệu
            compare_server_default=True,  # So sánh giá trị mặc định
            include_schemas=True,  # Bao gồm schemas
            render_as_batch=True,  # Hỗ trợ SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
