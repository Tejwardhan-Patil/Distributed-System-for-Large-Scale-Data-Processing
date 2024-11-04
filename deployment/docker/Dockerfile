# Base image for multi-stage builds
FROM python:3.10-slim AS base-python
FROM openjdk:17-slim AS base-java
FROM scala:2.13.6 AS base-scala

# Build stage for Python-based components (Ingestion, APIs, Monitoring)
FROM base-python AS python-build
WORKDIR /app
COPY ./data-ingestion/requirements.txt ./requirements.txt
COPY ./api/rest/requirements.txt ./api_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r api_requirements.txt

COPY ./data-ingestion/ ./data-ingestion/
COPY ./api/rest/ ./api/rest/
COPY ./monitoring/logging/ElkStackSetup.sh ./monitoring/logging/

# Build stage for Java-based components (gRPC, Security)
FROM base-java AS java-build
WORKDIR /app
COPY ./api/grpc/ ./api/grpc/
COPY ./security/authentication/OAuth2Setup.java ./security/authentication/
COPY ./storage/nosql/CassandraSetup.java ./storage/nosql/
RUN javac ./api/grpc/GrpcServer.java ./security/authentication/OAuth2Setup.java ./storage/nosql/CassandraSetup.java

# Build stage for Scala-based components (Spark, Luigi, Flink)
FROM base-scala AS scala-build
WORKDIR /app
COPY ./compute/spark/BatchProcessing.scala ./compute/spark/
COPY ./orchestration/luigi/DataProcessingTask.scala ./orchestration/luigi/
RUN scalac ./compute/spark/BatchProcessing.scala ./orchestration/luigi/DataProcessingTask.scala

# Final deployment image
FROM python:3.10-slim AS final
WORKDIR /app

# Copy Python components
COPY --from=python-build /app/data-ingestion/ ./data-ingestion/
COPY --from=python-build /app/api/rest/ ./api/rest/
COPY --from=python-build /app/monitoring/logging/ ./monitoring/logging/
COPY --from=python-build /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Copy Java components
COPY --from=java-build /app/api/grpc/ ./api/grpc/
COPY --from=java-build /app/security/authentication/ ./security/authentication/
COPY --from=java-build /app/storage/nosql/ ./storage/nosql/

# Copy Scala components
COPY --from=scala-build /app/compute/spark/ ./compute/spark/
COPY --from=scala-build /app/orchestration/luigi/ ./orchestration/luigi/

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose ports for various services
EXPOSE 5000 8080 7077 50051

# Start point for Python API (FastAPI/Flask), Java gRPC Server, or Spark jobs
CMD ["python", "api/rest/App.py"]