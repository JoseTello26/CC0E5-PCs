# Sistema de Detección de Anomalías en Tiempo Real

Este proyecto implementa un sistema de detección de anomalías en eventos de transacción usando Apache Kafka y Apache Flink, desplegado con Docker.

## Arquitectura

- **Producer**: Genera eventos de transacción simulados cada 500ms
- **Flink-JobManager/Taskmanager**: Procesa eventos en tiempo real y detecta anomalías
- **Kafka**: Broker de mensajes para comunicación entre componentes
- **Zookeeper**: Coordinador para Kafka

## Formato del Evento

Los eventos de transacción siguen este formato JSON:

```json
{
  "userId": "user123",
  "amount": 500.00,
  "timestamp": "2024-01-29T10:00:00",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "ipAddress": "192.168.1.1"
}
```

### Campos:
- `userId`: Identificador único del usuario
- `amount`: Monto de la transacción (doble)
- `timestamp`: Timestamp en formato ISO 8601
- `latitude`: Latitud de la ubicación
- `longitude`: Longitud de la ubicación
- `ipAddress`: Dirección IP de la transacción

## Reglas de Detección de Anomalías

El sistema detecta las siguientes anomalías:

### 1. **Monto Alto**
- **Condición**: `amount > 5000`
- **Descripción**: Transacciones con montos superiores a $5000

### 2. **Frecuencia Alta**
- **Condición**: Más de 5 eventos en ventana de 5 segundos por usuario
- **Descripción**: Usuario realizando muchas transacciones en poco tiempo

### 3. **Ubicación Sospechosa**
- **Condición**: Coordenadas fuera de rangos normales
- **Rangos normales**: 
  - Latitud: 25° a 50° (aproximadamente US)
  - Longitud: -125° a -65° (aproximadamente US)
- **Descripción**: Transacciones desde ubicaciones geográficas inusuales

### 4. **IP Sospechosa**
- **Condición**: IP que comienza con `10.` o `192.168.`
- **Descripción**: Direcciones IP de redes privadas (posible fraude)

## Inicio Rápido

1. **Clonar y navegar al proyecto:**
   ```bash
   cd PC5
   ```

2. **Levantar todos los servicios:**
   ```bash
   ./start.sh
   ```
   
   O manualmente:
   ```bash
   docker-compose up -d --build
   ```

3. **Verificar servicios:**
   - Flink Web UI: http://localhost:8081
   - Kafka: localhost:9092

4. **Ver logs en tiempo real:**
   ```bash
   docker-compose logs -f
   ```

## Estructura del Proyecto

```
├── consumer.py
├── docker-compose.yml
├── example-event.json
├── flink-job
│   ├── dependency-reduced-pom.xml
│   ├── Dockerfile
│   ├── pom.xml
│   ├── src/main/java/flink
│                  ├── AnomalyAlert.java
│                  ├── FlinkJobMain.java
│                  └── TransactionEvent.java
├── producer
│   ├── Dockerfile
│   ├── pom.xml
│   ├── src/main/java/producer
│                  ├── DataGenerator.java
│                  └── TransactionEvent.java
│   
├── README.md
└── start.sh
```