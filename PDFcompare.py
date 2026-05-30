import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                            QHBoxLayout, QWidget, QFileDialog, QLabel, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QRect
import fitz  # PyMuPDF
from difflib import SequenceMatcher

class PDFComparisonTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf1_path = None
        self.pdf2_path = None
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
        pdf1_layout.addWidget(self.pdf1_label)
        pdf1_layout.addWidget(self.pdf1_button)
        
        # PDF 2 selection
        pdf2_layout = QVBoxLayout()
        self.pdf2_label = QLabel('Second PDF: Not selected')
        self.pdf2_button = QPushButton('Select Second PDF')
        self.pdf2_button.clicked.connect(lambda: self.select_pdf(2))
        pdf2_layout.addWidget(self.pdf2_label)
        pdf2_layout.addWidget(self.pdf2_button)
        
        file_layout.addLayout(pdf1_layout)
        file_layout.addLayout(pdf2_layout)
        
        # Compare button
        self.compare_button = QPushButton('Compare PDFs')
        self.compare_button.clicked.connect(self.compare_pdfs)
        self.compare_button.setEnabled(False)
        
        # Status label
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Scroll areas for PDF views
        self.scroll_area1 = QScrollArea()
        self.scroll_area2 = QScrollArea()
        self.label1 = QLabel()
        self.label2 = QLabel()
        self.scroll_area1.setWidget(self.label1)
        self.scroll_area2.setWidget(self.label2)
        
        # Layout for scroll areas
        pdf_view_layout = QHBoxLayout()
        pdf_view_layout.addWidget(self.scroll_area1)
        pdf_view_layout.addWidget(self.scroll_area2)
        
        # Add all widgets to main layout
        layout.addLayout(file_layout)
        layout.addWidget(self.compare_button)
        layout.addWidget(self.status_label)
        layout.addLayout(pdf_view_layout)

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

    def compare_pdfs(self):
        try:
            self.status_label.setText('Comparing PDFs...')
            
            # Extract text with positions from both PDFs
            text1_with_positions = self.extract_text_with_positions(self.pdf1_path)
            text2_with_positions = self.extract_text_with_positions(self.pdf2_path)
            
            # Get differences
            differences = self.get_text_differences(text1_with_positions, text2_with_positions)
            
            # Render pages with differences highlighted
            self.render_pages_with_differences(text1_with_positions, text2_with_positions, differences)
            
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
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)
        
        highlighted_pixmaps1 = []
        highlighted_pixmaps2 = []
        
        for page_num in range(max(len(doc1), len(doc2))):
            pixmap1 = self.render_page_to_pixmap(self.pdf1_path, page_num) if page_num < len(doc1) else None
            pixmap2 = self.render_page_to_pixmap(self.pdf2_path, page_num) if page_num < len(doc2) else None
            
            painter1 = QPainter(pixmap1) if pixmap1 else None
            painter2 = QPainter(pixmap2) if pixmap2 else None
            
            for text, (x0, y0, x1, y1), page in differences:
                if page == page_num + 1:
                    if painter1:
                        painter1.setPen(QColor(255, 0, 0))
                        painter1.drawRect(QRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0)))
                    if painter2:
                        painter2.setPen(QColor(255, 0, 0))
                        painter2.drawRect(QRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0)))
            
            if painter1:
                painter1.end()
                highlighted_pixmaps1.append(pixmap1)
            if painter2:
                painter2.end()
                highlighted_pixmaps2.append(pixmap2)
        
        self.display_pixmaps(highlighted_pixmaps1, self.label1)
        self.display_pixmaps(highlighted_pixmaps2, self.label2)

    def display_pixmaps(self, pixmaps, label):
        combined_height = sum(pixmap.height() for pixmap in pixmaps)
        max_width = max(pixmap.width() for pixmap in pixmaps)

        combined_image = QImage(max_width, combined_height, QImage.Format_RGB888)
        combined_image.fill(Qt.white)

        painter = QPainter(combined_image)

        y_offset = 0
        for pixmap in pixmaps:
            painter.drawPixmap(0, y_offset, pixmap)
            y_offset += pixmap.height()

        painter.end()

        label.setPixmap(QPixmap.fromImage(combined_image))
        label.adjustSize()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFComparisonTool()
    ex.show()
    sys.exit(app.exec_())
