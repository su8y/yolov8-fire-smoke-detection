package com.example.preprocessor.service;

import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;

import org.springframework.stereotype.Service;

@Service
public class ImageResizer {

    public BufferedImage resize(BufferedImage originalImage, int targetWidth, int targetHeight) {
        if (originalImage == null) {
            throw new IllegalArgumentException("Original image cannot be null for resizing.");
        }

        BufferedImage resizedImage = new BufferedImage(targetWidth, targetHeight, originalImage.getType());
        
        Graphics2D g = resizedImage.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR); // 부드러운 리사이징
        g.drawImage(originalImage, 0, 0, targetWidth, targetHeight, null);
        g.dispose(); 

        return resizedImage;
    }
}
