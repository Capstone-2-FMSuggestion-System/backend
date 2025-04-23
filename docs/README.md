# Tài liệu API hệ thống Family Menu Suggestion System

Thư mục này chứa các tài liệu mô tả chi tiết về các API của hệ thống Family Menu Suggestion System.

## Danh sách tài liệu API

1. [Hướng dẫn kiểm thử API](API_TESTING_GUIDE.md) - Tài liệu hướng dẫn cách test các API trong hệ thống
2. [API Dashboard cho quản trị](dashboard_api.md) - Mô tả chi tiết các API dashboard cho quản trị
3. [Kế hoạch triển khai API Dashboard](dashboard_api_plan.md) - Kế hoạch chi tiết triển khai API dashboard
4. [Kế hoạch tái cấu trúc dự án](plan.md) - Kế hoạch tái cấu trúc dự án Flask API

## Sử dụng tài liệu

Các tài liệu này được thiết kế để cung cấp thông tin chi tiết cho:

- Nhà phát triển muốn tích hợp với hệ thống
- Tester cần kiểm thử các API
- Người quản trị hệ thống
- Thành viên mới trong dự án

## Quy ước mã trạng thái HTTP

Hệ thống sử dụng các mã trạng thái HTTP tiêu chuẩn:

- **200 OK**: Yêu cầu thành công
- **201 Created**: Tạo mới thành công
- **400 Bad Request**: Yêu cầu không hợp lệ (lỗi dữ liệu đầu vào)
- **401 Unauthorized**: Chưa xác thực
- **403 Forbidden**: Không có quyền truy cập
- **404 Not Found**: Không tìm thấy tài nguyên
- **500 Internal Server Error**: Lỗi server

## Xác thực

Tất cả các API yêu cầu xác thực (trừ một số API công khai) đều sử dụng JWT. Token cần được gửi trong header `Authorization` với định dạng `Bearer <token>`.

## API Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: Cung cấp khi triển khai

## Duy trì tài liệu

Các tài liệu này cần được cập nhật mỗi khi có thay đổi trong API. Để đóng góp vào tài liệu:

1. Tạo branch mới từ branch chính
2. Cập nhật tài liệu
3. Tạo Pull Request
4. Chờ review và merge 