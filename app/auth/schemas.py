# Đây là file schemas.py cho module auth
# Định nghĩa trực tiếp hoặc import từ user.schemas thay vì từ schemas.py gốc

from ..user.schemas import Token, TokenData, User, UserInDB, UserCreate, Login

# Trong tương lai, có thể chuyển định nghĩa các schema vào đây
