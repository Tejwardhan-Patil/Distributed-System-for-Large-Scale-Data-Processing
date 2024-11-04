import os
import logging
import json
import yaml
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Union


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_json(file_path: str) -> Dict:
    """Loads a JSON file from the specified path."""
    if not os.path.exists(file_path):
        logging.error(f"JSON file {file_path} does not exist.")
        return {}
    with open(file_path, 'r') as json_file:
        try:
            data = json.load(json_file)
            logging.info(f"Loaded JSON file from {file_path}")
            return data
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON file {file_path}: {e}")
            return {}


def load_yaml(file_path: str) -> Dict:
    """Loads a YAML file from the specified path."""
    if not os.path.exists(file_path):
        logging.error(f"YAML file {file_path} does not exist.")
        return {}
    with open(file_path, 'r') as yaml_file:
        try:
            data = yaml.safe_load(yaml_file)
            logging.info(f"Loaded YAML file from {file_path}")
            return data
        except yaml.YAMLError as e:
            logging.error(f"Error loading YAML file {file_path}: {e}")
            return {}


def save_json(data: Dict, file_path: str) -> None:
    """Saves a dictionary as a JSON file."""
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
            logging.info(f"Saved data to JSON file at {file_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON file {file_path}: {e}")


def save_yaml(data: Dict, file_path: str) -> None:
    """Saves a dictionary as a YAML file."""
    try:
        with open(file_path, 'w') as yaml_file:
            yaml.dump(data, yaml_file)
            logging.info(f"Saved data to YAML file at {file_path}")
    except Exception as e:
        logging.error(f"Failed to save YAML file {file_path}: {e}")


def calculate_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculates and returns the checksum for a file using the specified hashing algorithm."""
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} does not exist.")
        return ''
    
    hash_function = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_function.update(chunk)
        checksum = hash_function.hexdigest()
        logging.info(f"Calculated {algorithm} checksum for {file_path}")
        return checksum
    except Exception as e:
        logging.error(f"Failed to calculate checksum for {file_path}: {e}")
        return ''


def create_directory(path: str) -> None:
    """Creates a directory if it doesn't exist."""
    try:
        os.makedirs(path, exist_ok=True)
        logging.info(f"Directory created at {path}")
    except Exception as e:
        logging.error(f"Failed to create directory at {path}: {e}")


def validate_json_structure(data: Dict, required_keys: List[str]) -> bool:
    """Validates if the required keys are present in the JSON data."""
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        logging.error(f"Missing keys in JSON data: {missing_keys}")
        return False
    logging.info(f"JSON data contains all required keys: {required_keys}")
    return True


def get_current_timestamp() -> str:
    """Returns the current timestamp as a string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log_event(event_name: str, event_data: Union[str, Dict], log_level: str = 'info') -> None:
    """Logs an event with the specified log level."""
    log_func = getattr(logging, log_level.lower(), logging.info)
    if isinstance(event_data, dict):
        log_func(f"Event: {event_name} - Data: {json.dumps(event_data, indent=4)}")
    else:
        log_func(f"Event: {event_name} - Data: {event_data}")


def read_file_lines(file_path: str) -> List[str]:
    """Reads a file and returns its content as a list of lines."""
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} does not exist.")
        return []
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            logging.info(f"Read {len(lines)} lines from {file_path}")
            return lines
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}")
        return []


def write_to_file(file_path: str, content: str, mode: str = 'w') -> None:
    """Writes content to a file."""
    try:
        with open(file_path, mode) as file:
            file.write(content)
            logging.info(f"Written content to {file_path}")
    except Exception as e:
        logging.error(f"Failed to write to file {file_path}: {e}")


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merges two dictionaries, with dict2 overwriting dict1 values if key conflicts occur."""
    merged = {**dict1, **dict2}
    logging.info(f"Merged two dictionaries. Result: {merged}")
    return merged


def get_env_variable(var_name: str, default_value: Any = None) -> Any:
    """Fetches an environment variable, or returns a default value."""
    value = os.getenv(var_name, default_value)
    if value is not None:
        logging.info(f"Environment variable {var_name} found with value: {value}")
    else:
        logging.warning(f"Environment variable {var_name} not set, using default value: {default_value}")
    return value


def format_bytes(size_in_bytes: int) -> str:
    """Converts bytes into a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"


def delete_file(file_path: str) -> None:
    """Deletes a file from the file system."""
    try:
        os.remove(file_path)
        logging.info(f"File {file_path} deleted successfully.")
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
    except Exception as e:
        logging.error(f"Failed to delete file {file_path}: {e}")


def append_to_file(file_path: str, content: str) -> None:
    """Appends content to an existing file."""
    write_to_file(file_path, content, mode='a')


def file_exists(file_path: str) -> bool:
    """Checks if a file exists at the given path."""
    exists = os.path.exists(file_path)
    if exists:
        logging.info(f"File {file_path} exists.")
    else:
        logging.warning(f"File {file_path} does not exist.")
    return exists


def directory_exists(dir_path: str) -> bool:
    """Checks if a directory exists."""
    exists = os.path.isdir(dir_path)
    if exists:
        logging.info(f"Directory {dir_path} exists.")
    else:
        logging.warning(f"Directory {dir_path} does not exist.")
    return exists