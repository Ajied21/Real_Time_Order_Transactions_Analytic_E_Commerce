from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaOffsetsInitializer
)
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common import Types
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
from pyflink.common.serialization import Encoder
import json
import datetime

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_topics("data_staging.public.bronze_orders_raw") \
    .set_group_id("flink-orders-consumer") \
    .set_starting_offsets(
        KafkaOffsetsInitializer.earliest()
    ) \
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

sink = FileSink \
    .for_row_format(
        base_path="/opt/flink/output/orders",
        encoder=Encoder.simple_string_encoder("UTF-8")
    ) \
    .with_output_file_config(
        OutputFileConfig.builder()
        .with_part_prefix("orders")
        .with_part_suffix(".json")
        .build()
    ) \
    .build()

processed.sink_to(sink)

env.execute("Debezium Orders Kafka → JSON Files")