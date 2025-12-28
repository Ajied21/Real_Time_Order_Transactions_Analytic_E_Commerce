from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema, Encoder
from pyflink.datastream.connectors.kafka import KafkaSource
from pyflink.datastream.connectors.file_system import (
    FileSink,
    OutputFileConfig,
    RollingPolicy
)
from pyflink.common import WatermarkStrategy, Types
import json
import datetime

# ======================================
# ENVIRONMENT
# ======================================
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

# ======================================
# KAFKA SOURCE (DEBEZIUM)
# ======================================
kafka_source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_topics("orders.public.bronze_orders_raw") \
    .set_group_id("flink-orders-consumer") \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

stream = env.from_source(
    kafka_source,
    WatermarkStrategy.no_watermarks(),
    "Kafka Debezium Source"
)

# ======================================
# TRANSFORM
# ======================================
def extract_after(value):
    data = json.loads(value)
    payload = data.get("payload", {})
    after = payload.get("after")
    op = payload.get("op")

    if after is not None and op in ("c", "u"):
        event_date = datetime.date.today().isoformat()
        # partition manual per hari
        return f"date={event_date}/{json.dumps(after)}"

    return None

processed = (
    stream
    .map(extract_after, output_type=Types.STRING())
    .filter(lambda x: x is not None)
)

# ======================================
# FILE SINK (LOCAL)
# ======================================
file_sink = FileSink \
    .for_row_format(
        base_path="/opt/flink/output/orders",
        encoder=Encoder.simple_string_encoder()
    ) \
    .with_output_file_config(
        OutputFileConfig.builder()
        .with_part_prefix("orders")
        .with_part_suffix(".json")
        .build()
    ) \
    .with_rolling_policy(
        RollingPolicy.default_rolling_policy()
    ) \
    .build()

processed.sink_to(file_sink)

# ======================================
# EXECUTE
# ======================================
env.execute("Debezium Orders Kafka to Local Daily Files")