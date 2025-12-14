include .env

help:
	@echo "## docker-networks		- Build Docker Networks (amd64)"
	@echo "## docker-build			- Build Docker Images (amd64)"
	@echo "## debezium				- Capture database changes in real-time"
	@echo "## spark					- Run a Spark cluster, rebuild the postgres container, then create the destination tables "
	@echo "## kafka					- Spinup kafka cluster"
	@echo "## flink					- Create the destination and transformation tables"
	@echo "## airflow				- Build to orchestrator"
	@echo "## postgres				- Run database of relationship"
	@echo "## dbt					- Create the dimension and fact tables."
	@echo "## prometheus			- Metrics analysis data"
	@echo "## grafana				- Monitoring analysis data"
	@echo "## clean					- Cleanup all running containers related to the challenge."

docker-networks:
	@echo '__________________________________________________________'
	@echo 'Building Docker Networks for Batching and Streaming Processing ...'
	@echo '__________________________________________________________'
	@if docker network inspect batching-processing >/dev/null 2>&1; then \
		echo "Network 'batching-processing' already exists."; \
	else \
		echo "Creating network 'batching-processing'..."; \
		docker network create batching-processing; \
	fi
	@echo '__________________________________________________________'
	@if docker network inspect streaming-processing >/dev/null 2>&1; then \
		echo "Network 'streaming-processing' already exists."; \
	else \
		echo "Creating network 'streaming-processing'..."; \
		docker network create streaming-processing; \
	fi
	@echo '==========================================================='


# ---------
# Docker___
# ---------

postgres:
	@docker build -t staging_postgres -f ./docker/Dockerfile.postgres .
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-postgres.yaml --env-file .env up -d
	@echo '__________________________________________________________'
	@echo 'Postgres container created at port ${POSTGRES_PORT}...'
	@echo '__________________________________________________________'
	@echo 'Postgres Docker Host	: ${POSTGRES_CONTAINER_NAME}' &&\
		echo 'Postgres Account	: ${POSTGRES_USER}' &&\
		echo 'Postgres password	: ${POSTGRES_PASSWORD}' &&\
		echo 'Postgres Db		: ${POSTGRES_DB}'
	@echo '==========================================================='

docker-build-batching:
	@echo '__________________________________________________________'
	@echo 'Building Docker Images Batching for Kubernetes in Processing ...'
	@echo '__________________________________________________________'
	@docker build -t batching_airflow -f ./docker/Dockerfile.airflow .
	@echo '__________________________________________________________'
	@docker build -t batching_spark -f ./docker/Dockerfile.spark .
	@echo '==========================================================='

airflow:
	@echo '__________________________________________________________'
	@echo 'Creating Airflow Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-airflow.yaml --env-file .env up -d
	@echo '==========================================================='

spark:
	@echo '__________________________________________________________'
	@echo 'Creating Spark Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-spark.yaml --env-file .env up -d
	@echo '==========================================================='

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
	    mkdir -p ./scripts; \
	    curl -L -o ${DEBEZIUM_PATH} ${DEBEZIUM_URL}; \
	    echo "Download selesai → ${DEBEZIUM_PATH}"; \
	fi
	@echo "==========================================================="

create-debezium-ui-config:
	@echo "__________________________________________________________"
	@echo "Cek File Konfigurasi Debezium UI..."
	@if [ -f "./scripts/debezium-ui.properties" ]; then \
	    echo "FILE SUDAH ADA: debezium-ui.properties"; \
	else \
	    echo "FILE TIDAK ADA, MEMBUAT FILE..."; \
	    mkdir -p ./scripts; \
	    echo "debezium.ui.config.storage.url=http://debezium:8083" > ./scripts/debezium-ui.properties; \
	    echo "Config berhasil dibuat → ./scripts/debezium-ui.properties"; \
	fi
	@echo "==========================================================="

docker-build-streaming: download-debezium-connector-postgres create-debezium-ui-config
	@echo '__________________________________________________________'
	@echo 'Building Docker Images Streaming Processing ...'
	@echo '__________________________________________________________'
	@docker build -t streaming_kafka -f ./docker/Dockerfile.kafka .
	@echo '__________________________________________________________'
	@docker build -t streaming_debezium -f ./docker/Dockerfile.debezium .
	@echo '__________________________________________________________'
	@docker build -t streaming_flink -f ./docker/Dockerfile.flink .
	@echo '==========================================================='

kafka:
	@echo '__________________________________________________________'
	@echo 'Creating Kafka Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-kafka.yaml --env-file .env up -d
	@echo '==========================================================='

kafka-stop:
	@echo '__________________________________________________________'
	@echo 'Stopping Kafka Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-kafka.yaml --env-file .env stop
	@echo '==========================================================='

flink:
	@echo '__________________________________________________________'
	@echo 'Creating Flink Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-flink.yaml --env-file .env up -d
	@echo '==========================================================='

docker-build-monitoring:
	@echo '__________________________________________________________'
	@echo 'Building Docker Images Monitoring ...'
	@echo '__________________________________________________________'
	@docker build -t monitoring_grafana -f ./docker/Dockerfile.grafana .
	@echo '__________________________________________________________'
	@docker build -t monitoring_prometheus -f ./docker/Dockerfile.prometheus .
	@echo '==========================================================='

grafana-prometheus:
	@echo '__________________________________________________________'
	@echo 'Creating Grafana And Pometheus Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-grafana.yaml --env-file .env up -d
	@echo '__________________________________________________________'
	@docker compose -f ./docker-compose/docker-compose-prometheus.yaml --env-file .env up -d
	@echo '==========================================================='

# -------------
# Kubernetes___
# -------------

kubectl-database-k8s:
	@echo '__________________________________________________________'
	@echo 'Apply Kubernetes Database Processing ...'
	@echo '__________________________________________________________'
	@kubectl apply -R -f k8s/database/
	@echo '==========================================================='

kubectl-batching-k8s:
	@echo '__________________________________________________________'
	@echo 'Apply Kubernetes Batching Processing ...'
	@echo '__________________________________________________________'
	@kubectl apply -R -f k8s/batching/
	@echo '==========================================================='

kubectl-Stopping-batching-k8s:
	@echo '__________________________________________________________'
	@echo 'Stopping Kubernetes Batching ...'
	@echo '__________________________________________________________'
	@kubectl scale deployment airflow --replicas=0
	@echo '__________________________________________________________'
	kubectl scale deployment spark --replicas=0
	@echo '==========================================================='

kubectl-Starting-batching-k8s:
	@echo '__________________________________________________________'
	@echo 'Starting Kubernetes Batching ...'
	@echo '__________________________________________________________'
	@kubectl scale deployment airflow --replicas=1
	@echo '__________________________________________________________'
	kubectl scale deployment spark --replicas=1
	@echo '==========================================================='

kubectl-streaming-k8s:
	@echo '__________________________________________________________'
	@echo 'Apply Kubernetes Streaming Processing ...'
	@echo '__________________________________________________________'
	@kubectl apply -R -f k8s/streaming/
	@echo '==========================================================='

kubectl-Stopping-streaming-k8s:
	@echo '__________________________________________________________'
	@echo 'Stopping Kubernetes Streaming ...'
	@echo '__________________________________________________________'
	@kubectl scale deployment debezium --replicas=0
	@echo '__________________________________________________________'
	@kubectl scale deployment debezium-ui --replicas=0
	@echo '__________________________________________________________'
	kubectl scale deployment kafka --replicas=0
	@echo '__________________________________________________________'
	kubectl scale deployment kafka-ui --replicas=0
	@echo '==========================================================='

kubectl-Starting-streaming-k8s:
	@echo '__________________________________________________________'
	@echo 'Starting Kubernetes Streaming ...'
	@echo '__________________________________________________________'
	@kubectl scale deployment debezium --replicas=1
	@echo '__________________________________________________________'
	kubectl scale deployment debezium-ui --replicas=1
	@echo '__________________________________________________________'
	@kubectl scale deployment kafka --replicas=1
	@echo '__________________________________________________________'
	kubectl scale deployment kafka-ui --replicas=1
	@echo '==========================================================='

kubectl-monitoring-k8s:
	@echo '__________________________________________________________'
	@echo 'Apply Kubernetes Monitoring Processing ...'
	@echo '__________________________________________________________'
	@kubectl apply -R -f k8s/monitoring/
	@echo '==========================================================='

kubectl-Stopping-monitoring-k8s:
	@echo '__________________________________________________________'
	@echo 'Stopping Kubernetes Monitoring ...'
	@echo '__________________________________________________________'
	@kubectl scale deployment prometheus --replicas=0
	@echo '__________________________________________________________'
	@kubectl scale deployment grafana --replicas=0
	@echo '==========================================================='

kubectl-Starting-monitoring-k8s:
	@echo '__________________________________________________________'
	@echo 'Starting Kubernetes Monitoring ...'
	@echo '__________________________________________________________'
	@kubectl scale deployment prometheus --replicas=1
	@echo '__________________________________________________________'
	kubectl scale deployment grafana --replicas=1
	@echo '==========================================================='

# -------------
# Kubernetes___UI
# -------------

kubectl-running-database-k8s:
	@echo '__________________________________________________________'
	@echo 'Running Kubernetes Database Processing ...'
	@kubectl port-forward svc/pgadmin 8888:80 > /dev/null 2>&1 &
	@echo '==========================================================='

kubectl-running-batching-k8s:
	@echo '__________________________________________________________'
	@echo 'Running Kubernetes Batching Processing ...'
	@echo '__________________________________________________________'
	@kubectl port-forward svc/airflow 8085:8080 > /dev/null 2>&1 &
	@echo '__________________________________________________________'
	@kubectl port-forward svc/spark-worker 9100:9102 > /dev/null 2>&1 &
	@echo '==========================================================='

kubectl-running-streaming-k8s:
	@echo '__________________________________________________________'
	@echo 'Running Kubernetes Streaming Processing ...'
	@echo '__________________________________________________________'
	@kubectl port-forward svc/debezium-ui 8095:8095 > /dev/null 2>&1 &
	@echo '__________________________________________________________'
	@kubectl port-forward svc/kafka-ui 8087:8087 > /dev/null 2>&1 &
	@echo '__________________________________________________________'
	@kubectl port-forward svc/flink-jobmanager 8081:8081 > /dev/null 2>&1 &
	@echo '==========================================================='

kubectl-running-monitoring-k8s:
	@echo '__________________________________________________________'
	@echo 'Running Kubernetes Monitoring Processing ...'
	@echo '__________________________________________________________'
	@kubectl port-forward svc/prometheus 9191:9090 > /dev/null 2>&1 &
	@echo '__________________________________________________________'
	@kubectl port-forward svc/grafana 3000:3000 > /dev/null 2>&1 &
	@echo '==========================================================='

clean:
	@bash ./scripts/goodnight.sh