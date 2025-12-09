package com.example.preprocessor.config;

import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;

import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.ByteArraySerializer;
import org.apache.kafka.common.serialization.StringSerializer;

@Configuration
public class KafkaProducerConfig {
    private static final int LINGER_MS = 10;
    private static final int BATCH_SIZE = 16384;
    private static final int RETRY_COUNT = 3;
    private static final String ACK_TYPE = "all";

    @Value("${spring.kafka.bootstrap-servers}")
    private String bootstrapServers;

    @Bean
    public ProducerFactory<String, byte[]> producerFactory() {
        Map<String, Object> configProps = new HashMap<>();
        configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class); // 이미지 데이터는 byte[]로 전송
        configProps.put(ProducerConfig.ACKS_CONFIG, ACK_TYPE);
        configProps.put(ProducerConfig.RETRIES_CONFIG, RETRY_COUNT);
        configProps.put(ProducerConfig.BATCH_SIZE_CONFIG, BATCH_SIZE);
        configProps.put(ProducerConfig.LINGER_MS_CONFIG, LINGER_MS);

        return new DefaultKafkaProducerFactory<>(configProps);
    }

    @Bean
    public KafkaTemplate<String, byte[]> kafkaTemplate() {
         return new KafkaTemplate<>(producerFactory());
    }
}
 