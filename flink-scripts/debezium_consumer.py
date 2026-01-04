from pyflink.table import EnvironmentSettings, TableEnvironment

settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(settings)

t_env.execute_sql("""
CREATE TABLE kafka_orders (
    `payload` STRING
) WITH (
    'connector' = 'kafka',
    'topic' = 'data_staging.public.bronze_orders_raw',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'flink-orders-consumer',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'raw'
)
""")

t_env.execute_sql("""
CREATE TABLE orders_parquet (
    after_json STRING,
    source_json STRING,
    op STRING,
    ts_ms BIGINT,
    ts_us BIGINT,
    ts_ns BIGINT,
    transaction_json STRING,
    ingest_date STRING
) PARTITIONED BY (ingest_date)
WITH (
    'connector' = 'filesystem',
    'path' = '/opt/flink/output/orders_parquet',
    'format' = 'parquet'
)
""")

t_env.execute_sql("""
INSERT INTO orders_parquet
SELECT
    JSON_VALUE(payload, '$.payload.after'),
    JSON_VALUE(payload, '$.payload.source'),
    JSON_VALUE(payload, '$.payload.op'),
    CAST(JSON_VALUE(payload, '$.payload.ts_ms') AS BIGINT),
    CAST(JSON_VALUE(payload, '$.payload.ts_us') AS BIGINT),
    CAST(JSON_VALUE(payload, '$.payload.ts_ns') AS BIGINT),
    JSON_VALUE(payload, '$.payload.transaction'),
    CAST(CURRENT_DATE AS STRING)
FROM kafka_orders
""")