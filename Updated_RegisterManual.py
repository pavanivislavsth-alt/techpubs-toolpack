import sys
import os
import re
import time
import random
import string
import pandas as pd
from lxml import etree
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton, QLineEdit, QVBoxLayout, 
    QWidget, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt

class RegisterManualApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.excel_file = None
        self.sgml_file = None
        self.register_data_by_name = {}

    def initUI(self):
        self.setWindowTitle("Register Manual Creator")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()

        self.label_sgml_topic_id = QLabel("Enter SGML Topic ID:")
        layout.addWidget(self.label_sgml_topic_id, 0, 0)
        self.entry_sgml_topic_id = QLineEdit()
        layout.addWidget(self.entry_sgml_topic_id, 0, 1)

        self.label_excel = QLabel("Select Excel File:")
        layout.addWidget(self.label_excel, 1, 0)
        self.button_excel = QPushButton("Browse")
        self.button_excel.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #087563;
            }
            QPushButton:pressed {
                background-color: #06584C;
            }
        """)
        self.button_excel.clicked.connect(self.browse_excel)
        layout.addWidget(self.button_excel, 1, 1)

        self.label_sgml = QLabel("Select SGML File:")
        layout.addWidget(self.label_sgml, 2, 0)
        self.button_sgml = QPushButton("Browse")
        self.button_sgml.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #087563;
            }
            QPushButton:pressed {
                background-color: #06584C;
            }
        """)
        self.button_sgml.clicked.connect(self.browse_sgml)
        layout.addWidget(self.button_sgml, 2, 1)

        self.button_generate = QPushButton("Generate XML")
        self.button_generate.setStyleSheet("""
            QPushButton {
                background-color: #0A8276;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #087563;
            }
            QPushButton:pressed {
                background-color: #06584C;
            }
        """)
        self.button_generate.clicked.connect(self.generate_xml)
        layout.addWidget(self.button_generate, 3, 0, 1, 2)

        central_widget.setLayout(layout)
        self.resize(600, 200)

    def browse_excel(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file:
            self.excel_file = file
            self.label_excel.setText(f"Selected: {os.path.basename(file)}")

    def browse_sgml(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select SGML File", "", "SGML Files (*.sgml);;XML Files (*.xml);;All Files (*)", options=options)
        if file:
            self.sgml_file = file
            self.label_sgml.setText(f"Selected: {os.path.basename(file)}")

    def preprocess_sgml(self, content):
        """Replace &, <, and > with their respective XML entities within <desc> and <b> tags nested inside <cell> tags."""

        def replace_nested_special_chars(match):
            """Replaces special characters within nested tags."""
            tag, text = match.groups()
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            return f"<{tag}>{text}</{tag}>"

        def replace_cell_special_chars(match):
            """Replaces special characters within <cell> tags after processing nested tags."""
            text = match.group(1)
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')

            # Restore nested tags (already processed)
            text = text.replace('&lt;desc&gt;', '<desc>')
            text = text.replace('&lt;/desc&gt;', '</desc>')
            text = text.replace('&lt;b&gt;', '<b>')
            text = text.replace('&lt;/b&gt;', '</b>')

            return f"<cell>{text}</cell>"

        # First replace special characters in <desc> and <b> tags within <cell> tags
        content = re.sub(r'<(desc|b)>(.*?)</\1>', replace_nested_special_chars, content, flags=re.DOTALL)
        # Then replace special characters in <cell> tags
        content = re.sub(r'<cell>(.*?)</cell>', replace_cell_special_chars, content, flags=re.DOTALL)

        return content

    def parse_sgml(self, sgml_file):
        try:
            with open(sgml_file, 'r') as file:
                content = file.read()

            # Preprocess the SGML content to handle special characters
            content = self.preprocess_sgml(content)

            # Wrap the content in a single root element to make it well-formed XML
            wrapped_content = f"<root>{content}</root>"

            tree = etree.fromstring(wrapped_content)

            register_data = []

            for register in tree.xpath('//register'):
                reg_name = register.findtext('RegName').strip()
                reg_addr = register.findtext('RegAddr').strip()

                addr_table = []
                for row in register.xpath('addrtable/body/row'):
                    cells = [cell.xpath('string()').strip() for cell in row.xpath('cell')]
                    addr_table.append(cells)

                field_positions = []
                for field in register.xpath('fieldposition8'):
                    field_table = []
                    for row in field.xpath('body/row'):
                        cells = [cell.xpath('string()').strip() for cell in row.xpath('*')]
                        field_table.append(cells)
                    field_positions.append(field_table)

                field_list = []
                for row in register.xpath('fieldlist/body/row'):
                    cells = [cell.xpath('string()').strip() for cell in row.xpath('*')]
                    field_list.append(cells)

                # Generate a descriptive unique ID for each register
                unique_id = self.generate_descriptive_id(reg_name)

                register_data.append({
                    'name': reg_name,
                    'address': reg_addr,
                    'addr_table': addr_table,
                    'field_positions': field_positions,
                    'field_list': field_list,
                    'id': unique_id
                })

            return register_data
        except etree.XMLSyntaxError as e:
            QMessageBox.critical(self, "XML Syntax Error", f"Error parsing SGML file: {e}")
            print(f"Error parsing SGML file: {e}")
            return []

    def generate_descriptive_id(self, base_name):
        """Generate a descriptive ID based on the base_name."""
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        cleaned_base_name = ''.join(e for e in base_name if e.isalnum() or e == ' ').replace(' ', '_')
        return f"section_{cleaned_base_name}_{random_suffix}"

    def create_table(self, parent, rows, cols, colspecs=None, bold_first_row=False):
        table = etree.SubElement(parent, "table", colsep="1", rowsep="1", frame="all")
        tgroup = etree.SubElement(table, "tgroup", cols=str(cols))

        # Adding colspec
        if colspecs:
            for colnum, colspec in enumerate(colspecs, start=1):
                etree.SubElement(tgroup, "colspec", colname=f"c{colnum}", colnum=str(colnum), colwidth=colspec)

        # Adding rows
        for row_type, row_data in rows.items():
            section = etree.SubElement(tgroup, row_type)
            for idx, row in enumerate(row_data):
                row_elem = etree.SubElement(section, "row")
                for cell_idx, cell in enumerate(row):
                    entry = etree.SubElement(row_elem, "entry")
                    if cell_idx == len(row) - 1 and len(row) < cols:  # If last cell and row has fewer columns
                        entry.set("namest", f"c{cell_idx + 1}")
                        entry.set("nameend", f"c{cols}")
                    if bold_first_row and idx == 0:
                        b_elem = etree.SubElement(entry, "b")
                        b_elem.text = cell
                    else:
                        entry.text = cell

    def process_description(self, description, sgml_topic_id, sgml_filename):
        """Process the description text to replace register names with xref elements."""
        parts = re.split(r'(\b[A-Z0-9_]+\b)', description)
        processed_description = etree.Element("entry")
        
        for part in parts:
            if part in self.register_data_by_name:
                # Create the xref element
                xref = etree.Element("xref")
                xref.set("href", f"{sgml_topic_id}.xml#{sgml_topic_id}/{self.register_data_by_name[part]['id']}")
                xref.text = part
                processed_description.append(xref)
            else:
                if len(processed_description):
                    processed_description[-1].tail = (processed_description[-1].tail or '') + part
                else:
                    processed_description.text = (processed_description.text or '') + part
        
        return processed_description

    def create_excel_xml(self, excel_df, register_data, sgml_topic_id, sgml_filename):
        # Create main topic for Excel data
        NSMAP = {'xml': 'http://www.w3.org/XML/1998/namespace'}
        topic_id = f"qwk{int(time.time())}"
        root = etree.Element("topic", nsmap=NSMAP)
        root.set("id", topic_id)
        root.set("{http://www.w3.org/XML/1998/namespace}lang", "en-us")

        title = etree.SubElement(root, "title", ixia_locid="1")
        title.text = "Excel Data Topic"

        shortdesc = etree.SubElement(root, "shortdesc", ixia_locid="2")

        body = etree.SubElement(root, "body")

        # Adding Excel Data
        if not excel_df.empty:
            excel_section = etree.SubElement(body, "section", id="section_excel_data", ixia_locid="4")
            excel_section_title = etree.SubElement(excel_section, "title", ixia_locid="5")
            excel_section_title.text = "Excel Data"
            table = etree.SubElement(excel_section, "table", id="table_excel_data")
            tgroup = etree.SubElement(table, "tgroup", cols=str(len(excel_df.columns)))

            # Adding table header
            head_row = etree.SubElement(tgroup, "thead")
            header_row = etree.SubElement(head_row, "row")
            for idx, column in enumerate(excel_df.columns, start=6):
                entry = etree.SubElement(header_row, "entry", ixia_locid=str(idx))
                entry.text = column

            # Adding table body
            table_body = etree.SubElement(tgroup, "tbody")
            for index, row in excel_df.iterrows():
                register_name = str(row['Register'])
                body_row = etree.SubElement(table_body, "row")
                
                reg_entry = etree.SubElement(body_row, "entry")
                if register_name in self.register_data_by_name:
                    xref = etree.SubElement(reg_entry, "xref", href=f"{sgml_topic_id}.xml#{sgml_topic_id}/{self.register_data_by_name[register_name]['id']}")
                    xref.text = register_name
                else:
                    reg_entry.text = register_name

                addr_entry = etree.SubElement(body_row, "entry")
                addr_entry.text = str(row['Address'])
                
                # Process the description to replace register names with xref elements
                desc_elem = self.process_description(str(row['Description']), sgml_topic_id, sgml_filename)
                body_row.append(desc_elem)

        # Save the XML in the same directory as the Excel file
        output_dir = os.path.dirname(self.excel_file) if self.excel_file else os.path.dirname(self.sgml_file)
        output_xml = os.path.join(output_dir, f"{sgml_topic_id}_{int(time.time())}_excel_output.xml")

        tree = etree.ElementTree(root)
        tree.write(output_xml, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        
        return output_xml

    def create_sgml_xml(self, register_data, sgml_topic_id, output_xml_base_name):
        # Create main topic for SGML data
        NSMAP = {'xml': 'http://www.w3.org/XML/1998/namespace'}
        root = etree.Element("topic", nsmap=NSMAP)
        root.set("id", sgml_topic_id)
        root.set("{http://www.w3.org/XML/1998/namespace}lang", "en-us")

        title = etree.SubElement(root, "title", ixia_locid="1")
        title.text = "SGML Data Topic"

        shortdesc = etree.SubElement(root, "shortdesc", ixia_locid="2")

        body = etree.SubElement(root, "body")

        # Adding SGML Data
        if register_data:
            for reg in register_data:
                reg_elem = etree.SubElement(body, "section", id=reg['id'], ixia_locid="12")
                reg_title = etree.SubElement(reg_elem, "title", ixia_locid="13")
                reg_title.text = reg['name']
                
                # Add addr_table
                if reg['addr_table']:
                    rows = {
                        "tbody": reg['addr_table']
                    }
                    self.create_table(reg_elem, rows, len(reg['addr_table'][0]))

                # Add field positions
                for i, field_table in enumerate(reg['field_positions']):
                    if len(field_table) > 0:
                        header = field_table[0]
                        field_body = field_table[1:]  # Renamed to avoid conflict
                        rows = {
                            "thead": [header],
                            "tbody": field_body
                        }
                        colspecs = ["1*"] * len(header)  # Dynamically handle column count
                        self.create_table(reg_elem, rows, len(header), colspecs)

                # Add field list
                if reg['field_list']:
                    rows = {
                        "tbody": reg['field_list']
                    }
                    self.create_table(reg_elem, rows, len(reg['field_list'][0]), bold_first_row=True)

        # Save the XML in the same directory as the SGML file
        output_dir = os.path.dirname(self.excel_file) if self.excel_file else os.path.dirname(self.sgml_file)
        output_xml = os.path.join(output_dir, f"{output_xml_base_name.replace('_excel_output', '_sgml_output')}.xml")

        tree = etree.ElementTree(root)
        tree.write(output_xml, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        
        return output_xml

    def generate_xml(self):
        if not self.excel_file and not self.sgml_file:
            QMessageBox.critical(self, "Error", "Please select both Excel and SGML files")
            return

        sgml_topic_id = self.entry_sgml_topic_id.text().strip()
        if not sgml_topic_id:
            QMessageBox.critical(self, "Error", "Please enter an SGML Topic ID")
            return

        sgml_filename = f"{sgml_topic_id}.xml"

        # Step 1: Load Excel data
        registers_df = pd.read_excel(self.excel_file) if self.excel_file else pd.DataFrame()

        # Step 2: Parse SGML data
        register_data = self.parse_sgml(self.sgml_file) if self.sgml_file else []
        
        # Create a dictionary for quick lookup
        self.register_data_by_name = {reg['name']: reg for reg in register_data}

        # Step 3: Create XMLs
        excel_xml_path = self.create_excel_xml(registers_df, register_data, sgml_topic_id, sgml_filename)
        sgml_xml_path = self.create_sgml_xml(register_data, sgml_topic_id, os.path.basename(excel_xml_path))

        QMessageBox.information(self, "Success", f"XML files created successfully:\n{excel_xml_path}\n{sgml_xml_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = RegisterManualApp()
    ex.show()
    sys.exit(app.exec_())
