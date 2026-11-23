from enum import Enum
import cv2
import config
from detector import DetectedFace


class PrivacyMode(Enum):
    OFF = "Без цензуры"
    BLUR = "Размытие (Blur)"
    PIXELATE = "Пикселизация"


class Visualizer:
    @staticmethod
    def _apply_privacy(roi, mode: PrivacyMode, blur_strength: int):
        if mode == PrivacyMode.BLUR:
            # GaussianBlur требует строго нечётное положительное число
            ksize = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
            ksize = max(1, ksize)
            return cv2.GaussianBlur(roi, (ksize, ksize), 0)

        elif mode == PrivacyMode.PIXELATE:
            h, w = roi.shape[:2]
            blocks = config.PIXELATE_BLOCKS
            small_w = max(1, min(w, blocks))
            small_h = max(1, min(h, blocks))
            temp = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

        return roi

    @classmethod
    def draw_faces(
        cls,
        frame,
        faces: list[DetectedFace],
        mode: PrivacyMode = PrivacyMode.OFF,
        blur_strength: int = config.BLUR_STRENGTH,
        show_boxes: bool = True
    ):
        for face in faces:
            if mode != PrivacyMode.OFF and face.w > 0 and face.h > 0:
                roi = frame[face.y : face.y + face.h, face.x : face.x + face.w]
                frame[face.y : face.y + face.h, face.x : face.x + face.w] = cls._apply_privacy(
                    roi, mode, blur_strength
                )

            if show_boxes:
                cv2.rectangle(
                    frame,
                    (face.x, face.y),
                    (face.x + face.w, face.y + face.h),
                    config.BOX_COLOR,
                    config.BOX_THICKNESS
                )

                label = f"{config.LABEL_TEXT} {int(face.score * 100)}%"
                text_y = face.y - 10 if face.y > 25 else face.y + 22

                cv2.putText(
                    frame,
                    label,
                    (face.x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    config.BOX_COLOR,
                    2
                )
        return frame