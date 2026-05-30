import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QSizePolicy, QFrame, QMenuBar, 
    QAction, QMessageBox, QScrollArea
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from Updated_Final_PDFCompare import PDFComparisonTool
from Updated_TradeMark import PDFSearcherApp
from SVG3converter import VisioToSVGConverter
from Updated_RegisterManual import RegisterManualApp
from video2ppt import VideoCapture
from Updated_PCKGdiagram import PackageDiagramSearchApp
from PDFbrokenlink import PDFHyperlinkCheckerApp
from Video2Text4 import VideoToTextApp


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechPubs Toolpack 1.0")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

        # Resizing the icon image
        original_icon_path = resource_path('Assets/logo1.png')
        resized_icon_path = resource_path('Assets/logo1_resized.png')
        if os.path.exists(original_icon_path):
            self.resize_icon(original_icon_path, resized_icon_path, (256, 256))
        else:
            print(f"File not found: {original_icon_path}")

        # Set window icon
        if os.path.exists(resized_icon_path):
            self.setWindowIcon(QIcon(resized_icon_path))
        else:
            print(f"Resized icon not found: {resized_icon_path}")

        self.create_menu_bar()
        self.init_ui()

    def create_menu_bar(self):
        self.menu_bar = QMenuBar()
        self.menu_bar.setFont(QFont("Arial", 10))

        # File menu
        file_menu = self.menu_bar.addMenu('File')
        file_menu.setFont(QFont("Arial", 10))
        exit_action = QAction('Exit', self)
        exit_action.setFont(QFont("Arial", 10))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = self.menu_bar.addMenu('Help')
        help_menu.setFont(QFont("Arial", 10))
        about_action = QAction('About', self)
        about_action.setFont(QFont("Arial", 10))
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def init_ui(self):
        main_layout = QHBoxLayout()

        # Sidebar Layout
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)

        buttons = [
            ("PDF Link Checker", self.open_pdf_broken_link),
            ("PDF Trademark Checker", self.open_trademark_check),
            ("SVG Converter", self.open_svg_converter),
            ("Registers Manual XML Creator", self.open_register_manual),
            ("Video to PPT", self.open_video_to_ppt),
            ("Package Diagram Search", self.open_package_diagram),
            ("PDF Comparison Tool", self.open_pdf_compare),
            ("Video to Text converter", self.open_Video_to_Text)
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 10))
            btn.setToolTip(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0A8276;
                    color: white;
                    padding: 10px;
                    border-radius: 10px;
                    font-size: 14px;
                    margin-bottom: 10px;
                }
                QPushButton:hover {
                    background-color: #08695F;
                }
                QPushButton:pressed {
                    background-color: #065C53;
                }
            """)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(callback)
            sidebar.addWidget(btn)

        sidebar.addStretch()

        # Content Area
        content_layout = QVBoxLayout()

        title = QLabel("TechPubs Toolpack 1.0")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setStyleSheet("color: #0A8276;")
        title.setAlignment(Qt.AlignCenter)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_inner_layout = QVBoxLayout(content_widget)

        instructions = QLabel("""
        <h3><b>PDF Link Checker</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Click on the "Browse" button to select a PDF file.</li>
            <li>The application will extract hyperlinks from the PDF and check their validity.</li>
            <li>The results will be displayed showing the hyperlink status (Valid/Broken).</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application checks for broken hyperlinks in PDF files. It extracts hyperlinks from the PDF, sends a request to each link, and verifies if the link is valid or broken. The results are displayed in the interface for easy review.
        </p>
        <hr>
        <h3><b>PDF Trademark Checker</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Click on the "Browse" button to select a PDF file.</li>
            <li>The selected PDF will be searched for specific product names to check if their trademarks or registered marks are missing.</li>
            <li>The results will be displayed in the text area, indicating the page and line number of any missing marks.</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application searches a PDF file for specified product names and checks if their associated trademarks or registered marks are present. It highlights any instances where these marks are missing and provides detailed results, including page and line numbers.
        </p>
        <hr>
        <h3><b>SVG Converter</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Click on the "Browse..." button to select Visio (.vsdx, .vsd), EMF, or WMF files.</li>
            <li>The selected files will be listed in the input field.</li>
            <li>Click on the "Convert" button to start the conversion process.</li>
            <li>The application will convert the selected files to SVG format and save them in the same directory.</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application converts Visio, EMF, and WMF files to SVG format. It uses Microsoft Visio and Inkscape for the conversion process, and centers the content within the SVG files. The resulting SVG files are saved in the same directory as the input files.
        </p>
        <p><b>Note:</b> Please ensure that Inkscape is installed on your system. You can download and install Inkscape from the official website or through your system's package manager.</p>
        <hr>
        <h3><b>Registers Manual XML Creator</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Enter the SGML Topic ID in the provided field.</li>
            <li>Click on the "Browse" button to select an Excel file and an SGML file.</li>
            <li>Click on the "Generate XML" button to create XML files from the selected data.</li>
            <li>The application will generate and save the XML files in the same directory as the input files.</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application generates XML files from Excel and SGML input files. Users need to provide an SGML Topic ID and select the necessary files. The application processes the data and creates well-formed XML files, linking register names with descriptive IDs and ensuring proper formatting.
        </p>
        <hr>
        <h3><b>Video to PPT</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Click on the "Open MP4" button to select an MP4 video file.</li>
            <li>Use the "Play" and "Pause" buttons to control video playback.</li>
            <li>Click on the "Capture Frame" button to capture frames from the video.</li>
            <li>Once you have captured the desired frames, click on the "Create PPT" button to generate a PowerPoint presentation with the captured frames.</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application converts MP4 video files into PowerPoint presentations. Users can capture frames from the video and save them as slides in a PowerPoint file. The generated presentation is saved in the same directory as the video file.
        </p>
        <hr>
        <h3><b>Package Diagram Search</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Enter the Cypress Package Diagram Number in the provided field.</li>
            <li>Click on the "Search" button to find the corresponding Infineon Package Diagram Numbers.</li>
            <li>The results will be displayed in the text area.</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application searches for Infineon Package Diagram Numbers based on a given Cypress Package Diagram Number. Users input the Cypress number, and the application queries an Excel file to find and display the corresponding Infineon numbers.
        </p>
        <hr>
        <h3><b>PDF Comparison Tool</b></h3>
        <p><b>How to Use:</b></p>
        <ol style="font-size: 14px; color: #333;">
            <li>Open the application.</li>
            <li>Click on the "Select First PDF" button to select the first PDF file.</li>
            <li>Click on the "Select Second PDF" button to select the second PDF file.</li>
            <li>Once both files are selected, click on the "Compare PDFs" button to start the comparison.</li>
            <li>The application will highlight differences between the two PDF files and display the results side by side.</li>
        </ol>
        <p><b>Read Me:</b></p>
        <p style="font-size: 14px; color: #333;">
            This application compares two PDF files to find differences in their text content. It extracts text with positions from both PDFs, identifies discrepancies, and highlights the differences on the respective pages. The results are displayed side by side for easy comparison.
        </p>
        <p><b>Note:</b> For optimal performance, use this tool with smaller PDF files that have similar page layouts. Large files or files with significantly different layouts may impact the accuracy and performance of the comparison.
        </p>
        <hr>
        """)
        content_inner_layout.addWidget(instructions)

        scroll_area.setWidget(content_widget)

        content_layout.addWidget(title)
        content_layout.addWidget(scroll_area)

        # Main layout assembly
        main_layout.addLayout(sidebar, 1)
        main_layout.addLayout(content_layout, 3)

        container = QVBoxLayout()
        container.addWidget(self.menu_bar)
        container.addLayout(main_layout)
        self.setLayout(container)

    def show_about_dialog(self):
        QMessageBox.about(self, "About", "This is version 1.0 of the TechPubs Toolpack created by the Technical Publications department.")

    def resize_icon(self, original_path, resized_path, size):
        try:
            from PIL import Image
            image = Image.open(original_path)
            image = image.resize(size, Image.LANCZOS)
            image.save(resized_path)
        except FileNotFoundError as e:
            print(f"File not found: {e}")
        except Exception as e:
            print(f"Error resizing image: {e}")

    def open_pdf_compare(self):
        self.pdf_compare_tool = PDFComparisonTool()
        self.pdf_compare_tool.show()

    def open_trademark_check(self):
        self.trademark_check_tool = PDFSearcherApp()
        self.trademark_check_tool.show()

    def open_svg_converter(self):
        self.svg_converter_tool = VisioToSVGConverter()
        self.svg_converter_tool.show()

    def open_register_manual(self):
        self.register_manual_tool = RegisterManualApp()
        self.register_manual_tool.show()

    def open_video_to_ppt(self):
        self.video_to_ppt_tool = VideoCapture()
        self.video_to_ppt_tool.show()

    def open_package_diagram(self):
        self.package_diagram_tool = PackageDiagramSearchApp()
        self.package_diagram_tool.show()

    def open_pdf_broken_link(self):
        self.pdf_broken_link_tool = PDFHyperlinkCheckerApp()
        self.pdf_broken_link_tool.show()

    def open_Video_to_Text(self):
        self.pdf_broken_link_tool = VideoToTextApp()
        self.pdf_broken_link_tool.show()



if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont("Arial", 10))

        window = MainWindow()
        window.show()

        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")
