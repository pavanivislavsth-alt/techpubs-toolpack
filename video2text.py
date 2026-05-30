import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr


class AudioToTextThread(QThread):
    """Thread for processing audio chunks and converting to text."""
    update_signal = pyqtSignal(str)  # Signal to update the text output

    def __init__(self, audio_file, chunk_length_ms=10000):
        super().__init__()
        self.audio_file = audio_file
        self.chunk_length_ms = chunk_length_ms

    def run(self):
        """Process audio chunks and emit text updates."""
        try:
            chunk_files = self.split_audio(self.audio_file)
            recognizer = sr.Recognizer()
            full_text = ""
            for chunk in chunk_files:
                with sr.AudioFile(chunk) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    full_text += text + " "
                    self.update_signal.emit(full_text)  # Emit updated text
                os.remove(chunk)
        except sr.UnknownValueError:
            self.update_signal.emit("Error: Google Speech Recognition could not understand the audio.")
        except sr.RequestError as e:
            self.update_signal.emit(f"Error: Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            self.update_signal.emit(f"Error: {str(e)}")

    def split_audio(self, audio_file):
        """Split audio file into smaller chunks."""
        audio = AudioSegment.from_wav(audio_file)
        chunks = make_chunks(audio, self.chunk_length_ms)
        chunk_files = []
        for i, chunk in enumerate(chunks):
            chunk_name = f"chunk{i}.wav"
            chunk.export(chunk_name, format="wav")
            chunk_files.append(chunk_name)
        return chunk_files


class VideoToTextApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to Text Converter")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Video to Text Converter")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Upload Video Button
        self.upload_video_button = QPushButton("Upload Video File")
        self.upload_video_button.setFont(QFont("Arial", 14))
        self.upload_video_button.setStyleSheet(self.get_button_style())
        self.upload_video_button.clicked.connect(self.upload_video)
        main_layout.addWidget(self.upload_video_button)

        # Upload WAV Button
        self.upload_wav_button = QPushButton("Upload WAV Audio File")
        self.upload_wav_button.setFont(QFont("Arial", 14))
        self.upload_wav_button.setStyleSheet(self.get_button_style())
        self.upload_wav_button.clicked.connect(self.upload_wav_audio)
        main_layout.addWidget(self.upload_wav_button)

        # Text area to display generated text
        self.text_output = QTextEdit()
        self.text_output.setFont(QFont("Arial", 12))
        self.text_output.setReadOnly(True)
        self.text_output.setPlaceholderText("Generated text will appear here...")
        main_layout.addWidget(self.text_output)

        # Convert Button
        self.convert_button = QPushButton("Convert Audio to Text")
        self.convert_button.setFont(QFont("Arial", 14))
        self.convert_button.setStyleSheet(self.get_button_style())
        self.convert_button.clicked.connect(self.convert_audio_to_text)
        self.convert_button.setEnabled(False)
        main_layout.addWidget(self.convert_button)

        self.setLayout(main_layout)

    def get_button_style(self):
        """Returns a stylesheet for buttons."""
        return """
            QPushButton {
                background-color: #0A8276;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #08695F;
            }
            QPushButton:pressed {
                background-color: #065C53;
            }
        """

    def upload_video(self):
        """Open file dialog to select a video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.video_path = file_path
            self.upload_video_button.setText(f"Uploaded: {os.path.basename(file_path)}")
            self.convert_button.setEnabled(True)
            if hasattr(self, 'audio_path'):
                del self.audio_path

    def upload_wav_audio(self):
        """Open file dialog to select a WAV audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select WAV Audio File", "", "Audio Files (*.wav)"
        )
        if file_path:
            self.audio_path = file_path
            self.upload_wav_button.setText(f"Uploaded: {os.path.basename(file_path)}")
            self.convert_button.setEnabled(True)
            if hasattr(self, 'video_path'):
                del self.video_path

    def convert_audio_to_text(self):
        """Start the audio-to-text conversion process."""
        if not hasattr(self, 'video_path') and not hasattr(self, 'audio_path'):
            QMessageBox.warning(self, "Error", "No file uploaded!")
            return

        try:
            # Extract audio from video if necessary
            if hasattr(self, 'video_path'):
                audio_file = "temp_audio.wav"
                ffmpeg_command = f'ffmpeg -i "{self.video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_file}" -y'
                os.system(ffmpeg_command)
            else:
                audio_file = self.audio_path

            # Start the thread for audio-to-text conversion
            self.thread = AudioToTextThread(audio_file)
            self.thread.update_signal.connect(self.update_text_output)
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def update_text_output(self, text):
        """Update the text output area with new text."""
        self.text_output.setPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 12))
    window = VideoToTextApp()
    window.show()
    sys.exit(app.exec_())