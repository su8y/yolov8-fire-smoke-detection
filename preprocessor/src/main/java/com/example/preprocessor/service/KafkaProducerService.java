package com.example.preprocessor.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class KafkaProducerService {
    private static final Logger logger = LoggerFactory.getLogger(KafkaProducerService.class);

    private final KafkaTemplate<String, byte[]> kafkaTemplate;

    @Value("${kafka.topic.image-processed}")
    private String topicName;

    public KafkaProducerService(KafkaTemplate<String, byte[]> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * 이미지 바이트 배열을 Kafka 토픽으로 전송합니다.
     *
     * @param key        메시지 키 (예: 이미지 ID, 파일명)
     * @param imageBytes 처리된 이미지 바이트 배열
     */
    public void sendMessage(String key, byte[] imageBytes) {
        // 비동기 전송 및 콜백 처리로 성공/실패 로깅
        var future = kafkaTemplate.send(topicName, key, imageBytes);

        future.thenAccept(result -> {
            logger.info("Message sent successfully to Kafka. Topic: {}, Partition: {}, Offset: {}, Key: {}",
                    result.getRecordMetadata().topic(),
                    result.getRecordMetadata().partition(),
                    result.getRecordMetadata().offset(),
                    key);
        }).exceptionally(ex -> {
            logger.error("Failed to send message to Kafka. Key: {}, Error: {}", key, ex.getMessage(), ex);
            return null; // 예외 처리 후 null 반환 (또는 다른 CompletableFuture 처리)
        });
    }
}
