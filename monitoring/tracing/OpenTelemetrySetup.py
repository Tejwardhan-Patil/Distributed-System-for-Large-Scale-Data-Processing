from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
from opentelemetry.sdk.metrics import MeterProvider
from prometheus_client import start_http_server
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from flask import Flask, request
import time
import random
import requests

# Initialize Flask app
app = Flask(__name__)

# Initialize tracing provider and exporter
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Jaeger Exporter for traces
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)

# Span processor that forwards completed spans to the Jaeger exporter
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Console exporter for debugging
console_exporter = ConsoleSpanExporter()
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(console_exporter))

# Initialize metrics provider and exporter
metrics.set_meter_provider(MeterProvider())
meter = metrics.get_meter(__name__)

# Prometheus metrics exporter
prometheus_exporter = PrometheusMetricsExporter(meter)
start_http_server(8000)  # Start Prometheus metrics server on port 8000

# Register common metrics
request_counter = meter.create_counter(
    "requests_total",
    "Number of requests received",
    unit="requests",
)

response_histogram = meter.create_histogram(
    "request_duration_seconds",
    "Duration of requests in seconds",
    unit="seconds",
)

# Instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

@app.route('/')
def index():
    with tracer.start_as_current_span("index_span") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        response_time = random.uniform(0.1, 0.5)
        time.sleep(response_time)
        response_histogram.record(response_time)
        return "Hello, OpenTelemetry with Jaeger and Prometheus!", 200

@app.route('/metrics')
def metrics_endpoint():
    with tracer.start_as_current_span("metrics_span"):
        # Business logic with tracing and metrics
        start_time = time.time()
        request_counter.add(1)
        response_time = random.uniform(0.05, 0.2)
        time.sleep(response_time)
        duration = time.time() - start_time
        response_histogram.record(duration)
        return prometheus_exporter.get_metrics_page(), 200

@app.route('/trace')
def trace_endpoint():
    with tracer.start_as_current_span("trace_endpoint_span") as span:
        span.set_attribute("component", "trace")
        span.set_attribute("trace.custom", "demo-trace")
        time.sleep(random.uniform(0.2, 0.4))
        return "Traced endpoint.", 200

@app.route('/error')
def error_endpoint():
    with tracer.start_as_current_span("error_span") as span:
        span.set_attribute("error", True)
        try:
            1 / 0
        except ZeroDivisionError as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Division by zero"))
            return "An error occurred.", 500

@app.route('/external-call')
def external_call():
    with tracer.start_as_current_span("external_call_span") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", "https://httpbin.org/get")
        response = requests.get("https://httpbin.org/get")
        span.set_attribute("http.status_code", response.status_code)
        return f"External API call status: {response.status_code}", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)