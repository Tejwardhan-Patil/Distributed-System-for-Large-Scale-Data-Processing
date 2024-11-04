import unittest
import os
import yaml
from monitoring.prometheus.prometheus_config import PrometheusConfig
from monitoring.grafana.grafana_dashboards import GrafanaDashboards
from monitoring.logging.elk_stack_setup import ElkStackSetup
from monitoring.tracing.opentelemetry_setup import OpenTelemetrySetup

class TestMonitoringSetup(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.prometheus_config_path = "monitoring/prometheus/prometheus_config.yaml"
        cls.grafana_config_path = "monitoring/grafana/grafana_dashboards.json"
        cls.fluentd_config_path = "monitoring/logging/fluentd_config.yaml"
        cls.opentelemetry_config_path = "monitoring/tracing/jaeger_config.yaml"
        
        cls.prometheus_config = PrometheusConfig(cls.prometheus_config_path)
        cls.grafana_dashboards = GrafanaDashboards(cls.grafana_config_path)
        cls.elk_stack = ElkStackSetup(cls.fluentd_config_path)
        cls.opentelemetry_setup = OpenTelemetrySetup(cls.opentelemetry_config_path)

    def test_prometheus_config_file_exists(self):
        self.assertTrue(os.path.exists(self.prometheus_config_path), "Prometheus config file does not exist.")
    
    def test_grafana_dashboards_file_exists(self):
        self.assertTrue(os.path.exists(self.grafana_config_path), "Grafana dashboards file does not exist.")
    
    def test_fluentd_config_file_exists(self):
        self.assertTrue(os.path.exists(self.fluentd_config_path), "Fluentd config file does not exist.")
    
    def test_opentelemetry_config_file_exists(self):
        self.assertTrue(os.path.exists(self.opentelemetry_config_path), "OpenTelemetry config file does not exist.")

    def test_prometheus_config_loading(self):
        config = self.prometheus_config.load_config()
        self.assertIsInstance(config, dict, "Prometheus config should be a dictionary.")
        self.assertIn("global", config, "Prometheus global configuration missing.")
    
    def test_grafana_dashboards_loading(self):
        dashboards = self.grafana_dashboards.load_dashboards()
        self.assertIsInstance(dashboards, list, "Grafana dashboards should be a list.")
        self.assertGreater(len(dashboards), 0, "No dashboards found in Grafana configuration.")

    def test_fluentd_config_loading(self):
        with open(self.fluentd_config_path, 'r') as file:
            config = yaml.safe_load(file)
        self.assertIsInstance(config, dict, "Fluentd config should be a dictionary.")
        self.assertIn("inputs", config, "Fluentd inputs configuration missing.")
    
    def test_opentelemetry_config_loading(self):
        config = self.opentelemetry_setup.load_config()
        self.assertIsInstance(config, dict, "OpenTelemetry config should be a dictionary.")
        self.assertIn("service", config, "OpenTelemetry service configuration missing.")
    
    def test_prometheus_targets(self):
        config = self.prometheus_config.load_config()
        scrape_configs = config.get("scrape_configs", [])
        self.assertGreater(len(scrape_configs), 0, "No scrape configurations found in Prometheus config.")
        self.assertTrue(any(target['job_name'] == 'prometheus' for target in scrape_configs), "Prometheus job target not found in scrape_configs.")
    
    def test_grafana_dashboard_titles(self):
        dashboards = self.grafana_dashboards.load_dashboards()
        for dashboard in dashboards:
            self.assertIn("title", dashboard, "Grafana dashboard missing title field.")
            self.assertIsInstance(dashboard["title"], str, "Grafana dashboard title should be a string.")
    
    def test_fluentd_input_config(self):
        with open(self.fluentd_config_path, 'r') as file:
            config = yaml.safe_load(file)
        inputs = config.get("inputs", [])
        self.assertGreater(len(inputs), 0, "No inputs found in Fluentd configuration.")
        self.assertIn("type", inputs[0], "Fluentd input type is missing.")
    
    def test_opentelemetry_traces(self):
        config = self.opentelemetry_setup.load_config()
        self.assertIn("exporters", config, "OpenTelemetry exporters missing.")
        self.assertIn("jaeger", config["exporters"], "Jaeger exporter missing in OpenTelemetry config.")
    
    def test_prometheus_alert_rules(self):
        alert_rules_path = "monitoring/prometheus/alert_rules.yml"
        with open(alert_rules_path, 'r') as file:
            rules = yaml.safe_load(file)
        self.assertIsInstance(rules, dict, "Alert rules should be a dictionary.")
        self.assertIn("groups", rules, "Prometheus alert rules missing groups.")
        self.assertGreater(len(rules["groups"]), 0, "No groups found in Prometheus alert rules.")
    
    def test_grafana_datasources(self):
        datasources_path = "monitoring/grafana/datasources.yaml"
        with open(datasources_path, 'r') as file:
            datasources = yaml.safe_load(file)
        self.assertIsInstance(datasources, list, "Grafana datasources should be a list.")
        self.assertGreater(len(datasources), 0, "No datasources found in Grafana configuration.")
    
    def test_fluentd_output_config(self):
        with open(self.fluentd_config_path, 'r') as file:
            config = yaml.safe_load(file)
        outputs = config.get("outputs", [])
        self.assertGreater(len(outputs), 0, "No outputs found in Fluentd configuration.")
        self.assertIn("type", outputs[0], "Fluentd output type is missing.")
    
    def test_opentelemetry_resource_attributes(self):
        config = self.opentelemetry_setup.load_config()
        self.assertIn("resource", config, "OpenTelemetry resource configuration missing.")
        self.assertIn("attributes", config["resource"], "OpenTelemetry resource attributes missing.")
    
    def test_prometheus_scrape_interval(self):
        config = self.prometheus_config.load_config()
        self.assertIn("scrape_interval", config["global"], "Prometheus scrape interval missing.")
        self.assertRegex(config["global"]["scrape_interval"], r'^\d+[smh]$', "Invalid scrape interval format in Prometheus config.")
    
    def test_grafana_dashboard_panels(self):
        dashboards = self.grafana_dashboards.load_dashboards()
        for dashboard in dashboards:
            self.assertIn("panels", dashboard, "Grafana dashboard missing panels field.")
            self.assertIsInstance(dashboard["panels"], list, "Grafana dashboard panels should be a list.")
    
    def test_fluentd_buffer_config(self):
        with open(self.fluentd_config_path, 'r') as file:
            config = yaml.safe_load(file)
        buffers = config.get("buffers", [])
        self.assertGreater(len(buffers), 0, "No buffers found in Fluentd configuration.")
        self.assertIn("type", buffers[0], "Fluentd buffer type is missing.")
    
    def test_opentelemetry_sampler(self):
        config = self.opentelemetry_setup.load_config()
        self.assertIn("sampler", config, "OpenTelemetry sampler configuration missing.")
        self.assertEqual(config["sampler"], "always_on", "OpenTelemetry sampler should be 'always_on'.")
    
    def test_prometheus_relabel_configs(self):
        config = self.prometheus_config.load_config()
        self.assertIn("relabel_configs", config, "Prometheus relabel configurations missing.")
        self.assertIsInstance(config["relabel_configs"], list, "Prometheus relabel_configs should be a list.")
    
    def test_grafana_dashboard_template_vars(self):
        dashboards = self.grafana_dashboards.load_dashboards()
        for dashboard in dashboards:
            self.assertIn("templating", dashboard, "Grafana dashboard missing templating field.")
            self.assertIn("list", dashboard["templating"], "Grafana dashboard templating missing list field.")
    
    def test_fluentd_filter_config(self):
        with open(self.fluentd_config_path, 'r') as file:
            config = yaml.safe_load(file)
        filters = config.get("filters", [])
        self.assertGreater(len(filters), 0, "No filters found in Fluentd configuration.")
        self.assertIn("type", filters[0], "Fluentd filter type is missing.")
    
    def test_opentelemetry_exporters(self):
        config = self.opentelemetry_setup.load_config()
        self.assertIn("exporters", config, "OpenTelemetry exporters configuration missing.")
        self.assertIn("logging", config["exporters"], "Logging exporter missing in OpenTelemetry exporters.")
    
if __name__ == '__main__':
    unittest.main()