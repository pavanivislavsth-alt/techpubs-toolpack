import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QLabel, QScrollArea,
    QToolButton, QSizePolicy, QTextEdit, QSplitter, QFrame, QVBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QTextCursor
from PyQt5.QtCore import Qt, QRect, QSize
import fitz
from difflib import SequenceMatcher


class PDFComparisonTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf1_path = None
        self.pdf2_path = None
        self.differences = []
        self.current_diff_index = 0
        self.summary_visible = False  
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF Comparison Tool')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create file selection area
        file_layout = QHBoxLayout()

        # PDF 1 selection
        pdf1_layout = QVBoxLayout()
        self.pdf1_label = QLabel('First PDF: Not selected')
        self.pdf1_button = QPushButton('Select First PDF')
        self.pdf1_button.clicked.connect(lambda: self.select_pdf(1))
        self.pdf1_button.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #08695F;
            }
            QPushButton:pressed {
                background-color: #065C53;
            }
        """)
        pdf1_layout.addWidget(self.pdf1_label)
        pdf1_layout.addWidget(self.pdf1_button)

        # PDF 2 selection
        pdf2_layout = QVBoxLayout()
        self.pdf2_label = QLabel('Second PDF: Not selected')
        self.pdf2_button = QPushButton('Select Second PDF')
        self.pdf2_button.clicked.connect(lambda: self.select_pdf(2))
        self.pdf2_button.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #08695F;
            }
            QPushButton:pressed {
                background-color: #065C53;
            }
        """)
        pdf2_layout.addWidget(self.pdf2_label)
        pdf2_layout.addWidget(self.pdf2_button)

        file_layout.addLayout(pdf1_layout)
        file_layout.addLayout(pdf2_layout)

        # Compare button
        self.compare_button = QPushButton('Compare PDFs')
        self.compare_button.clicked.connect(self.compare_pdfs)
        self.compare_button.setEnabled(False)
        self.compare_button.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #08695F;
            }
            QPushButton:pressed {
                background-color: #065C53;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        # Status label
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)

        # Difference count button
        self.diff_count_button = QToolButton()
        self.diff_count_button.setText('Differences: 0')
        self.diff_count_button.setEnabled(False)
        self.diff_count_button.clicked.connect(self.toggle_summary)
        self.diff_count_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.diff_count_button.setFont(QFont('Arial', 10, QFont.Bold))
        self.diff_count_button.setStyleSheet("""
            QToolButton {
                background-color: #0A8276;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #08695F;
            }
            QToolButton:pressed {
                background-color: #065C53;
            }
            QToolButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        # Scroll areas for PDF views
        self.scroll_area1 = QScrollArea()
        self.scroll_area2 = QScrollArea()
        self.scroll_area1.setWidgetResizable(True)
        self.scroll_area2.setWidgetResizable(True)

        self.pdf1_container = QWidget()
        self.pdf1_layout = QVBoxLayout(self.pdf1_container)
        self.scroll_area1.setWidget(self.pdf1_container)

        self.pdf2_container = QWidget()
        self.pdf2_layout = QVBoxLayout(self.pdf2_container)
        self.scroll_area2.setWidget(self.pdf2_container)

        # Summary of differences
        self.summary_frame = QFrame()
        self.summary_frame.setFrameShape(QFrame.StyledPanel)
        self.summary_frame.setVisible(False)  # Initially hidden
        summary_layout = QVBoxLayout(self.summary_frame)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont('Arial', 10))
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
        """)
        summary_layout.addWidget(self.summary_text)

        # Splitter for PDF views and summary
        splitter = QSplitter(Qt.Vertical)
        pdf_view_widget = QWidget()
        pdf_view_layout = QHBoxLayout(pdf_view_widget)
        pdf_view_layout.addWidget(self.scroll_area1)
        pdf_view_layout.addWidget(self.scroll_area2)
        splitter.addWidget(pdf_view_widget)
        splitter.addWidget(self.summary_frame)
        splitter.setSizes([600, 200])

        # Add all widgets to main layout
        layout.addLayout(file_layout)
        layout.addWidget(self.compare_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.diff_count_button)
        layout.addWidget(splitter)

    def select_pdf(self, pdf_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f'Select PDF {pdf_num}', '', 'PDF files (*.pdf)')
        if file_path:
            if pdf_num == 1:
                self.pdf1_path = file_path
                self.pdf1_label.setText(f'First PDF: {file_path}')
            else:
                self.pdf2_path = file_path
                self.pdf2_label.setText(f'Second PDF: {file_path}')

        self.compare_button.setEnabled(bool(self.pdf1_path and self.pdf2_path))

    def extract_text_with_positions(self, pdf_path):
        doc = fitz.open(pdf_path)
        text_with_positions = []
        for page_num, page in enumerate(doc, start=1):
            words = page.get_text("words")
            for word in words:
                if len(word) == 8:
                    x0, y0, x1, y1, text, block_no, line_no, word_no = word
                else:
                    continue

                if text.strip():
                    text_with_positions.append((text.strip(), (x0, y0, x1, y1), page_num))
        doc.close()
        return text_with_positions

    def render_page_to_pixmap(self, pdf_path, page_num):
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        return pixmap

    def draw_differences(self, pixmap, differences, page_num):
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 0, 128))  
        for text, (x0, y0, x1, y1), diff_page_num in differences:
            if diff_page_num == page_num + 1: 
                rect = QRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0))
                painter.fillRect(rect, QColor(255, 255, 0, 128))  
        painter.end()

    def compare_pdfs(self):
        try:
            self.status_label.setText('Comparing PDFs...')
            QApplication.processEvents()  

            text1_with_positions = self.extract_text_with_positions(self.pdf1_path)
            text2_with_positions = self.extract_text_with_positions(self.pdf2_path)

            self.differences = self.get_text_differences(text1_with_positions, text2_with_positions)

            self.diff_count_button.setText(f'Differences: {len(self.differences)}')
            self.diff_count_button.setEnabled(len(self.differences) > 0)
            self.current_diff_index = 0

            self.render_pages_with_differences(text1_with_positions, text2_with_positions, self.differences)
            self.update_differences_summary()

            self.status_label.setText('Comparison complete!')

        except Exception as e:
            self.status_label.setText(f'Error: {str(e)}')

    def get_text_differences(self, text1_with_positions, text2_with_positions):
        text1 = [text for text, _, _ in text1_with_positions]
        text2 = [text for text, _, _ in text2_with_positions]

        matcher = SequenceMatcher(None, text1, text2)
        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ['replace', 'delete', 'insert']:
                for i in range(i1, i2):
                    differences.append((text1[i], text1_with_positions[i][1], text1_with_positions[i][2]))
                for j in range(j1, j2):
                    differences.append((text2[j], text2_with_positions[j][1], text2_with_positions[j][2]))
        return differences

    def render_pages_with_differences(self, text1_with_positions, text2_with_positions, differences):
        for i in reversed(range(self.pdf1_layout.count())):
            self.pdf1_layout.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.pdf2_layout.count())):
            self.pdf2_layout.itemAt(i).widget().setParent(None)
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)

        for page_num in range(max(len(doc1), len(doc2))):
            if page_num < len(doc1):
                pixmap1 = self.render_page_to_pixmap(self.pdf1_path, page_num)
                self.draw_differences(pixmap1, differences, page_num)
                label1 = QLabel()
                label1.setPixmap(pixmap1)
                self.pdf1_layout.addWidget(label1)

            if page_num < len(doc2):
                pixmap2 = self.render_page_to_pixmap(self.pdf2_path, page_num)
                self.draw_differences(pixmap2, differences, page_num)
                label2 = QLabel()
                label2.setPixmap(pixmap2)
                self.pdf2_layout.addWidget(label2)

    def update_differences_summary(self):
        self.summary_text.clear()
        for i, (text, (x0, y0, x1, y1), page_num) in enumerate(self.differences):
            self.summary_text.append(f"Difference {i + 1}: Page {page_num}, Text: '{text}'")
        self.summary_text.moveCursor(QTextCursor.Start)

    def toggle_summary(self):
        self.summary_visible = not self.summary_visible
        self.summary_frame.setVisible(self.summary_visible)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFComparisonTool()
    ex.show()
    sys.exit(app.exec_())