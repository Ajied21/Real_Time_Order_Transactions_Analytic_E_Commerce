from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import SimpleStringSchema, Encoder
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common import Types
from pyflink.datastream.connectors.file_system import (
    FileSink,
    OutputFileConfig,
    RollingPolicy,
)

import json
import os
import datetime

# =========================================================
# CONFIG
# =========================================================
BOOTSTRAP_SERVERS = "kafka:9092"

KAFKA_TOPICS = [
    "data_lake.public.bronze_customer_raw",
    "data_lake.public.bronze_orders_raw",
    "data_lake.public.bronze_payments_raw",
    "data_lake.public.bronze_product_raw",
    "data_lake.public.bronze_shipping_raw",
]

TABLE_TO_FOLDER = {
    "bronze_customer_raw": "customer",
    "bronze_orders_raw": "orders",
    "bronze_payments_raw": "payments",
    "bronze_product_raw": "product",
    "bronze_shipping_raw": "shipping",
}

BASE_OUTPUT_PATH = "s3a://real-time-ecommerce-analytics/data-lake"

# =========================================================
# MODE
# =========================================================
FLINK_MODE = os.getenv("FLINK_MODE", "normal")  # normal | backfill
BACKFILL_FROM_DATE = os.getenv("BACKFILL_FROM_DATE")  # YYYY-MM-DD
BACKFILL_FROM_HOUR = int(os.getenv("BACKFILL_FROM_HOUR", "0"))

INGEST_DATE = (
    BACKFILL_FROM_DATE
    if FLINK_MODE == "backfill" and BACKFILL_FROM_DATE
    else datetime.date.today().isoformat()
)

WIB = datetime.timezone(datetime.timedelta(hours=7))

# =========================================================
# FLINK ENV
# =========================================================
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)
env.enable_checkpointing(5000)

# =========================================================
# KAFKA OFFSET STRATEGY (FIXED)
# =========================================================
if FLINK_MODE == "backfill":
    if not BACKFILL_FROM_DATE:
        raise ValueError("BACKFILL_FROM_DATE wajib di-set saat backfill")

    backfill_dt = datetime.datetime.strptime(
        BACKFILL_FROM_DATE, "%Y-%m-%d"
    ).replace(hour=BACKFILL_FROM_HOUR)

    starting_offsets = KafkaOffsetsInitializer.timestamp(
        int(backfill_dt.timestamp() * 1000)
    )

    print(f"[BACKFILL] from {BACKFILL_FROM_DATE} hour {BACKFILL_FROM_HOUR}")

else:
    # ✅ PyFlink TIDAK punya OffsetResetStrategy
    starting_offsets = KafkaOffsetsInitializer.latest()

# =========================================================
# KAFKA SOURCE
# =========================================================
source = (
    KafkaSource.builder()
    .set_bootstrap_servers(BOOTSTRAP_SERVERS)
    .set_topics(*KAFKA_TOPICS)
    .set_group_id("flink-bronze-consumer")
    .set_starting_offsets(starting_offsets)
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

stream = env.from_source(
    source,
    WatermarkStrategy.no_watermarks(),
    "Kafka Debezium Multi Topic",
)

# =========================================================
# TRANSFORM
# =========================================================
def extract_payload(value):
    try:
        data = json.loads(value)
        payload = data.get("payload")
        if not payload:
            return None

        after = payload.get("after")
        source = payload.get("source")
        op = payload.get("op")

        if not after or op not in ("c", "u", "r"):
            return None

        # ===============================
        # FIX DATE (UTC -> WIB)
        # ===============================
        if "date" in after:
            dt_utc = datetime.datetime.fromisoformat(
                after["date"]
            ).replace(tzinfo=datetime.timezone.utc)

            dt_wib = dt_utc.astimezone(WIB)
            after["date"] = dt_wib.date().isoformat()

            # backfill filter
            if FLINK_MODE == "backfill":
                if after["date"] != BACKFILL_FROM_DATE:
                    return None

        table = source.get("table")

        result = {
            "op": op,
            "db": source.get("db"),
            "schema": source.get("schema"),
            "table_name": table,
            "_ingest_date": INGEST_DATE,
        }

        result.update(after)

        return table, json.dumps(result)

    except Exception as e:
        print("ERROR:", e)
        return None


processed = (
    stream
    .map(
        extract_payload,
        output_type=Types.TUPLE([Types.STRING(), Types.STRING()]),
    )
    .filter(lambda x: x is not None)
)

processed.print()

# =========================================================
# FILE SINK (S3)
# =========================================================
for table, folder in TABLE_TO_FOLDER.items():
    sink = (
        FileSink.for_row_format(
            f"{BASE_OUTPUT_PATH}/{folder}/{INGEST_DATE}",
            Encoder.simple_string_encoder("UTF-8"),
        )
        .with_output_file_config(
            OutputFileConfig.builder()
            .with_part_prefix(folder)
            .with_part_suffix(".json")
            .build()
        )
        .with_rolling_policy(RollingPolicy.on_checkpoint_rolling_policy())
        .build()
    )

    (
        processed
        .filter(lambda x, t=table: x[0] == t)
        .map(lambda x: x[1], output_type=Types.STRING())
        .sink_to(sink)
    )

# =========================================================
# EXECUTE
# =========================================================
env.execute("Flink Kafka → S3 Data Lake")