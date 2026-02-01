import argparse
import os
from datetime import date, datetime, timedelta
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from dotenv import load_dotenv

# =====================================================
# CONFIG
# =====================================================
TABLE_NAME = "product"
S3_BASE_PATH = "s3a://real-time-ecommerce-analytics/redshift/product/"

# =========================================================
# ENV
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f".env not found: {ENV_PATH}")

load_dotenv(ENV_PATH)

# =====================================================
# ARGUMENT
# =====================================================
parser = argparse.ArgumentParser()
parser.add_argument("--process_date")
parser.add_argument("--run_latest", action="store_true")
parser.add_argument("--run_all", action="store_true")
args = parser.parse_args()

# =====================================================
# SPARK (ENABLE S3A)
# =====================================================
spark = (
    SparkSession.builder
    .appName(f"Ingestion-{TABLE_NAME}")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID"))
    .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY"))
    .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-southeast-1.amazonaws.com")
    .getOrCreate()
    )

# =====================================================
# REDSHIFT
# =====================================================
def rs_conn():
    return psycopg2.connect(
        host=os.getenv("REDSHIFT_HOST"),
        dbname=os.getenv("REDSHIFT_DB"),
        user=os.getenv("REDSHIFT_USER"),
        password=os.getenv("REDSHIFT_PASSWORD"),
        port=os.getenv("REDSHIFT_PORT"),
    )

def max_date():
    conn = rs_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT MAX(date) FROM bronze.{TABLE_NAME}")
    d = cur.fetchone()[0]
    cur.close(); conn.close()
    return d

def delete_date(d):
    conn = rs_conn()
    cur = conn.cursor()
    cur.execute(
        f"DELETE FROM bronze.{TABLE_NAME} WHERE date = %s",
        (d,)
    )
    conn.commit()
    cur.close(); conn.close()

# =====================================================
# DATE LOGIC
# =====================================================
if args.process_date:
    dates = [datetime.strptime(args.process_date, "%Y-%m-%d").date()]

elif args.run_latest:
    last = max_date()
    dates = [date.today()] if last is None else [last + timedelta(days=1)]

elif args.run_all:
    start = date(2026, 1, 1)
    end = date.today()
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

else:
    raise ValueError("Pilih --process_date / --run_latest / --run_all")

# =====================================================
# MAIN
# =====================================================
for d in dates:
    s3_path = f"{S3_BASE_PATH}{d}/"
    print(f"Processing {TABLE_NAME} date={d}")
    print(f"Reading from {s3_path}")

    try:
        df = spark.read.parquet(s3_path)
    except Exception:
        print("No data folder, skip")
        continue

    if df.rdd.isEmpty():
        print("Empty data, skip")
        continue

    # add partition column
    df = df.withColumn("date", lit(str(d)))

    # delete old data
    delete_date(d)

    # write to Redshift
    df.write \
        .format("jdbc") \
        .option(
            "url",
            f"jdbc:postgresql://{os.getenv('REDSHIFT_HOST')}:{os.getenv('REDSHIFT_PORT')}/{os.getenv('REDSHIFT_DB')}"
        ) \
        .option("dbtable", f"bronze.{TABLE_NAME}") \
        .option("user", os.getenv("REDSHIFT_USER")) \
        .option("password", os.getenv("REDSHIFT_PASSWORD")) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

    print(f"SUCCESS load {TABLE_NAME} {d}")

spark.stop()