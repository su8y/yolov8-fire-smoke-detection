package com.example.preprocessor.strategy;

import java.awt.image.BufferedImage;
import java.io.IOException;

public interface ImageCompressionStrategy {

    /**
     * 주어진 이미지를 압축하여 바이트 배열로 반환합니다.
     *
     * @param image 압축할 이미지
     * @return 압축된 이미지 데이터 바이트 배열
     * @throws IOException 이미지 압축 중 발생할 수 있는 예외
     */
    byte[] compress(BufferedImage image) throws IOException;
} 