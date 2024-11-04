import unittest
import requests
import time
import sys
import os
from importlib import import_module

# Dynamically add the directories with hyphens to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data-ingestion/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../storage')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../compute/dask')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../orchestration/airflow')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api/rest')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils')))

# Import modules using import_module
start_stream_ingestion = import_module('ingestion_pipelines.StreamingIngestion').start_stream_ingestion
setup_data_lake = import_module('data_lake_setup').setup_data_lake
process_data_with_dask = import_module('DaskProcessing').process_data_with_dask
execute_pipeline = import_module('DataPipelineDAG').execute_pipeline
app = import_module('App').app
load_config = import_module('config_loader').load_config
cleanup_data = import_module('helpers').cleanup_data
check_data_integrity = import_module('helpers').check_data_integrity


class TestEndToEndPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up required resources, configurations, and initial data before tests.
        """
        print("Loading configurations...")
        cls.config = load_config("configs/config.dev.yaml")
        
        print("Setting up data lake...")
        setup_data_lake(cls.config["storage"]["data_lake"])
        
        print("Starting data ingestion...")
        cls.ingestion_process = start_stream_ingestion(cls.config["data_ingestion"]["streaming"])

        print("Waiting for ingestion to initialize...")
        time.sleep(10)  # Wait for the ingestion process to initialize

    @classmethod
    def tearDownClass(cls):
        """
        Clean up any resources used during the tests.
        """
        print("Terminating ingestion process...")
        cls.ingestion_process.terminate()

        print("Cleaning up data...")
        cleanup_data(cls.config["storage"]["data_lake"])

    def test_data_ingestion(self):
        """
        Test that data is successfully ingested into the data lake.
        """
        print("Checking ingested data...")
        ingested_data = check_data_integrity(self.config["storage"]["data_lake"]["ingestion_path"])
        self.assertIsNotNone(ingested_data, "No data ingested.")
        self.assertGreater(len(ingested_data), 0, "Ingested data is empty.")

    def test_data_processing(self):
        """
        Test that data is processed correctly using Dask.
        """
        print("Processing data with Dask...")
        processed_data = process_data_with_dask(self.config["compute"]["dask"]["processing_config"])
        
        print("Verifying processed data...")
        self.assertIsNotNone(processed_data, "Processed data is None.")
        self.assertGreater(len(processed_data), 0, "Processed data is empty.")
        
        for item in processed_data:
            self.assertIn("transformed_value", item, "Data transformation failed.")

    def test_airflow_pipeline_execution(self):
        """
        Test that the Airflow pipeline executes correctly.
        """
        print("Executing Airflow pipeline...")
        pipeline_status = execute_pipeline(self.config["orchestration"]["airflow"]["dag_id"])
        self.assertEqual(pipeline_status, "success", "Airflow pipeline execution failed.")
        
        print("Pipeline executed successfully.")

    def test_api_endpoint(self):
        """
        Test that the REST API endpoint returns the expected data.
        """
        print("Testing API endpoint...")
        test_client = app.test_client()

        response = test_client.get("/api/v1/data")
        self.assertEqual(response.status_code, 200, "API request failed.")
        
        response_data = response.json
        self.assertIsInstance(response_data, list, "Response data is not a list.")
        self.assertGreater(len(response_data), 0, "API returned empty data.")
        
        for item in response_data:
            self.assertIn("processed_value", item, "API response missing expected fields.")

    def test_storage_verification(self):
        """
        Test that data is stored correctly in the data lake.
        """
        print("Verifying data in data lake...")
        stored_data = check_data_integrity(self.config["storage"]["data_lake"]["storage_path"])
        self.assertIsNotNone(stored_data, "No data found in data lake.")
        self.assertGreater(len(stored_data), 0, "Data lake is empty.")
        
        for record in stored_data:
            self.assertIn("processed_value", record, "Data in lake is missing 'processed_value'.")

    def test_cleanup_data(self):
        """
        Test that old or irrelevant data is cleaned up from the data lake.
        """
        print("Testing data cleanup...")
        cleanup_data(self.config["storage"]["data_lake"]["cleanup_path"])
        
        cleaned_data = check_data_integrity(self.config["storage"]["data_lake"]["cleanup_path"])
        self.assertEqual(len(cleaned_data), 0, "Data cleanup failed. Data still present.")


if __name__ == "__main__":
    unittest.main()