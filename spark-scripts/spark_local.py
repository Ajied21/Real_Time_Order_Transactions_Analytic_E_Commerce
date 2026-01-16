import argparse
import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

# =========================
# LOAD .env
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "secret_aws", ".env")

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f".env not found: {ENV_PATH}")

load_dotenv(ENV_PATH)

# =========================
# ARGUMENT
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--table", required=True)
parser.add_argument("--process_date", required=True)
args = parser.parse_args()

# =========================
# SPARK SESSION
# =========================
spark = (
    SparkSession.builder
    .appName(f"bronze-{args.table}")
    .config(
        "spark.hadoop.fs.s3a.impl",
        "org.apache.hadoop.fs.s3a.S3AFileSystem"
    )
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.EnvironmentVariableCredentialsProvider"
    )
    .getOrCreate()
)

# =========================
# PATH
# =========================
INPUT_PATH = (
    f"s3a://real-time-ecommerce-analytics/"
    f"data-lake/{args.table}/{args.process_date}--*/*.json"
)

OUTPUT_PATH = (
    f"/home/spark-test/output/{args.table}/{args.process_date}"
)

print("READ :", INPUT_PATH)
print("WRITE:", OUTPUT_PATH)

# =========================
# PROCESS
# =========================
df = spark.read.json(INPUT_PATH)

if df.rdd.isEmpty():
    print("NO DATA FOUND")
    spark.stop()
    exit(0)

df = df.withColumn("_process_date", lit(args.process_date))

df.show(5, truncate=False)

df.write.mode("overwrite").json(OUTPUT_PATH)

spark.stop()