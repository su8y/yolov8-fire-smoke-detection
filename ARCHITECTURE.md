## Project Architecture

이 프로젝트는 두 가지 주요 워크플로우를 가집니다.

1.  **이벤트 기반 추론 파이프라인**: 이미지 처리를 위해 Kafka를 중심으로 한 비동기 파이프라인입니다.
2.  **독립형 REST API 서버**: 실시간 데모 및 간단한 테스트를 위한 단일 FastAPI 서버입니다.


## Module Dsecription
-   **`preprocessor` (Java/Spring)**: 클라이언트로부터 이미지를 받아 크기 조정, 압축 등 전처리를 수행한 후 Kafka 토픽으로 메시지를 전송합니다.
-   **`broker` (Kafka)**: `preprocessor`와 `consumer` 사이의 이미지 데이터를 안정적으로 중개하는 메시지 큐입니다.
-   **`consumer` (Python)**: Kafka 토픽에서 이미지 메시지를 실시간으로 구독(consume)하고, YOLOv8 모델을 사용해 화재/연기 탐지 추론을 수행합니다.
-   **`app` (Python/FastAPI)**: Kafka와 연동되지 않는 독립적인 API 서버입니다. 이미지 업로드, 추론, 결과 반환까지 모든 과정을 동기적으로 처리하며, 간단한 테스트 및 데모에 사용됩니다.