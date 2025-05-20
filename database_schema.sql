CREATE DATABASE IF NOT EXISTS `family_menu_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `family_menu_db`;

-- Disable foreign key checks for initial table creation
SET FOREIGN_KEY_CHECKS=0;


CREATE TABLE categories (
	category_id INTEGER NOT NULL AUTO_INCREMENT, 
	parent_id INTEGER, 
	name VARCHAR(50) NOT NULL, 
	description VARCHAR(500), 
	level INTEGER NOT NULL, 
	PRIMARY KEY (category_id), 
	FOREIGN KEY(parent_id) REFERENCES categories (category_id)
);

CREATE TABLE menus (
	menu_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(500), 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (menu_id)
);

CREATE TABLE promotions (
	promotion_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	discount DECIMAL(5, 2) NOT NULL, 
	start_date TIMESTAMP NULL, 
	end_date TIMESTAMP NULL, 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (promotion_id)
);

CREATE TABLE users (
	user_id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(50) NOT NULL, 
	password VARCHAR(255) NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	full_name VARCHAR(100), 
	avatar_url VARCHAR(255), 
	preferences JSON, 
	location VARCHAR(100), 
	`role` VARCHAR(20), 
	status VARCHAR(20), 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (user_id), 
	UNIQUE (username), 
	UNIQUE (email)
);

CREATE TABLE category_promotions (
	category_promotion_id INTEGER NOT NULL AUTO_INCREMENT, 
	category_id INTEGER NOT NULL, 
	promotion_id INTEGER NOT NULL, 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (category_promotion_id), 
	FOREIGN KEY(category_id) REFERENCES categories (category_id), 
	FOREIGN KEY(promotion_id) REFERENCES promotions (promotion_id)
);

CREATE TABLE favorite_menus (
	favorite_menu_id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	menu_id INTEGER NOT NULL, 
	PRIMARY KEY (favorite_menu_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id), 
	FOREIGN KEY(menu_id) REFERENCES menus (menu_id)
);

CREATE TABLE orders (
	order_id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	total_amount DECIMAL(10, 2) NOT NULL, 
	status VARCHAR(20), 
	payment_method VARCHAR(50), 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	recipient_name VARCHAR(128), 
	recipient_phone VARCHAR(32), 
	shipping_address VARCHAR(256), 
	shipping_city VARCHAR(64), 
	shipping_province VARCHAR(64), 
	shipping_postal_code VARCHAR(16), 
	PRIMARY KEY (order_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE products (
	product_id INTEGER NOT NULL AUTO_INCREMENT, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(1000), 
	price DECIMAL(10, 2) NOT NULL, 
	original_price DECIMAL(10, 2) NOT NULL, 
	unit VARCHAR(20), 
	stock_quantity INTEGER, 
	is_featured BOOL, 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (product_id), 
	FOREIGN KEY(category_id) REFERENCES categories (category_id)
);

CREATE TABLE cart_items (
	cart_item_id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	added_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (cart_item_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id), 
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE inventory (
	inventory_id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER, 
	unit VARCHAR(20), 
	last_updated TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (inventory_id), 
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE menu_items (
	menu_item_id INTEGER NOT NULL AUTO_INCREMENT, 
	menu_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (menu_item_id), 
	FOREIGN KEY(menu_id) REFERENCES menus (menu_id), 
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE order_items (
	order_item_id INTEGER NOT NULL AUTO_INCREMENT, 
	order_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	price DECIMAL(10, 2) NOT NULL, 
	PRIMARY KEY (order_item_id), 
	FOREIGN KEY(order_id) REFERENCES orders (order_id), 
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE payments (
	payment_id INTEGER NOT NULL AUTO_INCREMENT, 
	order_id INTEGER NOT NULL, 
	amount DECIMAL(10, 2) NOT NULL, 
	method VARCHAR(50), 
	status VARCHAR(20), 
	zp_trans_id VARCHAR(50), 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (payment_id), 
	FOREIGN KEY(order_id) REFERENCES orders (order_id)
);

CREATE TABLE product_images (
	image_id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	image_url VARCHAR(255) NOT NULL, 
	is_primary BOOL, 
	display_order INTEGER, 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (image_id), 
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE reviews (
	review_id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	rating INTEGER, 
	comment VARCHAR(1000), 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (review_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id), 
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE inventory_transactions (
	transaction_id INTEGER NOT NULL AUTO_INCREMENT, 
	inventory_id INTEGER NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	quantity INTEGER NOT NULL, 
	created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (transaction_id), 
	FOREIGN KEY(inventory_id) REFERENCES inventory (inventory_id)
);


-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS=1;
