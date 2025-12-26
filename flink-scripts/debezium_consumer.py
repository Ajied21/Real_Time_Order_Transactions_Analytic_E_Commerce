from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import KafkaSource
from pyflink.common import WatermarkStrategy

import json

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

kafka_source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_topics("orders.public.bronze_orders_raw") \
    .set_group_id("flink-orders-consumer") \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

stream = env.from_source(
    kafka_source,
    WatermarkStrategy.no_watermarks(),
    "Kafka Source"
)

def extract_after(value):
    data = json.loads(value)
    payload = data.get("payload", {})
    after = payload.get("after")
    op = payload.get("op")

    if after is not None and op in ["c", "u"]:
        return json.dumps(after)
    return None

processed = (
    stream
    .map(extract_after)
    .filter(lambda x: x is not None)
)

processed.print()

env.execute("Consume Debezium Orders")