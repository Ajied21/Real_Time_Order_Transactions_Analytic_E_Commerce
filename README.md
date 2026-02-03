## Real Time Order Transactions Analytic E-Commerce

E-commerce companies need a system that can:

- Collect order transactions in real time
- View order updates as they occur (NEW → PAID → SHIPPED → COMPLETED)
- Quickly calculate GMV (Gross Merchandise Value)
- Monitor sales activity by product, category, city, and hour
- Provide high-quality data for batch analysis
- Generate daily, weekly, and monthly reports
- That's why companies need a Real-Time + Batch Data Pipeline like the one you built.

## Project Objectives

This pipeline was built to:

Real-time objectives

- Capture order changes in PostgreSQL using Debezium CDC
- Send streaming events to Kafka
- Process events (streaming ETL) with Flink with low latency
- Save real-time snapshots to the Data Lake in S3 AWS

# ERD (Entity Relationship Diagram)

<div style="text-align: center;">
  <img src="./images/ERD.jpg" width="500">
</div>

# Data Architecture

<div style="text-align: center;">
  <img src="./images/Architecture.png" width="950">
</div>

# Technologies

| Technologies                        | Tools                                                               |
|-------------------------------------|---------------------------------------------------------------------|
| **Cloud**                           | Amazon Web Services (AWS)                                           |
| **Infrastructure as Code (IaC)**    | Terraform                                                           |
| **Container**                       | Docker & Kubernetes                                                 |
| **RDBMS**                           | PostgreSQL                                                          |
| **CDC**                             | Debezium                                                            |
| **Stream processing**               | Apache Kafka & Apache Flink                                         |
| **Programming**                     | Python and SQL                                                      |
| **Metric**                          | Prometheus                                                          |
| **Dashboard**                       | Grafana                                                             |

# Run Project

1. **Clone This Repo** 
2. **Open Docker Desktop**
3. **Run for create a dataset on S3** :
- `cd terraform`
- `terraform init`
- `terraform apply`
* if you want to delete the dataset, run this `terraform destroy`

**Procedure**

1. **Run for step database to active and inactive**

**start:**

- `make kubectl-Starting-batching-k8s`

**Run Create DB in Postgres**

`make DDL`

**Run Insert Data to DB Postgres**

`make DML`

**stop/delete:**

- `make kubectl-Stopping-batching-k8s`

2. **Run for step streaming to active and inactive**

**First Run Kafka and Flink:**

`make kubectl-streaming-k8s`

**Second Run Debezium:**

`make kubectl-running-streaming-debezium-k8s`

**stop/delete:**

`make kubectl-Stop-Streaming-k8s`

3. **Run for step Monitoring to active and inactive**

**start**

- `make kubectl-Starting-monitoring-k8s`

**stop/delete:**

- `make kubectl-Stopping-monitoring-k8s`


| Command        | Description                                                                              |
|----------------|------------------------------------------------------------------------------------------|
| `docker-build` | Build Docker Images (amd64) including its inter-container network.                       |
| `debezium`     | Capture database changes in real-time.                                                   |
| `kafka`        | Spin up a Kafka cluster.                                                                 |
| `flink`        | Run a Flink cluster, create transfrom and ingestion tables.                              |
| `postgres`     | Run the database of relationships.                                                       |
| `terraform`    | Automate several services that are needed, such as BigQuery.                             |
| `prometheus`   | Metrics real-time data.                                                                  |
| `grafana`      | Monitor real-time data.                                                                  |


**additional**

- development    = kubectl get deployment
- pods           = kubectl get pods
- service        = kubectl get svc
- ingress        = kubectl get ingress
- configmap      = kubectl get configmap
- secret         = kubectl get secret
- pv and pvc     = kubectl get pv and kubectl get pvc
- all resouces   = kubectl get all

**delete** 

- kubectl delete all --all
- kubectl delete pvc --all
- kubectl delete pv --all
- kubectl delete configmap --all
- kubectl delete secret --all