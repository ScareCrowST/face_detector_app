import os
import sys
from dataclasses import dataclass
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config


def get_resource_path(relative_path: str) -> str:
    """Находит путь к файлу модели при запуске из Python и из PyInstaller .exe"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


@dataclass
class DetectedFace:
    x: int
    y: int
    w: int
    h: int
    score: float


class FaceDetector:
    def __init__(self):
        model_full_path = get_resource_path(config.MODEL_PATH)
        if not os.path.exists(model_full_path):
            raise FileNotFoundError(
                f"Файл модели не найден: {model_full_path}\n"
                f"Положите {config.MODEL_PATH} в папку с программой."
            )

        base_options = python.BaseOptions(model_asset_path=model_full_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE
        )
        self.detector = vision.FaceDetector.create_from_options(options)

    def detect(self, frame) -> list[DetectedFace]:
        # Переводим BGR (OpenCV) в RGB и оборачиваем в формат mp.Image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        detection_result = self.detector.detect(mp_image)

        faces: list[DetectedFace] = []
        if detection_result.detections:
            frame_h, frame_w, _ = frame.shape

            for detection in detection_result.detections:
                bbox = detection.bounding_box

                # Новый API сразу возвращает координаты в пикселях
                x = max(0, int(bbox.origin_x))
                y = max(0, int(bbox.origin_y))
                w = min(int(bbox.width), frame_w - x)
                h = min(int(bbox.height), frame_h - y)

                score = float(detection.categories[0].score) if detection.categories else 0.0
                faces.append(DetectedFace(x=x, y=y, w=w, h=h, score=score))

        return faces

    def close(self):
        self.detector.close()