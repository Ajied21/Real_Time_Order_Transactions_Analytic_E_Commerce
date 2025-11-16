#!/bin/bash
set -euo pipefail

# Inisialisasi DB
airflow db migrate
airflow connections create-default-connections

# Tambahkan connection Postgres
airflow connections add 'postgres_main' \
    --conn-type 'postgres' \
    --conn-login $POSTGRES_USER \
    --conn-password $POSTGRES_PASSWORD \
    --conn-host $POSTGRES_CONTAINER_NAME \
    --conn-port $POSTGRES_PORT \
    --conn-schema $POSTGRES_DB \

# Tambahkan connection Spark
export SPARK_FULL_HOST_NAME="spark://$SPARK_MASTER_HOST_NAME"
airflow connections add 'spark_main' \
    --conn-type 'spark' \
    --conn-host $SPARK_FULL_HOST_NAME \
    --conn-port $SPARK_MASTER_PORT \

# Jalankan webserver **tanpa `--skip-if-exists`**
exec airflow webserver