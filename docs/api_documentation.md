
# API Documentation

## REST APIs

The system provides several REST endpoints for accessing and managing data. The Flask/FastAPI app serves the following routes:

### 1. `POST /data/ingest`

Ingest data into the system.

**Request:**

```json
{
  "source": "db",
  "data": {
    "records": [...]
  }
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Data ingested successfully"
}
```

### 2. `GET /data/status`

Retrieve the status of data ingestion pipelines.

**Response:**

```json
{
  "status": "running",
  "pipeline": "BatchIngestion"
}
```

## gRPC Services

### Service Definition (Protobuf)

```proto
syntax = "proto3";

service DataService {
  rpc GetData (DataRequest) returns (DataResponse);
}

message DataRequest {
  string id = 1;
}

message DataResponse {
  string data = 1;
}
```

### gRPC Call (Java)

```java
DataRequest request = DataRequest.newBuilder().setId("123").build();
DataResponse response = blockingStub.getData(request);
System.out.println(response.getData());
```

## Authentication

APIs are secured using OAuth2. Include a Bearer token in the `Authorization` header for all requests.
