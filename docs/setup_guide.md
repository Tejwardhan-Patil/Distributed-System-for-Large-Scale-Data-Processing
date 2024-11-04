# Setup Guide

## Prerequisites

- Docker
- Kubernetes
- Terraform
- Python 3.x
- Java 11+
- Scala 2.x
- Spark, Hadoop, Flink installed
- Prometheus, Grafana for monitoring
- Kafka or Kinesis for data streaming

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/repo.git
cd distributed-system
```

### 2. Build and Configure the System

Run the build script to compile and set up all components:

```bash
./scripts/build.sh
```

### 3. Set Up Data Storage

For HDFS:

```bash
./storage/hdfs/hdfs_setup.sh
```

For S3 or similar object storage, update the `s3_config.json` file and configure credentials.

### 4. Deploy to Kubernetes

Ensure Kubernetes is running and deploy using Helm charts:

```bash
helm install my-ds ./deployment/kubernetes/helm_chart/
```

### 5. Set Up Monitoring

Configure Prometheus and Grafana by updating `prometheus_config.yaml` and `grafana_dashboards.json`. Deploy monitoring services:

```bash
kubectl apply -f ./monitoring/prometheus/prometheus_config.yaml
```

### 6. Set Up Security

Configure OAuth2 and RBAC policies:

```bash
java -jar security/authentication/OAuth2Setup.java
```

### 7. Testing

Run unit and integration tests:

```bash
./scripts/test_deployment.sh
```

### 8. Running Pipelines

To run data ingestion pipelines, trigger the Airflow DAG:

```bash
airflow trigger_dag DataPipelineDAG
```

## Troubleshooting

- Check logs in `/var/log/distributed-system/` for error messages.
- Ensure correct cloud provider configurations (AWS, GCP, etc.) in the `configs/` folder.
