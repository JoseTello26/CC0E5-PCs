from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="kafka:9092",  # o "kafka:9092" si estás en Docker
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="debug-consumer",
    value_deserializer=lambda m: m.decode("utf-8"),
)

print("📥 Escuchando mensajes del topic 'transactions'...")
for message in consumer:
    print(f"📦 Recibido: {message.value}")
