# Sistema de Detección de Anomalías en Tiempo Real

Este proyecto implementa un sistema de detección de anomalías en eventos de transacción usando Apache Kafka y Apache Flink, desplegado con Docker.

## 🏗️ Arquitectura

- **Producer**: Genera eventos de transacción simulados cada 500ms
- **Flink Job**: Procesa eventos en tiempo real y detecta anomalías
- **Kafka**: Broker de mensajes para comunicación entre componentes
- **Zookeeper**: Coordinador para Kafka

## 📊 Formato del Evento

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

## 🔍 Reglas de Detección de Anomalías

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

## 🚀 Inicio Rápido

1. **Clonar y navegar al proyecto:**
   ```bash
   cd anomaly-flink-project
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

## 📁 Estructura del Proyecto

```
anomaly-flink-project/
├── producer/                 # Generador de eventos
│   ├── src/main/java/
│   │   └── producer/
│   │       └── DataGenerator.java
│   ├── pom.xml
│   └── Dockerfile
├── flink-job/               # Job de Flink
│   ├── src/main/java/flink/
│   │   ├── FlinkJobMain.java
│   │   └── TransactionEvent.java
│   ├── pom.xml
│   └── Dockerfile
├── docker-compose.yml       # Orquestación de contenedores
├── start.sh                 # Script de inicio
├── restart-service.sh       # Script para reiniciar servicios
├── example-event.json       # Ejemplo de evento
└── README.md
```

## 🛠️ Desarrollo

Para modificar el código:

1. Edita los archivos `.java` en tu editor
2. Reinicia el contenedor específico:
   ```bash
   # Para producer
   ./restart-service.sh producer
   
   # Para flink-job
   ./restart-service.sh flink-job
   
   # Para ambos
   ./restart-service.sh all
   ```

### Ejemplo de Modificación

Si quieres cambiar la frecuencia de generación de eventos en `DataGenerator.java`:

```java
// Cambiar de 500ms a 1000ms
TimeUnit.MILLISECONDS.sleep(1000);
```

Luego reinicia el producer:
```bash
./restart-service.sh producer
```

## 📊 Monitoreo

- **Flink Web UI**: http://localhost:8081
  - Ver jobs en ejecución
  - Monitorear throughput
  - Revisar logs de tareas
- **Logs de Kafka**: `docker-compose logs kafka`
- **Logs de Flink**: `docker-compose logs flink-jobmanager`
- **Logs del Producer**: `docker-compose logs producer`
- **Logs del Job**: `docker-compose logs flink-job`

## 🔧 Configuración

### Variables de Entorno

- `KAFKA_BOOTSTRAP_SERVERS`: Servidores de Kafka (default: kafka:9092)
- `FLINK_JOBMANAGER_HOST`: Host del JobManager de Flink
- `FLINK_JOBMANAGER_PORT`: Puerto del JobManager de Flink

### Puertos Expuestos

- **8081**: Flink Web UI
- **9092**: Kafka
- **2181**: Zookeeper

## 🛑 Parar el Sistema

```bash
docker-compose down
```

Para limpiar completamente (incluyendo volúmenes):
```bash
docker-compose down -v
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Servicios no inician**:
   ```bash
   docker-compose logs
   ```

2. **Producer no conecta a Kafka**:
   - Verificar que Kafka esté corriendo: `docker-compose ps kafka`
   - Revisar logs: `docker-compose logs kafka`

3. **Flink job no procesa eventos**:
   - Verificar Flink Web UI: http://localhost:8081
   - Revisar logs: `docker-compose logs flink-job`

4. **Cambios de código no se reflejan**:
   - Reiniciar el servicio específico: `./restart-service.sh [service]`
   - Verificar que los volúmenes estén montados correctamente

## 📈 Escalabilidad

El sistema está diseñado para escalar:

- **Kafka**: Agregar más brokers
- **Flink**: Aumentar TaskManagers
- **Producer**: Múltiples instancias
- **Análisis**: Agregar más jobs de Flink

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request 