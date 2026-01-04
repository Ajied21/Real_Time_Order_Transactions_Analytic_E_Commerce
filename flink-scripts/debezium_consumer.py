from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common import Types
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig, RollingPolicy
from pyflink.common.serialization import Encoder
import json
import datetime


# =========================================================
# Config
# =========================================================
BOOTSTRAP_SERVERS = "kafka:9092"

TOPICS = {
    "data_staging.public.bronze_customer_raw": "customer",
    "data_staging.public.bronze_orders_raw": "orders",
    "data_staging.public.bronze_payments_raw": "payments",
    "data_staging.public.bronze_product_raw": "product",
    "data_staging.public.bronze_shipping_raw": "shipping",
}

BASE_OUTPUT_PATH = "/opt/flink/output"


# =========================================================
# Flink Environment
# =========================================================
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)
env.enable_checkpointing(5000)


# =========================================================
# Kafka Source (MULTI TOPIC)
# =========================================================
source = (
    KafkaSource.builder()
    .set_bootstrap_servers(BOOTSTRAP_SERVERS)
    .set_topics(list(TOPICS.keys()))
    .set_group_id("flink-bronze-consumer")
    .set_starting_offsets(KafkaOffsetsInitializer.earliest())
    .set_value_only_deserializer(SimpleStringSchema())
    .build()
)

stream = env.from_source(
    source,
    WatermarkStrategy.no_watermarks(),
    "Kafka Debezium Multi Topic"
)


# =========================================================
# Transform: Debezium → Flat JSON
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

        result = {}
        result["op"] = op
        result.update(after)

        if source:
            result["connector"] = source.get("connector")
            result["db"] = source.get("db")
            result["schema"] = source.get("schema")
            result["table"] = source.get("table")
            result["source_ts_ms"] = source.get("ts_ms")

        result["event_ts_ms"] = payload.get("ts_ms")
        result["ts_us"] = payload.get("ts_us")
        result["ts_ns"] = payload.get("ts_ns")
        result["transaction"] = payload.get("transaction")
        result["_ingest_date"] = datetime.date.today().isoformat()

        return json.dumps(result)

    except Exception as e:
        print("JSON ERROR:", e)
        return None


processed = (
    stream
    .map(extract_payload, output_type=Types.STRING())
    .filter(lambda x: x is not None)
)


# =========================================================
# Sink PER TOPIC
# =========================================================
today = datetime.date.today().isoformat()

for topic, folder in TOPICS.items():
    sink = (
        FileSink.for_row_format(
            base_path=f"{BASE_OUTPUT_PATH}/{folder}/{today}",
            encoder=Encoder.simple_string_encoder("UTF-8"),
        )
        .with_output_file_config(
            OutputFileConfig.builder()
            .with_part_prefix(folder)
            .with_part_suffix(".json")
            .build()
        )
        .with_rolling_policy(RollingPolicy.default_rolling_policy())
        .build()
    )

    (
        processed
        .filter(lambda x, t=topic: f'"table":"{t.split(".")[-1]}"' in x)
        .sink_to(sink)
    )


# =========================================================
# Execute Job
# =========================================================
env.execute("Debezium Multi Topic → Bronze Files")