import argparse
import os
from pyspark.sql import SparkSession

# =========================
# ARGUMENT
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--table", required=True)
parser.add_argument("--process_date", required=True)
args = parser.parse_args()

# =========================
# CONFIG
# =========================
S3_SOURCE = f"s3://real-time-ecommerce-analytics/data-lake/{args.table}/{args.process_date}/"

REDSHIFT_URL = (
    f"jdbc:redshift://{os.getenv('REDSHIFT_HOST')}:5439/"
    f"{os.getenv('REDSHIFT_DB')}"
)

REDSHIFT_PROPERTIES = {
    "user": os.getenv("REDSHIFT_USER"),
    "password": os.getenv("REDSHIFT_PASSWORD"),
    "driver": "com.amazon.redshift.jdbc42.Driver"
}

TARGET_TABLE = f"bronze.{args.table}"

# =========================
# SPARK
# =========================
spark = SparkSession.builder.appName(
    f"ingest-{args.table}-{args.process_date}"
).getOrCreate()

# =========================
# READ DATA (ONLY NEW DATE)
# =========================
df = spark.read.parquet(S3_SOURCE)

# Optional: add partition column
df = df.withColumn("process_date", lit(args.process_date))

# =========================
# WRITE TO REDSHIFT
# =========================
df.write \
  .format("jdbc") \
  .option("url", REDSHIFT_URL) \
  .option("dbtable", TARGET_TABLE) \
  .option("user", REDSHIFT_PROPERTIES["user"]) \
  .option("password", REDSHIFT_PROPERTIES["password"]) \
  .mode("append") \
  .save()

spark.stop()

print(f"✅ Ingestion {args.table} {args.process_date} selesai")