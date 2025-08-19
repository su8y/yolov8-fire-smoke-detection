# Fire and Smoke Detection
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Spring](https://img.shields.io/badge/Spring-6DB33F?style=flat-square&logo=spring&logoColor=white)
![Java](https://img.shields.io/badge/Java-007396?style=flat-square&logo=java&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white)

RTMP / RTSP 기반 실시간 스트리밍 영상을 YOLOv8 기반 CNN 모델로 분석하여 불(fire)과 연기(smoke) 를 탐지하는 실시간 모니터링 프로젝트입니다.

### OverView

아래 이미지는 시스템이 불과 연기를 감지하기 전과 후의 상태를 명확하게 보여줍니다.

| 감지 전 상태 (Non-detection)                               | 감지 후 상태 (Detection)                               |
| :--------------------------------------------------------- | :------------------------------------------------------- |
| ![감지 전 이미지](images/non-detection.png)               | ![감지 후 이미지](images/detection.png)               |
| 화재나 연기가 감지되지 않은 **정상 상태**의 비디오 프레임입니다. | 화재 및 연기가 성공적으로 감지되어 **바운딩 박스**로 표시된 비디오 프레임입니다. |

오른쪽 이미지에서 볼 수 있듯이, YOLOv8 모델은 불꽃(`fire`)과 연기(`smoke`)를 정확히 구분하여 사각형 형태로 영역을 표시하고, 해당 객체의 클래스 이름과 신뢰도(%)를 함께 보여줍니다.

## 학습 데이터셋
본 프로젝트는 Kaggle에서 제공하는 다음 화재/연기 데이터셋을 사용해 학습했습니다.
[Kaggle-Smoke-Fire-Detection-YOLO](https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo/data)

## 평가 & 결과
아래 차트는 Loss, mAP 등의 학습 지표를 시각적으로 표현한 그래프입니다.
<image src='images/results.png'>

아래는 검증 데이터에 대한 YOLOv8의 탐지 성능을 시각화한 결과입니다.
<image src='images/confusion-matrix.png'>

아래는 검증 데이터에 대한 YOLOv8의 탐지 성능을 시각화한 결과입니다.
<image src='images/val_batch1_labels.jpg'>

## 웹 서버 별 성능
| 서버 구성 | TPS(sec) | response(avg, ms) |
| :---------| -----------:| -----------:|
| 단일 FastAPI | 38.3 |  4618 |


### 테스트 환경
Graphics: NVIDIA RTX A6000
Jmeter 
- **Thread Group**: Thread=200, Ramp up period=10, Duration=60, 
- **Image**: size=(800x544), ext=jpg

### 단일 FastAPI + restApi
TPS: 38.3 messages/sec 
> 서버 처리 병목이 추론 자체보다 이미지 디코딩·전송 지연·단일 인스턴스 구조에 집중됨을 확인했습니다.


### 전처리 서버 + 추론 서버 + kafka  (추론 서버만 계산, 전처리 서버 tps 600이상)
TPS: 45.65 messages/sec (913 messages in 20 seconds)
GPU 사용량이 낮음(5~20)
> 멀티 프로세스 구조로 인해 CPU 오버헤드는 줄었으나, GPU 활용률이 낮아 추론 서버 단일 처리 효율에 한계가 있었습니다.

### 전처리 서버 + 추론 서버 + kafka + BATCH_SIZE=max(8,16,32) = 32 (추론 서버만 계산, 전처리 서버 tps 600이상)
TPS: 60.4 messages/sec (1208 messages in 20 seconds)
GPU 사용량이 꽤 높음(20 ~ 50) 최대 60% 까지 튐.
> GPU에 Batch 처리로 연산 효율을 극대화하면서 단일 스레드 대비 ≈ 1.6배 향상된 TPS를 확인했습니다.
