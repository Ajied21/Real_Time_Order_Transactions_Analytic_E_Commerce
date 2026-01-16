import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

# =========================
# ARGUMENT
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--table", required=True)
parser.add_argument("--process_date", required=True)
args = parser.parse_args()

table = args.table
process_date = args.process_date

# =========================
# SPARK
# =========================
spark = (
    SparkSession.builder
    .appName(f"bronze-{table}")
    .getOrCreate()
)

# =========================
# READ S3 (ALL SUBTASK)
# =========================
input_path = (
    f"s3a://real-time-ecommerce-analytics/data-lake/"
    f"{table}/{process_date}--*/*.json"
)

df = spark.read.json(input_path)

if df.rdd.isEmpty():
    print(f"No data for {table} {process_date}")
    spark.stop()
    exit(0)

df = df.withColumn("_process_date", lit(process_date))

# =========================
# WRITE TO REDSHIFT
# =========================
(
    df.write
    .format("jdbc")
    .option("url", "jdbc:redshift://<endpoint>:5439/<db>")
    .option("dbtable", f"bronze.{table}")
    .option("user", "<user>")
    .option("password", "<password>")
    .option("driver", "com.amazon.redshift.jdbc42.Driver")
    .mode("append")
    .save()
)

spark.stop()