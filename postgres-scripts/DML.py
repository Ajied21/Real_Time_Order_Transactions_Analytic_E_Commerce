import psycopg2
from faker import Faker
import random
import time
from datetime import datetime

# =====================
# CONFIG
# =====================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "data_staging",
    "user": "user",
    "password": "admin123"
}

fake = Faker("id_ID")

# =====================
# CONNECT DB
# =====================
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

# =====================
# INSERT FUNCTIONS
# =====================

def insert_customer():
    query = """
    INSERT INTO customer (
        full_name, name_id, place_of_birth, date_of_birth,
        gender, email, phone, address, city, postal_code, registration
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING customer_id
    """
    cur.execute(query, (
        fake.name(),
        fake.uuid4(),
        fake.city(),
        fake.date_of_birth(minimum_age=18, maximum_age=60),
        random.choice(["M", "F"]),
        fake.email(),
        fake.phone_number(),
        fake.address(),
        fake.city(),
        fake.postcode(),
        datetime.now()
    ))
    return cur.fetchone()[0]


def insert_product():
    query = """
    INSERT INTO product (
        product_name, category, brand, base_price
    ) VALUES (%s,%s,%s,%s)
    RETURNING product_id
    """
    cur.execute(query, (
        fake.word().title(),
        random.choice(["Electronics", "Fashion", "Food", "Books"]),
        random.choice(["Samsung", "Apple", "Xiaomi", "Nike", "Adidas"]),
        random.randint(50_000, 5_000_000)
    ))
    return cur.fetchone()[0]


def insert_shipping():
    query = """
    INSERT INTO shipping (
        courier, pick_up, delivery, shipping_status, shipping_cost
    ) VALUES (%s,%s,%s,%s,%s)
    RETURNING shipping_id
    """
    cur.execute(query, (
        random.choice(["JNE", "J&T", "SiCepat", "AnterAja"]),
        fake.city(),
        fake.city(),
        random.choice(["CREATED", "IN_TRANSIT", "DELIVERED"]),
        random.randint(10_000, 50_000)
    ))
    return cur.fetchone()[0]


def insert_order(customer_id, product_id, shipping_id):
    qty = random.randint(1, 5)
    price = random.randint(50_000, 5_000_000)
    subtotal = qty * price
    discount = random.randint(0, int(subtotal * 0.2))
    total = subtotal - discount

    query = """
    INSERT INTO orders (
        customer_id, shipping_id, product_id,
        quantity, item_price, subtotal, discount, total_amount
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING order_id
    """
    cur.execute(query, (
        customer_id,
        shipping_id,
        product_id,
        qty,
        price,
        subtotal,
        discount,
        total
    ))
    return cur.fetchone()[0]


def insert_payment(order_id):
    query = """
    INSERT INTO payments (
        order_id, payment_method, payment_status, amount
    ) VALUES (%s,%s,%s,%s)
    RETURNING payment_id
    """
    cur.execute(query, (
        order_id,
        random.choice(["TRANSFER", "QRIS", "COD", "EWALLET"]),
        random.choice(["PAID", "PENDING"]),
        random.randint(50_000, 5_000_000)
    ))
    return cur.fetchone()[0]


# =====================
# MAIN LOOP
# =====================
if __name__ == "__main__":
    print("🚀 Starting fake data generator (CDC-ready)...")

    try:
        while True:
            customer_id = insert_customer()
            product_id = insert_product()
            shipping_id = insert_shipping()
            order_id = insert_order(customer_id, product_id, shipping_id)
            payment_id = insert_payment(order_id)

            print(
                f"✅ Order {order_id} | "
                f"Customer {customer_id} | "
                f"Product {product_id} | "
                f"Payment {payment_id}"
            )

            # delay supaya CDC kelihatan real-time
            time.sleep(random.randint(2, 5))

    except KeyboardInterrupt:
        print("\n⛔ Stopped by user")

    finally:
        cur.close()
        conn.close()