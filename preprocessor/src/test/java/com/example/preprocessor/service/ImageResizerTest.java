package com.example.preprocessor.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import java.awt.image.BufferedImage;

@ExtendWith(MockitoExtension.class)
public class ImageResizerTest {
    @InjectMocks
    private ImageResizer imageResizer;

    private BufferedImage originalImage;
    private final int ORIGINAL_WIDTH = 100;
    private final int ORIGINAL_HEIGHT = 50;

    @BeforeEach
    void setUp() {
        originalImage = new BufferedImage(ORIGINAL_WIDTH, ORIGINAL_HEIGHT, BufferedImage.TYPE_INT_RGB);
    }

    @Test
    @DisplayName("유효한 이미지와 크기로 이미지 리사이징에 성공해야 한다")
    void should_resize_image_successfully() {
        int targetWidth = 200;
        int targetHeight = 100;

        // when
        BufferedImage resizedImage = imageResizer.resize(originalImage, targetWidth, targetHeight);

        // then
        assertNotNull(resizedImage);
        assertEquals(targetWidth, resizedImage.getWidth());
        assertEquals(targetHeight, resizedImage.getHeight());
        assertEquals(originalImage.getType(), resizedImage.getType());
    }


    @Test
    @DisplayName("입력 이미지가 null일 경우 Exception을 발생시켜야 한다")
    void should_throw_exception_when_original_image_is_null() {
        // given
        BufferedImage nullImage = null;
        int targetWidth = 100;
        int targetHeight = 100;

        // when & then
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            imageResizer.resize(nullImage, targetWidth, targetHeight);
        });

        assertEquals("Original image cannot be null for resizing.", exception.getMessage());
    }
}
