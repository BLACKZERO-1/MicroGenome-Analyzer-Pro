import os
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class DataManagerView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.staged_files = [] # Stores file paths before import
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(25)
        self.layout.setContentsMargins(40, 40, 40, 40)

        # 1. Header Section
        self.create_header()

        # 2. Upload "Drop Zone"
        self.create_upload_area()

        # 3. Staging Area (Table)
        self.create_staging_table()

        # 4. Footer Actions
        self.create_action_bar()

    def create_header(self):
        header = QHBoxLayout()
        
        # Title Block
        title_box = QVBoxLayout()
        title = QLabel("📥 Data Manager")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: #1B2559;")
        
        desc = QLabel("Import, validate, and organize raw sequencing data (FASTA, FASTQ, GBK).")
        desc.setStyleSheet("font-size: 14px; color: #707EAE; font-family: 'Segoe UI';")
        
        title_box.addWidget(title)
        title_box.addWidget(desc)
        
        header.addLayout(title_box)
        header.addStretch()
        
        # File Counter Badge
        self.lbl_count = QLabel("0 Files Ready")
        self.lbl_count.setStyleSheet("""
            background-color: #E3F2FD; color: #1565C0; font-weight: bold; 
            padding: 10px 20px; border-radius: 12px; font-size: 14px;
        """)
        header.addWidget(self.lbl_count)

        self.layout.addLayout(header)

    def create_upload_area(self):
        # A clickable frame that looks like a Drag & Drop zone
        self.drop_frame = QFrame()
        self.drop_frame.setFixedHeight(180)
        self.drop_frame.setCursor(Qt.PointingHandCursor)
        self.drop_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FC;
                border: 2px dashed #4318FF;
                border-radius: 20px;
            }
            QFrame:hover {
                background-color: #EEF2FF;
                border: 2px dashed #2B3674;
            }
        """)
        
        # Enable clicking on the frame by overriding mousePressEvent
        self.drop_frame.mousePressEvent = self.open_file_dialog

        # Layout inside the frame
        df_layout = QVBoxLayout(self.drop_frame)
        df_layout.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel("📂")
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        main_lbl = QLabel("Click to Browse Files")
        main_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #4318FF; background: transparent; border: none;")
        main_lbl.setAlignment(Qt.AlignCenter)
        
        sub_lbl = QLabel("Supported formats: .fasta, .fna, .fastq, .gbk, .txt")
        sub_lbl.setStyleSheet("font-size: 13px; color: #A3AED0; background: transparent; border: none;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        
        df_layout.addWidget(icon_lbl)
        df_layout.addWidget(main_lbl)
        df_layout.addWidget(sub_lbl)
        
        self.layout.addWidget(self.drop_frame)

    def create_staging_table(self):
        lbl = QLabel("Staged Files")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2559;")
        self.layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File Name", "Format", "Size", "Validation Status"])
        
        # --- STATIC EXCEL CONFIGURATION ---
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setShowGrid(True)  # Keep Grid lines
        self.table.setAlternatingRowColors(False) 
        
        # Row Numbers (Vertical Header)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(40)
        
        # Disable Interaction Triggers
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection) # No clicking rows
        self.table.setFocusPolicy(Qt.NoFocus) # No dotted focus lines

        # Stylesheet: FORCE WHITE BACKGROUND on Hover/Selection
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #D0D0D0; /* Visible Gray Grid */
                border: 1px solid #A0A0A0;
                font-size: 13px;
                color: #333333;
                outline: none;
            }
            
            QHeaderView::section {
                background-color: #F8F9FA; /* Gray Headers */
                color: #444444;
                font-weight: bold;
                border: 1px solid #D0D0D0;
                padding: 6px;
                font-size: 12px;
            }
            
            QTableWidget::item {
                padding-left: 5px;
                border: none;
                background-color: white;
                color: #333333;
            }
            
            /* FORCE OVERRIDE: Any hover, focus, or selection stays WHITE */
            QTableWidget::item:hover {
                background-color: white;
                color: #333333;
            }
            QTableWidget::item:selected {
                background-color: white;
                color: #333333;
            }
            QTableWidget::item:focus {
                background-color: white;
                color: #333333;
            }
            
            /* Vertical Header Styling (Row Numbers) */
            QHeaderView::section:vertical {
                background-color: #F8F9FA;
                border-right: 1px solid #D0D0D0;
                border-bottom: 1px solid #D0D0D0;
            }
        """)
        
        self.layout.addWidget(self.table)

    def create_action_bar(self):
        bar = QHBoxLayout()
        
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setFixedSize(120, 45)
        self.btn_clear.setStyleSheet("""
            QPushButton { background: white; color: #E31A1A; border: 1px solid #E31A1A; border-radius: 10px; font-weight: 600; }
            QPushButton:hover { background: #FFF5F5; }
        """)
        self.btn_clear.clicked.connect(self.clear_staging)
        
        self.btn_import = QPushButton("Import to Database ➔")
        self.btn_import.setFixedSize(200, 45)
        self.btn_import.setStyleSheet("""
            QPushButton { background: #4318FF; color: white; border-radius: 10px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background: #3311CC; }
        """)
        self.btn_import.clicked.connect(self.process_import)
        
        bar.addWidget(self.btn_clear)
        bar.addStretch()
        bar.addWidget(self.btn_import)
        
        self.layout.addLayout(bar)

    # --- LOGIC ---

    def open_file_dialog(self, event):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Sequences", "", 
            "Sequences (*.fasta *.fna *.fastq *.gbk *.txt);;All Files (*)"
        )
        if files:
            for f in files:
                if f not in self.staged_files:
                    self.staged_files.append(f)
            self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.staged_files))
        self.lbl_count.setText(f"{len(self.staged_files)} Files Ready")
        
        for i, path in enumerate(self.staged_files):
            name = os.path.basename(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            ext = os.path.splitext(name)[1].lower()
            
            fmt_type = "UNKNOWN"
            if ext in ['.fasta', '.fna', '.txt']: fmt_type = "FASTA"
            elif ext in ['.fastq']: fmt_type = "FASTQ"
            elif ext in ['.gbk', '.gb']: fmt_type = "GENBANK"
            
            # Status Logic
            status = "Ready to Import"
            
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(fmt_type))
            self.table.setItem(i, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
            
            item_status = QTableWidgetItem(status)
            item_status.setForeground(QColor("#05CD99") if size_mb > 0 else QColor("#E31A1A"))
            item_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(i, 3, item_status)

    def clear_staging(self):
        self.staged_files = []
        self.refresh_table()

    def process_import(self):
        if not self.staged_files:
            QMessageBox.warning(self, "No Files", "Please drop files or click to browse first.")
            return

        # SIMULATION OF DB INSERTION
        try:
            count = len(self.staged_files)
            # 1. Loop through files (Placeholder for DB Logic)
            for file_path in self.staged_files:
                filename = os.path.basename(file_path)
                print(f"Importing {filename} to Database...")

            # 2. Success Message
            QMessageBox.information(self, "Import Successful", 
                                    f"Successfully imported {count} files into the Local Database.\n\nYou can now proceed to QC or Annotation.")
            
            # 3. Clear List
            self.clear_staging()
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))