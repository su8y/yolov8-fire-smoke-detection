import os
import random
import cv2
from fastapi.staticfiles import StaticFiles
import numpy as np
import io
import base64
import logging
from pathlib import Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
import uvicorn
from fastapi import FastAPI, File, Request, UploadFile, HTTPException
from PIL import Image
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fire and Smoke Detection API",
    description="YOLOv8을 사용하여 이미지에서 불과 연기를 감지하는 API",
    version="1.0.0",
)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=f"{BASE_DIR}/static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR) +"/templates")

try:
    model = YOLO(f"{BASE_DIR}/best-fire-smoke-yolo8s.pt")
    logger.info("YOLO 모델이 성공적으로 로드되었습니다.")
except Exception as e:
    logger.error(f"YOLO 모델 로드 실패: {str(e)}")
    model = None

@app.get("/",response_class=HTMLResponse, summary="Response Index Page")
async def read_root(request: Request):
    data = {
        "request": request,
        "title" : "FastAPI AI 모델 분류 예제",
    }
    return templates.TemplateResponse("index.html", data)

@app.get("/monitor",response_class=HTMLResponse, summary="Response Index Page")
async def read_monitor(request: Request):
    data = {
        "request": request,
        "title" : "FastAPI AI 모델 모니터링 POC",
    }
    return templates.TemplateResponse("monitor.html", data)

@app.post("/detection",summary="YOLOv8 AI Fire Detection")
async def detectionYOLOv8(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="YOLO 모델을 로드할 수 없습니다.")
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    file_extension = '.' + file.filename.split('.')[-1].lower() # type: ignore
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}"
        )
    
    try:
        # 업로드된 파일을 읽기
        contents = await file.read()
        
        # PIL Image로 변환
        image = Image.open(io.BytesIO(contents))
        image.save("requestimage.jpeg")
        
        # RGB로 변환 (YOLO 모델은 RGB 형식을 기대)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # numpy 배열로 변환
        image_array = np.array(image)
        print(f"이미지 배열 shape: {image_array.shape}") # (높이, 너비, 채널)
        print(f"이미지 배열 dtype: {image_array.dtype}") # uint8 이어야 함
        
        # YOLO 모델로 예측 수행
        results = model(image)
        
       

        # 결과 파싱
        detections = []
        fire_detected = False
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i, box in enumerate(boxes):
                    # 바운딩 박스 좌표 (x1, y1, x2, y2)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # 신뢰도 점수
                    confidence = float(box.conf[0])
                    
                    # 클래스 ID 및 이름
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    
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
        
        # 결과 이미지 생성 (바운딩 박스 그리기)
        result_image = image_array.copy()
        
        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
            
            # 바운딩 박스 색상 설정 (fire: 빨간색, nofire: 초록색)
            color = (255, 0, 0) if detection["class_name"] == "fire" else (0, 255, 0)
            
            # 바운딩 박스 그리기
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # 레이블 텍스트 추가
            label = f"{detection['class_name']}: {detection['confidence']:.2f}"
            cv2.putText(result_image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        cv2.imwrite("test.jpeg", result_image)
        # 결과 이미지를 base64로 인코딩
        result_pil = Image.fromarray(result_image)
        buffer = io.BytesIO()
        result_pil.save(buffer, format='JPEG')
        result_image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # 응답 데이터 구성
        response_data = {
            "status": "success",
            "fire_detected": fire_detected,
            "detection_count": len(detections),
            "detections": detections,
            "image_info": {
                "filename": file.filename,
                "size": file.size,
                "dimensions": {
                    "width": image.width,
                    "height": image.height
                }
            },
            "result_image": f"data:image/jpeg;base64,{result_image_base64}"
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"화재 감지 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류가 발생했습니다: {str(e)}")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)