import base64
from datetime import datetime
import os
from tabnanny import verbose
import time
from confluent_kafka import Consumer, KafkaError
from PIL import Image
import io
import uuid

import cv2
import logging
import numpy as np
import torch
import torchvision
from ultralytics import YOLO # 이미지 파일명으로 사용할 고유 ID 생성
from torchvision import transforms # to tensor test

def parse_yolov8_output(output, conf_threshold=0.25, iou_threshold=0.45):
    """
    YOLOv8 raw output을 파싱
    
    Args:
        output: model.model()의 출력 (tuple 또는 list)
        conf_threshold: 신뢰도 임계값
        iou_threshold: NMS IoU 임계값
    
    Returns:
        List of detections per image
    """
    # YOLOv8 출력 형태: (1, 84, 8400) 또는 리스트
    # 84 = 4(bbox) + 80(classes)
    
    if isinstance(output, (list, tuple)):
        output = output[0]  # 첫 번째 출력 사용
    
    batch_size = output.shape[0]
    num_classes = output.shape[1] - 4  # 4는 bbox 좌표
    
    all_detections = []
    
    for batch_idx in range(batch_size):
        predictions = output[batch_idx].T  # (8400, 84) -> (num_anchors, 84)
        
        # bbox와 클래스 점수 분리
        boxes = predictions[:, :4]  # (num_anchors, 4) - x_center, y_center, w, h
        scores = predictions[:, 4:]  # (num_anchors, 80)
        
        # 최대 신뢰도와 클래스 ID
        max_scores, class_ids = scores.max(dim=1)
        
        # 신뢰도 필터링
        mask = max_scores > conf_threshold
        boxes = boxes[mask]
        max_scores = max_scores[mask]
        class_ids = class_ids[mask]
        
        if boxes.shape[0] == 0:
            all_detections.append([])
            continue
        
        # 중심 좌표를 xyxy 형식으로 변환
        x_center, y_center, w, h = boxes.T
        x1 = x_center - w / 2
        y1 = y_center - h / 2
        x2 = x_center + w / 2
        y2 = y_center + h / 2
        boxes_xyxy = torch.stack([x1, y1, x2, y2], dim=1)
        
        # NMS (Non-Maximum Suppression)
        keep_indices = torchvision.ops.nms(boxes_xyxy, max_scores, iou_threshold)
        
        # 최종 detection
        final_boxes = boxes_xyxy[keep_indices]
        final_scores = max_scores[keep_indices]
        final_classes = class_ids[keep_indices]
        
        detections = []
        for i in range(len(final_boxes)):
            detection = {
                "bbox": final_boxes[i].tolist(),  # [x1, y1, x2, y2]
                "confidence": float(final_scores[i]),
                "class_id": int(final_classes[i])
            }
            detections.append(detection)
        
        all_detections.append(detections)
    
    return all_detections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
end_time = None;

# --- Kafka 및 저장소 설정 ---
KAFKA_BROKER = 'localhost:9092'  # Kafka 브로커 주소 (필요에 따라 변경)
KAFKA_TOPIC = 'hello-world'      # Kafka 토픽 이름
CONSUMER_GROUP_ID = 'image_saver_group_v1' # 컨슈머 그룹 ID

try:
    # 현재 파일 기준 app/best-fire-smoke-yolo8s.pt 경로 설정
    weight = os.path.abspath("best-fire-smoke-yolo8s.pt" )
    if not os.path.exists(weight):
        raise FileNotFoundError(f"Weight file not found: {weight}")
    print("Load exist weight ", weight)
    model = YOLO(weight).model
    model.to('cuda')  # GPU 사용을 위해 모델을 CUDA로 이동
    model.eval()
    print("YOLO 모델이 성공적으로 로드되었습니다.")
    print("클래스 이름:", model.names)
    classnames = model.names
except Exception as e:
    print(f"YOLO 모델 로드 실패: {str(e)}")
    model = None

to_tensor = transforms.Compose([
    transforms.ToTensor()
])
TARGET_SIZE = (640, 640)
def toImage(image_bytes):
    """
    PIL Image 객체를 NumPy 배열로 변환합니다.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != 'RGB': image = image.convert('RGB')

    # # PIL to Tensor
    # image = np.array(image)              # HWC, uint8
    # image = image[:, :, ::-1].copy()     # RGB → BGR (YOLO 내부 처리용)
    # image = torch.from_numpy(image)      # Tensor
    # image = image.permute(2, 0, 1).float()
    image = image.resize(TARGET_SIZE)  # 모든 이미지 같은 크기로
    return transforms.ToTensor()(image)


def parse_results(results):
    detections = []
    fire_detected = False

    for res in results:
        for i, box in enumerate(res.boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = classnames[class_id]
            
            # fire 클래스 감지 여부 확인
            if class_name == 'fire' or class_name == 'smoke':
                fire_detected = True
            
            detection = {
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence,
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
            }
            detections.append(detection)
    return [fire_detected, detections]

start_time = time.time()
message_count = 0

def consume_images_from_kafka():
    global start_time, message_count, model
    # Kafka Consumer 설정
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': CONSUMER_GROUP_ID,
        'auto.offset.reset': 'earliest' # 'earliest'는 가장 오래된 메시지부터, 'latest'는 최신 메시지부터
    }

    consumer = None
    try:
        consumer = Consumer(conf)
        consumer.subscribe([KAFKA_TOPIC])

        print(f"Listening for messages on topic '{KAFKA_TOPIC}'...")
        BATCH_SIZE = 8 
        image_batch = []
        key_batch = []
        while True:
            # 메시지 폴링 (timeout 설정으로 일정 시간 대기)
            msg = consumer.poll(timeout=1.0) # 1초 대기

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # 토픽의 끝에 도달 (더 이상 새 메시지가 없을 때)
                    print(f"%% Reached end of partition {msg.partition()} in topic {msg.topic()} %%")
                elif msg.error():
                    print(f"Consumer error: {msg.error()}")
                continue

            # 메시지 처리
            key_bytes = msg.key()
            image_bytes = msg.value()
            
            # 키(key)는 바이트이므로 디코딩 (Producer에서 String으로 보냈다면)
            # Producer가 UUID.randomUUID().toString()으로 보냈으므로 UTF-8 디코딩
            image_key = key_bytes.decode('utf-8') if key_bytes else str(uuid.uuid4()) # 키 없으면 새 UUID 생성

            try:
                image = toImage(image_bytes)                                   
            except Exception as e:
                print("Image load failed", e)
            message_count += 1

            image_batch.append(image)
            key_batch.append(image_key)
            if len(image_batch) < BATCH_SIZE: continue


            try:
                # 바이트 데이터를 Pillow Image 객체로 변환
                with torch.no_grad():
                    # YOLO 모델로 예측 수행
                    if model is None:
                        print("Model is not loaded. Skipping inference.")
                        continue
                    # Batch Tensor -> GPU
                    start = time.time()
                    batch_tensor = torch.stack(image_batch).to('cuda')
                    elapsed = time.time() - start
                    # print(f"Transform batch of {len(image_batch)} images in {elapsed:.3f} sec, FPS: {len(image_batch)/elapsed:.2f}")

                    # Inference
                    results = model(batch_tensor)

                    elapsed = time.time() - start
                    image_batch = []  # 배치 처리 후 이미지 리스트 초기화
                    key_batch = []    # 배치 처리 후 키 리스트 초기화
                    logger.info(f"Processed batch of {len(image_batch)} images in {elapsed:.3f} sec, FPS: {len(image_batch)/elapsed:.2f}")
                    end_time = time.time()


            except Exception as e:
                print(f"Error processing image: {e}")
                # 결과 파싱
    except KeyboardInterrupt:
        elapsed_time = end_time - start_time
        tps = message_count / elapsed_time if elapsed_time > 0 else 0
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] TPS: {tps:.2f} messages/sec ({message_count} messages in {elapsed_time:.2f} seconds)")
        logger.info("\nConsumer stopped by user.")
    except KafkaError as e:
        print(f"Kafka error: {e}")
    finally:
        if consumer:
            consumer.close()
            print("Kafka Consumer closed.")

if __name__ == '__main__':
    consume_images_from_kafka()
    

