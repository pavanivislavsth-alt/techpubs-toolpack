import os
import re
import threading
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPlainTextEdit, QLineEdit, QPushButton, QProgressBar, QLabel,
    QFileDialog, QMessageBox, QFrame, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread, QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup


BRAND_PRIMARY = "#0A8276"
BRAND_WHITE   = "#FFFFFF"
BRAND_TEXT    = "#1D1D1D"
NEUTRAL_BG    = "#F7F7F7"
NEUTRAL_TROUGH= "#E6E6E6"
PRIMARY_HOVER = "#087568"


def scrape_single_ecn(ecn_url: str):
    textarea_text = ""
    jira_only = ""
    ecn_text = "ECN not found"
    member_text = "Member not found"
    language_text = "Language not found"
    division_text = "Division not found"
    pl_text = "PL not found"
    doc_rev_text = "Doc Rev not found"
    doc_name_text = "Doc name not found"
    external_internal_text = "External/Internal not found"

    task_type_text = "Editorial"
    revision_type_text = "Revise"        
    revision_source_text = ""             

    driver = None
    try:
        driver = webdriver.Chrome()
        driver.get(ecn_url)
        wait = WebDriverWait(driver, 12)

        # Handle the informational/login splash if it appears
     
        try:
            checkbox = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="dont-show-again"]'))
            )
            checkbox.click()
        except Exception:
            pass  # popup not present

        try:
            forward_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="forward-button"]'))
            )
            forward_btn.click()
        except Exception:
            pass  # forward button not present
   

        # Grab the big textarea for various regex pulls
        try:
            textarea_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/table[2]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr[9]/td/textarea')
            ))
            textarea_text = textarea_element.get_attribute("value") or ""
        except (TimeoutException, NoSuchElementException):
            pass

        # Extract Jira link
        jira_match = re.search(
            r'(https?://jirard\.intra\.infineon\.com/browse/[^\s]+)',
            textarea_text,
            flags=re.IGNORECASE
        )
        jira_only = jira_match.group(1).strip() if jira_match else ""

        # ECN id
        try:
            ecn_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "body > table:nth-child(2) > tbody > tr > td > table > tbody > tr:nth-child(1) > td > table > tbody > tr > td:nth-child(2) > font:nth-child(1) > strong")
            ))
            ecn_text = ecn_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # Member
        try:
            member_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "body > table:nth-child(2) > tbody > tr > td > table > tbody > tr:nth-child(1) > td > table > tbody > tr > td:nth-child(2) > font:nth-child(5) > a")
            ))
            member_text = member_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # Language
        try:
            language_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#item1 > table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(1) > td:nth-child(5)")
            ))
            language_text = language_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # Division
        try:
            division_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#ui-id-2 > table > tbody > tr.section0 > td:nth-child(4)")
            ))
            division_text = division_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # PL
        try:
            pl_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#ui-id-2 > table > tbody > tr:nth-child(2) > td:nth-child(2)")
            ))
            pl_text = pl_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # Doc Rev (existing)
        try:
            doc_rev_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#myTable > tbody > tr > td:nth-child(5) > div")
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", doc_rev_element)
            doc_rev_text = doc_rev_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # Doc name (existing)
        try:
            doc_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#myTable > tbody > tr > td:nth-child(3)")
            ))
            doc_name_text = doc_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

        # External/Internal (existing)
        try:
            external_internal_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#myTable > tbody > tr > td:nth-child(8)")
            ))
            external_internal_text = external_internal_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            pass

    
        try:
            rev_cell = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#myTable > tbody > tr > td:nth-child(5)")
            ))
            revision_source_text = (rev_cell.text or "").strip()
            if "**" in revision_source_text:
                revision_type_text = "new"
            else:
                revision_type_text = "Revise"
        except (TimeoutException, NoSuchElementException):
            # keep default "Revise" if we can't read it
            pass

    except WebDriverException:
        return {
            "Quarter": None, "Member": None, "Task type": None, "Revision type": None,
            "Status": "Failed",
            "Language": None, "Division": None, "PL": None,
            "Doc ID": None, "Doc name": None, "Doc Rev": None,
            "ECN": f"Failed: {ecn_url}", "Jira": None,
            "Doc count": None, "Page count": None, "Effort hours": None,
            "External or Internal": None
        }
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

    # Parse metrics from textarea
    doc_id_match = re.search(r'Spec#([\d\-]+)', textarea_text)
    page_count_match = re.search(r'PageCount#(\d+)', textarea_text, flags=re.IGNORECASE)
    effort_match = re.search(r'Effort#(\d+)', textarea_text, flags=re.IGNORECASE)
    doc_id = doc_id_match.group(1) if doc_id_match else None
    page_count = page_count_match.group(1) if page_count_match else None
    effort_hours = effort_match.group(1) if effort_match else None

    # Quarter calculation
    today = datetime.today()
    month = today.month
    if month in [10, 11, 12]:
        quarter = "IFX25/26-Q1"
    elif month in [1, 2, 3]:
        quarter = "IFX25/26-Q2"
    elif month in [4, 5, 6]:
        quarter = "IFX25/26-Q3"
    else:
        quarter = "IFX25/26-Q4"

    return {
        "Quarter": quarter,
        "Member": member_text,
        "Task type": task_type_text,           
        "Revision type": revision_type_text,   
        "Status": "Complete",
        "Language": language_text,
        "Division": division_text,
        "PL": pl_text,
        "Doc ID": doc_id,
        "Doc Rev": doc_rev_text,
        "Doc name": doc_name_text,
        "ECN": ecn_text,
        "Jira": jira_only,
        "Doc count": 1,
        "Page count": page_count,
        "Effort hours": effort_hours,
        "External or Internal": external_internal_text
    }


def scrape_batch_to_excel(urls, excel_path, sheet_name="ECN", progress_callback=None):
    urls = [u.strip() for u in urls if u.strip()]
    if not urls:
        raise ValueError("No ECN URLs provided.")
    if not excel_path.strip():
        raise ValueError("Excel path is empty.")

    # Ensure directory exists
    dir_name = os.path.dirname(excel_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    # Collect NEW rows only
    new_rows = []
    total = len(urls)
    done = 0
    for url in urls:
        new_rows.append(scrape_single_ecn(url))
        done += 1
        if progress_callback:
            progress_callback(done, total)

    # UPDATED: columns now include "Task type" and "Revision type" after "Member"
    columns = [
        "Quarter", "Member", "Task type", "Revision type", "Status",
        "Language", "Division", "PL",
        "Doc ID", "Doc Rev", "Doc name", "ECN", "Jira",
        "Doc count", "Page count", "Effort hours", "External or Internal"
    ]
    df_new = pd.DataFrame(new_rows, columns=columns)

    # Append logic: if file + sheet exist, append; else create.
    sheet_exists = False
    file_exists = os.path.exists(excel_path)

    if file_exists:
        try:
            # Check if sheet exists
            existing_df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
            sheet_exists = True
            startrow = existing_df.shape[0] + 1  # append below existing data
        except Exception:
            # File exists but sheet may not exist or unreadable
            startrow = 0
            sheet_exists = False
    else:
        startrow = 0

    # Try overlay append if supported; else fallback to replace
    if file_exists and sheet_exists:
        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                df_new.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=startrow)
        except TypeError:
            existing_df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
            out_df = pd.concat([existing_df, df_new], ignore_index=True)
            with pd.ExcelWriter(excel_path, engine="openpyxl", mode='a', if_sheet_exists='replace') as writer:
                out_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        mode = 'a' if file_exists else 'w'
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode=mode) as writer:
            df_new.to_excel(writer, sheet_name=sheet_name, index=False)

    return None


class ScrapeWorker(QObject):
    progress = pyqtSignal(int, int)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, urls, excel_path):
        super().__init__()
        self.urls = urls
        self.excel_path = excel_path

    def run(self):
        try:
            scrape_batch_to_excel(
                urls=self.urls,
                excel_path=self.excel_path,
                sheet_name="ECN",
                progress_callback=lambda d, t: self.progress.emit(d, t)
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECN Batch Scraper")
        self.resize(980, 660)

        self.setStyleSheet(f"""
            QWidget {{
                background: {NEUTRAL_BG};
                color: {BRAND_TEXT};
                font-family: 'Segoe UI';
                font-size: 11pt;
            }}
            QFrame#Card {{
                background: {BRAND_WHITE};
                border: 1px solid #E6E6E6;
                border-radius: 12px;
            }}
            QLineEdit, QPlainTextEdit {{
                background: #FAFAFA;
                border: 1px solid #E6E6E6;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton#Primary {{
                background: {BRAND_PRIMARY};
                color: {BRAND_WHITE};
                border: none;
                border-radius: 20px;
                padding: 10px 18px;
                font-weight: bold;
            }}
            QPushButton#Primary:hover {{
                background: {PRIMARY_HOVER};
            }}
            QPushButton#Primary:pressed {{
                background: #065C54;
            }}
            QPushButton#Ghost {{
                background: {BRAND_WHITE};
                color: {BRAND_TEXT};
                border: 1px solid #E6E6E6;
                border-radius: 20px;
                padding: 10px 18px;
            }}
            QPushButton#Ghost:pressed {{
                background: #D7D7D7;
            }}
            QProgressBar {{
                border: 1px solid #E6E6E6;
                border-radius: 14px;
                background: {NEUTRAL_TROUGH};
                text-align: center;
                color: {BRAND_TEXT};
            }}
            QProgressBar::chunk {{
                border-radius: 14px;
                background-color: {BRAND_PRIMARY};
                width: 20px;
                margin: 0px;
            }}
        """)

        # Central widget
        central = QWidget(self)
        self.setCentralWidget(central)
        v = QVBoxLayout(central)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        # Header
        title = QLabel("ECN Batch Scraper")
        title.setStyleSheet(f"font-size: 22pt; font-weight: 800; color: {BRAND_TEXT};")
        v.addWidget(title, alignment=Qt.AlignLeft)

        # Card container
        card = QFrame(objectName="Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)
        v.addWidget(card)

        # URLs
        urls_label = QLabel("Batch ECN URLs (one per line)")
        urls_label.setStyleSheet("font-weight: 600;")
        urls_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.url_text = QPlainTextEdit()
        self.url_text.setPlaceholderText("Paste ECN URLs here — one per line")
        self.url_text.setFixedHeight(260)
        grid.addWidget(urls_label, 0, 0, 1, 1, alignment=Qt.AlignTop | Qt.AlignLeft)
        grid.addWidget(self.url_text, 0, 1, 1, 2)

        # Excel path
        path_label = QLabel("Excel Path (.xlsx)")
        path_label.setStyleSheet("font-weight: 600;")
        path_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Choose where to save the Excel file (*.xlsx)")

        self.browse_btn = QPushButton("Browse…", objectName="Ghost")
        self.browse_btn.clicked.connect(self.on_browse)
        grid.addWidget(path_label, 1, 0, 1, 1)
        grid.addWidget(self.path_edit, 1, 1, 1, 1)
        grid.addWidget(self.browse_btn, 1, 2, 1, 1, alignment=Qt.AlignLeft)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("0% Complete")
        grid.addWidget(self.progress, 2, 1, 1, 2)

        # Buttons
        self.run_btn = QPushButton("Run", objectName="Primary")
        self.clear_btn = QPushButton("Clear", objectName="Ghost")
        self.run_btn.clicked.connect(self.on_run)
        self.clear_btn.clicked.connect(self.on_clear)
        grid.addWidget(self.run_btn, 3, 1, 1, 1, alignment=Qt.AlignRight)
        grid.addWidget(self.clear_btn, 3, 2, 1, 1, alignment=Qt.AlignLeft)

        # Column sizing
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnMinimumWidth(0, 180)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 0)
        grid.setRowStretch(2, 0)
        grid.setRowStretch(3, 0)

        # Thread placeholders
        self.thread = None
        self.worker = None

        # Progress animation
        self._display_percent = 0
        self._target_percent = 0
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._animate_progress)
        self._anim.start(40)  # ~25 fps

        # Shadows for buttons
        self._attach_button_shadow(self.run_btn)
        self._attach_button_shadow(self.clear_btn)
        self._attach_button_shadow(self.browse_btn)

        # Keep animations
        self._btn_anims = []

    def on_browse(self):
        self._pulse_button(self.browse_btn)
        dlg = QFileDialog(self, "Save Excel As")
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setNameFilter('Excel Files (*.xlsx)')
        dlg.setOption(QFileDialog.DontConfirmOverwrite, True)
        dlg.selectFile("ecnfetch.xlsx")
        if dlg.exec_():
            file_name = dlg.selectedFiles()[0]
            if not file_name.lower().endswith('.xlsx'):
                file_name += '.xlsx'
            self.path_edit.setText(file_name)

    def on_clear(self):
        self._pulse_button(self.clear_btn)
        self.url_text.clear()
        self.path_edit.clear()
        self._display_percent = 0
        self._target_percent = 0
        self.progress.setValue(0)
        self.progress.setFormat("0% Complete")
        self._apply_progress_text_contrast(dark=True)

    def on_run(self):
        self._pulse_button(self.run_btn)
        urls = [line.strip() for line in self.url_text.toPlainText().splitlines() if line.strip()]
        save_path = self.path_edit.text().strip()
        if not urls or not save_path:
            self._target_percent = min(5, self._target_percent + 5)
            return

        # Disable during run
        self.run_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)

        # Reset progress
        self._display_percent = 0
        self._target_percent = 0
        self.progress.setValue(0)
        self.progress.setFormat("0% Complete")
        self._apply_progress_text_contrast(dark=True)

        # Start worker
        self.thread = QThread()
        self.worker = ScrapeWorker(urls, save_path)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress_signal)
        self.worker.error.connect(self.on_error_signal)
        self.worker.finished.connect(self.on_finished_signal)

        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_progress_signal(self, done, total):
        percent = int((done / max(total, 1)) * 100)
        self._target_percent = percent

    def _animate_progress(self):
        if self._display_percent < self._target_percent:
            step = max(1, int((self._target_percent - self._display_percent) * 0.25))
            self._display_percent = min(self._target_percent, self._display_percent + step)
        elif self._display_percent > self._target_percent:
            step = max(1, int((self._display_percent - self._target_percent) * 0.25))
            self._display_percent = max(self._target_percent, self._display_percent - step)
        self.progress.setValue(self._display_percent)
        if self._display_percent >= 100:
            self.progress.setFormat("Complete")
            self._apply_progress_text_contrast(dark=False)
        else:
            self.progress.setFormat(f"{self._display_percent}% Complete")
            self._apply_progress_text_contrast(dark=(self._display_percent < 35))

    def on_finished_signal(self):
        self.run_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self._target_percent = 100

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Success")
        msg.setText("Fetch completed.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setStyleSheet(
            f"QPushButton {{ background: {BRAND_PRIMARY}; color: {BRAND_WHITE}; border-radius: 18px; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background: {PRIMARY_HOVER}; }}"
        )
        ret = msg.exec_()
        if ret == QMessageBox.Ok:
            self.on_clear()

    def on_error_signal(self, msg):
        self.run_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", msg)

    def _apply_progress_text_contrast(self, dark: bool):
        text_color = BRAND_TEXT if dark else BRAND_WHITE
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #E6E6E6;
                border-radius: 14px;
                background: {NEUTRAL_TROUGH};
                text-align: center;
                color: {text_color};
            }}
            QProgressBar::chunk {{
                border-radius: 14px;
                background-color: {BRAND_PRIMARY};
                width: 20px;
                margin: 0px;
            }}
        """)

    def _attach_button_shadow(self, btn: QPushButton):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(Qt.black)
        btn.setGraphicsEffect(shadow)

    def _pulse_button(self, btn: QPushButton):
        rect = btn.geometry()
        expanded = rect.adjusted(-3, -3, 3, 3)

        anim_out = QPropertyAnimation(btn, b"geometry")
        anim_out.setDuration(120)
        anim_out.setStartValue(rect)
        anim_out.setEndValue(expanded)
        anim_out.setEasingCurve(QEasingCurve.OutQuad)

        anim_in = QPropertyAnimation(btn, b"geometry")
        anim_in.setDuration(120)
        anim_in.setStartValue(expanded)
        anim_in.setEndValue(rect)
        anim_in.setEasingCurve(QEasingCurve.InQuad)

        seq = QSequentialAnimationGroup(self)
        seq.addAnimation(anim_out)
        seq.addAnimation(anim_in)

        self._btn_anims.append(seq)
        seq.finished.connect(lambda: self._btn_anims.remove(seq))
        seq.start()


def main():
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()