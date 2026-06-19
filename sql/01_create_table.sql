DROP TABLE IF EXISTS online_retail;

CREATE TABLE online_retail (
    invoice_no VARCHAR(30),
    stock_code VARCHAR(50),
    description VARCHAR(MAX),
    quantity INTEGER,
    invoice_date DATETIME2,
    unit_price NUMERIC(10, 2),
    customer_id VARCHAR(50),
    country VARCHAR(100)
);