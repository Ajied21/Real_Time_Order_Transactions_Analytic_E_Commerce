from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common import Types
from pyflink.common.watermark_strategy import WatermarkStrategy
import json
import datetime

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_topics("data_staging.public.bronze_orders_raw") \
    .set_group_id("flink-orders-consumer") \
    .set_starting_offsets(KafkaSource.OffsetInitializer.earliest()) \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

stream = env.from_source(
    source,
    WatermarkStrategy.no_watermarks(),
    "Kafka Source"
)

def extract_after(value):
    data = json.loads(value)
    payload = data.get("payload", {})
    after = payload.get("after")
    op = payload.get("op")

    if after and op in ("c", "u"):
        after["_ingest_date"] = datetime.date.today().isoformat()
        return json.dumps(after)
    return None

processed = (
    stream
    .map(extract_after, output_type=Types.STRING())
    .filter(lambda x: x is not None)
)

processed.write_as_text(
    "/opt/flink/output/orders",
    file_system_write_mode="OVERWRITE"
)

env.execute("Debezium Orders Kafka → JSON Files")