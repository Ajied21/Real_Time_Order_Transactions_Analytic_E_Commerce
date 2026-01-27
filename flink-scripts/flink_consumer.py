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
    "data_staging.public.bronze_customer_raw",
    "data_staging.public.bronze_orders_raw",
    "data_staging.public.bronze_payments_raw",
    "data_staging.public.bronze_product_raw",
    "data_staging.public.bronze_shipping_raw",
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
# MODE (NORMAL / BACKFILL)
# =========================================================
FLINK_MODE = os.getenv("FLINK_MODE", "normal")  # normal | backfill
BACKFILL_FROM_DATE = os.getenv("BACKFILL_FROM_DATE")  # YYYY-MM-DD
BACKFILL_FROM_HOUR = int(os.getenv("BACKFILL_FROM_HOUR", "0"))

INGEST_DATE = datetime.date.today().isoformat()

# =========================================================
# FLINK ENVIRONMENT
# =========================================================
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

# wajib untuk FileSink & offset commit
env.enable_checkpointing(5000)

# =========================================================
# KAFKA OFFSET STRATEGY
# =========================================================
if FLINK_MODE == "backfill":
    if not BACKFILL_FROM_DATE:
        raise ValueError(
            "BACKFILL_FROM_DATE wajib di-set saat FLINK_MODE=backfill"
        )

    backfill_dt = datetime.datetime.strptime(
        BACKFILL_FROM_DATE, "%Y-%m-%d"
    ).replace(hour=BACKFILL_FROM_HOUR)

    backfill_ts_ms = int(backfill_dt.timestamp() * 1000)

    print(
        f"[BACKFILL MODE] Replay Kafka from {backfill_dt} "
        f"(timestamp_ms={backfill_ts_ms})"
    )

    starting_offsets = KafkaOffsetsInitializer.timestamp(backfill_ts_ms)

else:
    print("[NORMAL MODE] Using committed Kafka offsets")

    starting_offsets = KafkaOffsetsInitializer.committed_offsets(
        KafkaOffsetsInitializer.OffsetResetStrategy.LATEST
    )

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
# TRANSFORM: Debezium → (table, json_string)
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

        table = source.get("table")

        result = {
            "op": op,
            "connector": source.get("connector"),
            "db": source.get("db"),
            "schema": source.get("schema"),
            "table_name": table,
            "source_ts_ms": source.get("ts_ms"),
            "event_ts_ms": payload.get("ts_ms"),
            "ts_us": payload.get("ts_us"),
            "ts_ns": payload.get("ts_ns"),
            "transaction": payload.get("transaction"),
            "_ingest_date": INGEST_DATE,
        }

        # actual row data
        result.update(after)

        return table, json.dumps(result)

    except Exception as e:
        print("JSON ERROR:", e)
        return None


processed = (
    stream
    .map(
        extract_payload,
        output_type=Types.TUPLE([Types.STRING(), Types.STRING()]),
    )
    .filter(lambda x: x is not None)
)

# DEBUG (optional)
processed.print()

# =========================================================
# FILE SINK PER TABLE (PARTITION BY INGEST DATE)
# =========================================================
for table, folder in TABLE_TO_FOLDER.items():

    sink_path = (
        f"{BASE_OUTPUT_PATH}/{folder}/_ingest_date={INGEST_DATE}"
    )

    sink = (
        FileSink.for_row_format(
            base_path=sink_path,
            encoder=Encoder.simple_string_encoder("UTF-8"),
        )
        .with_output_file_config(
            OutputFileConfig.builder()
            .with_part_prefix(folder)
            .with_part_suffix(".json")
            .build()
        )
        .with_rolling_policy(
            RollingPolicy.on_checkpoint_rolling_policy()
        )
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
env.execute(
    "Flink Bronze Multi Topic → S3 "
    "(Normal & Backfill Mode, Partitioned by Ingest Date)")