import random
import json
import csv
import string
from faker import Faker
import pandas as pd
import numpy as np
import time

# Initialize Faker for generating fake data
fake = Faker()

# Define constants for data generation
ROWS = 100000
BATCH_SIZE = 10000
OUTPUT_FORMAT = ['csv', 'json', 'parquet']

class DataGenerator:
    def __init__(self, output_type='csv', rows=ROWS, batch_size=BATCH_SIZE):
        self.output_type = output_type
        self.rows = rows
        self.batch_size = batch_size

    def _generate_row(self):
        """Generate a single row of synthetic data."""
        return {
            'id': fake.uuid4(),
            'name': fake.name(),
            'email': fake.email(),
            'phone_number': fake.phone_number(),
            'address': fake.address(),
            'date_of_birth': fake.date_of_birth().isoformat(),
            'created_at': fake.date_time_this_decade().isoformat(),
            'updated_at': fake.date_time_this_decade().isoformat(),
            'status': random.choice(['active', 'inactive']),
            'transaction_amount': round(random.uniform(10.5, 1000.99), 2)
        }

    def _generate_batch(self):
        """Generate a batch of synthetic data."""
        return [self._generate_row() for _ in range(self.batch_size)]

    def generate_data(self):
        """Generate synthetic data in batches."""
        data = []
        for _ in range(0, self.rows, self.batch_size):
            batch = self._generate_batch()
            data.extend(batch)
        return data

    def save_to_csv(self, data, file_name='data.csv'):
        """Save the generated data to a CSV file."""
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def save_to_json(self, data, file_name='data.json'):
        """Save the generated data to a JSON file."""
        with open(file_name, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)

    def save_to_parquet(self, data, file_name='data.parquet'):
        """Save the generated data to a Parquet file."""
        df = pd.DataFrame(data)
        df.to_parquet(file_name, engine='pyarrow')

    def generate_and_save(self):
        """Generate data and save to the selected output format."""
        data = self.generate_data()
        if self.output_type == 'csv':
            self.save_to_csv(data)
        elif self.output_type == 'json':
            self.save_to_json(data)
        elif self.output_type == 'parquet':
            self.save_to_parquet(data)

def timer(func):
    """Decorator for timing the execution of functions."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")
        return result
    return wrapper

class DistributedDataGenerator(DataGenerator):
    def __init__(self, nodes=4, **kwargs):
        super().__init__(**kwargs)
        self.nodes = nodes

    def distribute_batches(self):
        """Distribute batch generation across nodes."""
        node_data = []
        for i in range(self.nodes):
            node_data.append(self._generate_batch())
            print(f"Generated batch for node {i + 1}")
        return node_data

    @timer
    def generate_data_distributed(self):
        """Generate data distributed across multiple nodes."""
        all_data = []
        for _ in range(self.rows // (self.batch_size * self.nodes)):
            node_data = self.distribute_batches()
            for data in node_data:
                all_data.extend(data)
        return all_data

    def save_distributed_data(self):
        """Generate distributed data and save in the chosen format."""
        data = self.generate_data_distributed()
        if self.output_type == 'csv':
            self.save_to_csv(data, 'distributed_data.csv')
        elif self.output_type == 'json':
            self.save_to_json(data, 'distributed_data.json')
        elif self.output_type == 'parquet':
            self.save_to_parquet(data, 'distributed_data.parquet')

if __name__ == '__main__':
    # Usage
    generator = DataGenerator(output_type='csv', rows=50000, batch_size=10000)
    generator.generate_and_save()

    # Distributed data generation
    distributed_generator = DistributedDataGenerator(output_type='parquet', rows=100000, batch_size=20000, nodes=5)
    distributed_generator.save_distributed_data()