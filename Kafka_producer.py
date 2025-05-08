from kafka import KafkaProducer
import json

# Sample data (in real usage, import or generate this dynamically)
vouchsys_metrics = json.load(open("vouchsys_metrics.json"))

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send to topic
producer.send('vouchsys-metrics', vouchsys_metrics)
producer.flush()

print("Metrics sent to Kafka topic 'vouchsys-metrics'")
