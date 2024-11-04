import unittest
import os
import subprocess
import yaml
import time

class TestBatchIngestion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load configuration from YAML
        with open('data-ingestion/config/ingestion_config.yaml', 'r') as file:
            cls.config = yaml.safe_load(file)

        cls.source_dir = cls.config['source_directory']
        cls.dest_dir = cls.config['destination_directory']
        cls.batch_size = cls.config['batch_size']
        cls.file_format = cls.config['file_format']

        # Set up directories for testing
        os.makedirs(cls.source_dir, exist_ok=True)
        os.makedirs(cls.dest_dir, exist_ok=True)

    def setUp(self):
        """Prepare necessary environment variables before each test"""
        os.environ['SOURCE_DIR'] = self.source_dir
        os.environ['DESTINATION_DIR'] = self.dest_dir
        os.environ['BATCH_SIZE'] = str(self.batch_size)
        os.environ['FILE_FORMAT'] = self.file_format

    def run_batch_ingestion(self, source_dir=None, dest_dir=None):
        """Helper function to invoke Scala batch ingestion via subprocess"""
        if not source_dir:
            source_dir = os.environ['SOURCE_DIR']
        if not dest_dir:
            dest_dir = os.environ['DESTINATION_DIR']
        
        # Call the Scala BatchIngestion via a subprocess
        result = subprocess.run(
            ['scala', 'data-ingestion/src/ingestion_pipelines/BatchIngestion.scala', source_dir, dest_dir],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result

    def test_valid_ingestion(self):
        """Test valid batch ingestion"""
        # Create mock data files for ingestion
        test_file = os.path.join(self.source_dir, f'test_data.{self.file_format}')
        with open(test_file, 'w') as f:
            f.write('id,name,age\n1,Nate,30\n2,Paul,25')

        result = self.run_batch_ingestion()
        self.assertEqual(result.returncode, 0, "Ingestion failed for valid data")

        # Verify that the file has been ingested into the destination directory
        dest_file = os.path.join(self.dest_dir, f'test_data.{self.file_format}')
        self.assertTrue(os.path.exists(dest_file), "Destination file does not exist")

    def test_ingestion_with_invalid_format(self):
        """Test ingestion with an unsupported file format"""
        os.environ['FILE_FORMAT'] = 'txt'  # Invalid format
        result = self.run_batch_ingestion()
        self.assertNotEqual(result.returncode, 0, "Ingestion should fail with invalid file format")

    def test_empty_source_directory(self):
        """Test ingestion when the source directory is empty"""
        empty_source_dir = os.path.join(self.source_dir, 'empty')
        os.makedirs(empty_source_dir, exist_ok=True)
        result = self.run_batch_ingestion(source_dir=empty_source_dir)
        self.assertNotEqual(result.returncode, 0, "Ingestion should fail for empty source directory")

    def test_batch_size_limit(self):
        """Test batch ingestion with specific batch size"""
        # Create multiple files to test batch size
        for i in range(self.batch_size + 1):
            with open(os.path.join(self.source_dir, f'data_part_{i}.{self.file_format}'), 'w') as f:
                f.write(f'id,name,age\n{i},Person{i},{20 + i}')
        
        result = self.run_batch_ingestion()
        self.assertEqual(result.returncode, 0, "Batch ingestion failed when processing large batch")

        # Check how many files were ingested
        ingested_files = os.listdir(self.dest_dir)
        self.assertEqual(len(ingested_files), self.batch_size, "Batch size exceeded during ingestion")

    def test_partial_ingestion_on_failure(self):
        """Test that partial ingestion happens when failure occurs"""
        # Create some valid and some invalid data files
        for i in range(3):
            with open(os.path.join(self.source_dir, f'valid_data_{i}.{self.file_format}'), 'w') as f:
                f.write(f'id,name,age\n{i},Person{i},{20 + i}')
        
        # Adding an invalid file to cause failure
        with open(os.path.join(self.source_dir, f'invalid_data.txt'), 'w') as f:
            f.write("Invalid content")

        result = self.run_batch_ingestion()
        self.assertNotEqual(result.returncode, 0, "Ingestion should fail due to invalid data format")

        # Ensure that only the valid files were ingested
        ingested_files = os.listdir(self.dest_dir)
        valid_files = [f for f in ingested_files if f.endswith(self.file_format)]
        self.assertEqual(len(valid_files), 3, "Valid files should be ingested before failure")

    def test_ingestion_performance(self):
        """Test ingestion performance under load"""
        start_time = time.time()
        
        # Create a large dataset for performance testing
        for i in range(1000):
            with open(os.path.join(self.source_dir, f'perf_data_{i}.{self.file_format}'), 'w') as f:
                f.write(f'id,name,age\n{i},Person{i},{20 + i}')
        
        result = self.run_batch_ingestion()
        self.assertEqual(result.returncode, 0, "Ingestion failed under load")

        elapsed_time = time.time() - start_time
        self.assertLess(elapsed_time, 60, "Ingestion took too long under load")

    def test_ingestion_logs(self):
        """Test that proper logs are generated during ingestion"""
        result = self.run_batch_ingestion()
        log_file = os.path.join(self.dest_dir, 'ingestion.log')

        self.assertTrue(os.path.exists(log_file), "Ingestion log not found")
        with open(log_file, 'r') as log:
            log_content = log.read()
            self.assertIn("Ingestion completed successfully", log_content)

    def test_config_loading(self):
        """Test configuration loading from YAML file"""
        self.assertTrue(self.config['batch_size'] > 0, "Batch size should be greater than 0")
        self.assertTrue(len(self.config['source_directory']) > 0, "Source directory should be set")
        self.assertTrue(len(self.config['destination_directory']) > 0, "Destination directory should be set")
        self.assertIn(self.config['file_format'], ['csv', 'json'], "Unsupported file format in config")

    def test_handle_large_files(self):
        """Test ingestion with large data files"""
        large_file = os.path.join(self.source_dir, f'large_file.{self.file_format}')
        with open(large_file, 'w') as f:
            for i in range(1000000):  # 1 million rows
                f.write(f'{i},Person{i},{20 + i}\n')
        
        result = self.run_batch_ingestion()
        self.assertEqual(result.returncode, 0, "Ingestion failed for large files")

        # Verify the large file was ingested correctly
        ingested_files = os.listdir(self.dest_dir)
        self.assertIn(f'large_file.{self.file_format}', ingested_files)

    def test_ingestion_retry(self):
        """Test ingestion retry mechanism after failure"""
        # Create a file that causes failure initially
        invalid_file = os.path.join(self.source_dir, f'bad_data.{self.file_format}')
        with open(invalid_file, 'w') as f:
            f.write('corrupt,data\n')
        
        result = self.run_batch_ingestion()
        self.assertNotEqual(result.returncode, 0, "Ingestion should fail due to corrupt data")

        # Fix the file and retry ingestion
        with open(invalid_file, 'w') as f:
            f.write('id,name,age\n1,Nate,30\n')
        
        result = self.run_batch_ingestion()
        self.assertEqual(result.returncode, 0, "Ingestion retry failed after fixing the file")

    def test_multiple_format_ingestion(self):
        """Test ingestion with multiple file formats"""
        os.environ['FILE_FORMAT'] = 'json' 

        # Create a JSON file for ingestion
        json_file = os.path.join(self.source_dir, 'data.json')
        with open(json_file, 'w') as f:
            f.write('{"id": 1, "name": "Nate", "age": 30}\n{"id": 2, "name": "Paul", "age": 25}\n')

        result = self.run_batch_ingestion()
        self.assertEqual(result.returncode, 0, "Ingestion failed for JSON format")

        # Verify JSON file ingestion
        ingested_files = os.listdir(self.dest_dir)
        self.assertIn('data.json', ingested_files)

    @classmethod
    def tearDownClass(cls):
        """Clean up directories after tests"""
        subprocess.run(['rm', '-rf', cls.source_dir, cls.dest_dir])

if __name__ == '__main__':
    unittest.main()