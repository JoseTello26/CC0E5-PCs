from kafka import KafkaConsumer
from flask import Flask, jsonify
import json
import threading
import time
from datetime import datetime
import pandas as pd

app = Flask(__name__)

kafka_buffer = []
alerts_buffer = []
data_lock = threading.Lock()
consumer_thread = None
alerts_consumer_thread = None
is_running = False

def deserialize(msg):
    try:
        data = json.loads(msg)
        if "timestamp" in data and data["timestamp"]:
            data["timestamp"] = pd.to_datetime(data["timestamp"])
        else:
            data["timestamp"] = pd.to_datetime(time.time(), unit='s')
        return data
    except Exception as e:
        print(f"❌ Error al deserializar el mensaje '{msg}': {e}")
        return None

def deserialize_alert(msg):
    try:
        data = json.loads(msg)
        if "detectionTime" in data and data["detectionTime"]:
            data["detectionTime"] = pd.to_datetime(data["detectionTime"])
        else:
            data["detectionTime"] = pd.to_datetime(time.time(), unit='s')
        return data
    except Exception as e:
        print(f"❌ Error al deserializar la alerta '{msg}': {e}")
        return None

def kafka_consumer_worker():
    global kafka_buffer, is_running
    
    consumer = KafkaConsumer(
        "transactions",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="api-consumer",
        value_deserializer=lambda m: m.decode("utf-8"),
    )
    
    print("🚀 Hilo de Kafka (transactions) iniciado. Esperando mensajes...")
    
    batch_size = 50
    batch_count = 0
    
    while is_running:
        # Leer hasta 50 mensajes o hasta que no haya más disponibles
        messages_read = 0
        for message in consumer:
            if not is_running:
                break
                
            data = deserialize(message.value)
            print(f"📨 Mensaje recibido: {data}")
            if data:
                with data_lock:
                    kafka_buffer.append(data)
                    messages_read += 1
                    print(f"✅ Datos agregados al buffer. Total en buffer: {len(kafka_buffer)}")
            
            if messages_read >= batch_size:
                break
        
        if messages_read > 0:
            batch_count += 1
            print(f"📦 Lote {batch_count} completado. Leídos {messages_read} mensajes. Total en buffer: {len(kafka_buffer)}")
            print(f"⏳ Esperando 5 segundos antes del siguiente lote...")
            time.sleep(5)  # Esperar 5 segundos antes del siguiente lote
        else:
            # Si no hay mensajes, esperar un poco antes de intentar de nuevo
            time.sleep(1)
    
    consumer.close()
    print("🛑 Consumer de Kafka (transactions) detenido.")

def kafka_alerts_consumer_worker():
    global alerts_buffer, is_running
    
    consumer = KafkaConsumer(
        "alerts",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="api-alerts-consumer",
        value_deserializer=lambda m: m.decode("utf-8"),
    )
    
    print("🚨 Hilo de Kafka (alerts) iniciado. Esperando alertas...")
    
    while is_running:
        for message in consumer:
            if not is_running:
                break
                
            alert_data = deserialize_alert(message.value)
            print(f"🚨 Alerta recibida: {alert_data}")
            if alert_data:
                with data_lock:
                    alerts_buffer.append(alert_data)
                    print(f"Alerta agregada al buffer. Total de alertas: {len(alerts_buffer)}")
        
        # Si no hay mensajes, esperar un poco antes de intentar de nuevo
        time.sleep(1)
    
    consumer.close()
    print("Consumer de Kafka (alerts) detenido.")

def start_kafka_consumer():
    global consumer_thread, alerts_consumer_thread, is_running
    if not is_running:
        is_running = True
        consumer_thread = threading.Thread(target=kafka_consumer_worker, daemon=True)
        alerts_consumer_thread = threading.Thread(target=kafka_alerts_consumer_worker, daemon=True)
        consumer_thread.start()
        alerts_consumer_thread.start()
        print("Consumers de Kafka iniciados.")

def stop_kafka_consumer():
    global is_running
    is_running = False
    print("Deteniendo consumers de Kafka...")

# --- Endpoints de la API ---

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud de la API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "transactions_buffer_size": len(kafka_buffer),
        "alerts_buffer_size": len(alerts_buffer),
        "consumer_running": is_running
    })

@app.route('/data', methods=['GET'])
def get_data():
    """Obtener todos los datos del buffer y limpiarlo"""
    global kafka_buffer
    
    with data_lock:
        if kafka_buffer:
            # Convertir los datos a formato serializable
            data_to_send = []
            for item in kafka_buffer:
                item_copy = item.copy()
                if isinstance(item_copy['timestamp'], pd.Timestamp):
                    item_copy['timestamp'] = item_copy['timestamp'].isoformat()
                data_to_send.append(item_copy)
            
            # Limpiar el buffer
            buffer_size = len(kafka_buffer)
            kafka_buffer.clear()
            
            print(f"📤 Enviando {len(data_to_send)} elementos desde la API")
            
            return jsonify({
                "success": True,
                "data": data_to_send,
                "count": len(data_to_send),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": True,
                "data": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            })

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Obtener todas las alertas del buffer y limpiarlo"""
    global alerts_buffer
    
    with data_lock:
        if alerts_buffer:
            # Convertir las alertas a formato serializable
            alerts_to_send = []
            for alert in alerts_buffer:
                alert_copy = alert.copy()
                if isinstance(alert_copy['detectionTime'], pd.Timestamp):
                    alert_copy['detectionTime'] = alert_copy['detectionTime'].isoformat()
                alerts_to_send.append(alert_copy)
            
            alerts_count = len(alerts_buffer)
            alerts_buffer.clear()
            
            print(f"🚨 Enviando {len(alerts_to_send)} alertas desde la API")
            
            return jsonify({
                "success": True,
                "alerts": alerts_to_send,
                "count": len(alerts_to_send),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": True,
                "alerts": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            })

@app.route('/buffer-size', methods=['GET'])
def get_buffer_size():
    """Obtener el tamaño actual de los buffers sin limpiarlos"""
    with data_lock:
        return jsonify({
            "transactions_buffer_size": len(kafka_buffer),
            "alerts_buffer_size": len(alerts_buffer),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/start', methods=['POST'])
def start_consumer():
    """Iniciar los consumers de Kafka"""
    start_kafka_consumer()
    return jsonify({
        "success": True,
        "message": "Consumers iniciados",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/stop', methods=['POST'])
def stop_consumer():
    """Detener los consumers de Kafka"""
    stop_kafka_consumer()
    return jsonify({
        "success": True,
        "message": "Consumers detenidos",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Iniciar los consumers automáticamente
    start_kafka_consumer()
    
    print("Iniciando API Flask en puerto 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
