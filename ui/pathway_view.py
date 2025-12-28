import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QComboBox, QTextEdit, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QScrollArea, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor, QFont

from core.pathways.pathway_engine import PathwayWorker

class PathwayView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager # Store Database
        self.worker = None
        self.current_analysis_id = None

        # --- STYLESHEET ---
        self.setStyleSheet("""
            QWidget { background-color: #F8F9FC; font-family: 'Segoe UI', sans-serif; }
            QLabel#header { color: #2B3674; font-size: 24px; font-weight: 900; }
            QLabel#subheader { color: #A3AED0; font-size: 13px; font-weight: 500; margin-bottom: 10px; }
            QLabel#section_title { 
                background-color: #1B2559; color: white; 
                font-weight: bold; padding: 8px; border-radius: 4px;
            }
            QFrame#card { 
                background-color: #FFFFFF; border: 2px solid #2B3674; border-radius: 12px; 
            }
            QComboBox {
                padding: 8px; border: 2px solid #000000; border-radius: 6px;
                background-color: #FFFFFF; color: #000000; font-weight: 600;
            }
            QPushButton { border-radius: 8px; font-weight: bold; font-size: 13px; padding: 10px; border: 2px solid black; }
            QPushButton#btn_run { background-color: #4318FF; color: white; border-color: #2B3674; }
            QPushButton#btn_run:hover { background-color: #3311CC; }
            QPushButton#btn_refresh { background-color: #FFD700; color: black; }
            QTableWidget {
                background-color: white; border: 2px solid black; gridline-color: black;
                color: black; font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2B3674; color: white; padding: 6px; border: 1px solid white; font-weight: bold;
            }
            QTextEdit { background-color: #000000; color: #00FF00; border: 3px solid #444444; border-radius: 6px; }
        """)

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.content_widget = QWidget()
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # 1. HEADER
        header_box = QVBoxLayout()
        header_box.addWidget(QLabel("METABOLIC PATHWAYS ENGINE", objectName="header"))
        header_box.addWidget(QLabel("Functional Analysis & Data Mining Module", objectName="subheader"))
        self.layout.addLayout(header_box)

        # 2. CONTROLS CARD
        control_card = QFrame(); control_card.setObjectName("card")
        cl = QVBoxLayout(control_card); cl.setContentsMargins(20, 20, 20, 20)
        
        cl.addWidget(QLabel(" 1. INPUT ANNOTATION FILE", objectName="section_title"))
        row_input = QHBoxLayout()
        self.combo_files = QComboBox()
        self.refresh_files()
        
        self.btn_refresh = QPushButton("↻ REFRESH"); self.btn_refresh.setObjectName("btn_refresh")
        self.btn_refresh.clicked.connect(self.refresh_files)
        
        row_input.addWidget(self.combo_files, 3); row_input.addWidget(self.btn_refresh, 1)
        cl.addLayout(row_input)
        
        cl.addSpacing(10)
        cl.addWidget(QLabel(" 2. ACTION", objectName="section_title"))
        self.btn_run = QPushButton("⚡ RUN MINING & GENERATE CHART"); self.btn_run.setObjectName("btn_run")
        self.btn_run.clicked.connect(self.run_analysis)
        cl.addWidget(self.btn_run)
        self.layout.addWidget(control_card)

        # 3. CHART CARD
        chart_card = QFrame(); chart_card.setObjectName("card")
        cc_l = QVBoxLayout(chart_card); cc_l.setContentsMargins(20, 20, 20, 20)
        cc_l.addWidget(QLabel(" 3. METABOLIC PROFILE", objectName="section_title"))
        
        self.img_lbl = QLabel("Chart will appear here after analysis.")
        self.img_lbl.setAlignment(Qt.AlignCenter); self.img_lbl.setMinimumHeight(400)
        self.img_lbl.setStyleSheet("border: 2px dashed #000000; color: #555555; background: #F9F9F9; font-weight: bold;")
        cc_l.addWidget(self.img_lbl)
        self.layout.addWidget(chart_card)

        # 4. DATA TABLE
        table_card = QFrame(); table_card.setObjectName("card")
        tl = QVBoxLayout(table_card); tl.setContentsMargins(20, 20, 20, 20)
        tl.addWidget(QLabel(" 4. DETAILED DATA TABLE", objectName="section_title"))
        
        self.table = QTableWidget(); self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Pathway", "Enzyme Found", "Gene ID", "Full Annotation"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) 
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(350)
        tl.addWidget(self.table)
        self.layout.addWidget(table_card)

        # 5. LOGS
        log_card = QFrame(); log_card.setObjectName("card")
        ll = QVBoxLayout(log_card); ll.setContentsMargins(20, 20, 20, 20)
        ll.addWidget(QLabel(" 5. SYSTEM ACTIVITY LOG", objectName="section_title"))
        self.console = QTextEdit(); self.console.setReadOnly(True); self.console.setMinimumHeight(150)
        ll.addWidget(self.console)
        self.layout.addWidget(log_card)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def log(self, msg):
        self.console.append(f"> {msg}")
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def refresh_files(self):
        self.combo_files.clear()
        annot_dir = os.path.join(os.getcwd(), "results", "annotation")
        if os.path.exists(annot_dir):
            files = [f for f in os.listdir(annot_dir) if f.endswith(('.tsv', '.txt'))]
            if files: self.combo_files.addItems(files)
            else: self.combo_files.addItem("-- No Annotation Files Found --")

    def run_analysis(self):
        filename = self.combo_files.currentText()
        if not filename or "--" in filename:
            self.log("❌ Error: Please select a valid file.")
            return

        filepath = os.path.join(os.getcwd(), "results", "annotation", filename)
        
        self.console.clear(); self.table.setRowCount(0)
        self.btn_run.setEnabled(False); self.btn_run.setText("MINING DATA...")
        
        # DB: Start Log
        if self.db:
            try:
                base = filename.split('.')[0]
                proj = self.db.search_projects(base)
                pid = proj[0]['project_id'] if proj else None
                if pid: self.current_analysis_id = self.db.start_analysis(pid, "pathways")
            except: pass

        self.worker = PathwayWorker(filepath)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, result_img, data_list):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("⚡ RUN MINING & GENERATE CHART")
        
        if success:
            self.log("✅ Analysis Complete.")
            
            # 1. Update Chart
            if os.path.exists(result_img):
                pix = QPixmap(result_img)
                self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.img_lbl.setStyleSheet("border: 2px solid #000000;")
            
            # 2. Update Table
            self.table.setRowCount(len(data_list))
            for row, item in enumerate(data_list):
                self.table.setItem(row, 0, QTableWidgetItem(item['Pathway']))
                
                enz = QTableWidgetItem(item['Enzyme/Keyword'])
                enz.setForeground(QColor("#D32F2F")); enz.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table.setItem(row, 1, enz)
                
                self.table.setItem(row, 2, QTableWidgetItem(str(item['Gene ID / Location'])))
                self.table.setItem(row, 3, QTableWidgetItem(item['Full Annotation']))
            
            # DB: Complete
            if self.db and self.current_analysis_id:
                self.db.complete_analysis(self.current_analysis_id, success=True)
                
        else:
            self.log(f"❌ Analysis Failed.")
            self.img_lbl.setText("Analysis Error")