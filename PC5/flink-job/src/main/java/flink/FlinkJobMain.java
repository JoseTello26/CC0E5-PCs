package flink;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.util.Collector;
import org.apache.flink.streaming.api.functions.ProcessFunction;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.assigners.SlidingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.functions.FilterFunction;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class FlinkJobMain {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers("kafka:9092")
                .setTopics("transactions")
                .setGroupId("anomaly-detection-" + System.currentTimeMillis())
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        DataStream<String> rawStream = env.fromSource(
                source,
                WatermarkStrategy.noWatermarks(),
                "Kafka Source"
        );

        // Print raw messages
        rawStream
            .process(new ProcessFunction<String, String>() {
                @Override
                public void processElement(String value, Context ctx, Collector<String> out) {
                    System.out.println("📦 Recibido raw: " + value);
                    out.collect(value);
                }
            })
            .print("Raw Messages");

        // Parse JSON to TransactionEvent and filter nulls
        DataStream<TransactionEvent> events = rawStream
            .map(new JsonToTransactionEventMapper())
            .filter(new FilterFunction<TransactionEvent>() {
                @Override
                public boolean filter(TransactionEvent event) throws Exception {
                    if (event == null) {
                        System.out.println("❌ Filtrando evento nulo");
                        return false;
                    }
                    return true;
                }
            })
            .name("Parse JSON Events");

        // Print parsed events
        events
            .process(new ProcessFunction<TransactionEvent, TransactionEvent>() {
                @Override
                public void processElement(TransactionEvent event, Context ctx, Collector<TransactionEvent> out) {
                    System.out.println("📊 Evento parseado: " + event.toString());
                    out.collect(event);
                }
            })
            .print("Parsed Events");

        // Detect anomalies in sliding window of 5 seconds
        DataStream<AnomalyAlert> anomalyStream = events
            .keyBy(TransactionEvent::getUserId)
            .window(SlidingProcessingTimeWindows.of(Time.seconds(5), Time.seconds(1)))
            .process(new AnomalyDetectionFunction())
            .name("Anomaly Detection");

        // Print anomaly alerts
        anomalyStream
            .process(new ProcessFunction<AnomalyAlert, AnomalyAlert>() {
                @Override
                public void processElement(AnomalyAlert alert, Context ctx, Collector<AnomalyAlert> out) {
                    System.out.println("🚨 ANOMALY DETECTED: " + alert.toString());
                    out.collect(alert);
                }
            })
            .print("Anomaly Alerts");

        env.execute("Transaction Anomaly Detection");
    }

    // Mapper to convert JSON string to TransactionEvent
    public static class JsonToTransactionEventMapper implements MapFunction<String, TransactionEvent> {
        private transient ObjectMapper objectMapper;

        @Override
        public TransactionEvent map(String json) throws Exception {
            if (objectMapper == null) {
                objectMapper = new ObjectMapper();
                objectMapper.registerModule(new JavaTimeModule());
            }

            try {
                System.out.println("🔄 Parsing JSON: " + json);
                TransactionEvent event = objectMapper.readValue(json, TransactionEvent.class);
                System.out.println("✅ Successfully parsed: " + event.toString());
                return event;
            } catch (Exception e) {
                System.out.println("❌ Error parsing JSON: " + json + " - " + e.getMessage());
                return null;
            }
        }
    }

    // Window function for anomaly detection
    public static class AnomalyDetectionFunction extends ProcessWindowFunction<TransactionEvent, AnomalyAlert, String, TimeWindow> {
        
        @Override
        public void process(String userId, 
                          ProcessWindowFunction<TransactionEvent, AnomalyAlert, String, TimeWindow>.Context context,
                          Iterable<TransactionEvent> events, 
                          Collector<AnomalyAlert> collector) throws Exception {
            
            List<TransactionEvent> eventList = new ArrayList<>();
            events.forEach(eventList::add);
            
            if (eventList.isEmpty()) {
                return;
            }
            
            System.out.println("🔍 Processing window for user " + userId + " with " + eventList.size() + " events");
            
            // Check for anomalies
            List<String> anomalies = new ArrayList<>();
            
            // 1. Check for high frequency (more than 5 events in window)
            if (eventList.size() > 5) {
                String anomaly = "HIGH_FREQUENCY: " + eventList.size() + " events in 5s window";
                anomalies.add(anomaly);
                System.out.println("⚠️ " + anomaly);
            }
            
            // 2. Check individual events for anomalies
            for (TransactionEvent event : eventList) {
                if (event.isHighAmount()) {
                    String anomaly = "HIGH_AMOUNT: $" + event.getAmount() + " for user " + userId;
                    anomalies.add(anomaly);
                    System.out.println("⚠️ " + anomaly);
                }
                
                if (event.isSuspiciousLocation()) {
                    String anomaly = "SUSPICIOUS_LOCATION: lat=" + event.getLatitude() + 
                                ", lon=" + event.getLongitude() + " for user " + userId;
                    anomalies.add(anomaly);
                    System.out.println("⚠️ " + anomaly);
                }
                
                if (event.isSuspiciousIp()) {
                    String anomaly = "SUSPICIOUS_IP: " + event.getIpAddress() + " for user " + userId;
                    anomalies.add(anomaly);
                    System.out.println("⚠️ " + anomaly);
                }
            }
            
            // If anomalies found, create alert
            if (!anomalies.isEmpty()) {
                AnomalyAlert alert = new AnomalyAlert(
                    userId,
                    eventList.size(),
                    anomalies,
                    LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                    context.window().getStart(),
                    context.window().getEnd()
                );
                System.out.println("🚨 Creating anomaly alert: " + alert.toString());
                collector.collect(alert);
            } else {
                System.out.println("✅ No anomalies detected for user " + userId + " in this window");
            }
        }
    }
}
