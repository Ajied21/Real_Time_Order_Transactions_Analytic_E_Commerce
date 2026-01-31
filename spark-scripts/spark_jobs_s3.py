import argparse
import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from py4j.java_gateway import java_import

# =====================================================
# LOAD ENV (.env)
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f".env not found: {ENV_PATH}")

load_dotenv(ENV_PATH)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise RuntimeError("AWS credential not found in .env")

# =====================================================
# ARGUMENT
# =====================================================
parser = argparse.ArgumentParser(description="Spark Bronze to S3")
parser.add_argument("--table", help="specific table (customer, orders, etc)")
parser.add_argument("--process_date", help="specific date folder (ex: 2026-01-28)")
parser.add_argument("--run_all", action="store_true", help="run all tables & dates")
args = parser.parse_args()

# =====================================================
# SPARK SESSION
# =====================================================
spark = (
    SparkSession.builder
    .appName("bronze-to-s3")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY_ID)
    .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.endpoint", f"s3.{AWS_REGION}.amazonaws.com")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .getOrCreate()
)

sc = spark.sparkContext
hadoop_conf = sc._jsc.hadoopConfiguration()

java_import(sc._gateway.jvm, "org.apache.hadoop.fs.FileSystem")
java_import(sc._gateway.jvm, "org.apache.hadoop.fs.Path")
java_import(sc._gateway.jvm, "java.net.URI")

# =====================================================
# PATH CONFIG
# =====================================================
S3_BASE = "s3a://real-time-ecommerce-analytics/data-lake"
OUTPUT_BASE = "s3a://real-time-ecommerce-analytics/redshift"

# =====================================================
# HELPER FUNCTIONS
# =====================================================
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

# =====================================================
# RESOLVE TABLES
# =====================================================
if args.table:
    tables = [args.table]
elif args.run_all:
    tables = list_dirs(S3_BASE)
else:
    raise ValueError("Gunakan --table atau --run_all")

# =====================================================
# MAIN PROCESS
# =====================================================
for table in tables:
    table_path = f"{S3_BASE}/{table}"

    if args.process_date:
        dates = [args.process_date]
    else:
        dates = list_dirs(table_path)

    for d in dates:
        # 🔥 FIX UTAMA: recursive read (handle folder jam)
        input_path = f"{table_path}/{d}/**/*.json"
        output_path = f"{OUTPUT_BASE}/{table}/{d}"

        print("=" * 80)
        print(f"TABLE : {table}")
        print(f"DATE  : {d}")
        print(f"READ  : {input_path}")
        print(f"WRITE : {output_path}")

        try:
            df = spark.read.json(input_path)
        except Exception as e:
            print(f"❌ READ FAILED: {e}")
            continue

        if df.rdd.isEmpty():
            print("⚠️ NO DATA, SKIP")
            continue

        df = df.withColumn("_process_date", lit(d))

        (
            df.write
            .mode("overwrite")
            .parquet(output_path)
        )

        print("✅ WRITE SUCCESS")

spark.stop()