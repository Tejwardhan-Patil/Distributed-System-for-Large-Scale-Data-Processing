import unittest
import os
import time
import subprocess
import sys
from importlib import import_module

# Dynamically add the directories with hyphens to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data-ingestion/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../storage/data-lake')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../compute/dask')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../orchestration/airflow')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api/rest')))

# Import modules using import_module
StreamingIngestion = import_module('ingestion_pipelines.StreamingIngestion').StreamingIngestion
DataCleaning = import_module('preprocessing.DataCleaning').DataCleaning
DataLakeSetup = import_module('data_lake_setup').DataLakeSetup
DaskProcessing = import_module('DaskProcessing').DaskProcessing
DataPipelineDAG = import_module('DataPipelineDAG').DataPipelineDAG
App = import_module('App').App

class TestPipelineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cleaning_service = DataCleaning()
        cls.streaming_ingestion = StreamingIngestion()
        cls.data_lake = DataLakeSetup()
        cls.processing_service = DaskProcessing()
        cls.api_service = App()

        # Start required services before the tests
        cls.start_services()
        cls.start_airflow_dag()

    @classmethod
    def tearDownClass(cls):
        # Stop services after tests
        cls.stop_services()

    @staticmethod
    def start_services():
        """Starts services needed for integration test."""
        print("Starting services...")
        os.system("service hdfs start")
        os.system("service spark start")
        os.system("service dask start")
        os.system("service airflow start")

    @staticmethod
    def stop_services():
        """Stops services after integration test."""
        print("Stopping services...")
        os.system("service hdfs stop")
        os.system("service spark stop")
        os.system("service dask stop")
        os.system("service airflow stop")

    @staticmethod
    def start_airflow_dag():
        """Start the Airflow DAG that manages the data pipeline."""
        print("Starting Airflow DAG for the pipeline...")
        subprocess.run(["airflow", "dags", "trigger", "data_pipeline_dag"])

    def test_ingestion_process(self):
        """Test the data ingestion process through Kafka."""
        print("Testing ingestion process...")
        result = self.streaming_ingestion.ingest_data('source_data_stream')
        self.assertTrue(result, "Ingestion failed.")

    def test_data_cleaning(self):
        """Test data cleaning process."""
        print("Testing data cleaning...")
        raw_data = "raw_data_sample"
        cleaned_data = self.cleaning_service.clean(raw_data)
        self.assertNotEqual(cleaned_data, raw_data, "Data cleaning failed.")

    def test_data_storage_in_lake(self):
        """Test data is properly stored in the data lake."""
        print("Testing data storage in data lake...")
        sample_data = "cleaned_data_sample"
        storage_result = self.data_lake.store_data(sample_data)
        self.assertTrue(storage_result, "Data storage in the lake failed.")

    def test_dask_processing(self):
        """Test data processing using Dask."""
        print("Testing Dask processing...")
        processed_data = self.processing_service.process_data('data_lake_path')
        self.assertIsNotNone(processed_data, "Dask processing failed.")
        self.assertGreater(len(processed_data), 0, "Processed data is empty.")

    def test_data_pipeline_dag_execution(self):
        """Test if the Airflow DAG executes correctly."""
        print("Testing Airflow DAG execution...")
        dag_result = subprocess.run(["airflow", "tasks", "run", "data_pipeline_dag", "start_task", "--local"], capture_output=True)
        self.assertIn("Task completed", dag_result.stdout.decode(), "Airflow DAG execution failed.")

    def test_rest_api_response(self):
        """Test if the REST API is responding correctly after pipeline completion."""
        print("Testing REST API response...")
        api_response = self.api_service.client.get('/data/status')
        self.assertEqual(api_response.status_code, 200, "API did not return 200 OK.")
        self.assertIn('status', api_response.json(), "API response format incorrect.")

    def test_end_to_end_pipeline(self):
        """Test the entire data pipeline from ingestion to API response."""
        print("Testing end-to-end pipeline...")

        # Ingest data
        ingestion_result = self.streaming_ingestion.ingest_data('source_data_stream')
        self.assertTrue(ingestion_result, "End-to-end pipeline failed at ingestion.")

        # Clean data
        raw_data = "raw_data_sample"
        cleaned_data = self.cleaning_service.clean(raw_data)
        self.assertNotEqual(cleaned_data, raw_data, "End-to-end pipeline failed at cleaning.")

        # Store cleaned data in the lake
        storage_result = self.data_lake.store_data(cleaned_data)
        self.assertTrue(storage_result, "End-to-end pipeline failed at storage.")

        # Process data using Dask
        processed_data = self.processing_service.process_data('data_lake_path')
        self.assertIsNotNone(processed_data, "End-to-end pipeline failed at processing.")
        self.assertGreater(len(processed_data), 0, "Processed data is empty in end-to-end pipeline.")

        # Check API response for processed data
        api_response = self.api_service.client.get('/data/processed')
        self.assertEqual(api_response.status_code, 200, "End-to-end pipeline failed at API response.")
        self.assertIn('data', api_response.json(), "API response missing data in end-to-end pipeline.")

    def test_monitoring_logs(self):
        """Test if monitoring services like ELK stack capture logs properly."""
        print("Testing monitoring and logging...")
        elk_status = subprocess.run(["curl", "-X", "GET", "http://localhost:9200/_cluster/health"], capture_output=True)
        self.assertIn('"status":"green"', elk_status.stdout.decode(), "ELK Stack not working as expected.")

    def test_security_encryption(self):
        """Test if encryption works properly for data at rest."""
        print("Testing security encryption...")
        sample_data = "sensitive_data_sample"
        encrypted_data = subprocess.run(["python3", "EncryptData.py", "--data", sample_data], capture_output=True)
        self.assertIn("Encrypted", encrypted_data.stdout.decode(), "Data encryption failed.")

if __name__ == '__main__':
    unittest.main()