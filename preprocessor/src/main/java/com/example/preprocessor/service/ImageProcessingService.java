package com.example.preprocessor.service;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.UUID;

import javax.imageio.ImageIO;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.example.preprocessor.strategy.ImageCompressionStrategy;

@Service
public class ImageProcessingService {
    
    private static final int TARGET_WIDTH = 600;
    private static final int TARGET_HEIGHT = 600;

    private final ImageResizer imageResizer;
    private final ImageCompressionStrategy imageCompressor;   // DIP: 인터페이스에 의존
    private final KafkaProducerService kafkaProducerService;

    public ImageProcessingService(
            ImageResizer imageResizer,
            ImageCompressionStrategy imageCompressor,   // 주입될 실제 구현체는 JpegImageCompressor
            KafkaProducerService kafkaProducerService) {
        this.imageResizer = imageResizer;
        this.imageCompressor = imageCompressor;
        this.kafkaProducerService = kafkaProducerService;
    }

    /**
     * 업로드된 이미지를 처리하고 Kafka에 전송하는 메인 로직.
     *
     * @param file 업로드된 이미지 파일
     * @return 처리된 이미지의 고유 ID (Kafka Key)
     * @throws IOException 이미지 처리 중 발생할 수 있는 예외
     */
    public String processAndSendImage(MultipartFile file) throws IOException {
        // 1. 이미지 읽기
        BufferedImage originalImage = ImageIO.read(file.getInputStream());
        if (originalImage == null) {
            throw new IllegalArgumentException("Could not read image from provided file. Invalid format or corrupted file.");
        }

        // 2. 이미지 리사이징
        BufferedImage resizedImage = imageResizer.resize(originalImage, TARGET_WIDTH, TARGET_HEIGHT);


        // 4. 이미지 압축 (JPEG)
        byte[] compressedImageBytes = imageCompressor.compress(resizedImage);

        // 5. Kafka 토픽에 전송
        String imageId = UUID.randomUUID().toString(); // 고유 이미지 ID 생성
        kafkaProducerService.sendMessage(imageId, compressedImageBytes);
        // 원본 저장 
        //ByteArrayOutputStream baso = new ByteArrayOutputStream();
        //ImageIO.write(resizedImage, "jpg", baso);
        //kafkaProducerService.sendMessage(imageId + "_original", baso.toByteArray());
        



        return imageId;
    }
}
