package com.example.preprocessor.controller;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.preprocessor.service.ImageProcessingService;
import org.springframework.web.bind.annotation.RequestBody;


@RestController
@RequestMapping("/api/images")
public class ImageUploadController {

    private static final Logger logger = LoggerFactory.getLogger(ImageUploadController.class);

    private final ImageProcessingService imageProcessingService;

    public ImageUploadController(ImageProcessingService imageProcessingService) {
        this.imageProcessingService = imageProcessingService;
    }
    @PostMapping("/test")
    public String postMethodName() {
        return "test";
    }
    

    @PostMapping("/upload-process")
    @CrossOrigin(origins = "*") // CORS 설정: 모든 도메인 허용
    public ResponseEntity<String> uploadAndProcessImage(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return new ResponseEntity<>("Please select a file to upload.", HttpStatus.BAD_REQUEST);
        }
        if (!file.getContentType().startsWith("image/")) {
            return new ResponseEntity<>("Only image files are allowed.", HttpStatus.BAD_REQUEST);
        }

        try {
            String imageId = imageProcessingService.processAndSendImage(file);
            return new ResponseEntity<>("Image processed and sent to Kafka with ID: " + imageId, HttpStatus.OK);
        } catch (IllegalArgumentException e) {
            logger.error("Image processing error: {}", e.getMessage());
            return new ResponseEntity<>("Image processing failed: " + e.getMessage(), HttpStatus.BAD_REQUEST);
        } catch (IOException e) {
            logger.error("Error during image processing or Kafka sending: {}", e.getMessage(), e);
            return new ResponseEntity<>("Error processing image: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            logger.error("An unexpected error occurred: {}", e.getMessage(), e);
            return new ResponseEntity<>("An unexpected error occurred: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
