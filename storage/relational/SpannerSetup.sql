-- Setting up Spanner Instance
CREATE INSTANCE `spanner-instance` 
  CONFIG `regional-us-central1` 
  NODE_COUNT 3 
  DISPLAY_NAME "Spanner Instance";

-- Creating a Database within the Spanner Instance
CREATE DATABASE `spanner-database` 
  INSTANCE `spanner-instance`;

-- Schema Definitions

-- Create Table: Users
CREATE TABLE Users (
    UserID STRING(36) NOT NULL,
    FirstName STRING(50),
    LastName STRING(50),
    Email STRING(100),
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)
) PRIMARY KEY (UserID);

-- Create Table: Orders
CREATE TABLE Orders (
    OrderID STRING(36) NOT NULL,
    UserID STRING(36) NOT NULL,
    ProductID STRING(36) NOT NULL,
    Quantity INT64 NOT NULL,
    OrderDate TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    Status STRING(20),
    TotalAmount FLOAT64 NOT NULL
) PRIMARY KEY (OrderID),
  INTERLEAVE IN PARENT Users ON DELETE CASCADE;

-- Create Table: Products
CREATE TABLE Products (
    ProductID STRING(36) NOT NULL,
    ProductName STRING(100) NOT NULL,
    Description STRING(MAX),
    Price FLOAT64 NOT NULL,
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)
) PRIMARY KEY (ProductID);

-- Create Table: Categories
CREATE TABLE Categories (
    CategoryID STRING(36) NOT NULL,
    CategoryName STRING(100) NOT NULL,
    Description STRING(MAX)
) PRIMARY KEY (CategoryID);

-- Create Table: ProductCategories
CREATE TABLE ProductCategories (
    ProductID STRING(36) NOT NULL,
    CategoryID STRING(36) NOT NULL
) PRIMARY KEY (ProductID, CategoryID),
  INTERLEAVE IN PARENT Products ON DELETE CASCADE;

-- Foreign Keys

ALTER TABLE Orders
ADD CONSTRAINT FK_UserID FOREIGN KEY (UserID)
REFERENCES Users (UserID);

ALTER TABLE ProductCategories
ADD CONSTRAINT FK_ProductID FOREIGN KEY (ProductID)
REFERENCES Products (ProductID);

ALTER TABLE ProductCategories
ADD CONSTRAINT FK_CategoryID FOREIGN KEY (CategoryID)
REFERENCES Categories (CategoryID);

-- Create Table: Inventory
CREATE TABLE Inventory (
    InventoryID STRING(36) NOT NULL,
    ProductID STRING(36) NOT NULL,
    Quantity INT64 NOT NULL,
    WarehouseLocation STRING(100),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)
) PRIMARY KEY (InventoryID),
  INTERLEAVE IN PARENT Products ON DELETE CASCADE;

-- Create Table: Payments
CREATE TABLE Payments (
    PaymentID STRING(36) NOT NULL,
    OrderID STRING(36) NOT NULL,
    PaymentMethod STRING(50),
    PaymentStatus STRING(20),
    PaymentDate TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)
) PRIMARY KEY (PaymentID),
  INTERLEAVE IN PARENT Orders ON DELETE CASCADE;

-- Create Table: ShippingDetails
CREATE TABLE ShippingDetails (
    ShippingID STRING(36) NOT NULL,
    OrderID STRING(36) NOT NULL,
    ShippingAddress STRING(200),
    ShippingStatus STRING(20),
    ShippingDate TIMESTAMP,
    DeliveryDate TIMESTAMP
) PRIMARY KEY (ShippingID),
  INTERLEAVE IN PARENT Orders ON DELETE CASCADE;

-- Indexes for optimized querying

CREATE INDEX idx_user_email
ON Users (Email);

CREATE INDEX idx_order_date
ON Orders (OrderDate DESC);

CREATE INDEX idx_product_price
ON Products (Price);

CREATE INDEX idx_inventory_quantity
ON Inventory (Quantity);

CREATE INDEX idx_payment_status
ON Payments (PaymentStatus);

-- Constraints for data integrity

ALTER TABLE Users
ADD CONSTRAINT chk_email_format CHECK (REGEXP_CONTAINS(Email, r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"));

ALTER TABLE Orders
ADD CONSTRAINT chk_quantity_positive CHECK (Quantity > 0);

ALTER TABLE Products
ADD CONSTRAINT chk_price_positive CHECK (Price > 0);

ALTER TABLE Payments
ADD CONSTRAINT chk_payment_method CHECK (PaymentMethod IN ("Credit Card", "PayPal", "Bank Transfer"));

-- Create Table: UserSessions for tracking user activities
CREATE TABLE UserSessions (
    SessionID STRING(36) NOT NULL,
    UserID STRING(36) NOT NULL,
    LoginTimestamp TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    LogoutTimestamp TIMESTAMP
) PRIMARY KEY (SessionID),
  INTERLEAVE IN PARENT Users ON DELETE CASCADE;

-- Create Table: Reviews for capturing product feedback
CREATE TABLE Reviews (
    ReviewID STRING(36) NOT NULL,
    UserID STRING(36) NOT NULL,
    ProductID STRING(36) NOT NULL,
    Rating INT64 NOT NULL CHECK (Rating >= 1 AND Rating <= 5),
    ReviewText STRING(MAX),
    ReviewDate TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)
) PRIMARY KEY (ReviewID),
  INTERLEAVE IN PARENT Products ON DELETE CASCADE;

-- Add constraints for Reviews
ALTER TABLE Reviews
ADD CONSTRAINT chk_rating CHECK (Rating BETWEEN 1 AND 5);

-- Index for Reviews
CREATE INDEX idx_product_reviews
ON Reviews (ProductID, Rating DESC);

-- Add Sharding for high scalability (use HASH for ProductID and UserID)
CREATE INDEX idx_product_hash
ON Products (MOD(FARM_FINGERPRINT(ProductID), 100));

CREATE INDEX idx_user_hash
ON Users (MOD(FARM_FINGERPRINT(UserID), 100));

-- Optimizing for large-scale reads
CREATE INDEX idx_order_status
ON Orders (Status);

-- Optimize querying product by category
CREATE INDEX idx_product_category
ON ProductCategories (CategoryID, ProductID);