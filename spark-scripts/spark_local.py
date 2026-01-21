import argparse
import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from py4j.java_gateway import java_import

# =========================
# LOAD ENV
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "secret_aws", ".env")
load_dotenv(ENV_PATH)

# =========================
# ARGUMENT
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--table", help="custom table (customer, orders, etc)")
parser.add_argument("--process_date", help="custom date-hour (YYYY-MM-DD--HH)")
parser.add_argument("--run_all", action="store_true")
args = parser.parse_args()

# =========================
# SPARK SESSION
# =========================
spark = (
    SparkSession.builder
    .appName("data-ingestion")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.EnvironmentVariableCredentialsProvider"
    )
    .getOrCreate()
)

sc = spark.sparkContext
hadoop_conf = sc._jsc.hadoopConfiguration()

java_import(sc._gateway.jvm, "org.apache.hadoop.fs.FileSystem")
java_import(sc._gateway.jvm, "org.apache.hadoop.fs.Path")
java_import(sc._gateway.jvm, "java.net.URI")

# =========================
# BASE PATH
# =========================
S3_BASE = "s3a://real-time-ecommerce-analytics/data-lake"
OUTPUT_BASE = "/opt/app/output/bronze_csv"

# =========================
# HELPER
# =========================
def get_fs(path):
    uri = sc._gateway.jvm.URI(path)
    return sc._gateway.jvm.FileSystem.get(uri, hadoop_conf)

def list_dirs(path):
    fs = get_fs(path)
    p = sc._gateway.jvm.Path(path)
    if not fs.exists(p):
        return []
    return [
        f.getPath().getName()
        for f in fs.listStatus(p)
        if f.isDirectory()
    ]

# =========================
# MAIN LOGIC
# =========================
if args.run_all:
    tables = list_dirs(S3_BASE)
elif args.table:
    tables = [args.table]
else:
    raise ValueError("Gunakan --run_all atau --table")

for table in tables:
    table_path = f"{S3_BASE}/{table}"

    if args.process_date:
        dates = [args.process_date]
    else:
        dates = list_dirs(table_path)

    for d in dates:
        input_path = f"{table_path}/{d}/*.json"
        output_path = f"{OUTPUT_BASE}/{table}/{d}"

        print(f"READ  : {input_path}")
        print(f"WRITE : {output_path}")

        df = spark.read.json(input_path)

        if df.rdd.isEmpty():
            print("NO DATA, SKIP")
            continue

        df = df.withColumn("_process_date", lit(d))

        df.coalesce(1) \
          .write \
          .mode("overwrite") \
          .option("header", True) \
          .csv(output_path)

spark.stop()