import psycopg2
from faker import Faker
import random
import time
import hashlib
from datetime import datetime
import uuid

# =====================
# CONFIG
# =====================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "data_lake",
    "user": "user",
    "password": "admin123"
}

fake = Faker("id_ID")
SOURCE_SYSTEM = "faker_app"
TOPIC_PREFIX = "bronze_topic"

# =====================
# CONNECT DB
# =====================
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()


# =====================
# HELPER
# =====================
def generate_hash(*values):
    raw = "|".join([str(v) for v in values])
    return hashlib.sha256(raw.encode()).hexdigest()


# =====================
# INSERT BRONZE CUSTOMER
# =====================
def insert_bronze_customer():
    customer_id = str(uuid.uuid4())

    values = (
        customer_id,
        datetime.now().strftime("%Y-%m-%d"),
        fake.name(),
        fake.uuid4(),
        fake.city(),
        fake.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        random.choice(["M", "F"]),
        fake.email(),
        fake.phone_number(),
        fake.address(),
        fake.city(),
        fake.postcode(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    row_hash = generate_hash(*values)

    query = """
    INSERT INTO bronze_customer_raw (
        customer_id, date, full_name, name_id, place_of_birth,
        date_of_birth, gender, email, phone, address, city,
        postal_code, registration,
        _op_type, _source_system, _topic_name, _row_hash
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(query, (*values, "I", SOURCE_SYSTEM, f"{TOPIC_PREFIX}.customer", row_hash))

    return customer_id


# =====================
# INSERT BRONZE PRODUCT
# =====================
def insert_bronze_product():
    product_id = str(uuid.uuid4())

    values = (
        product_id,
        datetime.now().strftime("%Y-%m-%d"),
        fake.word().title(),
        random.choice(["Electronics", "Fashion", "Food", "Books"]),
        random.choice(["Samsung", "Apple", "Xiaomi", "Nike", "Adidas"]),
        str(random.randint(50_000, 5_000_000))
    )

    row_hash = generate_hash(*values)

    query = """
    INSERT INTO bronze_product_raw (
        product_id, date, product_name, category, brand, base_price,
        _op_type, _source_system, _topic_name, _row_hash
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(query, (*values, "I", SOURCE_SYSTEM, f"{TOPIC_PREFIX}.product", row_hash))

    return product_id


# =====================
# INSERT BRONZE SHIPPING
# =====================
def insert_bronze_shipping():
    shipping_id = str(uuid.uuid4())

    values = (
        shipping_id,
        datetime.now().strftime("%Y-%m-%d"),
        random.choice(["JNE", "J&T", "SiCepat", "AnterAja"]),
        fake.city(),
        fake.city(),
        random.choice(["CREATED", "IN_TRANSIT", "DELIVERED"]),
        str(random.randint(10_000, 50_000))
    )

    row_hash = generate_hash(*values)

    query = """
    INSERT INTO bronze_shipping_raw (
        shipping_id, date, courier, pick_up, delivery,
        shipping_status, shipping_cost,
        _op_type, _source_system, _topic_name, _row_hash
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(query, (*values, "I", SOURCE_SYSTEM, f"{TOPIC_PREFIX}.shipping", row_hash))

    return shipping_id


# =====================
# INSERT BRONZE ORDER
# =====================
def insert_bronze_order(customer_id, product_id, shipping_id):
    order_id = str(uuid.uuid4())

    qty = random.randint(1, 5)
    price = random.randint(50_000, 5_000_000)
    subtotal = qty * price
    discount = random.randint(0, int(subtotal * 0.2))
    total = subtotal - discount

    values = (
        order_id,
        datetime.now().strftime("%Y-%m-%d"),
        customer_id,
        shipping_id,
        str(uuid.uuid4()),  # payment_id (sementara raw)
        product_id,
        str(qty),
        str(price),
        str(subtotal),
        str(discount),
        str(total)
    )

    row_hash = generate_hash(*values)

    query = """
    INSERT INTO bronze_orders_raw (
        order_id, date, customer_id, shipping_id, payment_id,
        product_id, quantity, item_price, subtotal,
        discount, total_amount,
        _op_type, _source_system, _topic_name, _row_hash
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(query, (*values, "I", SOURCE_SYSTEM, f"{TOPIC_PREFIX}.orders", row_hash))

    return order_id


# =====================
# INSERT BRONZE PAYMENT
# =====================
def insert_bronze_payment(order_id):
    payment_id = str(uuid.uuid4())

    values = (
        payment_id,
        datetime.now().strftime("%Y-%m-%d"),
        order_id,
        random.choice(["TRANSFER", "QRIS", "COD", "EWALLET"]),
        random.choice(["PAID", "PENDING"]),
        str(random.randint(50_000, 5_000_000))
    )

    row_hash = generate_hash(*values)

    query = """
    INSERT INTO bronze_payments_raw (
        payment_id, date, order_id,
        payment_method, payment_status, amount,
        _op_type, _source_system, _topic_name, _row_hash
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(query, (*values, "I", SOURCE_SYSTEM, f"{TOPIC_PREFIX}.payments", row_hash))


# =====================
# MAIN LOOP
# =====================
if __name__ == "__main__":
    print("🚀 Inserting data into BRONZE RAW tables...")

    try:
        while True:
            customer_id = insert_bronze_customer()
            product_id = insert_bronze_product()
            shipping_id = insert_bronze_shipping()
            order_id = insert_bronze_order(customer_id, product_id, shipping_id)
            insert_bronze_payment(order_id)

            print(f"✅ Bronze data inserted | order_id={order_id}")

            time.sleep(random.randint(2, 5))

    except KeyboardInterrupt:
        print("\n⛔ Stopped by user")

    finally:
        cur.close()
        conn.close()