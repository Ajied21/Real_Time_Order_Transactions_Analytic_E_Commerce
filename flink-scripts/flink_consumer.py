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

# local
# BASE_OUTPUT_PATH = "/opt/flink/output"

# cloud (aws/s3)
BASE_OUTPUT_PATH = "s3a://real-time-ecommerce-analytics/data-lake"

TODAY = datetime.date.today().isoformat()

# =========================================================
# FLINK ENVIRONMENT
# =========================================================
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

# WAJIB untuk FileSink
env.enable_checkpointing(5000)


# =========================================================
# KAFKA SOURCE (MULTI TOPIC)
# =========================================================
source = (
    KafkaSource.builder()
    .set_bootstrap_servers(BOOTSTRAP_SERVERS)
    .set_topics(*KAFKA_TOPICS)
    .set_group_id("flink-bronze-consumer")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
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

        result = {}
        result["op"] = op
        result.update(after)

        result["connector"] = source.get("connector")
        result["db"] = source.get("db")
        result["schema"] = source.get("schema")
        result["table"] = table
        result["source_ts_ms"] = source.get("ts_ms")

        result["event_ts_ms"] = payload.get("ts_ms")
        result["ts_us"] = payload.get("ts_us")
        result["ts_ns"] = payload.get("ts_ns")
        result["transaction"] = payload.get("transaction")
        result["_ingest_date"] = TODAY

        return table, json.dumps(result)

    except Exception as e:
        print("JSON ERROR:", e)
        return None


processed = (
    stream
    .map(extract_payload, output_type=Types.TUPLE([Types.STRING(), Types.STRING()]))
    .filter(lambda x: x is not None)
)

# DEBUG (lihat di log taskmanager)
processed.print()


# =========================================================
# FILE SINK PER TABLE (AMAN & STABIL)
# =========================================================
for table, folder in TABLE_TO_FOLDER.items():

    sink = (
        FileSink.for_row_format(
            base_path=f"{BASE_OUTPUT_PATH}/{folder}",
            encoder=Encoder.simple_string_encoder("UTF-8"),
        )
        .with_output_file_config(
            OutputFileConfig.builder()
            .with_part_prefix(folder)
            .with_part_suffix(".json")
            .build()
        )
        # ⬅️ PENTING: file langsung ditulis saat checkpoint
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
env.execute("Flink Transform  Multi Topic → Bronze Files")