-- Software Purchase Billing System Database Schema

-- Create Database if not exists
CREATE DATABASE IF NOT EXISTS software_billing_db;

-- Select the database
USE software_billing_db;

-- Create Bills table
CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_no VARCHAR(50) NOT NULL UNIQUE,
    customer_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL,
    address TEXT NOT NULL,
    software_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    license_key VARCHAR(100) NOT NULL,
    bill_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_name (customer_name),
    INDEX idx_mobile_number (mobile_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
