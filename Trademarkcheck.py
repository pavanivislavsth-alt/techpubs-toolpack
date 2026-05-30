import sys
import re
import os
from PyPDF2 import PdfReader
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton, QVBoxLayout, 
    QHBoxLayout, QWidget, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt

class PDFSearcherApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("PDF Searcher")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()

        self.file_label = QLabel("Select PDF file:")
        layout.addWidget(self.file_label, 0, 0)

        self.file_button = QPushButton("Browse")
        self.file_button.setFixedSize(100, 40)  # Set the fixed size for the Browse button
        self.file_button.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #087563;
            }
            QPushButton:pressed {
                background-color: #06584C;
            }
        """)
        self.file_button.clicked.connect(self.select_and_search_pdf)
        layout.addWidget(self.file_button, 0, 1)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("font-family: Arial; font-size: 10pt;")
        layout.addWidget(self.result_text, 1, 0, 1, 2)

        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("background-color: gray; padding: 5px;")
        layout.addWidget(self.status_bar, 2, 0, 1, 2)

        central_widget.setLayout(layout)

    def select_and_search_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.file_label.setText(f"Selected file: {os.path.basename(file_path)}")
            self.search_pdf(file_path)

    def search_pdf(self, file_path):
        self.status_bar.setText("Searching...")
        self.result_text.clear()

        # Define the product names with their corresponding trademarks or registered marks
        products = {
            "SECORA": "™",
            "CIPURSE": "™",
            "SOLIDFLASH": "™",
            "FCOS": "™",
            "NRG": "™",
            "SmartLEWIS": "™",
            "OPTIGA": "™",
            "TEGRION": "™",
            "XMC": "™",
            "PSoC": "™",
            "AURIX": "™",
            "TRAVEO": "™",
            "TriCore": "™",
            "CAPSENSE": "™",
            "HITFET": "™",
            "OPTIREG": "™",
            "LITIX": "™",
            "EiceDRIVER": "™",
            "PROFET": "™",
            "SPIDERSPOC": "™",
            "XENSIV": "™",
            "REAL3": "™",
            "RASIC": "™",
            "CoolSiC": "™",
            "AutomotiveHybridPACK": "™",
            "SEMPER": "™",
            "NovalithIC": "™",
            "TEMPFET": "™",
            "MOTIX": "™",
            "EXCELON": "™",
            "ULTREON": "™",
            "QDR": "™",
            "MOBL": "™",
            "MIRRORBIT": "™",
            "RADSTOP": "™",
            "HYPERBUS": "™",
            "HYPERFLASH": "™",
            "HYPERRAM": "™",
            "PRO-SIL": "™",
            "AIROC": "™",
            "ModusToolbox": "™",
            "WICED": "™",
            "my-d": "™",
            "Contactlessmemoriesmy-d": "™",
            "CIRRENT": "™",
            "TEGRION securitycontrollers": "™",
            "XMC-SCP": "™",
            "FLEX": "™",
            "Cortex": "®",
            "ARM": "®",
            "Bluetooth": "®"
        }

        # Open the PDF file
        pdf = PdfReader(file_path)

        # Initialize a dictionary to store the page numbers and lines of products with missing marks
        missing_marks = {}

        # Iterate through each page of the PDF
        for page_num in range(len(pdf.pages)):
            page_text = pdf.pages[page_num].extract_text()
            lines = page_text.split('\n')
            # Iterate through each product
            for product, mark in products.items():
                pattern = rf'\b{re.escape(product)}\b(?:(?!\s*{mark})|$)'
                for line_num, line in enumerate(lines, start=1):
                    if re.search(pattern, line, re.IGNORECASE):
                        if product not in missing_marks:
                            missing_marks[product] = [(page_num + 1, line_num, line)]
                        else:
                            missing_marks[product].append((page_num + 1, line_num, line))

        # Display the results
        for product, locations in missing_marks.items():
            self.result_text.append(f"Product '{product}' is missing the {products[product]} mark:\n")
            for location in locations:
                self.result_text.append(f"• Page {location[0]}, Line {location[1]}:  {location[2]}\n")
        self.status_bar.setText("Ready")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFSearcherApp()
    ex.show()
    sys.exit(app.exec_())
