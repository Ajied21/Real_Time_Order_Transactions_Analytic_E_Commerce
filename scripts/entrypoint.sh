#!/bin/bash
set -euo pipefail

# Inisialisasi Database Airflow
airflow db migrate
airflow connections create-default-connections || true

# === Koneksi Postgres ===
POSTGRES_URI="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER_NAME}:${POSTGRES_PORT}/${POSTGRES_DB}"

# Cek apakah koneksi sudah ada
if ! airflow connections get 'postgres_main' >/dev/null 2>&1; then
    airflow connections add 'postgres_main' --conn-uri "$POSTGRES_URI"
else
    echo "Connection postgres_main sudah ada — skip"
fi


# === Koneksi Spark ===
if ! airflow connections get 'spark_main' >/dev/null 2>&1; then
    airflow connections add 'spark_main' \
        --conn-type 'spark' \
        --conn-host "$SPARK_MASTER_HOST_NAME" \
        --conn-port "$SPARK_MASTER_PORT"
else
    echo "Connection spark_main sudah ada — skip"
fi

# Jalankan apiserver
exec airflow api-server
