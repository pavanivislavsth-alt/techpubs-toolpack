import os
import ssl
import fitz  
import urllib.request
from PyQt5.QtWidgets import (QMainWindow, QWidget, QGridLayout, QLabel, 
                             QTextBrowser, QScrollBar, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

class PDFHyperlinkCheckerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("PDF Hyperlink Checker")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()

        self.file_label = QLabel("Select a PDF document:")
        layout.addWidget(self.file_label, 0, 0)

        self.result_text = QTextBrowser()
        self.result_text.setOpenExternalLinks(True)
        self.result_text.setStyleSheet("font-family: Arial; font-size: 10pt;")
        layout.addWidget(self.result_text, 1, 0, 1, 2)

        self.scrollbar = QScrollBar(Qt.Vertical)
        self.result_text.setVerticalScrollBar(self.scrollbar)
        layout.addWidget(self.scrollbar, 1, 2, 1, 1)

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
        self.file_button.clicked.connect(self.extract_hyperlinks)
        layout.addWidget(self.file_button, 0, 1)

        central_widget.setLayout(layout)
        self.resize(800, 400)

    def extract_hyperlinks(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            file_path = os.path.normpath(file_path)  # Normalize the file path
            print(f"Normalized file path: {file_path}")
            try:
                doc = fitz.open(file_path)
                hyperlinks = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    links = page.get_links()
                    for link in links:
                        if 'uri' in link:
                            hyperlink_address = link['uri']
                            rect = link['from']  # Get the rectangle area of the link
                            words = page.get_text("words")  # Get all words on the page
                            hyperlink_text = []
                            for word in words:
                                word_rect = fitz.Rect(word[:4])
                                if rect.intersects(word_rect):
                                    hyperlink_text.append(word[4])
                            hyperlink_text = " ".join(hyperlink_text)
                            try:
                                ctx = ssl.create_default_context()
                                ctx.check_hostname = False
                                ctx.verify_mode = ssl.CERT_NONE
                                req = urllib.request.Request(hyperlink_address, method="HEAD")
                                req.add_header("User-Agent", "Mozilla/5.0")
                                with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                                    if response.status == 200:
                                        link_status = "Valid"
                                    else:
                                        link_status = "Broken"
                            except urllib.error.HTTPError as e:
                                if e.code == 404:
                                    link_status = "Broken"
                                else:
                                    link_status = "Unknown"
                            except urllib.error.URLError as e:
                                link_status = "Broken"
                            except Exception as e:
                                link_status = "Unknown"
                            hyperlinks.append((hyperlink_text, hyperlink_address, page_num + 1, link_status))
                        else:
                            print(f"No URI found in link on page {page_num + 1}: {link}")
                doc.close()

                # Display the hyperlinks in the text edit
                self.result_text.clear()  # Clear the text box
                html_output = "<html><body>"
                for text, address, page_num, status in hyperlinks:
                    display_text = f"{text}: <a href=\"{address}\" target=\"_blank\">{address}</a> (Page {page_num}) - {status}"
                    if status == "Broken":
                        html_output += f'<div style="margin-bottom: 15px; color:red;">{display_text}</div>'
                    else:
                        html_output += f'<div style="margin-bottom: 15px; color:black;">{display_text}</div>'
                html_output += "</body></html>"
                self.result_text.setHtml(html_output)
            except Exception as e:
                print(f"Error opening file: {e}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ex = PDFHyperlinkCheckerApp()
    ex.show()
    sys.exit(app.exec_())
