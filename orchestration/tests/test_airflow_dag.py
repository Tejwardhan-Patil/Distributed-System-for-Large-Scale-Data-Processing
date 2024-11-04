import pytest
from airflow.models import DagBag
from airflow.utils.dates import days_ago
from datetime import timedelta

# Load the DAGBag from the specified DAG folder
@pytest.fixture(scope="module")
def dag_bag():
    return DagBag(dag_folder="orchestration/airflow/")

# Test if the DAG file is loaded successfully
def test_dag_loaded(dag_bag):
    assert len(dag_bag.dags) > 0, "No DAGs loaded. Check the DAG file path."

# Test the specific DAG for validity
def test_dag_validity(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    assert dag is not None, "DAG 'data_pipeline_dag' not found."

# Test for task count in the DAG
def test_task_count(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    task_count = len(dag.tasks)
    assert task_count == 5, f"Expected 5 tasks, but got {task_count}."

# Test if specific tasks exist
def test_task_existence(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    task_ids = list(map(lambda task: task.task_id, dag.tasks))
    assert "start_task" in task_ids, "'start_task' not found in DAG"
    assert "data_ingestion_task" in task_ids, "'data_ingestion_task' not found in DAG"
    assert "data_processing_task" in task_ids, "'data_processing_task' not found in DAG"
    assert "data_validation_task" in task_ids, "'data_validation_task' not found in DAG"
    assert "end_task" in task_ids, "'end_task' not found in DAG"

# Test the DAG's default arguments
def test_dag_default_args(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    default_args = dag.default_args
    assert "owner" in default_args and default_args["owner"] == "airflow"
    assert "depends_on_past" in default_args and not default_args["depends_on_past"]
    assert "start_date" in default_args and default_args["start_date"] == days_ago(1)

# Test the task dependencies
def test_task_dependencies(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    
    start_task = dag.get_task("start_task")
    data_ingestion_task = dag.get_task("data_ingestion_task")
    data_processing_task = dag.get_task("data_processing_task")
    data_validation_task = dag.get_task("data_validation_task")
    end_task = dag.get_task("end_task")
    
    # Check the direct downstream dependencies of each task
    assert data_ingestion_task in start_task.downstream_list, "data_ingestion_task not downstream of start_task"
    assert data_processing_task in data_ingestion_task.downstream_list, "data_processing_task not downstream of data_ingestion_task"
    assert data_validation_task in data_processing_task.downstream_list, "data_validation_task not downstream of data_processing_task"
    assert end_task in data_validation_task.downstream_list, "end_task not downstream of data_validation_task"

# Test if tasks have the correct trigger rule
def test_trigger_rule(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    
    data_validation_task = dag.get_task("data_validation_task")
    end_task = dag.get_task("end_task")
    
    assert data_validation_task.trigger_rule == "all_success", "Incorrect trigger rule for data_validation_task"
    assert end_task.trigger_rule == "all_done", "Incorrect trigger rule for end_task"

# Test if tasks have correct retries configuration
def test_task_retries(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    
    data_processing_task = dag.get_task("data_processing_task")
    end_task = dag.get_task("end_task")
    
    assert data_processing_task.retries == 3, "Incorrect retries for data_processing_task"
    assert end_task.retries == 0, "Incorrect retries for end_task"

# Test DAG schedule interval
def test_dag_schedule_interval(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    assert dag.schedule_interval == "0 12 * * *", "DAG schedule interval is incorrect."

# Test SLA configuration in tasks
def test_task_sla(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    
    data_ingestion_task = dag.get_task("data_ingestion_task")
    data_processing_task = dag.get_task("data_processing_task")
    
    assert data_ingestion_task.sla == timedelta(hours=2), "SLA for data_ingestion_task is incorrect"
    assert data_processing_task.sla == timedelta(hours=3), "SLA for data_processing_task is incorrect"
    
# Test if tasks have correct execution timeout
def test_task_execution_timeout(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    
    data_validation_task = dag.get_task("data_validation_task")
    
    assert data_validation_task.execution_timeout == timedelta(minutes=30), "Execution timeout for data_validation_task is incorrect"

# Test if DAG is paused by default
def test_dag_paused_by_default(dag_bag):
    dag = dag_bag.get_dag("data_pipeline_dag")
    assert dag.is_paused_upon_creation, "DAG should be paused upon creation"