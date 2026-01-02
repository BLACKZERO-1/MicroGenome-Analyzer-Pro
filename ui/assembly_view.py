import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QFrame, QSplitter, QTextEdit, QProgressBar,
    QComboBox, QSpinBox, QGroupBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal

# Matplotlib Imports
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.assembly.assembly_engine import AssemblyEngine

# --- WORKER THREAD ---
class AssemblyWorker(QThread):
    log_signal = Signal(str)
    status_signal = Signal(str) # For the graphical stepper
    finished_signal = Signal(dict) # Returns results data

    def __init__(self, tool, r1, r2, long_reads, threads, mem, do_trim, do_busco):
        super().__init__()
        self.engine = AssemblyEngine()
        self.params = (tool, r1, r2, long_reads, threads, mem, do_trim, do_busco)

    def run(self):
        # Run Engine
        for line in self.engine.run_assembly(*self.params):
            if line.startswith("STATUS:"):
                self.status_signal.emit(line.replace("STATUS:", ""))
            else:
                self.log_signal.emit(line)
        
        # Get Data for Charts
        results = self.engine.get_results_data()
        self.finished_signal.emit(results)

# --- MATPLOTLIB CANVAS ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

# --- MAIN VIEW ---
class AssemblyView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # Global Button Stylesheet
        self.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0; 
                border: 1px solid #CCCCCC; 
                border-radius: 6px; 
                padding: 6px 12px;
                color: #333333;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E0E0E0; 
                border: 1px solid #AAAAAA;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
                border: 1px solid #999999;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DDD;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        self.create_header()
        self.create_progress_stepper() 
        self.create_workspace()

    def create_header(self):
        header = QFrame()
        header.setStyleSheet("""
            QFrame { 
                background: white; 
                border-bottom: 2px solid #F0F2F5; 
            }
        """)
        header.setFixedHeight(70)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(10, 0, 10, 0)
        
        lbl = QLabel("🧬 Genome Assembly Lab")
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #1B2559;")
        
        self.btn_run = QPushButton("🚀 Run Pipeline")
        self.btn_run.setFixedSize(160, 40)
        # Override default style for the Primary Action Button
        self.btn_run.setStyleSheet("""
            QPushButton { 
                background-color: #27AE60; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px; 
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #219150; }
            QPushButton:pressed { background-color: #196F3D; }
            QPushButton:disabled { background-color: #AAB7B8; color: #F0F3F4; }
        """)
        self.btn_run.clicked.connect(self.start_assembly)

        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(self.btn_run)
        self.layout.addWidget(header)

    def create_progress_stepper(self):
        """Creates the 'Cleaning -> Assembly -> QC' visual bar"""
        self.step_frame = QFrame()
        self.step_frame.setFixedHeight(60)
        self.step_frame.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #E0E5F2;")
        lay = QHBoxLayout(self.step_frame)
        lay.setContentsMargins(20, 0, 20, 0)
        
        self.steps = {}
        step_names = ["Initializing", "Auto-Cleaning", "Constructing Graph", "Polishing"]
        
        for i, name in enumerate(step_names):
            lbl = QLabel(f"○  {name}")
            lbl.setStyleSheet("color: #A3AED0; font-weight: 600; font-size: 13px;")
            lay.addWidget(lbl)
            if i < len(step_names) - 1:
                lay.addStretch() # Space them out evenly
            self.steps[name] = lbl
            
        self.layout.addWidget(self.step_frame)

    def update_stepper(self, active_text):
        """Highlights the current step in the visual bar"""
        # Reset all
        for lbl in self.steps.values():
            lbl.setStyleSheet("color: #A3AED0; font-weight: 600;")
            if "●" in lbl.text(): 
                lbl.setText(lbl.text().replace("●", "○"))

        # Find best match
        for key, lbl in self.steps.items():
            if key.split()[0] in active_text: 
                # Highlight Color: Blue (#4318FF)
                lbl.setStyleSheet("color: #4318FF; font-weight: 800; font-size: 14px;")
                lbl.setText(lbl.text().replace("○", "●"))

    def create_workspace(self):
        splitter = QSplitter(Qt.Horizontal)

        # --- LEFT PANEL: INPUTS ---
        left_panel = QWidget()
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 10, 0)
        
        # 1. Inputs Group
        grp_input = QGroupBox("1. Input Data")
        form_input = QFormLayout()
        form_input.setVerticalSpacing(15)
        
        self.btn_r1 = QPushButton("Select Forward Reads (R1)...")
        self.btn_r2 = QPushButton("Select Reverse Reads (R2)...")
        
        # Connect
        self.btn_r1.clicked.connect(lambda: self.select_file('r1'))
        self.btn_r2.clicked.connect(lambda: self.select_file('r2'))
        
        form_input.addRow("Forward (FASTQ):", self.btn_r1)
        form_input.addRow("Reverse (FASTQ):", self.btn_r2)
        grp_input.setLayout(form_input)

        # 2. Options Group
        grp_opts = QGroupBox("2. Configuration")
        form_opts = QFormLayout()
        form_opts.setVerticalSpacing(15)
        
        self.combo_tool = QComboBox()
        self.combo_tool.addItems(["spades", "unicycler", "flye"])
        self.combo_tool.setStyleSheet("padding: 5px; border: 1px solid #CCC; border-radius: 4px;")
        
        self.chk_trim = QCheckBox("Auto-Clean Reads (FastP)")
        self.chk_trim.setChecked(True)
        self.chk_trim.setStyleSheet("color: #333; font-size: 13px;")
        
        self.chk_busco = QCheckBox("Check Completeness (BUSCO)")
        self.chk_busco.setChecked(True)
        self.chk_busco.setStyleSheet("color: #333; font-size: 13px;")
        
        form_opts.addRow("Assembler Tool:", self.combo_tool)
        form_opts.addRow(self.chk_trim)
        form_opts.addRow(self.chk_busco)
        grp_opts.setLayout(form_opts)

        left_lay.addWidget(grp_input)
        left_lay.addWidget(grp_opts)
        left_lay.addStretch()

        # --- RIGHT PANEL: TABS ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E0E5F2; background: white; border-radius: 4px; }
            QTabBar::tab {
                background: #F4F7FE; color: #707EAE; padding: 10px 20px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
                font-weight: bold; margin-right: 2px;
            }
            QTabBar::tab:selected { background: white; color: #4318FF; border-bottom: 2px solid #4318FF; }
        """)
        
        # Tab 1: Terminal
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background: #111827; color: #4ADE80; font-family: Consolas; font-size: 12px; border: none;")
        self.tabs.addTab(self.terminal, "🖥️ Live Console")
        
        # Tab 2: Visual Results
        self.results_tab = QWidget()
        self.results_tab.setStyleSheet("background: white;")
        res_lay = QVBoxLayout(self.results_tab)
        
        # Stats Table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(180)
        self.table.setSelectionMode(QTableWidget.NoSelection) # Disable selection highlighting
        
        # FIX: Explicitly set item styles and hover styles to prevent brown color
        self.table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #E0E5F2; 
                gridline-color: #F0F2F5; 
                background-color: white;
                color: #333333;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F0F2F5;
            }
            /* FORCE HOVER TO STAY WHITE */
            QTableWidget::item:hover {
                background-color: white;
                color: #333333;
            }
            QHeaderView::section { 
                background-color: #F4F7FE; 
                color: #1B2559; 
                padding: 8px; 
                font-weight: bold; 
                border: none;
            }
        """)
        res_lay.addWidget(self.table)
        
        # N50 Chart Label
        lbl_chart = QLabel("N50 Cumulative Curve")
        lbl_chart.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px; color: #1B2559;")
        res_lay.addWidget(lbl_chart)

        # Chart
        self.chart = MplCanvas(self, width=5, height=4, dpi=100)
        res_lay.addWidget(self.chart)
        
        self.tabs.addTab(self.results_tab, "📊 Analysis Report")
        
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tabs)
        splitter.setSizes([350, 650])
        self.layout.addWidget(splitter)

        # Variables
        self.path_r1 = ""
        self.path_r2 = ""

    def select_file(self, ftype):
        fname, _ = QFileDialog.getOpenFileName(self, "Select FASTQ", "", "FASTQ (*.fastq *.gz)")
        if fname:
            short_name = "..." + fname[-25:] if len(fname) > 25 else fname
            if ftype == 'r1': 
                self.path_r1 = fname
                self.btn_r1.setText(f"📄 {short_name}")
                self.btn_r1.setStyleSheet("text-align: left; padding-left: 10px; background-color: #E8F5E9; border: 1px solid #27AE60; color: #27AE60;")
            elif ftype == 'r2': 
                self.path_r2 = fname
                self.btn_r2.setText(f"📄 {short_name}")
                self.btn_r2.setStyleSheet("text-align: left; padding-left: 10px; background-color: #E8F5E9; border: 1px solid #27AE60; color: #27AE60;")

    def start_assembly(self):
        self.terminal.clear()
        self.tabs.setCurrentIndex(0) # Switch to log
        self.btn_run.setEnabled(False)
        self.btn_run.setText("⏳ Running...")
        
        self.worker = AssemblyWorker(
            self.combo_tool.currentText(), self.path_r1, self.path_r2, None,
            4, 8, self.chk_trim.isChecked(), self.chk_busco.isChecked()
        )
        self.worker.log_signal.connect(self.terminal.append)
        self.worker.status_signal.connect(self.update_stepper)
        self.worker.finished_signal.connect(self.show_results)
        self.worker.start()

    def show_results(self, data):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("🚀 Run Pipeline")
        self.tabs.setCurrentIndex(1) # Switch to charts
        
        # 1. Update Table
        self.table.setRowCount(0)
        metrics = [
            ("N50 Length", f"{data['n50']:,} bp"),
            ("Total Size", f"{data['total_len']:,} bp"),
            ("Contig Count", str(data['count'])),
            ("GC Content", f"{data['gc']}%"),
            ("Completeness (BUSCO)", data['busco'])
        ]
        for k, v in metrics:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(k))
            self.table.setItem(row, 1, QTableWidgetItem(v))

        # 2. Draw N50 Chart
        ax = self.chart.axes
        ax.clear()
        
        # Draw Curve
        ax.plot(data['plot_data'], color="#4318FF", linewidth=2.5, label="Cumulative Length")
        
        # Fill Area
        ax.fill_between(range(len(data['plot_data'])), data['plot_data'], color="#4318FF", alpha=0.1)
        
        # Styling
        ax.set_title("") # Title is handled by QLabel above
        ax.set_xlabel("Contig Index (Sorted)", fontsize=9)
        ax.set_ylabel("Cumulative Length (bp)", fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc="lower right")
        
        self.chart.draw()