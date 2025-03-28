# API Testing Guide for Family Menu Suggestion System

This document provides a comprehensive guide for testing all APIs available in the Family Menu Suggestion System. For each API endpoint, you'll find information about the required inputs, expected outputs, and data types.

## Table of Contents

1. [Authentication APIs](#authentication-apis)
2. [User APIs](#user-apis)
3. [E-Commerce APIs](#e-commerce-apis)
4. [Payment APIs](#payment-apis)
5. [Inventory APIs](#inventory-apis)
6. [Admin APIs](#admin-apis)

---

## Authentication APIs

Base URL: `/api/auth`

### Register

- **Endpoint**: `POST /api/auth/register`
- **Description**: Register a new user
- **Input**:
  ```json
  {
    "username": "string",
    "email": "string",
    "full_name": "string" (optional),
    "role": "string" (optional, default: "user"),
    "password": "string"
  }
  ```
- **Output**:
  ```json
  {
    "token": "string",
    "user_id": "integer"
  }
  ```
- **Notes**: 
  - Password must be at least 6 characters
  - Only admin users can assign roles other than "user"

### Login

- **Endpoint**: `POST /api/auth/login`
- **Description**: Authenticate a user and get access token
- **Input**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Output**:
  ```json
  {
    "token": "string",
    "token_type": "string",
    "user_id": "integer",
    "role": "string"
  }
  ```

---

## User APIs

Base URL: `/api/users`

### Get Current User Info

- **Endpoint**: `GET /api/users/me`
- **Description**: Get information about the currently authenticated user
- **Authentication**: Required (Bearer token)
- **Input**: None
- **Output**:
  ```json
  {
    "user_id": "integer",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string"
  }
  ```

### Update User Info

- **Endpoint**: `PUT /api/users/me`
- **Description**: Update information for the currently authenticated user
- **Authentication**: Required (Bearer token)
- **Input**:
  ```json
  {
    "username": "string" (optional),
    "email": "string" (optional),
    "full_name": "string" (optional),
    "password": "string" (optional),
    "role": "string" (optional),
    "location": "string" (optional)
  }
  ```
- **Output**:
  ```json
  {
    "message": "string"
  }
  ```

### Get Cart Items

- **Endpoint**: `GET /api/users/cart`
- **Description**: Get all items in the user's cart
- **Authentication**: Required (Bearer token)
- **Input**: None
- **Output**:
  ```json
  [
    {
      "cart_item_id": "integer",
      "product_id": "integer",
      "product_name": "string",
      "quantity": "integer",
      "price": "float",
      "total": "float"
    }
  ]
  ```

### Add to Cart

- **Endpoint**: `POST /api/users/cart`
- **Description**: Add a product to the user's cart
- **Authentication**: Required (Bearer token)
- **Input**:
  ```json
  {
    "product_id": "integer",
    "quantity": "integer"
  }
  ```
- **Output**:
  ```json
  {
    "message": "string",
    "cart_item_id": "integer"
  }
  ```

### Update Cart Item

- **Endpoint**: `PUT /api/users/cart/{cart_item_id}`
- **Description**: Update the quantity of an item in the cart
- **Authentication**: Required (Bearer token)
- **Path Parameters**: `cart_item_id` (integer)
- **Query Parameters**: `quantity` (integer)
- **Input**: None
- **Output**:
  ```json
  {
    "message": "string"
  }
  ```

### Remove from Cart

- **Endpoint**: `DELETE /api/users/cart/{cart_item_id}`
- **Description**: Remove an item from the cart
- **Authentication**: Required (Bearer token)
- **Path Parameters**: `cart_item_id` (integer)
- **Input**: None
- **Output**:
  ```json
  {
    "message": "string"
  }
  ```

---

## E-Commerce APIs

Base URL: `/api/e-commerce`

### Get Categories

- **Endpoint**: `GET /api/e-commerce/categories`
- **Description**: Get all product categories
- **Input**: None
- **Output**:
  ```json
  [
    {
      "category_id": "integer",
      "name": "string",
      "description": "string",
      "parent_id": "integer",
      "level": "integer"
    }
  ]
  ```

### Get Products

- **Endpoint**: `GET /api/e-commerce/products`
- **Description**: Get products with optional filtering
- **Query Parameters**:
  - `name` (string, optional): Filter by product name
  - `category_id` (integer, optional): Filter by category
  - `price_min` (float, optional): Minimum price
  - `price_max` (float, optional): Maximum price
- **Input**: None
- **Output**:
  ```json
  [
    {
      "product_id": "integer",
      "category_id": "integer",
      "name": "string",
      "description": "string",
      "price": "float",
      "image_url": "string",
      "unit": "string",
      "stock_quantity": "integer",
      "is_featured": "boolean",
      "created_at": "string"
    }
  ]
  ```

### Get Product

- **Endpoint**: `GET /api/e-commerce/products/{product_id}`
- **Description**: Get details of a specific product
- **Path Parameters**: `product_id` (integer)
- **Input**: None
- **Output**:
  ```json
  {
    "product_id": "integer",
    "category_id": "integer",
    "name": "string",
    "description": "string",
    "price": "float",
    "image_url": "string",
    "unit": "string",
    "stock_quantity": "integer",
    "is_featured": "boolean",
    "created_at": "string"
  }
  ```

### Get Product Reviews

- **Endpoint**: `GET /api/e-commerce/products/{product_id}/reviews`
- **Description**: Get all reviews for a specific product
- **Path Parameters**: `product_id` (integer)
- **Input**: None
- **Output**:
  ```json
  [
    {
      "review_id": "integer",
      "user_id": "integer",
      "product_id": "integer",
      "rating": "integer",
      "comment": "string",
      "created_at": "string",
      "user_name": "string"
    }
  ]
  ```

### Create Product Review

- **Endpoint**: `POST /api/e-commerce/products/{product_id}/reviews`
- **Description**: Create a review for a product
- **Authentication**: Required (Bearer token)
- **Path Parameters**: `product_id` (integer)
- **Input**:
  ```json
  {
    "user_id": "integer",
    "product_id": "integer",
    "rating": "integer",
    "comment": "string" (optional)
  }
  ```
- **Output**:
  ```json
  {
    "review_id": "integer",
    "user_id": "integer",
    "product_id": "integer",
    "rating": "integer",
    "comment": "string",
    "created_at": "string",
    "user_name": "string"
  }
  ```

---

## Payment APIs

Base URL: `/api/payments`

### Create ZaloPay Payment

- **Endpoint**: `POST /api/payments/zalopay/create`
- **Description**: Create a payment order with ZaloPay
- **Input**:
  ```json
  {
    "user_id": "integer",
    "cart_items": [
      {
        "product_id": "integer",
        "quantity": "integer"
      }
    ],
    "payment_method": "string"
  }
  ```
- **Query Parameters**: `payment_method` (enum: "zalopayapp", "ATM", "CC", "QR", default: "zalopayapp")
- **Output**:
  ```json
  {
    "order_url": "string",
    "zp_trans_id": "string",
    "app_trans_id": "string",
    "payment_method": "string"
  }
  ```

### ZaloPay Callback

- **Endpoint**: `POST /api/payments/zalopay/callback`
- **Description**: Callback endpoint for ZaloPay to notify payment status
- **Input**:
  ```json
  {
    "data": "string",
    "mac": "string",
    "type": "integer"
  }
  ```
- **Output**:
  ```json
  {
    "return_code": "integer",
    "return_message": "string"
  }
  ```

### Check ZaloPay Status

- **Endpoint**: `GET /api/payments/zalopay/status/{app_trans_id}`
- **Description**: Check the status of a ZaloPay payment
- **Path Parameters**: `app_trans_id` (string)
- **Input**: None
- **Output**: Response from ZaloPay API

### Get ZaloPay Payment Methods

- **Endpoint**: `GET /api/payments/zalopay/payment-methods`
- **Description**: Get available ZaloPay payment methods
- **Input**: None
- **Output**:
  ```json
  {
    "payment_methods": [
      {
        "id": "string",
        "name": "string",
        "description": "string",
        "icon_url": "string"
      }
    ]
  }
  ```

---

## Inventory APIs

Base URL: `/api/inventory`

### Get Inventory

- **Endpoint**: `GET /api/inventory/`
- **Description**: Get all inventory items
- **Authentication**: Required (Bearer token, role: admin or staff)
- **Input**: None
- **Output**:
  ```json
  [
    {
      "inventory_id": "integer",
      "product_id": "integer",
      "product_name": "string",
      "quantity": "integer",
      "unit": "string",
      "last_updated": "string"
    }
  ]
  ```

### Create Inventory

- **Endpoint**: `POST /api/inventory/`
- **Description**: Create a new inventory item
- **Authentication**: Required (Bearer token, role: admin or staff)
- **Input**:
  ```json
  {
    "product_id": "integer",
    "quantity": "integer",
    "unit": "string"
  }
  ```
- **Output**:
  ```json
  {
    "message": "string",
    "inventory_id": "integer"
  }
  ```

### Update Inventory

- **Endpoint**: `PUT /api/inventory/{inventory_id}`
- **Description**: Update an inventory item
- **Authentication**: Required (Bearer token, role: admin or staff)
- **Path Parameters**: `inventory_id` (integer)
- **Input**:
  ```json
  {
    "inventory_id": "integer",
    "type": "string" ("add" or "remove"),
    "quantity": "integer"
  }
  ```
- **Output**:
  ```json
  {
    "message": "string",
    "new_quantity": "integer"
  }
  ```

---

## Admin APIs

Base URL: `/api/admin`

### Get All Users

- **Endpoint**: `GET /api/admin/users`
- **Description**: Get all users in the system
- **Authentication**: Required (Bearer token, role: admin)
- **Input**: None
- **Output**:
  ```json
  [
    {
      "user_id": "integer",
      "username": "string",
      "email": "string",
      "full_name": "string",
      "role": "string",
      "created_at": "string"
    }
  ]
  ```

### Create Admin User

- **Endpoint**: `POST /api/admin/users`
- **Description**: Create a new user (admin can create users with any role)
- **Authentication**: Required (Bearer token, role: admin)
- **Input**:
  ```json
  {
    "username": "string",
    "email": "string",
    "full_name": "string" (optional),
    "role": "string" (optional, default: "user"),
    "password": "string"
  }
  ```
- **Output**:
  ```json
  {
    "message": "string",
    "user_id": "integer"
  }
  ```

### Get All Products

- **Endpoint**: `GET /api/admin/products`
- **Description**: Get all products in the system
- **Authentication**: Required (Bearer token, role: admin)
- **Input**: None
- **Output**:
  ```json
  [
    {
      "product_id": "integer",
      "name": "string",
      "category_id": "integer",
      "price": "float",
      "stock_quantity": "integer",
      "is_featured": "boolean"
    }
  ]
  ```

### Create Product

- **Endpoint**: `POST /api/admin/products`
- **Description**: Create a new product
- **Authentication**: Required (Bearer token, role: admin)
- **Input**:
  ```json
  {
    "category_id": "integer",
    "name": "string",
    "description": "string" (optional),
    "price": "float",
    "image_url": "string" (optional),
    "unit": "string" (optional),
    "stock_quantity": "integer",
    "is_featured": "boolean" (default: false)
  }
  ```
- **Output**:
  ```json
  {
    "message": "string",
    "product_id": "integer"
  }
  ```

### Get All Orders

- **Endpoint**: `GET /api/admin/orders`
- **Description**: Get all orders in the system
- **Authentication**: Required (Bearer token, role: admin)
- **Input**: None
- **Output**:
  ```json
  [
    {
      "order_id": "integer",
      "user_id": "integer",
      "total_amount": "float",
      "status": "string",
      "payment_method": "string",
      "created_at": "string"
    }
  ]
  ```

### Create Promotion

- **Endpoint**: `POST /api/admin/promotions`
- **Description**: Create a new promotion
- **Authentication**: Required (Bearer token, role: admin)
- **Input**:
  ```json
  {
    "name": "string",
    "discount": "float",
    "start_date": "string",
    "end_date": "string"
  }
  ```
- **Output**:
  ```json
  {
    "message": "string",
    "promotion_id": "integer"
  }
  ```