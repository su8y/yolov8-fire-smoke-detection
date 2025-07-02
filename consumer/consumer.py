import base64
from datetime import datetime
import os
from tabnanny import verbose
import time
from confluent_kafka import Consumer, KafkaException
from PIL import Image
import io
import uuid

import cv2
import numpy as np
import torch
import torchvision
from ultralytics import YOLO # 이미지 파일명으로 사용할 고유 ID 생성

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
    model = YOLO(weight)
    model.to('cuda')  # GPU 사용을 위해 모델을 CUDA로 이동
    model.eval()
    print("YOLO 모델이 성공적으로 로드되었습니다.")
    print("클래스 이름:", model.names)
    classnames = model.names
except Exception as e:
    print(f"YOLO 모델 로드 실패: {str(e)}")
    model = None

def toImage(image_bytes):
    """
    PIL Image 객체를 NumPy 배열로 변환합니다.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != 'RGB': image = image.convert('RGB')

    return image


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
        while True:
            # 메시지 폴링 (timeout 설정으로 일정 시간 대기)
            msg = consumer.poll(timeout=1.0) # 1초 대기

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException.PARTITION_EOF:
                    # 토픽의 끝에 도달 (더 이상 새 메시지가 없을 때)
                    print(f"%% Reached end of partition {msg.partition()} in topic {msg.topic()} %%")
                elif msg.error():
                    print(f"Consumer error: {msg.error()}")
                continue

            # 메시지 처리
            key_bytes = msg.key()
            image_bytes = msg.value()

            message_count += 1
            # 키(key)는 바이트이므로 디코딩 (Producer에서 String으로 보냈다면)
            # Producer가 UUID.randomUUID().toString()으로 보냈으므로 UTF-8 디코딩
            image_key = key_bytes.decode('utf-8') if key_bytes else str(uuid.uuid4()) # 키 없으면 새 UUID 생성

            print(f"Received message from topic '{msg.topic()}', partition {msg.partition()}, offset {msg.offset()}")
            print(f"  Key: {image_key}, Image Bytes Size: {len(image_bytes)} bytes")

            try:
                # 바이트 데이터를 Pillow Image 객체로 변환
                # JPEG 형식을 가정합니다. 만약 PNG 등 다른 형식이라면, Pillow가 알아서 감지합니다.
                with torch.no_grad():
                    # YOLO 모델로 예측 수행
                    if model is None:
                        print("Model is not loaded. Skipping inference.")
                        continue
                    image = toImage(image_bytes)                                    
                    inference_results = model(image)
                    [isFire, detections] = parse_results(inference_results)
                    print(f"Fire detected: {isFire}, Detections: {len(detections)}")

            except Exception as e:
                print(f"Error processing image: {e}")
                # 결과 파싱
    except KeyboardInterrupt:
        elapsed_time = time.time() - start_time
        tps = message_count / elapsed_time if elapsed_time > 0 else 0
        print(f"[{datetime.now().strftime('%H:%M:%S')}] TPS: {tps:.2f} messages/sec ({message_count} messages in {elapsed_time:.2f} seconds)")
        print("\nConsumer stopped by user.")
    except KafkaException as e:
        print(f"Kafka error: {e}")
    finally:
        if consumer:
            consumer.close()
            print("Kafka Consumer closed.")

if __name__ == '__main__':
    consume_images_from_kafka()