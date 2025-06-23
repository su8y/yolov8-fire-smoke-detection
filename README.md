# Fire and Smoke Detection

## VOLOv8
YOLOv8을 사용해서 실시간(real-time)영상을 통해서 불과 연기를 감지하는 프로젝트.

사전 학습된 YOLOv8을 사용하여 video frame을 통해서 불과 연기를 학습시킨다. 

<video width='640' height='360' controls>
    <source src="images/wildfire.mp4" type="video/mp4">
</video>
<video width='640' height='360' controls>
    <source src="images/wildfire_after.mp4" type="video/mp4">
</video>


## 데이터 
[Kaggle-Smoke-Fire-Detection-YOLO](https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo/data)

## 평가
- 아래 차트는 학습, 테스트, 검증 세트에 대한 손실, MAP 점수.
<image src='images/results.png'>

- 혼동 행렬
<image src='images/confusion-matrix.png'>


## 결과
<image src='images/val_batch1_labels.jpg'>

