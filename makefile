include .env

help:
	@echo "## docker-networks		- Build Docker Networks (amd64)"
	@echo "## docker-build			- Build Docker Images (amd64)"
	@echo "## spark					- Run a Spark cluster, rebuild the postgres container, then create the destination tables "
	@echo "## kafka					- Spinup kafka cluster"
	@echo "## flink					- Create the destination and transformation tables"
	@echo "## airflow				- Build to orchestrator"
	@echo "## postgres				- Run database of relationship"
	@echo "## grafana				- Monitoring analysis data"
	@echo "## clean					- Cleanup all running containers related to the challenge."

docker-networks:
	@echo '__________________________________________________________'
	@echo 'Building Docker Networks for Batching and Streaming Processing ...'
	@echo '__________________________________________________________'
	@if docker network inspect Batching-Processing >/dev/null 2>&1; then \
		echo "Network 'Batching-Processing' already exists."; \
	else \
		echo "Creating network 'Batching-Processing'..."; \
		docker network create Batching-Processing; \
	fi
	@echo '__________________________________________________________'
	@if docker network inspect Streaming-Processing >/dev/null 2>&1; then \
		echo "Network 'Streaming-Processing' already exists."; \
	else \
		echo "Creating network 'Streaming-Processing'..."; \
		docker network create Streaming-Processing; \
	fi
	@echo '==========================================================='

postgres-create:
	@docker build -t Staging/postgres -f ./docker/Dockerfile.postgres .
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-postgres.yml --env-file .env up -d
	@echo '__________________________________________________________'
	@echo 'Postgres container created at port ${POSTGRES_PORT}...'
	@echo '__________________________________________________________'
	@echo 'Postgres Docker Host	: ${POSTGRES_CONTAINER_NAME}' &&\
		echo 'Postgres Account	: ${POSTGRES_USER}' &&\
		echo 'Postgres password	: ${POSTGRES_PASSWORD}' &&\
		echo 'Postgres Db		: ${POSTGRES_DB}'
	@echo '==========================================================='

postgres-create-warehouse-and-backup:
	@echo '__________________________________________________________'
	@echo 'Creating Warehouse and Backup Databases...'
	@echo '__________________________________________________________'
	@if docker exec -i ${POSTGRES_CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tAc "SELECT 1 FROM pg_database WHERE datname='warehouse'" | grep -q 1; then \
		echo 'Database "warehouse" already exists.'; \
	else \
		docker exec -i ${POSTGRES_CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE DATABASE warehouse"; \
		echo 'Database "warehouse" created.'; \
	fi; \
	if docker exec -i ${POSTGRES_CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tAc "SELECT 1 FROM pg_database WHERE datname='backup'" | grep -q 1; then \
		echo 'Database "backup" already exists.'; \
	else \
		docker exec -i ${POSTGRES_CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE DATABASE backup"; \
		echo 'Database "backup" created.'; \
	fi
	@echo '==========================================================='

postgres: postgres-create postgres-create-warehouse-and-backup

docker-build-batching:
	@echo '__________________________________________________________'
	@echo 'Building Docker Images Batching Processing ...'
	@echo '__________________________________________________________'
	@docker build -t Batching/airflow -f ./docker/Dockerfile.airflow .
	@echo '__________________________________________________________'
	@docker build -t Batching/spark -f ./docker/Dockerfile.spark .
	@echo '==========================================================='

airflow:
	@echo '__________________________________________________________'
	@echo 'Creating Airflow Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-airflow.yml --env-file .env up -d
	@echo '==========================================================='

spark:
	@echo '__________________________________________________________'
	@echo 'Creating Spark Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-spark.yml --env-file .env up -d
	@echo '==========================================================='

# spark-produce-crypto:
# 	@echo '__________________________________________________________'
# 	@echo 'Producing streaming cryptocurrency events ...'
# 	@echo '__________________________________________________________'
# 	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-1 \
# 		spark-submit \
# 		/spark-scripts/cryptocurrency.py

# spark-consume-assets:
# 	@echo '__________________________________________________________'
# 	@echo 'Consuming Assets events ...'
# 	@echo '__________________________________________________________'
# 	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
# 		spark-submit \
# 		/spark-scripts/assets.py

# spark-consume-rates:
# 	@echo '__________________________________________________________'
# 	@echo 'Consuming Rates events ...'
# 	@echo '__________________________________________________________'
# 	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
# 		spark-submit \
# 		/spark-scripts/rates.py

# spark-consume-exchanges:
# 	@echo '__________________________________________________________'
# 	@echo 'Consuming Exchanges events ...'
# 	@echo '__________________________________________________________'
# 	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
# 		spark-submit \
# 		/spark-scripts/exchanges.py

# spark-consume-markets:
# 	@echo '__________________________________________________________'
# 	@echo 'Consuming Markets events ...'
# 	@echo '__________________________________________________________'
# 	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
# 		spark-submit \
# 		/spark-scripts/markets.py

download-debezium-connector-postgres:
	@echo "__________________________________________________________"
	@echo "Cek Plugin Debezium..."
	@if [ -f "${DEBEZIUM_PATH}" ]; then \
	    echo "FILE SUDAH ADA: ${DEBEZIUM_FILE}"; \
	else \
	    echo "FILE TIDAK ADA, MENDOWNLOAD..."; \
	    mkdir -p ./docker/file; \
	    curl -L -o ${DEBEZIUM_PATH} ${DEBEZIUM_URL}; \
	    echo "Download selesai → ${DEBEZIUM_PATH}"; \
	fi
	@echo "==========================================================="

create-debezium-ui-config:
	@echo "__________________________________________________________"
	@echo "Cek File Konfigurasi Debezium UI..."
	@if [ -f "./docker/file/debezium-ui.properties" ]; then \
	    echo "FILE SUDAH ADA: debezium-ui.properties"; \
	else \
	    echo "FILE TIDAK ADA, MEMBUAT FILE..."; \
	    mkdir -p ./docker/file; \
	    echo "debezium.ui.config.storage.url=http://debezium:8083" > ./docker/file/debezium-ui.properties; \
	    echo "Config berhasil dibuat → ./docker/file/debezium-ui.properties"; \
	fi
	@echo "==========================================================="

docker-build-streaming: download-debezium-connector-postgres create-debezium-ui-config
	@echo '__________________________________________________________'
	@echo 'Building Docker Images Streaming Processing ...'
	@echo '__________________________________________________________'
	@docker build -t Streaming/kafka -f ./docker/Dockerfile.kafka .
	@echo '__________________________________________________________'
	@docker build -t Streaming/debezium -f ./docker/Dockerfile.debezium .
	@echo '__________________________________________________________'
	@docker build -t Streaming/flink -f ./docker/Dockerfile.flink .
	@echo '==========================================================='

kafka:
	@echo '__________________________________________________________'
	@echo 'Creating Kafka Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-kafka.yml --env-file .env up -d
	@echo '==========================================================='

kafka-stop:
	@echo '__________________________________________________________'
	@echo 'Stopping Kafka Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-kafka.yml --env-file .env stop
	@echo '==========================================================='

flink:
	@echo '__________________________________________________________'
	@echo 'Creating Flink Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-flink.yml --env-file .env up -d
	@echo '==========================================================='

docker-build-monitoring:
	@echo '__________________________________________________________'
	@echo 'Building Docker Images Monitoring ...'
	@echo '__________________________________________________________'
	@docker build -t Monitoring/grafana -f ./docker/Dockerfile.grafana .
	@echo '==========================================================='

grafana:
	@echo '__________________________________________________________'
	@echo 'Creating Grafana Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-grafana.yml --env-file .env up -d
	@echo '==========================================================='

clean:
	@bash ./scripts/goodnight.sh