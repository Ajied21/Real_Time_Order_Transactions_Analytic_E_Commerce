import argparse
import os
from datetime import datetime, date, timedelta
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from dotenv import load_dotenv

# =========================================================
# ENV
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f".env not found: {ENV_PATH}")

load_dotenv(ENV_PATH)

# =========================================================
# ARGUMENTS
# =========================================================
parser = argparse.ArgumentParser()
parser.add_argument("--table", required=True)
parser.add_argument("--process_date", required=False)
parser.add_argument("--start_date", required=False)
parser.add_argument("--end_date", required=False)
args = parser.parse_args()

# =========================================================
# DATE RESOLUTION
# =========================================================
def resolve_dates(args):
    if args.process_date:
        return [args.process_date]

    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        if start > end:
            raise ValueError("start_date cannot be after end_date")

        dates = []
        d = start
        while d <= end:
            dates.append(d.strftime("%Y-%m-%d"))
            d += timedelta(days=1)
        return dates

    return [(date.today() - timedelta(days=1)).strftime("%Y-%m-%d")]

PROCESS_DATES = resolve_dates(args)

# =========================================================
# CONFIG
# =========================================================
REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
REDSHIFT_DB = os.getenv("REDSHIFT_DB")
REDSHIFT_USER = os.getenv("REDSHIFT_USER")
REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")
REDSHIFT_PORT = os.getenv("REDSHIFT_PORT")

REDSHIFT_URL = f"jdbc:redshift://{REDSHIFT_HOST}:{REDSHIFT_PORT}/{REDSHIFT_DB}"
TARGET_TABLE = f"bronze.{args.table}"

# =========================================================
# IDEMPOTENT DELETE
# =========================================================
def delete_existing_data(table, process_date):
    conn = psycopg2.connect(
        host=REDSHIFT_HOST,
        port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD,
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'bronze'
          AND table_name = '{table}'
          AND column_name = 'process_date'
    """)

    if not cur.fetchone():
        raise RuntimeError(
            f"Column process_date does not exist in bronze.{table}"
        )

    cur.execute(f"""
        DELETE FROM bronze.{table}
        WHERE process_date = '{process_date}'
    """)

    cur.close()
    conn.close()

# =========================================================
# SPARK
# =========================================================
spark = (
    SparkSession.builder
    .appName(f"ingest-{args.table}")
    .getOrCreate()
)

# =========================================================
# MAIN LOOP
# =========================================================
for process_date in PROCESS_DATES:
    print(f"🚀 Processing {args.table} | {process_date}")

    S3_SOURCE = (
        f"s3a://real-time-ecommerce-analytics/redshift/"
        f"{args.table}/{process_date}--*/"
    )

    try:
        df = spark.read.parquet(S3_SOURCE)

        if df.rdd.isEmpty():
            print(f"⚠️ SKIP {args.table} | {process_date} (no data)")
            continue

        df = df.withColumn("process_date", lit(process_date))

        delete_existing_data(args.table, process_date)

        df.write \
          .format("jdbc") \
          .option("url", REDSHIFT_URL) \
          .option("dbtable", TARGET_TABLE) \
          .option("user", REDSHIFT_USER) \
          .option("password", REDSHIFT_PASSWORD) \
          .mode("append") \
          .save()

        print(f"✅ SUCCESS {args.table} | {process_date}")

    except Exception as e:
        print(f"❌ FAILED {args.table} | {process_date}")
        print(str(e))
        continue

spark.stop()
print("🎉 INGESTION FINISHED")