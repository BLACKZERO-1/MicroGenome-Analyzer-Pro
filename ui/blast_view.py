import sys
import csv
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QComboBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox, QFileDialog, QTabWidget,
    QFrame, QDoubleSpinBox, QSlider, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QColor, QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

from core.blast.blast_engine import BlastEngine

# --- WORKER THREAD ---
class BlastWorker(QThread):
    status_signal = Signal(str)
    finished_signal = Signal(dict)

    def __init__(self, db_manager, text, file, program, db_target):
        super().__init__()
        self.engine = BlastEngine(db_manager)
        self.params = (text, file, program, db_target)

    def run(self):
        text_in, file_path, program, db = self.params
        seqs = self.engine.parse_input(text_in, file_path)
        
        if not seqs:
            self.finished_signal.emit({"status": "error", "message": "No valid sequences found."})
            return

        for item in self.engine.run_blast(seqs, program, db):
            if isinstance(item, str) and item.startswith("STATUS:"):
                self.status_signal.emit(item.replace("STATUS:", ""))
            elif isinstance(item, dict):
                self.finished_signal.emit(item)

# --- MATPLOTLIB CANVAS ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # Force White Background for Charts
        self.fig.patch.set_facecolor('white')
        self.axes.set_facecolor('white')
        super().__init__(self.fig)

# --- MAIN VIEW ---
class BlastView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.results_data = [] 
        self.file_path = None
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # --- PROFESSIONAL STYLESHEET (Fixed Colors) ---
        self.setStyleSheet("""
            QWidget {
                background-color: #F4F7FE;
                color: #333333;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                background-color: white;
                font-weight: bold;
                border: 1px solid #E0E5F2;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #1B2559;
            }
            QPushButton {
                background-color: #FFFFFF; 
                border: 1px solid #D1D9E6; 
                border-radius: 6px; 
                padding: 6px 12px;
                color: #1B2559;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F0F2F5;
                border: 1px solid #B0B8C6;
            }
            QPushButton:pressed {
                background-color: #E1E4E8;
            }
            QTextEdit, QComboBox, QDoubleSpinBox {
                background-color: white;
                border: 1px solid #D1D9E6;
                border-radius: 6px;
                padding: 5px;
                color: #333;
            }
            /* Fix Black Tab Container Issue */
            QTabWidget::pane { 
                border: 1px solid #E0E5F2; 
                background: white; 
                border-radius: 8px; 
            }
            QTabBar::tab {
                background: #E0E5F2; 
                color: #707EAE; 
                padding: 8px 20px;
                border-top-left-radius: 6px; 
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected { 
                background: white; 
                color: #4318FF; 
                border-bottom: 2px solid #4318FF; 
            }
        """)

        self.create_header()
        self.create_workspace()

    def create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: white; border-radius: 10px;")
        
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 20, 0)
        
        lbl = QLabel("🔍 BLAST Identification Hub")
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #1B2559; border: none;")
        
        self.btn_run = QPushButton("⚡ Run Analysis")
        self.btn_run.setFixedSize(160, 40)
        # Primary Action Button Style
        self.btn_run.setStyleSheet("""
            QPushButton { 
                background-color: #4318FF; 
                color: white; 
                font-weight: bold; 
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #3311CC; }
            QPushButton:pressed { background-color: #220099; }
            QPushButton:disabled { background-color: #A0A0A0; }
        """)
        self.btn_run.clicked.connect(self.run_blast)

        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(self.btn_run)
        self.layout.addWidget(header)

    def create_workspace(self):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(0)

        # --- LEFT PANEL: INPUT ---
        left = QWidget()
        l_lay = QVBoxLayout(left)
        l_lay.setContentsMargins(0,0,10,0)
        
        # 1. Input Group
        grp_in = QGroupBox("1. Query Sequences")
        v_in = QVBoxLayout()
        v_in.setSpacing(10)
        
        self.btn_upload = QPushButton("📂 Load Multi-FASTA File")
        self.btn_upload.clicked.connect(self.select_file)
        
        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("color: #A3AED0; font-size: 11px; margin-bottom: 5px; border:none;")
        
        self.txt_seq = QTextEdit()
        self.txt_seq.setPlaceholderText(">Seq1\nATGCGTAGCT...\n>Seq2\nMKVLTAG...")
        self.txt_seq.textChanged.connect(self.auto_detect_type)
        
        v_in.addWidget(self.btn_upload)
        v_in.addWidget(self.lbl_file)
        v_in.addWidget(QLabel("Or Paste Text Below:", styleSheet="font-weight:bold; border:none;"))
        v_in.addWidget(self.txt_seq)
        grp_in.setLayout(v_in)

        # 2. Settings Group
        grp_set = QGroupBox("2. Configuration")
        v_set = QVBoxLayout()
        v_set.setSpacing(10)
        
        self.combo_prog = QComboBox()
        self.combo_prog.addItems(["blastn (Nucleotide)", "blastp (Protein)"])
        
        self.combo_db = QComboBox()
        self.combo_db.addItems(["NCBI nt (Remote)", "NCBI nr (Remote)", "SwissProt (Curated)"])
        
        v_set.addWidget(QLabel("Algorithm:", styleSheet="border:none;"))
        v_set.addWidget(self.combo_prog)
        v_set.addWidget(QLabel("Target Database:", styleSheet="border:none;"))
        v_set.addWidget(self.combo_db)
        grp_set.setLayout(v_set)

        l_lay.addWidget(grp_in, 2)
        l_lay.addWidget(grp_set, 1)

        # --- RIGHT PANEL: RESULTS ---
        right = QWidget()
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(0,0,0,0)
        
        # Status Bar
        top_bar = QHBoxLayout()
        self.lbl_status = QLabel("System Ready")
        self.lbl_status.setStyleSheet("color: #05CD99; font-weight: bold; border:none;")
        
        self.combo_batch = QComboBox()
        self.combo_batch.setPlaceholderText("Select a Query from Batch...")
        self.combo_batch.currentIndexChanged.connect(self.update_hit_view)
        self.combo_batch.setMinimumWidth(250)
        
        top_bar.addWidget(self.lbl_status)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Viewing Result:", styleSheet="font-weight:bold; color:#707EAE; border:none;"))
        top_bar.addWidget(self.combo_batch)
        r_lay.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        
        # TAB 1: ALIGNMENT REPORT
        self.tab_hits = QWidget()
        self.tab_hits.setStyleSheet("background-color: white;")
        t_lay = QVBoxLayout(self.tab_hits)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background: #F4F7FE; border-radius: 6px; padding: 5px;")
        tool_lay = QHBoxLayout(toolbar)
        tool_lay.setContentsMargins(5, 5, 5, 5)
        
        self.spin_ident = QDoubleSpinBox()
        self.spin_ident.setRange(0, 100)
        self.spin_ident.setValue(0)
        self.spin_ident.setSuffix("%")
        self.spin_ident.setFixedWidth(80)
        self.spin_ident.valueChanged.connect(lambda: self.update_hit_view(self.combo_batch.currentIndex()))

        self.btn_export = QPushButton("💾 Export CSV")
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_cons = QPushButton("🧬 Consensus")
        self.btn_cons.clicked.connect(self.show_consensus)
        
        tool_lay.addWidget(QLabel("Filter Identity >", styleSheet="border:none;"))
        tool_lay.addWidget(self.spin_ident)
        tool_lay.addStretch()
        tool_lay.addWidget(self.btn_cons)
        tool_lay.addWidget(self.btn_export)
        t_lay.addWidget(toolbar)
        
        # Hit Map
        self.map_canvas = MplCanvas(self, width=5, height=2, dpi=100)
        t_lay.addWidget(QLabel("<b>Alignment Hit Map</b> (Red > 90% Identity)", styleSheet="color:#2B3674; border:none;"))
        t_lay.addWidget(self.map_canvas)
        
        # Table (FIXED STYLING)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Accession", "Description", "E-Value", "Identity", "Score"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self.open_ncbi_link)
        
        # !!! VITAL: Table Stylesheet to fix Visibility & Hover !!!
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E5F2;
                border: 1px solid #E0E5F2;
                color: #333333;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F0F2F5;
            }
            QTableWidget::item:selected {
                background-color: #E6F0FF; /* Soft Blue Selection */
                color: #4318FF;
            }
            QTableWidget::item:hover {
                background-color: #F8F9FA; /* Very light gray hover - NO BROWN */
            }
            QHeaderView::section {
                background-color: #F4F7FE;
                color: #4318FF;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #E0E5F2;
            }
        """)
        t_lay.addWidget(self.table)
        t_lay.addWidget(QLabel("Double-click row to open NCBI", styleSheet="color:#A3AED0; font-size:11px; font-style:italic; border:none;"))
        
        # TAB 2: TAXONOMY
        self.tab_tax = QWidget()
        self.tab_tax.setStyleSheet("background-color: white;")
        x_lay = QVBoxLayout(self.tab_tax)
        self.tax_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        x_lay.addWidget(QLabel("<b>Species Distribution (Batch Summary)</b>", styleSheet="color:#2B3674; border:none;"))
        x_lay.addWidget(self.tax_canvas)
        
        self.tabs.addTab(self.tab_hits, "🧬 Alignment Report")
        self.tabs.addTab(self.tab_tax, "🌍 Taxonomy Stats")
        
        r_lay.addWidget(self.tabs)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([350, 650])
        self.layout.addWidget(splitter)

    # --- ACTIONS ---
    def select_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open FASTA", "", "FASTA (*.fasta *.fa *.txt)")
        if fname:
            self.file_path = fname
            self.lbl_file.setText(f"Loaded: {fname.split('/')[-1]}")
            self.txt_seq.setDisabled(True) 
            self.txt_seq.setStyleSheet("background-color: #F0F2F5; color: #A3AED0;")

    def auto_detect_type(self):
        txt = self.txt_seq.toPlainText().upper()
        if not txt: return
        protein_chars = set("EFILPQZ")
        if any(c in protein_chars for c in txt if c.isalpha()):
            self.combo_prog.setCurrentIndex(1)
        else:
            self.combo_prog.setCurrentIndex(0)

    def run_blast(self):
        self.btn_run.setEnabled(False)
        self.lbl_status.setText("⏳ Processing Batch...")
        self.lbl_status.setStyleSheet("color: #FFB547; font-weight: bold; border:none;")
        
        self.worker = BlastWorker(
            self.db, self.txt_seq.toPlainText(), self.file_path,
            self.combo_prog.currentText().split()[0], self.combo_db.currentText()
        )
        self.worker.status_signal.connect(self.lbl_status.setText)
        self.worker.finished_signal.connect(self.handle_results)
        self.worker.start()

    def handle_results(self, data):
        self.btn_run.setEnabled(True)
        if data.get("status") == "error":
            QMessageBox.critical(self, "Error", data["message"])
            return
            
        self.results_data = data["results"]
        self.taxonomy_data = data["taxonomy"]
        self.lbl_status.setText("✅ Analysis Complete")
        self.lbl_status.setStyleSheet("color: #05CD99; font-weight: bold; border:none;")
        
        self.combo_batch.clear()
        for i, res in enumerate(self.results_data):
            self.combo_batch.addItem(f"{i+1}. {res['query']} ({len(res['hits'])} hits)")
            
        self.draw_taxonomy_chart()
        if self.results_data: self.update_hit_view(0)

    def update_hit_view(self, index):
        if index < 0 or index >= len(self.results_data): return
        
        result = self.results_data[index]
        min_ident = self.spin_ident.value()
        
        # Filter Hits
        filtered_hits = [h for h in result['hits'] if h['identity_raw'] >= min_ident]
        
        # Update Table
        self.table.setRowCount(0)
        for row, h in enumerate(filtered_hits):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(h['accession']))
            self.table.setItem(row, 1, QTableWidgetItem(h['description']))
            self.table.setItem(row, 2, QTableWidgetItem(h['e_value']))
            self.table.setItem(row, 3, QTableWidgetItem(h['identity']))
            self.table.setItem(row, 4, QTableWidgetItem(str(h['score'])))
            
            # E-Value Traffic Light
            color = QColor("#05CD99") if h['e_value_raw'] < 1e-10 else QColor("#E31A1A")
            self.table.item(row, 2).setForeground(color)
            self.table.item(row, 2).setFont(QFont("Segoe UI", 9, QFont.Bold))

        self.draw_hit_map(filtered_hits)

    def draw_hit_map(self, hits):
        ax = self.map_canvas.axes
        ax.clear()
        if not hits:
            self.map_canvas.draw(); return

        full_len = hits[0]['full_len']
        # Grey Query Bar
        ax.barh(y=10, width=full_len, height=5, left=0, color="#E0E5F2", label="Query")
        
        y_pos = 10
        for i, h in enumerate(hits[:10]): 
            y_pos -= 2.2
            # Blue vs Red colors
            color = "#E31A1A" if h['identity_raw'] > 90 else "#4318FF"
            rect = patches.Rectangle((h['start'], y_pos), h['end']-h['start'], 1.8, color=color)
            ax.add_patch(rect)
            
        ax.set_ylim(y_pos-2, 15)
        ax.set_xlim(0, full_len)
        ax.set_yticks([])
        ax.set_xlabel("Sequence Position (bp)")
        self.map_canvas.draw()

    def draw_taxonomy_chart(self):
        ax = self.tax_canvas.axes
        ax.clear()
        if not self.taxonomy_data: return
        
        labels = list(self.taxonomy_data.keys())
        sizes = list(self.taxonomy_data.values())
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
            pctdistance=0.85, colors=['#4318FF', '#05CD99', '#FFB547', '#E31A1A', '#868CFF']
        )
        centre_circle = matplotlib.patches.Circle((0,0),0.70,fc='white')
        ax.add_artist(centre_circle)
        ax.axis('equal')  
        self.tax_canvas.draw()

    def export_csv(self):
        idx = self.combo_batch.currentIndex()
        if idx == -1: return
        
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "blast_results.csv", "CSV (*.csv)")
        if not path: return
        
        result = self.results_data[idx]
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Accession", "Description", "E-Value", "Identity", "Score"])
            for h in result['hits']:
                writer.writerow([h['accession'], h['description'], h['e_value'], h['identity'], h['score']])
        
        QMessageBox.information(self, "Success", "Data exported successfully.")

    def show_consensus(self):
        idx = self.combo_batch.currentIndex()
        if idx == -1: return
        
        cons = self.results_data[idx].get('consensus', 'N/A')
        
        d = QDialog(self)
        d.setWindowTitle("Consensus Sequence")
        d.resize(500, 300)
        d.setStyleSheet("background-color: white;")
        lay = QVBoxLayout(d)
        txt = QTextEdit()
        txt.setPlainText(cons)
        txt.setReadOnly(True)
        txt.setStyleSheet("background-color: #F4F7FE; border: 1px solid #D1D9E6; font-family: Consolas;")
        lay.addWidget(QLabel("Consensus (Top 5 Hits):", styleSheet="color: #2B3674; font-weight: bold;"))
        lay.addWidget(txt)
        d.exec()

    def open_ncbi_link(self, index):
        row = index.row()
        acc = self.table.item(row, 0).text()
        url = f"https://www.ncbi.nlm.nih.gov/nucleotide/{acc}"
        QDesktopServices.openUrl(QUrl(url))