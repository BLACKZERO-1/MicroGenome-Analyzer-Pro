import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QScrollArea)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QPixmap

# IMPORT YOUR WORKER
# Ensure your backend file is named 'annotation_worker.py' inside 'core/annotation/'
from core.annotation.annotation_engine import AnnotationWorker

# ==============================================================================
# 1. WIDGET: CIRCULAR PLOT VIEWER
# ==============================================================================
class CircularPlotWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(450)  # Large square area
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            border: 2px dashed #E0E5F2; 
            border-radius: 12px; 
            background: white;
            color: #A3AED0;
            font-weight: 700;
        """)
        self.setText("Circular Genome Map will appear here...")
    
    def update_image(self, image_path):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            self.setStyleSheet("border: 1px solid #E0E5F2; border-radius: 12px; background: white;")
        else:
            self.setText("❌ Plot File Not Found")
            self.setStyleSheet("border: 2px dashed #FF5252; color: #FF5252;")

# ==============================================================================
# 2. WIDGET: LINEAR GENOME MAP
# ==============================================================================
class GenomeMapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(120)
        self.genes = []      
        self.genome_len = 1  
        self.setStyleSheet("background: transparent;")

    def update_map(self, gff_file, total_length):
        self.genes = []
        self.genome_len = max(1, total_length)
        if os.path.exists(gff_file):
            with open(gff_file, 'r') as f:
                for line in f:
                    if "\tCDS\t" in line:
                        cols = line.split("\t")
                        if len(cols) > 4:
                            try:
                                start = int(cols[3])
                                end = int(cols[4])
                                self.genes.append((start, end))
                            except: pass
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        
        # DNA Backbone
        y_center = h / 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#E0E5F2")))
        painter.drawRoundedRect(0, y_center - 8, w, 16, 8, 8)
        
        # Genes
        if self.genes:
            scale = w / self.genome_len
            painter.setBrush(QBrush(QColor("#4318FF"))) 
            for start, end in self.genes:
                x = start * scale
                gene_w = max(3, (end - start) * scale)
                painter.drawRect(QRectF(x, y_center - 15, gene_w, 30))
        else:
            painter.setPen(QColor("#A3AED0"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Waiting for Analysis Results...")

# ==============================================================================
# 3. WIDGET: HISTOGRAM
# ==============================================================================
class GeneHistogramWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(200)
        self.lengths = []
        self.setStyleSheet("background: transparent;")

    def update_data(self, gff_file):
        self.lengths = []
        if os.path.exists(gff_file):
            with open(gff_file, 'r') as f:
                for line in f:
                    if "\tCDS\t" in line:
                        cols = line.split("\t")
                        if len(cols) > 4:
                            try:
                                l = int(cols[4]) - int(cols[3])
                                self.lengths.append(l)
                            except: pass
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        painter.setPen(QPen(QColor("#E0E5F2"), 1, Qt.DashLine))
        painter.drawLine(0, h-30, w, h-30)
        painter.drawLine(0, h/2, w, h/2)
        
        if not self.lengths:
            painter.setPen(QColor("#A3AED0"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data Available")
            return

        bins = [0] * 25
        max_len = 3000
        for l in self.lengths:
            idx = min(24, int(l / (max_len/25)))
            bins[idx] += 1
        
        max_count = max(bins) if bins else 1
        bar_w = (w / 25) - 6
        
        painter.setBrush(QBrush(QColor("#05CD99"))) 
        painter.setPen(Qt.NoPen)

        for i, count in enumerate(bins):
            bar_h = (count / max_count) * (h - 60)
            x = (i * (w/25)) + 3
            y = h - 30 - bar_h
            painter.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)

# ==============================================================================
# 4. MAIN DASHBOARD VIEW
# ==============================================================================
class AnnotationView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None 

        # --- STYLESHEET ---
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            QLabel#main_title { color: #2B3674; font-size: 26px; font-weight: 900; }
            QLabel#sub_title { color: #A3AED0; font-size: 14px; font-weight: 500; }
            
            QFrame#panel_box { 
                background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E0E5F2; 
            }
            QLabel#panel_title { 
                color: #2B3674; font-size: 14px; font-weight: 800; text-transform: uppercase;
                border-bottom: 2px solid #F0F0F0; padding-bottom: 15px; margin-bottom: 15px;
            }
            QLabel#chart_label { color: #A3AED0; font-size: 12px; font-weight: 700; margin-top: 10px; }
            
            QLabel#path_display { 
                background-color: #F8F9FC; color: #707EAE; font-size: 13px; border-radius: 8px; 
                padding-left: 15px; border: 1px solid #E0E5F2; 
            }
            QLabel#path_display[active="true"] { 
                background-color: #F0FDF4; color: #059669; border: 1px solid #059669; font-weight: 600;
            }
            
            QPushButton { border-radius: 8px; font-weight: 600; font-size: 13px; border: none; }
            QPushButton#btn_browse { background-color: #E9EDF7; color: #4318FF; }
            QPushButton#btn_browse:hover { background-color: #DCE4F5; }
            QPushButton#btn_run { background: #4318FF; color: white; font-size: 14px; font-weight: 700; }
            QPushButton#btn_run:hover { background: #3311CC; }
            
            QTextEdit#terminal { 
                background-color: #111C44; color: #00E676; font-family: 'Consolas', monospace; 
                border-radius: 8px; padding: 20px; border: none; 
            }
            QFrame#stat_card { background: #F8F9FC; border-radius: 12px; border: 1px solid #E0E5F2; }
            QLabel#stat_val { font-size: 26px; font-weight: 900; color: #2B3674; }
        """)

        # --- LAYOUT SETUP ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.content_widget = QWidget()
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(25)

        # --- BUILD SECTIONS ---
        self.setup_header()
        self.setup_controls()
        self.setup_metrics() # Updated with new tools!
        self.setup_visuals()
        self.setup_logs()

        self.layout.addStretch()
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)

    def setup_header(self):
        h = QHBoxLayout()
        icon = QLabel("🧬"); icon.setStyleSheet("font-size: 40px; background: transparent;")
        v = QVBoxLayout(); v.setSpacing(4)
        t1 = QLabel("Genome Annotation Engine"); t1.setObjectName("main_title")
        t2 = QLabel("Prodigal + DIAMOND + BLAST Pipeline"); t2.setObjectName("sub_title")
        v.addWidget(t1); v.addWidget(t2)
        h.addWidget(icon); h.addSpacing(20); h.addLayout(v); h.addStretch()
        self.layout.addLayout(h)

    def setup_controls(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(25, 25, 25, 25)
        l.addWidget(QLabel("📂  INPUT CONFIGURATION", objectName="panel_title", alignment=Qt.AlignCenter))

        row = QHBoxLayout()
        self.path_lbl = QLabel("  No Input File Selected"); self.path_lbl.setObjectName("path_display")
        self.path_lbl.setFixedHeight(45)
        btn_browse = QPushButton("Browse File"); btn_browse.setObjectName("btn_browse")
        btn_browse.setFixedSize(140, 45)
        btn_browse.clicked.connect(self.select_file)
        row.addWidget(self.path_lbl); row.addSpacing(15); row.addWidget(btn_browse)
        l.addLayout(row)
        l.addSpacing(15)

        self.btn_run = QPushButton("START ANALYSIS PIPELINE"); self.btn_run.setObjectName("btn_run")
        self.btn_run.setFixedHeight(55)
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_process)
        l.addWidget(self.btn_run)
        
        self.progress = QProgressBar(); self.progress.setFixedHeight(4); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("background: transparent; border: none; QProgressBar::chunk { background: #4318FF; }")
        l.addWidget(self.progress)
        self.layout.addWidget(panel)

    def setup_metrics(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(25, 25, 25, 25)
        l.addWidget(QLabel("📊  ANALYSIS RESULTS", objectName="panel_title", alignment=Qt.AlignCenter))

        # Row 1: Core Metrics
        row1 = QHBoxLayout(); row1.setSpacing(20)
        self.gc_card, self.gc_val = self.create_card("GC Content", "0%", "#4318FF")
        self.gene_card, self.gene_val = self.create_card("Genes Detected", "0", "#05CD99")
        self.anno_card, self.anno_val = self.create_card("Proteins Annotated", "0", "#FFAB00")
        row1.addWidget(self.gc_card); row1.addWidget(self.gene_card); row1.addWidget(self.anno_card)
        
        # Row 2: Advanced Metrics (NEW TOOLS)
        row2 = QHBoxLayout(); row2.setSpacing(20)
        self.domain_card, self.domain_val = self.create_card("Functional Domains (RPS-BLAST)", "0", "#E04F5F")
        self.rna_card, self.rna_val = self.create_card("Special Genes (rRNA/tRNA)", "0", "#3EACFF")
        row2.addWidget(self.domain_card); row2.addWidget(self.rna_card)

        l.addLayout(row1)
        l.addSpacing(15)
        l.addLayout(row2)
        
        self.layout.addWidget(panel)

    def setup_visuals(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(25, 25, 25, 25); l.setSpacing(10)
        l.addWidget(QLabel("🧬  GENOME VISUALIZATION", objectName="panel_title", alignment=Qt.AlignCenter))

        # 1. Circular Plot
        l.addWidget(QLabel("CIRCULAR GENOME MAP", objectName="chart_label"))
        self.circular_plot = CircularPlotWidget()
        l.addWidget(self.circular_plot)
        l.addSpacing(20)

        # 2. Linear Map
        l.addWidget(QLabel("LINEAR GENOME BROWSER", objectName="chart_label"))
        self.genome_map = GenomeMapWidget()
        l.addWidget(self.genome_map)
        l.addSpacing(20)

        # 3. Histogram
        l.addWidget(QLabel("GENE LENGTH DISTRIBUTION (BP)", objectName="chart_label"))
        self.histogram = GeneHistogramWidget()
        l.addWidget(self.histogram)
        
        self.layout.addWidget(panel)

    def setup_logs(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(25, 25, 25, 25)
        l.addWidget(QLabel("📝  EXECUTION LOGS", objectName="panel_title", alignment=Qt.AlignCenter))

        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        self.terminal.setPlaceholderText("System Ready...")
        self.terminal.setMinimumHeight(200)
        l.addWidget(self.terminal)
        self.layout.addWidget(panel)

    def create_card(self, title, default, color):
        card = QFrame(); card.setObjectName("stat_card")
        l = QVBoxLayout(card); l.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel(title); lbl.setStyleSheet("color: #A3AED0; font-size: 12px; font-weight: 700;")
        val = QLabel(default); val.setObjectName("stat_val"); val.setStyleSheet(f"color: {color};")
        l.addWidget(lbl); l.addWidget(val)
        return card, val

    # --- LOGIC ---

    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Genome", "", "FASTA Files (*.fasta *.fa *.fna)")
        if f:
            self.path_lbl.setText(f"  📄 {f}")
            self.path_lbl.setProperty("active", True)
            self.path_lbl.style().unpolish(self.path_lbl); self.path_lbl.style().polish(self.path_lbl)
            self.btn_run.setEnabled(True)
            self.log(f"Input source loaded: {f}")

    def log(self, msg):
        self.terminal.append(f"> {msg}")
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())

    def run_process(self):
        raw_path = self.path_lbl.text().replace("  📄 ", "").strip()
        self.terminal.clear(); self.progress.setValue(0); self.btn_run.setEnabled(False)
        
        # Reset Stats
        self.gc_val.setText("0%")
        self.gene_val.setText("0")
        self.anno_val.setText("0")
        self.domain_val.setText("0")
        self.rna_val.setText("0")
        
        # Reset Widgets
        self.circular_plot.setText("Generating Plot..."); self.circular_plot.setPixmap(QPixmap())
        self.genome_map.genes = []; self.genome_map.repaint()
        self.histogram.lengths = []; self.histogram.repaint()
        
        self.log("Initializing Worker Thread...")
        self.worker = AnnotationWorker(raw_path)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.stats_signal.connect(self.update_stats)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_stats(self, data):
        # Update Core Metrics
        self.gc_val.setText(f"{data.get('gc', 0):.2f}%")
        self.gene_val.setText(f"{data.get('genes', 0):,}")
        self.anno_val.setText(f"{data.get('annotated', 0):,}")
        
        # Update NEW Metrics (Domains & RNA)
        self.domain_val.setText(f"{data.get('domains', 0):,}")
        self.rna_val.setText(f"{data.get('rna', 0):,}")

    def on_finished(self, success, msg):
        self.btn_run.setEnabled(True)
        if success:
            self.log("--- PIPELINE FINISHED SUCCESSFULLY ---")
            raw_path = self.path_lbl.text().replace("  📄 ", "").strip()
            base_name = os.path.basename(raw_path).split('.')[0]
            
            # Paths
            results_dir = os.path.join(os.getcwd(), "results", "annotation")
            gff_path = os.path.join(results_dir, f"{base_name}.gff")
            png_path = os.path.join(results_dir, "genome_circle.png")
            
            # Update Visuals
            self.log("📊 Loading Visualizations...")
            total_len = os.path.getsize(raw_path)
            
            self.genome_map.update_map(gff_path, total_len)
            self.histogram.update_data(gff_path)
            self.circular_plot.update_image(png_path)
            
        else:
            self.log(f"ERROR: {msg}")