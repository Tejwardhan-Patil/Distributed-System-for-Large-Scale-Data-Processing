#!/bin/bash

# Define directories
CORE_COMPONENTS_DIR="core_components"
DEPLOYMENT_DIR="deployment"
UTILS_DIR="utils"
TESTS_DIR="tests"

# Clean previous builds
echo "Cleaning previous builds..."
if [ -d "build" ]; then
  rm -rf build
fi
mkdir build

# Build data ingestion components
echo "Building data ingestion components..."
cd data-ingestion/src
scalac ingestion_pipelines/BatchIngestion.scala -d ../../build/BatchIngestion.jar
python3 -m compileall preprocessing/DataCleaning.py
scalac preprocessing/DataTransformation.scala -d ../../build/DataTransformation.jar
cd ../../

# Build distributed storage components
echo "Building distributed storage components..."
cd storage/
javac nosql/CassandraSetup.java -d ../build/
psql -f relational/SpannerSetup.sql
python3 data_lake/data_lake_setup.py
bash hdfs/hdfs_setup.sh
cd ../

# Build distributed computing components
echo "Building distributed computing components..."
cd compute/spark/
scalac BatchProcessing.scala -d ../../build/BatchProcessing.jar
scalac StreamProcessing.scala -d ../../build/StreamProcessing.jar
cd ../../

cd compute/hadoop/
javac MapReduceJob.java -d ../../build/
cd ../../

cd compute/dask/
python3 -m compileall DaskProcessing.py
cd ../../

# Build orchestration and workflow management components
echo "Building orchestration and workflow components..."
cd orchestration/airflow/
python3 -m compileall DataPipelineDAG.py
cd ../../

cd orchestration/luigi/
scalac DataProcessingTask.scala -d ../../build/LuigiDataProcessing.jar
cd ../../

# Build security components
echo "Building security components..."
cd security/encryption/
python3 -m compileall EncryptData.py
cd ../../

cd security/authentication/
javac OAuth2Setup.java -d ../../build/
cd ../../

# Package and finalize build
echo "Packaging build..."
cd build
jar cf core_components.jar *
echo "Build complete."