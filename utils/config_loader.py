import os
import yaml
import json
from typing import Dict, Any

class ConfigLoader:
    """Class to load and manage configuration settings from various file formats."""

    def __init__(self, env: str = 'dev', config_dir: str = './configs'):
        """
        Initializes ConfigLoader with environment and configuration directory.
        
        Args:
            env (str): Environment name ('dev', 'prod', etc.).
            config_dir (str): Path to the directory containing configuration files.
        """
        self.env = env
        self.config_dir = config_dir
        self.config = {}

    def _load_yaml(self, filepath: str) -> Dict[str, Any]:
        """
        Loads a YAML configuration file.

        Args:
            filepath (str): Path to the YAML file.

        Returns:
            dict: Parsed YAML configuration as a dictionary.
        """
        with open(filepath, 'r') as file:
            return yaml.safe_load(file)

    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """
        Loads a JSON configuration file.

        Args:
            filepath (str): Path to the JSON file.

        Returns:
            dict: Parsed JSON configuration as a dictionary.
        """
        with open(filepath, 'r') as file:
            return json.load(file)

    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merges two dictionaries.

        Args:
            base (dict): Base configuration dictionary.
            override (dict): Override configuration dictionary.

        Returns:
            dict: Merged dictionary.
        """
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                base[key] = self._merge_dicts(base[key], value)
            else:
                base[key] = value
        return base

    def _load_config(self, filename: str) -> Dict[str, Any]:
        """
        Loads a configuration file based on its extension.

        Args:
            filename (str): Name of the configuration file.

        Returns:
            dict: Parsed configuration as a dictionary.
        """
        filepath = os.path.join(self.config_dir, filename)
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            return self._load_yaml(filepath)
        elif filename.endswith('.json'):
            return self._load_json(filepath)
        else:
            raise ValueError(f"Unsupported config file format: {filename}")

    def load(self) -> None:
        """
        Loads and merges environment-specific and common configuration files.

        Raises:
            ValueError: If configuration files cannot be loaded or merged.
        """
        common_config = f"config.common.yaml"
        env_config = f"config.{self.env}.yaml"

        self.config = self._load_config(common_config)

        # Merge environment-specific config
        try:
            env_config_data = self._load_config(env_config)
            self.config = self._merge_dicts(self.config, env_config_data)
        except FileNotFoundError:
            print(f"No environment-specific config found for {self.env}, using common config only.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value by key.

        Args:
            key (str): Configuration key.
            default (Any): Default value if the key is not found.

        Returns:
            Any: Configuration value or default value.
        """
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
        except KeyError:
            return default
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Sets a configuration value by key.

        Args:
            key (str): Configuration key.
            value (Any): Value to set.
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self, filepath: str) -> None:
        """
        Saves the current configuration to a YAML file.

        Args:
            filepath (str): File path to save the configuration.
        """
        with open(filepath, 'w') as file:
            yaml.dump(self.config, file)

    def load_from_env(self) -> None:
        """
        Loads configuration values from environment variables.
        Environment variables must be in the form of CONFIG_KEY=value.
        """
        for key, value in os.environ.items():
            if key.startswith('CONFIG_'):
                config_key = key[len('CONFIG_'):].lower().replace('__', '.')
                self.set(config_key, value)

    def print(self) -> None:
        """
        Prints the current configuration to the console.
        """
        print(json.dumps(self.config, indent=4))

    def get_config_for_service(self, service_name: str) -> Dict[str, Any]:
        """
        Retrieves configuration for a specific service.

        Args:
            service_name (str): Name of the service.

        Returns:
            dict: Configuration for the specified service.
        """
        return self.get(f'services.{service_name}', {})

# Usage
if __name__ == "__main__":
    config_loader = ConfigLoader(env='prod')
    config_loader.load()
    config_loader.load_from_env()

    # Get a specific config value
    db_host = config_loader.get('database.host', 'localhost')
    print(f"Database Host: {db_host}")

    # Set and save a new configuration value
    config_loader.set('database.port', 5432)
    config_loader.save('./configs/config.updated.yaml')

    # Print the configuration
    config_loader.print()

    # Get configuration for a specific service
    service_config = config_loader.get_config_for_service('webserver')
    print(f"Webserver Config: {service_config}")