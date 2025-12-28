import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QListWidget, QProgressBar, 
                               QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

# IMPORT ENGINE
from core.reports.report_engine import ReportWorker

class ReportView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.worker = None
        self.selected_project_id = None
        self.report_path = ""

        # --- STYLESHEET ---
        self.setStyleSheet("""
            QWidget { background-color: #F8F9FC; font-family: 'Segoe UI', sans-serif; }
            QLabel#header { color: #2B3674; font-size: 24px; font-weight: 900; }
            QLabel#subheader { color: #A3AED0; font-size: 13px; font-weight: 500; margin-bottom: 10px; }
            QFrame#card { background-color: #FFFFFF; border: 1px solid #E0E5F2; border-radius: 12px; }
            QListWidget { border: 2px dashed #E0E5F2; border-radius: 6px; padding: 5px; color: #2B3674; font-weight: 600; }
            QPushButton { border-radius: 8px; font-weight: bold; font-size: 13px; padding: 12px; border: none; }
            QPushButton#btn_pdf { background-color: #E04F5F; color: white; }
            QPushButton#btn_pdf:hover { background-color: #C22F3E; }
            QPushButton#btn_refresh { background-color: #E9EDF7; color: #4318FF; }
            QPushButton#btn_open { background-color: #05CD99; color: white; }
            QPushButton#btn_open:disabled { background-color: #A3AED0; }
            QTextEdit { background-color: #111C44; color: #00E676; border-radius: 6px; font-family: Consolas; }
        """)

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(20)

        # 1. HEADER
        h = QHBoxLayout()
        v = QVBoxLayout()
        v.addWidget(QLabel("PROJECT REPORT GENERATOR", objectName="header"))
        v.addWidget(QLabel("Compile Analysis Results into Professional PDF Reports", objectName="subheader"))
        h.addWidget(QLabel("📑", styleSheet="font-size: 40px;")); h.addSpacing(15); h.addLayout(v); h.addStretch()
        main_layout.addLayout(h)

        # 2. SELECTION CARD
        card = QFrame(); card.setObjectName("card")
        l = QVBoxLayout(card); l.setContentsMargins(20, 20, 20, 20)
        
        l.addWidget(QLabel("📂 SELECT PROJECT DATABASE", styleSheet="font-weight:bold; color:#2B3674;"))
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.select_project)
        l.addWidget(self.project_list)
        
        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("↻ Refresh List"); self.btn_refresh.setObjectName("btn_refresh")
        self.btn_refresh.clicked.connect(self.load_projects)
        
        self.btn_pdf = QPushButton("📄 GENERATE PDF REPORT"); self.btn_pdf.setObjectName("btn_pdf")
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.generate_report)

        self.btn_open = QPushButton("📂 OPEN PDF"); self.btn_open.setObjectName("btn_open")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self.open_pdf)
        
        btn_row.addWidget(self.btn_refresh, 1)
        btn_row.addWidget(self.btn_pdf, 2)
        btn_row.addWidget(self.btn_open, 1)
        l.addLayout(btn_row)
        
        self.progress = QProgressBar(); self.progress.setFixedHeight(4); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("border:none; background:#E0E5F2; QProgressBar::chunk { background: #E04F5F; }")
        l.addWidget(self.progress)
        
        main_layout.addWidget(card)

        # 3. LOGS
        log_card = QFrame(); log_card.setObjectName("card")
        ll = QVBoxLayout(log_card); ll.setContentsMargins(20, 20, 20, 20)
        ll.addWidget(QLabel("📝 GENERATION LOGS", styleSheet="font-weight:bold; color:#2B3674;"))
        self.terminal = QTextEdit(); self.terminal.setReadOnly(True)
        ll.addWidget(self.terminal)
        main_layout.addWidget(log_card)

        # Load initial data
        self.load_projects()

    def load_projects(self):
        self.project_list.clear()
        if self.db:
            try:
                projects = self.db.get_all_projects()
                if not projects:
                    self.project_list.addItem("No projects found in database.")
                
                for p in projects:
                    # FIX: Handle dictionary keys safely
                    p_id = p.get('project_id') or p.get('id')
                    p_name = p.get('name') or p.get('project_name') or "Untitled Project"
                    status = p.get('status', 'unknown')
                    
                    status_icon = "✅" if status == 'completed' else "⏳"
                    self.project_list.addItem(f"{status_icon}  {p_name} (ID: {p_id})")
            except Exception as e:
                self.terminal.append(f"> ❌ DB Error: {e}")
        else:
            self.terminal.append("> ⚠️ Database not connected.")

    def select_project(self, item):
        txt = item.text()
        if "No projects" in txt: return
        # Parse ID from string "Name (ID: 1)"
        try:
            pid = int(txt.split("ID: ")[1].replace(")", ""))
            self.selected_project_id = pid
            self.btn_pdf.setEnabled(True)
            self.terminal.append(f"> Selected Project ID: {pid}")
        except: pass

    def generate_report(self):
        if not self.selected_project_id: return
        
        self.terminal.clear(); self.progress.setValue(5)
        self.btn_pdf.setEnabled(False)
        self.btn_open.setEnabled(False)
        
        # Fetch Project Data
        project_data = {}
        if self.db:
            # Fetch basic info
            try:
                # We need to manually execute this if get_project_by_id isn't in manager
                # Or reuse get_all_projects and filter (safer if method missing)
                projects = self.db.get_all_projects()
                target = next((p for p in projects if p.get('project_id') == self.selected_project_id), None)
                
                if target:
                    project_data = dict(target)
                    # FIX: Ensure 'project_name' exists for the PDF engine
                    if 'name' in project_data:
                        project_data['project_name'] = project_data['name']
                
                # Fetch Analysis Results (Annotation)
                a_res = self.db.get_annotation_results(self.selected_project_id)
                if a_res: project_data.update(dict(a_res))
                
            except Exception as e:
                self.terminal.append(f"> Data Fetch Warning: {e}")

        self.worker = ReportWorker(project_data)
        self.worker.log_signal.connect(self.terminal.append)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, pdf_path):
        self.btn_pdf.setEnabled(True)
        if success:
            self.report_path = pdf_path
            self.btn_open.setEnabled(True)
            self.terminal.append(f"> ✅ Report Generated: {pdf_path}")
            QMessageBox.information(self, "Success", f"PDF Report Saved:\n{pdf_path}")
        else:
            self.terminal.append("> ❌ Failed to generate report.")

    def open_pdf(self):
        if self.report_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.report_path))