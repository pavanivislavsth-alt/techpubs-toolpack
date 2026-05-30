import sys
import os
import subprocess
import win32com.client
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QStatusBar, QSizePolicy)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class VisioToSVGConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Visio to SVG Converter')
        self.setGeometry(100, 100, 600, 200)
        
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Input file selection layout
        input_layout = QHBoxLayout()
        input_label = QLabel('Input Files:')
        self.input_line_edit = QLineEdit()
        self.input_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_button = QPushButton('Browse...')
        input_button.setFixedSize(100, 40)
        input_button.clicked.connect(self.select_input_files)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_line_edit)
        input_layout.addWidget(input_button)
        
        # Convert button layout
        convert_layout = QHBoxLayout()
        convert_button = QPushButton('Convert')
        convert_button.setFixedSize(100, 40)
        convert_button.clicked.connect(self.start_conversion)
        convert_layout.addStretch()
        convert_layout.addWidget(convert_button)
        convert_layout.addStretch()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Adding layouts to main layout
        main_layout.addLayout(input_layout)
        main_layout.addLayout(convert_layout)
        
        # Set primary color for buttons
        primary_color = "#0A8276"
        input_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_color}; 
                color: white;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #087563;
            }}
            QPushButton:pressed {{
                background-color: #06584C;
            }}
        """)
        convert_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_color}; 
                color: white;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #087563;
            }}
            QPushButton:pressed {{
                background-color: #06584C;
            }}
        """)
        
        self.show()

    def select_input_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Select Files', '', 'Visio, EMF and WMF Files (*.vsdx *.vsd *.emf *.wmf)')
        if files:
            self.input_line_edit.setText(';'.join(files))
            self.status_bar.showMessage('Selected input files', 5000)

    def start_conversion(self):
        input_files = self.input_line_edit.text().split(';')
        if not input_files:
            self.status_bar.showMessage('Please select input files', 5000)
            return
        self.convert_files_to_svg(input_files)

    def convert_files_to_svg(self, input_files):
        for input_file in input_files:
            input_file = input_file.strip()
            output_dir = os.path.dirname(input_file)
            if input_file.lower().endswith(('.vsdx', '.vsd')):
                self.convert_visio_to_svg(input_file, output_dir)
            elif input_file.lower().endswith('.emf'):
                self.convert_emf_to_svg(input_file, output_dir)
            elif input_file.lower().endswith('.wmf'):
                self.convert_wmf_to_svg(input_file, output_dir)

    def convert_visio_to_svg(self, input_file, output_dir):
        try:
            visio = win32com.client.Dispatch("Visio.Application")
            visio.Visible = False
            self.status_bar.showMessage("Starting Visio conversion...")

            if os.path.exists(input_file):
                filename = os.path.basename(input_file)
                base_name = os.path.splitext(filename)[0]

                try:
                    input_file = os.path.abspath(input_file)
                    output_file = os.path.abspath(output_dir)

                    print(f"Opening file: {input_file}")
                    self.status_bar.showMessage(f"Opening file: {input_file}")
                    doc = visio.Documents.Open(input_file)

                    for i, page in enumerate(doc.Pages):
                        svg_path = os.path.join(output_file, f"{base_name}_Page_{i+1}.svg")
                        print(f"Saving as SVG: {svg_path}")
                        self.status_bar.showMessage(f"Saving as SVG: {svg_path}")
                        page.Export(svg_path)

                        # Center the SVG content
                        self.center_svg_content(svg_path)

                    doc.Close()
                    print(f"Processed {filename} successfully.\n")
                    self.status_bar.showMessage(f"Converted file successfully")
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    self.status_bar.showMessage(f"Error processing {filename}: {e}")
            else:
                print(f"File not found: {input_file}")
                self.status_bar.showMessage(f"File not found: {input_file}")

            visio.Quit()
            self.status_bar.showMessage("All Visio conversions completed successfully!", 5000)
        except Exception as e:
            print(f"Error with Visio application: {e}")
            self.status_bar.showMessage(f"An error occurred with Visio application: {e}", 5000)

    def convert_emf_to_svg(self, input_file, output_dir):
        self.convert_vector_to_svg(input_file, output_dir, "EMF")

    def convert_wmf_to_svg(self, input_file, output_dir):
        self.convert_vector_to_svg(input_file, output_dir, "WMF")

    def convert_vector_to_svg(self, input_file, output_dir, file_type):
        try:
            input_file = os.path.abspath(input_file)
            filename = os.path.basename(input_file)
            base_name = os.path.splitext(filename)[0]
            output_file = os.path.join(output_dir, f"{base_name}.svg")

            # Path to Inkscape executable
            inkscape_path = r"C:\Program Files\Inkscape\inkscape.exe"

            # Command to convert EMF/WMF to SVG using Inkscape
            command = [
                inkscape_path,
                f"--file={input_file}",
                f"--export-plain-svg={output_file}"
            ]
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Print standard output and error
            print(f"stdout: {result.stdout.decode('utf-8')}")
            print(f"stderr: {result.stderr.decode('utf-8')}")

            # Center the SVG content
            self.center_svg_content(output_file)

            self.status_bar.showMessage(f"Converted {file_type} file {input_file} successfully", 5000)
        except subprocess.CalledProcessError as e:
            print(f"Error converting {file_type} file {input_file}: {e}")
            print(f"stdout: {e.stdout.decode('utf-8')}")
            print(f"stderr: {e.stderr.decode('utf-8')}")
            self.status_bar.showMessage(f"Error converting {file_type} file {input_file}: {e}", 5000)
    
    def center_svg_content(self, svg_file):
        try:
            with open(svg_file, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            # Add centering attributes to the SVG content
            content = content.replace('<svg ', '<svg style="display: block; margin: auto;" ')
            
            with open(svg_file, 'w', encoding='utf-8', errors='ignore') as file:
                file.write(content)
                
            print(f"Centered SVG content for {svg_file}")
        except Exception as e:
            print(f"Error centering SVG content for {svg_file}: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VisioToSVGConverter()
    sys.exit(app.exec_())
