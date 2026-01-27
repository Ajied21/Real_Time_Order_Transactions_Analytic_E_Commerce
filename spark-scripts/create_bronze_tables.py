import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# =====================================================
# Load ENV
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# =====================================================
# Config
# =====================================================
SCHEMA = "bronze"

# RESET MODE
# true  -> DROP & CREATE (DEV / REPROCESS)
# false -> CREATE IF NOT EXISTS (PROD SAFE)
RESET_BRONZE = os.getenv("RESET_BRONZE", "false").lower() == "true"

# =====================================================
# Redshift Connection
# =====================================================
conn = psycopg2.connect(
    host=os.getenv("REDSHIFT_HOST"),
    port=os.getenv("REDSHIFT_PORT"),
    dbname=os.getenv("REDSHIFT_DB"),
    user=os.getenv("REDSHIFT_USER"),
    password=os.getenv("REDSHIFT_PASSWORD")
)
conn.autocommit = True
cur = conn.cursor()

# =====================================================
# Table Definitions (BRONZE = RAW / STRING FIRST)
# =====================================================
TABLE_DEFINITIONS = {
    "customer": [
        ("_ingest_date", "VARCHAR(65535)"),
        ("_ingestion_time", "BIGINT"),
        ("_is_deleted", "BOOLEAN"),
        ("_load_date", "BIGINT"),
        ("_op_type", "VARCHAR(65535)"),
        ("_row_hash", "VARCHAR(65535)"),
        ("_source_system", "VARCHAR(65535)"),
        ("_topic_name", "VARCHAR(65535)"),
        ("address", "VARCHAR(65535)"),
        ("city", "VARCHAR(65535)"),
        ("connector", "VARCHAR(65535)"),
        ("customer_id", "VARCHAR(65535)"),
        ("date", "VARCHAR(65535)"),
        ("date_of_birth", "VARCHAR(65535)"),
        ("db", "VARCHAR(65535)"),
        ("email", "VARCHAR(65535)"),
        ("event_ts_ms", "BIGINT"),
        ("full_name", "VARCHAR(65535)"),
        ("gender", "VARCHAR(65535)"),
        ("name_id", "VARCHAR(65535)"),
        ("op", "VARCHAR(65535)"),
        ("phone", "VARCHAR(65535)"),
        ("place_of_birth", "VARCHAR(65535)"),
        ("postal_code", "VARCHAR(65535)"),
        ("registration", "VARCHAR(65535)"),
        ("schema", "VARCHAR(65535)"),
        ("source_ts_ms", "BIGINT"),
        ("table_name", "VARCHAR(65535)"),
        ("transaction", "VARCHAR(65535)"),
        ("ts_ns", "BIGINT"),
        ("ts_us", "BIGINT"),
        ("_process_date", "VARCHAR(65535)")
    ],

    "orders": [
        ("_ingest_date", "VARCHAR(65535)"),
        ("_ingestion_time", "BIGINT"),
        ("_is_deleted", "BOOLEAN"),
        ("_load_date", "BIGINT"),
        ("_op_type", "VARCHAR(65535)"),
        ("_row_hash", "VARCHAR(65535)"),
        ("_source_system", "VARCHAR(65535)"),
        ("_topic_name", "VARCHAR(65535)"),
        ("connector", "VARCHAR(65535)"),
        ("customer_id", "VARCHAR(65535)"),
        ("date", "VARCHAR(65535)"),
        ("db", "VARCHAR(65535)"),
        ("discount", "VARCHAR(65535)"),
        ("event_ts_ms", "BIGINT"),
        ("item_price", "VARCHAR(65535)"),
        ("op", "VARCHAR(65535)"),
        ("order_id", "VARCHAR(65535)"),
        ("payment_id", "VARCHAR(65535)"),
        ("product_id", "VARCHAR(65535)"),
        ("quantity", "VARCHAR(65535)"),
        ("schema", "VARCHAR(65535)"),
        ("shipping_id", "VARCHAR(65535)"),
        ("source_ts_ms", "BIGINT"),
        ("subtotal", "VARCHAR(65535)"),
        ("table_name", "VARCHAR(65535)"),
        ("total_amount", "VARCHAR(65535)"),
        ("transaction", "VARCHAR(65535)"),
        ("ts_ns", "BIGINT"),
        ("ts_us", "BIGINT"),
        ("_process_date", "VARCHAR(65535)")
    ],

    "payments": [
        ("_ingest_date", "VARCHAR(65535)"),
        ("_ingestion_time", "BIGINT"),
        ("_is_deleted", "BOOLEAN"),
        ("_load_date", "BIGINT"),
        ("_op_type", "VARCHAR(65535)"),
        ("_row_hash", "VARCHAR(65535)"),
        ("_source_system", "VARCHAR(65535)"),
        ("_topic_name", "VARCHAR(65535)"),
        ("amount", "VARCHAR(65535)"),
        ("connector", "VARCHAR(65535)"),
        ("date", "VARCHAR(65535)"),
        ("db", "VARCHAR(65535)"),
        ("event_ts_ms", "BIGINT"),
        ("op", "VARCHAR(65535)"),
        ("order_id", "VARCHAR(65535)"),
        ("payment_id", "VARCHAR(65535)"),
        ("payment_method", "VARCHAR(65535)"),
        ("payment_status", "VARCHAR(65535)"),
        ("schema", "VARCHAR(65535)"),
        ("source_ts_ms", "BIGINT"),
        ("table_name", "VARCHAR(65535)"),
        ("transaction", "VARCHAR(65535)"),
        ("ts_ns", "BIGINT"),
        ("ts_us", "BIGINT"),
        ("_process_date", "VARCHAR(65535)")
    ],

    "product": [
        ("_ingest_date", "VARCHAR(65535)"),
        ("_ingestion_time", "BIGINT"),
        ("_is_deleted", "BOOLEAN"),
        ("_load_date", "BIGINT"),
        ("_op_type", "VARCHAR(65535)"),
        ("_row_hash", "VARCHAR(65535)"),
        ("_source_system", "VARCHAR(65535)"),
        ("_topic_name", "VARCHAR(65535)"),
        ("base_price", "VARCHAR(65535)"),
        ("brand", "VARCHAR(65535)"),
        ("category", "VARCHAR(65535)"),
        ("connector", "VARCHAR(65535)"),
        ("date", "VARCHAR(65535)"),
        ("db", "VARCHAR(65535)"),
        ("event_ts_ms", "BIGINT"),
        ("op", "VARCHAR(65535)"),
        ("product_id", "VARCHAR(65535)"),
        ("product_name", "VARCHAR(65535)"),
        ("schema", "VARCHAR(65535)"),
        ("source_ts_ms", "BIGINT"),
        ("table_name", "VARCHAR(65535)"),
        ("transaction", "VARCHAR(65535)"),
        ("ts_ns", "BIGINT"),
        ("ts_us", "BIGINT"),
        ("_process_date", "VARCHAR(65535)")
    ],

    "shipping": [
        ("_ingest_date", "VARCHAR(65535)"),
        ("_ingestion_time", "BIGINT"),
        ("_is_deleted", "BOOLEAN"),
        ("_load_date", "BIGINT"),
        ("_op_type", "VARCHAR(65535)"),
        ("_row_hash", "VARCHAR(65535)"),
        ("_source_system", "VARCHAR(65535)"),
        ("_topic_name", "VARCHAR(65535)"),
        ("connector", "VARCHAR(65535)"),
        ("courier", "VARCHAR(65535)"),
        ("date", "VARCHAR(65535)"),
        ("db", "VARCHAR(65535)"),
        ("delivery", "VARCHAR(65535)"),
        ("event_ts_ms", "BIGINT"),
        ("op", "VARCHAR(65535)"),
        ("pick_up", "VARCHAR(65535)"),
        ("schema", "VARCHAR(65535)"),
        ("shipping_cost", "VARCHAR(65535)"),
        ("shipping_id", "VARCHAR(65535)"),
        ("shipping_status", "VARCHAR(65535)"),
        ("source_ts_ms", "BIGINT"),
        ("table_name", "VARCHAR(65535)"),
        ("transaction", "VARCHAR(65535)"),
        ("ts_ns", "BIGINT"),
        ("ts_us", "BIGINT"),
        ("_process_date", "VARCHAR(65535)")
    ]
}

# =====================================================
# Create Schema
# =====================================================
cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")

# =====================================================
# Create Tables (SAFE MODE)
# =====================================================
for table, columns in TABLE_DEFINITIONS.items():
    print(f"🛠 Processing table bronze.{table}")

    if RESET_BRONZE:
        print("⚠️ RESET_BRONZE = true → drop & recreate")
        cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{table};")

    cols_sql = ",\n    ".join([f"{col} {dtype}" for col, dtype in columns])

    ddl = f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA}.{table} (
        {cols_sql}
    )
    DISTSTYLE AUTO;
    """

    cur.execute(ddl)

cur.close()
conn.close()

print("🎉 Bronze DDL finished successfully (SAFE & PROD READY)")