from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.empty_operator import EmptyOperator
from airflow.operators.email_operator import EmailOperator
from airflow.operators.bash_operator import BashOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import logging

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 9, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'DataPipelineDAG',
    default_args=default_args,
    description='An ETL pipeline DAG',
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1,
)

def extract_data(**kwargs):
    logging.info("Extracting data from source...")
    # Data extraction logic
    source_path = Variable.get("source_data_path")
    logging.info(f"Data extracted from {source_path}")

def transform_data(**kwargs):
    logging.info("Transforming data...")
    # Data transformation logic
    input_path = Variable.get("source_data_path")
    output_path = Variable.get("transformed_data_path")
    # Perform transformation
    logging.info(f"Data transformed and saved to {output_path}")

def load_data(**kwargs):
    logging.info("Loading data into the data warehouse...")
    # Data loading logic
    warehouse_path = Variable.get("warehouse_data_path")
    # Load data
    logging.info(f"Data loaded into {warehouse_path}")

extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=extract_data,
    provide_context=True,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_task',
    python_callable=transform_data,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_task',
    python_callable=load_data,
    provide_context=True,
    dag=dag,
)

# Cleanup old files
cleanup_task = BashOperator(
    task_id='cleanup_task',
    bash_command="sh /cleanup_script.sh",
    dag=dag,
)

# Email notification
email_task = EmailOperator(
    task_id='email_notification',
    to='team@website.com',
    subject='Data Pipeline Status',
    html_content='<p>Data Pipeline completed successfully.</p>',
    dag=dag,
)

# Empty operator for start and end
start_task = EmptyOperator(
    task_id='start_task',
    dag=dag,
)

end_task = EmptyOperator(
    task_id='end_task',
    dag=dag,
)

# Define pipeline workflow
start_task >> extract_task >> transform_task >> load_task >> cleanup_task >> email_task >> end_task