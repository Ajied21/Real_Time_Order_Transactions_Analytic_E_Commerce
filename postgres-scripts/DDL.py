import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "data_staging",
    "user": "user",
    "password": "admin123"
}

conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

def create_tables():
    queries = [

        # =====================
        # CUSTOMER
        # =====================
        """
        CREATE TABLE IF NOT EXISTS customer (
            customer_id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            full_name VARCHAR(100),
            name_id VARCHAR(50),
            place_of_birth VARCHAR(50),
            date_of_birth DATE,
            gender CHAR(1),
            email VARCHAR(100),
            phone VARCHAR(30),
            address TEXT,
            city VARCHAR(50),
            postal_code VARCHAR(10),
            registration TIMESTAMP
        );
        """,

        # =====================
        # PRODUCT
        # =====================
        """
        CREATE TABLE IF NOT EXISTS product (
            product_id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            product_name VARCHAR(100),
            category VARCHAR(50),
            brand VARCHAR(50),
            base_price NUMERIC(12,2)
        );
        """,

        # =====================
        # SHIPPING
        # =====================
        """
        CREATE TABLE IF NOT EXISTS shipping (
            shipping_id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            courier VARCHAR(30),
            pick_up VARCHAR(50),
            delivery VARCHAR(50),
            shipping_status VARCHAR(20),
            shipping_cost NUMERIC(12,2)
        );
        """,

        # =====================
        # ORDERS (FACT)
        # =====================
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_id INT,
            shipping_id INT,
            product_id INT,
            quantity INT,
            item_price NUMERIC(12,2),
            subtotal NUMERIC(12,2),
            discount NUMERIC(12,2),
            total_amount NUMERIC(12,2),

            CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
            CONSTRAINT fk_shipping FOREIGN KEY (shipping_id) REFERENCES shipping(shipping_id),
            CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES product(product_id)
        );
        """,

        # =====================
        # PAYMENTS
        # =====================
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            order_id INT,
            payment_method VARCHAR(30),
            payment_status VARCHAR(20),
            amount NUMERIC(12,2),

            CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
        """
    ]

    for q in queries:
        cur.execute(q)

    print("✅ All tables created successfully")

if __name__ == "__main__":
    create_tables()
    cur.close()
    conn.close()