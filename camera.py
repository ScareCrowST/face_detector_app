import cv2


class Camera:
    def __init__(self, source: int = 0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть камеру с индексом {source}")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        # Зеркально отражаем кадр по горизонтали для естественного восприятия
        return cv2.flip(frame, 1)

    def release(self):
        if self.cap.isOpened():
            self.cap.release()