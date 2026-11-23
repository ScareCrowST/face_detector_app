import time
from tkinter import messagebox
import cv2
from PIL import Image
import customtkinter as ctk

import config
from camera import Camera
from detector import FaceDetector
from visualizer import Visualizer, PrivacyMode

# Настройка тёмной темы и синего акцента
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FaceDetectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Face Detector Studio")
        self.geometry("1120x680")
        self.minsize(900, 560)

        # Инициализация модулей компьютерного зрения
        try:
            self.camera = Camera(config.CAMERA_INDEX)
            self.detector = FaceDetector()
        except Exception as e:
            messagebox.showerror("Ошибка инициализации", str(e))
            self.destroy()
            return

        self.visualizer = Visualizer()

        # Переменные состояния
        self.prev_time = time.perf_counter()
        self.fps = 0.0
        self.is_running = True

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Запуск цикла обновления видео
        self.update_frame()

    def _build_ui(self):
        # Сетка окна: колонка 0 — видео (растягивается), колонка 1 — панель управления
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # --- Левая область: видеопоток ---
        self.video_frame = ctk.CTkFrame(self, corner_radius=12)
        self.video_frame.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")

        self.video_label = ctk.CTkLabel(self.video_frame, text="Запуск камеры...")
        self.video_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Правая область: панель управления ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=12)
        self.sidebar.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Заголовок
        ctk.CTkLabel(
            self.sidebar,
            text="Панель управления",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 15), padx=20)

        # Блок статистики
        stats_box = ctk.CTkFrame(self.sidebar, corner_radius=8)
        stats_box.pack(fill="x", padx=16, pady=(0, 20))

        self.fps_label = ctk.CTkLabel(
            stats_box, text="FPS: 0", font=ctk.CTkFont(size=15, weight="bold")
        )
        self.fps_label.pack(anchor="w", padx=14, pady=(10, 2))

        self.faces_label = ctk.CTkLabel(
            stats_box, text="Найдено лиц: 0", font=ctk.CTkFont(size=15)
        )
        self.faces_label.pack(anchor="w", padx=14, pady=(2, 10))

        # Выбор режима приватности (радиокнопки)
        ctk.CTkLabel(
            self.sidebar,
            text="Режим маскировки:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(5, 8))

        self.mode_var = ctk.StringVar(value=PrivacyMode.OFF.name)
        for mode in PrivacyMode:
            rb = ctk.CTkRadioButton(
                self.sidebar,
                text=mode.value,
                variable=self.mode_var,
                value=mode.name,
                command=self._on_mode_change
            )
            rb.pack(anchor="w", padx=24, pady=6)

        # Ползунок силы блюра
        self.blur_title = ctk.CTkLabel(
            self.sidebar,
            text=f"Сила размытия: {config.BLUR_STRENGTH}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.blur_title.pack(anchor="w", padx=20, pady=(22, 6))

        self.blur_slider = ctk.CTkSlider(
            self.sidebar,
            from_=15,
            to=151,
            number_of_steps=68,
            command=self._on_slider_change
        )
        self.blur_slider.set(config.BLUR_STRENGTH)
        self.blur_slider.pack(fill="x", padx=20, pady=(0, 15))
        self.blur_slider.configure(state="disabled")  # Активен только в режиме BLUR

        # Переключатель отображения зелёной рамки
        self.show_box_var = ctk.BooleanVar(value=True)
        self.box_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Показывать рамку",
            variable=self.show_box_var
        )
        self.box_switch.pack(anchor="w", padx=20, pady=15)

        # Кнопка выхода внизу панели
        self.quit_btn = ctk.CTkButton(
            self.sidebar,
            text="Выход",
            fg_color="#c0392b",
            hover_color="#962d22",
            command=self.on_closing
        )
        self.quit_btn.pack(side="bottom", fill="x", padx=20, pady=20)

    def _on_mode_change(self):
        # Включаем ползунок только когда выбран режим размытия
        if self.mode_var.get() == PrivacyMode.BLUR.name:
            self.blur_slider.configure(state="normal")
        else:
            self.blur_slider.configure(state="disabled")

    def _on_slider_change(self, value):
        val = int(value)
        if val % 2 == 0:
            val += 1
        self.blur_title.configure(text=f"Сила размытия: {val}")

    def update_frame(self):
        if not self.is_running:
            return

        frame = self.camera.get_frame()
        if frame is not None:
            faces = self.detector.detect(frame)

            # Расчёт сглаженного FPS
            curr_time = time.perf_counter()
            delta_time = curr_time - self.prev_time
            self.prev_time = curr_time
            if delta_time > 0:
                current_fps = 1.0 / delta_time
                self.fps = (self.fps * 0.9) + (current_fps * 0.1) if self.fps > 0 else current_fps

            active_mode = PrivacyMode[self.mode_var.get()]
            blur_val = int(self.blur_slider.get())

            # Отрисовка рамок и эффектов
            processed = self.visualizer.draw_faces(
                frame,
                faces,
                mode=active_mode,
                blur_strength=blur_val,
                show_boxes=self.show_box_var.get()
            )

            # Конвертация BGR (OpenCV) -> RGB (PIL) -> CTkImage
            rgb_image = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)

            # Подгоняем размер картинки под текущий размер контейнера с сохранением пропорций
            container_w = max(320, self.video_frame.winfo_width() - 20)
            container_h = max(240, self.video_frame.winfo_height() - 20)
            img_h, img_w = rgb_image.shape[:2]
            scale = min(container_w / img_w, container_h / img_h)
            new_size = (int(img_w * scale), int(img_h * scale))

            ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=new_size)
            self.video_label.configure(image=ctk_img, text="")
            self.video_label.image = ctk_img  # Сохраняем ссылку, чтобы сборщик мусора не удалил кадр

            # Обновление цифр в панели
            self.fps_label.configure(text=f"FPS: {int(self.fps)}")
            self.faces_label.configure(text=f"Найдено лиц: {len(faces)}")

        # Планируем следующий кадр через 10 мс
        self.after(10, self.update_frame)

    def on_closing(self):
        self.is_running = False
        self.detector.close()
        self.camera.release()
        self.destroy()


if __name__ == "__main__":
    app = FaceDetectorApp()
    app.mainloop()