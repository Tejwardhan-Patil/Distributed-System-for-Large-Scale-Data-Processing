# Data Pipelines Documentation

## Overview

The system integrates both batch and streaming pipelines for data ingestion, processing, and storage. Pipelines are orchestrated using Airflow and managed through a modular approach.

## Batch Ingestion Pipeline

1. **Source**: Reads data from databases using `DbConnector.java` or from files using `BatchIngestion.scala`.
2. **Preprocessing**: Data is cleaned and transformed using `DataCleaning.py` and `DataTransformation.scala`.
3. **Storage**: Data is stored in HDFS, object storage (S3), or data lakes.

## Streaming Ingestion Pipeline

1. **Source**: Real-time data streams from Kafka or Kinesis.
2. **Processing**: Stream processing via `StreamProcessing.scala` for real-time transformations.
3. **Storage**: Data is stored in HDFS or NoSQL (Cassandra).

## Data Transformation

- Transformations are handled by custom functions defined in `DataTransformation.scala` and `DataCleaning.py`.
- Spark and Flink are used for distributed processing.

## Pipeline Orchestration

Airflow DAGs manage the pipeline execution, with tasks defined in `DataPipelineDAG.py`. Dependencies and retries are handled automatically.
