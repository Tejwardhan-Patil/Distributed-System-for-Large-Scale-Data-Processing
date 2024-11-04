import json
import os
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import logging
import yaml
import psycopg2

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StreamingIngestion")

# Load Configuration
def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

# Kafka Consumer for Streaming Data
class StreamingConsumer:
    def __init__(self, config):
        self.kafka_topic = config['kafka']['topic']
        self.bootstrap_servers = config['kafka']['bootstrap_servers']
        self.consumer = KafkaConsumer(
            self.kafka_topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        logger.info(f"Kafka Consumer initialized for topic: {self.kafka_topic}")

    def consume(self):
        for message in self.consumer:
            logger.info(f"Received message: {message.value}")
            yield message.value

# Database Connector for storing data
class DatabaseConnector:
    def __init__(self, config):
        self.db_config = config['database']
        self.connection = self.connect()

    def connect(self):
        conn = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['dbname']
        )
        logger.info("Connected to the database")
        return conn

    def insert_data(self, data):
        cursor = self.connection.cursor()
        query = """INSERT INTO ingestion_data (timestamp, data) VALUES (%s, %s);"""
        cursor.execute(query, (datetime.now(), json.dumps(data)))
        self.connection.commit()
        cursor.close()
        logger.info(f"Data inserted into database: {data}")

# Kafka Producer for sending processed data to another topic
class StreamingProducer:
    def __init__(self, config):
        self.bootstrap_servers = config['kafka']['bootstrap_servers']
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        logger.info("Kafka Producer initialized")

    def send_data(self, topic, data):
        self.producer.send(topic, value=data)
        self.producer.flush()
        logger.info(f"Data sent to Kafka topic {topic}: {data}")

# Data Transformation Function
def transform_data(data):
    logger.info(f"Transforming data: {data}")
    # Simple transformation: Add a processed_at timestamp
    data['processed_at'] = datetime.now().isoformat()
    return data

# Streaming Ingestion Pipeline
class StreamingIngestionPipeline:
    def __init__(self, config):
        self.consumer = StreamingConsumer(config)
        self.db_connector = DatabaseConnector(config)
        self.producer = StreamingProducer(config)
        self.output_topic = config['kafka']['output_topic']

    def run(self):
        for message in self.consumer.consume():
            # Process the data
            transformed_data = transform_data(message)
            
            # Save the data to the database
            self.db_connector.insert_data(transformed_data)
            
            # Publish the transformed data to another Kafka topic
            self.producer.send_data(self.output_topic, transformed_data)

# Error Handling
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            raise
    return wrapper

@handle_errors
def main():
    # Load configuration
    config_path = os.getenv("CONFIG_PATH", "data-ingestion/config/ingestion_config.yaml")
    config = load_config(config_path)

    # Start the streaming ingestion pipeline
    ingestion_pipeline = StreamingIngestionPipeline(config)
    ingestion_pipeline.run()

if __name__ == "__main__":
    main()