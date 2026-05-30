import sys
import os
import subprocess
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
from PyQt5.QtCore import Qt, QThreadPool, QRunnable, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTextEdit, QStatusBar, QProgressBar, QMessageBox
import concurrent.futures

class VideoToTextApp(QWidget):
    def __init__(self):
        super().__init__()

        self.video_path = None
        self.audio_path = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Video to Text Converter")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel("Video to Text Converter")
        self.title_label.setFont(QFont("Helvetica Neue", 24, QFont.Bold))
        self.layout.addWidget(self.title_label)

        self.upload_video_button = QPushButton("Upload Video File")
        self.upload_video_button.clicked.connect(self.upload_video)
        self.upload_video_button.setStyleSheet("background-color: #0A8276; color: white; font-size: 16px;")
        self.layout.addWidget(self.upload_video_button)

        self.upload_wav_button = QPushButton("Upload WAV Audio File")
        self.upload_wav_button.clicked.connect(self.upload_wav_audio)
        self.upload_wav_button.setStyleSheet("background-color: #0A8276; color: white; font-size: 16px;")
        self.layout.addWidget(self.upload_wav_button)


        self.status_bar = QStatusBar()
        self.layout.addWidget(self.status_bar)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        self.text_output = QTextEdit()
        self.layout.addWidget(self.text_output)

        
        self.convert_button = QPushButton("Convert Audio to Text")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet("background-color: #0A8276; color: white; font-size: 16px;")
        self.layout.addWidget(self.convert_button)

        self.save_button = QPushButton("Save Text")
        self.save_button.clicked.connect(self.save_text)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("background-color: #0A8276; color: white; font-size: 16px;")
        self.layout.addWidget(self.save_button)

        self.apply_palette()

        self.show()
    

    def apply_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(239, 240, 241))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.AlternateBase, QColor(224, 224, 224))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)

    def upload_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if file_path:
            self.video_path = file_path
            self.upload_video_button.setText(f"Uploaded: {os.path.basename(file_path)}")
            self.convert_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.status_bar.showMessage("Video file uploaded")

    def upload_wav_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select WAV Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.audio_path = file_path
            self.upload_wav_button.setText(f"Uploaded: {os.path.basename(file_path)}")
            self.convert_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.status_bar.showMessage("WAV audio file uploaded")

    def split_audio(self, audio_file, chunk_length_ms=60000):
        audio = AudioSegment.from_wav(audio_file)
        chunks = make_chunks(audio, chunk_length_ms)
        chunk_files = []
        for i, chunk in enumerate(chunks):
            chunk_name = f"chunk{i}.wav"
            chunk.export(chunk_name, format="wav")
            chunk_files.append(chunk_name)
        return chunk_files

    def process_chunk(self, chunk):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(chunk) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            os.remove(chunk)
            return text
        except sr.UnknownValueError:
            return "[Unrecognizable Audio]"
        except sr.RequestError as e:
            return f"[Request Error: {e}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def convert_audio_to_text(self):
        if not self.video_path and not self.audio_path:
            QMessageBox.critical(self, "Error", "No file uploaded!")
            return

        self.status_bar.showMessage("Starting conversion process...")
        full_text = ""

        try:
            if self.video_path:
                self.status_bar.showMessage("Extracting audio from video...")
                audio_file = "temp_audio.wav"
                ffmpeg_command = [
                    'ffmpeg', '-i', self.video_path,
                    '-vn', '-acodec', 'pcm_s16le',
                    '-ar', '16000', '-ac', '1', audio_file, '-y'
                ]
                subprocess.run(ffmpeg_command, check=True)
            else:
                audio_file = self.audio_path

            self.status_bar.showMessage("Splitting audio into chunks...")
            chunk_files = self.split_audio(audio_file)

            self.status_bar.showMessage("Processing audio chunks...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(self.process_chunk, chunk_files))

            full_text = " ".join(results)
            self.update_text_output(full_text)

            if self.video_path:
                os.remove(audio_file)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"ffmpeg error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def update_text_output(self, text):
        QMetaObject.invokeMethod(self.text_output, "setText", Qt.QueuedConnection, Q_ARG(str, text))

    def start_conversion(self):
        self.convert_button.setEnabled(False)
        self.status_bar.showMessage("Converting...")
        self.progress_bar.setRange(0, 0)
        task = ConvertTask(self.convert_audio_to_text, self)
        QThreadPool.globalInstance().start(task)

    def save_text(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Text File", "", "Text Files (*.txt)")
        if file_path and self.text_output.toPlainText().strip():
            with open(file_path, "w") as file:
                file.write(self.text_output.toPlainText().strip())
            self.status_bar.showMessage("Text saved successfully!")
            self.convert_button = QPushButton("Convert Audio to Text")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet("background-color: #0A8276; color: white; font-size: 16px;")
        self.layout.addWidget(self.convert_button)

        self.save_button = QPushButton("Save Text")
        self.save_button.clicked.connect(self.save_text)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("background-color: #0A8276; color: white; font-size: 16px;")
        self.layout.addWidget(self.save_button)

class ConvertTask(QRunnable):
    def __init__(self, func, app):
        super().__init__()
        self.func = func
        self.app = app

    def run(self):
        self.func()
        QMetaObject.invokeMethod(self.app.convert_button, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, True))
        QMetaObject.invokeMethod(self.app.save_button, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, True))
        QMetaObject.invokeMethod(self.app.status_bar, "showMessage", Qt.QueuedConnection, Q_ARG(str, "Conversion complete!"))
        QMetaObject.invokeMethod(self.app.progress_bar, "setRange", Qt.QueuedConnection, Q_ARG(int, 0), Q_ARG(int, 100))
        QMetaObject.invokeMethod(self.app.progress_bar, "setValue", Qt.QueuedConnection, Q_ARG(int, 100))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = VideoToTextApp()
    sys.exit(app.exec_())
