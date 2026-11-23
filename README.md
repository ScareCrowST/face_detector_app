# Face Detector Studio

Desktop face detection application built with Python, **OpenCV**, **MediaPipe (BlazeFace)**.

## Prerequisites

Python 3.9 – 3.12

A working webcam

# Installation & Running from Source
## 1. Clone the repository:

```bash
git clone [https://github.com/ScareCrowST/face_detector_app.git](https://github.com/ScareCrowST/face_detector_app.git)
cd face_detector_app
```

## 2. Create and activate a virtual environment:

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 4. Run the application:
```bash
python main.py
```

# Building a Standalone Executable (.exe)
```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "FaceDetector" --collect-all mediapipe --collect-all customtkinter --add-data "blaze_face_short_range.tflite;." main.py
```

## License

[MIT License](https://choosealicense.com/licenses/mit/)
