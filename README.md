# Fire and Smoke Detection

## VOLOv8
YOLOv8을 사용해서 실시간(real-time)영상을 통해서 불과 연기를 감지하는 프로젝트.

### 감지 전후 비교

아래 이미지는 시스템이 불과 연기를 감지하기 전과 후의 상태를 명확하게 보여줍니다.

| 감지 전 상태 (Non-detection)                               | 감지 후 상태 (Detection)                               |
| :--------------------------------------------------------- | :------------------------------------------------------- |
| ![감지 전 이미지](images/non-detection.png)               | ![감지 후 이미지](images/detection.png)               |
| 화재나 연기가 감지되지 않은 **정상 상태**의 비디오 프레임입니다. | 화재 및 연기가 성공적으로 감지되어 **바운딩 박스**로 표시된 비디오 프레임입니다. |

오른쪽 이미지에서 볼 수 있듯이, YOLOv8 모델은 불꽃(`fire`)과 연기(`smoke`)를 정확히 구분하여 사각형 형태로 영역을 표시하고, 해당 객체의 클래스 이름과 신뢰도(%)를 함께 보여줍니다.

## 데이터 
[Kaggle-Smoke-Fire-Detection-YOLO](https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo/data)

## 평가
- 아래 차트는 학습, 테스트, 검증 세트에 대한 손실, MAP 점수.
<image src='images/results.png'>

- 혼동 행렬
<image src='images/confusion-matrix.png'>


## 결과
<image src='images/val_batch1_labels.jpg'>

