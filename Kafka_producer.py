from kafka import KafkaProducer
import json

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
import logging

# Set up OpenTelemetry resource
resource = Resource(attributes={
    "service.name": "vouchsys-metrics-producer"
})

# Setup tracer
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# Setup metrics
reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
meter = metrics.get_meter(__name__)
messages_counter = meter.create_counter(
    name="messages_sent",
    unit="1",
    description="Number of Kafka messages sent"
)

# Setup logging
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogExporter()))
logging_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.basicConfig(level=logging.INFO, handlers=[logging_handler])
logger = logging.getLogger(__name__)

# Load sample data
vouchsys_metrics = json.load(open("vouchsys_metrics.json"))

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send to topic with tracing
with tracer.start_as_current_span("send_metrics_to_kafka") as span:
    try:
        producer.send('vouchsys-metrics', vouchsys_metrics)
        producer.flush()
        logger.info("Metrics sent to Kafka topic 'vouchsys-metrics'")
        messages_counter.add(1, {"topic": "vouchsys-metrics"})
    except Exception as e:
        logger.error(f"Failed to send metrics to Kafka: {e}")
        span.record_exception(e)
        span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, str(e)))
