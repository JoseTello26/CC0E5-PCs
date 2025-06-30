package producer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.TimeUnit;

public class DataGenerator {
    private static final String TOPIC = "transactions";
    private static final String KAFKA_BOOTSTRAP_SERVERS = "kafka:9092";

    public static void main(String[] args) throws Exception {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA_BOOTSTRAP_SERVERS);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        KafkaProducer<String, String> producer = new KafkaProducer<>(props);

        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());

        Random rand = new Random();

        String[] userIds = {"user1", "user2", "user3", "user4"};
        Map<String, double[]> userLocations = new HashMap<>();
        userLocations.put("user1", new double[]{40.0, -100.0});
        userLocations.put("user2", new double[]{41.0, -101.0});
        userLocations.put("user3", new double[]{42.0, -102.0});
        userLocations.put("user4", new double[]{43.0, -103.0});

        String[] suspiciousIps = {"192.168.1.1", "10.0.0.1"};

        for (int i = 0; i < 30; i++) {
            String userId = userIds[rand.nextInt(userIds.length)];

            // Base location
            double[] baseLocation = userLocations.get(userId);
            double latitude = baseLocation[0];
            double longitude = baseLocation[1];

            // 15% chance of suspicious location
            if (rand.nextDouble() < 0.15) {
                latitude = 10.0;
                longitude = -140.0;
            }

            // 20% high amount
            double amount = rand.nextDouble() < 0.2 ? 8000.0 : 100.0 + rand.nextInt(900);

            // 10% suspicious IP
            String ip = rand.nextDouble() < 0.1 ? suspiciousIps[rand.nextInt(suspiciousIps.length)] : "203.0.113.1";

            TransactionEvent event = new TransactionEvent(
                    userId,
                    amount,
                    LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                    latitude,
                    longitude,
                    ip
            );

            String json = mapper.writeValueAsString(event);
            ProducerRecord<String, String> record = new ProducerRecord<>(TOPIC, userId, json);
            producer.send(record);
            System.out.printf("✅ Enviado: %s\n", json);
            TimeUnit.MILLISECONDS.sleep(500);
        }

        producer.close();
    }
}
