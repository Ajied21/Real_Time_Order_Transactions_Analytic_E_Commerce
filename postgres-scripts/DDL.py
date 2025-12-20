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


def create_bronze_tables():
    queries = [

        # =====================
        # BRONZE CUSTOMER RAW
        # =====================
        """
        CREATE TABLE IF NOT EXISTS bronze_customer_raw (
            _op_type            VARCHAR(5),
            _is_deleted         BOOLEAN DEFAULT FALSE,
            _source_system      VARCHAR(50),
            _topic_name         VARCHAR(100),
            _ingestion_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            _load_date          DATE DEFAULT CURRENT_DATE,
            _row_hash           VARCHAR(64),
            customer_id         VARCHAR(50),
            date                VARCHAR(50),
            full_name           VARCHAR(100),
            name_id             VARCHAR(50),
            place_of_birth      VARCHAR(50),
            date_of_birth       VARCHAR(50),
            gender              VARCHAR(10),
            email               VARCHAR(100),
            phone               VARCHAR(30),
            address             TEXT,
            city                VARCHAR(50),
            postal_code         VARCHAR(10),
            registration        VARCHAR(50)
        );
        """,

        # =====================
        # BRONZE PRODUCT RAW
        # =====================
        """
        CREATE TABLE IF NOT EXISTS bronze_product_raw (
            _op_type            VARCHAR(5),
            _is_deleted         BOOLEAN DEFAULT FALSE,
            _source_system      VARCHAR(50),
            _topic_name         VARCHAR(100),
            _ingestion_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            _load_date          DATE DEFAULT CURRENT_DATE,
            _row_hash           VARCHAR(64),
            product_id          VARCHAR(50),
            date                VARCHAR(50),
            product_name        VARCHAR(100),
            category            VARCHAR(50),
            brand               VARCHAR(50),
            base_price          VARCHAR(50)
        );
        """,

        # =====================
        # BRONZE SHIPPING RAW
        # =====================
        """
        CREATE TABLE IF NOT EXISTS bronze_shipping_raw (
            _op_type            VARCHAR(5),
            _is_deleted         BOOLEAN DEFAULT FALSE,
            _source_system      VARCHAR(50),
            _topic_name         VARCHAR(100),
            _ingestion_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            _load_date          DATE DEFAULT CURRENT_DATE,
            _row_hash           VARCHAR(64),
            shipping_id         VARCHAR(50),
            date                VARCHAR(50),
            courier             VARCHAR(30),
            pick_up             VARCHAR(50),
            delivery            VARCHAR(50),
            shipping_status     VARCHAR(30),
            shipping_cost       VARCHAR(50)
        );
        """,

        # =====================
        # BRONZE PAYMENTS RAW
        # =====================
        """
        CREATE TABLE IF NOT EXISTS bronze_payments_raw (
            _op_type            VARCHAR(5),
            _is_deleted         BOOLEAN DEFAULT FALSE,
            _source_system      VARCHAR(50),
            _topic_name         VARCHAR(100),
            _ingestion_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            _load_date          DATE DEFAULT CURRENT_DATE,
            _row_hash           VARCHAR(64),
            payment_id          VARCHAR(50),
            date                VARCHAR(50),
            order_id            VARCHAR(50),
            payment_method      VARCHAR(30),
            payment_status      VARCHAR(30),
            amount              VARCHAR(50)
        );
        """,

        # =====================
        # BRONZE ORDERS RAW
        # =====================
        """
        CREATE TABLE IF NOT EXISTS bronze_orders_raw (
            _op_type            VARCHAR(5),
            _is_deleted         BOOLEAN DEFAULT FALSE,
            _source_system      VARCHAR(50),
            _topic_name         VARCHAR(100),
            _ingestion_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            _load_date          DATE DEFAULT CURRENT_DATE,
            _row_hash           VARCHAR(64),
            order_id            VARCHAR(50),
            date                VARCHAR(50),
            customer_id         VARCHAR(50),
            shipping_id         VARCHAR(50),
            payment_id          VARCHAR(50),
            product_id          VARCHAR(50),
            quantity            VARCHAR(50),
            item_price          VARCHAR(50),
            subtotal            VARCHAR(50),
            discount            VARCHAR(50),
            total_amount        VARCHAR(50)
        );
        """
    ]

    for q in queries:
        cur.execute(q)

    print("✅ Bronze RAW tables created successfully")


if __name__ == "__main__":
    create_bronze_tables()
    cur.close()
    conn.close()