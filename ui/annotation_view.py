import os
import csv
from collections import Counter
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QScrollArea, QMessageBox, QTabWidget,
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QLineEdit, QSplitter)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QPixmap, QFont

# IMPORT ENGINES
from core.annotation.annotation_engine import AnnotationWorker
from core.online.remote_blast import RemoteBlastWorker

# ==============================================================================
# 🎨 CUSTOM VISUALIZATION WIDGETS
# ==============================================================================

class ChartWidget(QWidget):
    """Base class for custom painted charts"""
    def __init__(self, title):
        super().__init__()
        self.setFixedHeight(250)
        self.title = title
        self.data = []  # Generic data holder
        self.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #2B3674;")

    def paint_header(self, painter, w):
        painter.setPen(QColor("#2B3674"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(15, 25, self.title)
        painter.setPen(QColor("#E0E5F2"))
        painter.drawLine(0, 35, w, 35)

class HistogramWidget(ChartWidget):
    """Visualizes Gene Length Distribution (Test 1)"""
    def update_data(self, lengths):
        self.data = lengths
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Background & Header
        painter.setBrush(QColor("white")); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 8, 8)
        self.paint_header(painter, w)

        if not self.data:
            painter.setPen(QColor("#A3AED0")); painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        # Binning
        bins = [0] * 20
        max_len = 3000
        for l in self.data:
            idx = min(19, int(l / (max_len/20)))
            bins[idx] += 1
            
        max_count = max(bins) if bins else 1
        bar_w = (w - 40) / 20
        
        # Draw Bars
        painter.setBrush(QColor("#4318FF"))
        for i, count in enumerate(bins):
            bar_h = (count / max_count) * (h - 60)
            x = 20 + (i * bar_w)
            y = h - 20 - bar_h
            painter.drawRect(int(x), int(y), int(bar_w - 2), int(bar_h))

class BarChartWidget(ChartWidget):
    """Visualizes Top Categories (Test 2 & 3)"""
    def update_data(self, labeled_counts):
        # Expected: [('Name', count), ...]
        self.data = labeled_counts[:8] # Top 8
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        painter.setBrush(QColor("white")); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 8, 8)
        self.paint_header(painter, w)

        if not self.data:
            painter.setPen(QColor("#A3AED0")); painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        max_val = self.data[0][1] if self.data else 1
        row_h = (h - 50) / 8
        
        for i, (name, count) in enumerate(self.data):
            y = 45 + (i * row_h)
            bar_w = (count / max_val) * (w - 180)
            
            # Label
            painter.setPen(QColor("#2B3674"))
            painter.drawText(10, int(y), 150, int(row_h), Qt.AlignVCenter | Qt.AlignRight, name[:25])
            
            # Bar
            painter.setBrush(QColor("#05CD99"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(170, int(y+5), int(bar_w), int(row_h-10), 4, 4)
            
            # Value
            painter.setPen(QColor("#A3AED0"))
            painter.drawText(int(170 + bar_w + 10), int(y), 50, int(row_h), Qt.AlignVCenter, str(count))

class GenomeMapWidget(QWidget):
    """Linear Genome Browser (Test 5)"""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(120)
        self.genes = []      
        self.genome_len = 1  
        self.setStyleSheet("background: white; border: 1px solid #2B3674; border-radius: 8px;")

    def update_map(self, genes_list, total_len):
        self.genes = genes_list
        self.genome_len = max(1, total_len)
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Track line
        y_center = h / 2
        painter.setPen(QPen(QColor("#E0E5F2"), 2))
        painter.drawLine(10, int(y_center), w-10, int(y_center))
        
        if not self.genes:
            painter.drawText(self.rect(), Qt.AlignCenter, "Waiting for Genome Data...")
            return
            
        # Draw Genes
        scale = (w - 20) / self.genome_len
        painter.setPen(QPen(QColor("black"), 1))
        
        for g in self.genes:
            # g = {'start': int, 'end': int, 'strand': str}
            x = 10 + (g['start'] * scale)
            gw = max(2, (g['end'] - g['start']) * scale)
            
            if g['strand'] == '+':
                painter.setBrush(QColor("#4318FF"))
                y = y_center - 20
            else:
                painter.setBrush(QColor("#E04F5F")) # Red for reverse
                y = y_center + 5
                
            painter.drawRect(int(x), int(y), int(gw), 15)

# ==============================================================================
# 🧩 REUSABLE RESULT TAB (Table + Text Report)
# ==============================================================================
class ResultTab(QWidget):
    def __init__(self, headers):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Splitter for Visual/Table vs Text Report
        splitter = QSplitter(Qt.Vertical)
        
        # TOP: Visualization Container
        self.visual_container = QWidget()
        self.visual_layout = QVBoxLayout(self.visual_container)
        self.visual_layout.setContentsMargins(0,0,0,0)
        splitter.addWidget(self.visual_container)
        
        # MIDDLE: Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # --- FIXED TABLE STYLING: Always Visible Grid & Headers ---
        self.table.setRowCount(50) # Show 50 empty rows by default so grid is visible
        self.table.setShowGrid(True)  # CRITICAL: Force grid
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                color: #000000; 
                gridline-color: #9E9E9E; /* VISIBLE GREY GRID */
                border: 2px solid #2B3674;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QTableWidget::item { 
                color: #000000; 
                padding: 5px;
                border-bottom: 1px solid #E0E0E0;
            }
            
            /* --- FIX: REMOVE HOVER COLOR --- */
            QTableWidget::item:hover {
                background-color: transparent;
                color: #000000;
            }
            
            QHeaderView::section { 
                background-color: #2B3674; /* Dark Blue Header */
                color: #FFFFFF;            /* White Text */
                font-weight: bold; 
                font-size: 13px;
                border: 1px solid #FFFFFF;
                padding: 6px;
                min-height: 30px;          /* FORCE HEADER HEIGHT */
            }
            QTableWidget::item:selected {
                background-color: #4318FF;
                color: #FFFFFF;
            }
        """)
        splitter.addWidget(self.table)
        
        # BOTTOM: Text Report
        self.report_box = QTextEdit()
        self.report_box.setReadOnly(True)
        self.report_box.setMaximumHeight(100)
        self.report_box.setStyleSheet("""
            background: #F9FAFB; 
            color: #1B2559; 
            font-family: Consolas; 
            border: 2px solid #2B3674;
            padding: 5px;
        """)
        splitter.addWidget(self.report_box)
        
        layout.addWidget(splitter)
        
    def set_visual(self, widget):
        self.visual_layout.addWidget(widget)

    def set_report(self, text):
        self.report_box.setHtml(f"<div style='padding:10px;'><b>ANALYSIS REPORT:</b><br>{text}</div>")
    
    def load_safe_data(self, rows):
        self.table.setRowCount(0) # Clear dummy rows
        
        MAX_ROWS = 500
        total = len(rows)
        display_rows = rows[:MAX_ROWS]
        
        self.table.setRowCount(len(display_rows))
        for i, row_data in enumerate(display_rows):
            for j, val in enumerate(row_data):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        
        if total == 0:
            self.table.setRowCount(50)

# ==============================================================================
# 🚀 MAIN ANNOTATION VIEW
# ==============================================================================
class AnnotationView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.worker = None
        self.remote_worker = None # For Online Check
        self.current_project_id = None
        self.full_file_path = None
        
        # --- STYLES ---
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: 2px solid #2B3674; background: white; border-radius: 8px; }
            QTabBar::tab { background: #E9EDF7; color: #2B3674; padding: 10px 20px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; border: 1px solid #D0D7DE; }
            QTabBar::tab:selected { background: #4318FF; color: white; border: 1px solid #4318FF; }
            QPushButton { border-radius: 6px; padding: 8px 15px; font-weight: bold; font-size: 13px; }
            QPushButton:disabled { background: #A3AED0; color: #F4F7FE; border: none; }
        """)

        layout = QVBoxLayout(self)
        
        # 1. HEADER & CONTROLS
        self.setup_header(layout)
        
        # 2. MAIN TABS
        self.tabs = QTabWidget()
        
        # --- TAB 1: GENE PREDICTION ---
        self.tab_genes = ResultTab(["Gene ID", "Start", "End", "Strand", "Length (bp)"])
        self.hist_widget = HistogramWidget("Gene Length Distribution")
        self.tab_genes.set_visual(self.hist_widget)
        self.tabs.addTab(self.tab_genes, "1. Genes (Prodigal)")
        
        # --- TAB 2: ANNOTATION ---
        self.tab_anno = ResultTab(["Gene ID", "Product / Function", "Identity (%)", "E-Value"])
        self.func_chart = BarChartWidget("Top Gene Functions")
        self.tab_anno.set_visual(self.func_chart)
        self.tabs.addTab(self.tab_anno, "2. Annotation (DIAMOND)")
        
        # --- TAB 3: DOMAINS ---
        self.tab_domains = ResultTab(["Query ID", "Pfam Domain", "Identity (%)", "E-Value"])
        self.domain_chart = BarChartWidget("Top Functional Domains")
        self.tab_domains.set_visual(self.domain_chart)
        self.tabs.addTab(self.tab_domains, "3. Domains (RPS-BLAST)")
        
        # --- TAB 4: SPECIAL GENES ---
        self.tab_rna = ResultTab(["Type", "Match ID", "Identity (%)", "Length"])
        self.rna_visual = QLabel("No RNA Data"); self.rna_visual.setAlignment(Qt.AlignCenter)
        self.rna_visual.setStyleSheet("font-size: 18px; color: #2B3674; font-weight: bold; padding: 20px; border: 2px dashed #2B3674; border-radius: 8px;")
        self.tab_rna.set_visual(self.rna_visual)
        self.tabs.addTab(self.tab_rna, "4. Special Genes (RNA)")
        
        # --- TAB 5: VISUALIZATION ---
        self.tab_vis = QWidget()
        vis_layout = QVBoxLayout(self.tab_vis)
        self.linear_map = GenomeMapWidget()
        self.circular_plot = QLabel(); self.circular_plot.setAlignment(Qt.AlignCenter)
        self.circular_plot.setStyleSheet("border: 2px solid #2B3674; border-radius: 12px; background: white;")
        self.circular_plot.setMinimumHeight(350)
        vis_layout.addWidget(QLabel("Linear Genome Browser", styleSheet="font-weight:bold; color:#2B3674;"))
        vis_layout.addWidget(self.linear_map)
        vis_layout.addWidget(QLabel("Circular Genome Map", styleSheet="font-weight:bold; color:#2B3674; margin-top:10px;"))
        vis_layout.addWidget(self.circular_plot)
        self.tabs.addTab(self.tab_vis, "5. Genome Map")
        
        layout.addWidget(self.tabs)
        
        # 3. LOGGING
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True); self.terminal.setMaximumHeight(80)
        self.terminal.setStyleSheet("background: #111C44; color: #00E676; font-family: Consolas; border: 2px solid #2B3674; border-radius: 6px;")
        layout.addWidget(self.terminal)

    def setup_header(self, layout):
        container = QFrame()
        container.setStyleSheet("background: white; border-radius: 12px; border: 2px solid #2B3674;")
        l = QHBoxLayout(container)
        
        l.addWidget(QLabel("🧬 <b>Genome Annotation Pipeline</b>", styleSheet="font-size: 16px; color: #2B3674; border:none;"))
        
        self.path_lbl = QLabel("No File Selected"); self.path_lbl.setStyleSheet("color: #707EAE; margin-left: 20px; border:none;")
        l.addWidget(self.path_lbl)
        
        l.addStretch()
        
        # NEW ONLINE BUTTON
        self.btn_online = QPushButton("🌍 Verify Selected (NCBI)")
        self.btn_online.setStyleSheet("""
            background-color: #2ECC71; color: white; border: 2px solid #27AE60; padding: 8px 15px;
        """)
        self.btn_online.setEnabled(False) # Enabled only after run
        self.btn_online.clicked.connect(self.run_online_verification)
        l.addWidget(self.btn_online)

        # SELECT FILE
        btn_browse = QPushButton("📂 Select FASTA")
        btn_browse.setStyleSheet("""
            background-color: #E9EDF7; color: #4318FF; border: 2px solid #D0D7DE; padding: 8px 15px;
        """)
        btn_browse.clicked.connect(self.select_file)
        l.addWidget(btn_browse)
        
        # RUN
        self.btn_run = QPushButton("▶ Run Analysis")
        self.btn_run.setStyleSheet("""
            background-color: #4318FF; color: #FFFFFF; border: 2px solid #2B3674; padding: 8px 15px;
        """)
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_process)
        l.addWidget(self.btn_run)
        
        layout.addWidget(container)

    # --- LOGIC ---

    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Genome", "", "FASTA (*.fasta *.fa *.fna)")
        if f:
            self.full_file_path = f
            self.path_lbl.setText(os.path.basename(f))
            self.btn_run.setEnabled(True)
            self.btn_run.setStyleSheet("background-color: #4318FF; color: white; border: 2px solid #2B3674;")
            self.terminal.append(f"> File Selected: {f}")
            if self.db:
                try:
                    existing = self.db.get_project_by_path(f)
                    if existing: self.current_project_id = existing['project_id']
                    else: self.current_project_id = self.db.create_project(os.path.basename(f), f, os.path.getsize(f))
                except: pass

    def run_process(self):
        if not self.full_file_path: return
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("background-color: #A3AED0; color: white;") 
        self.terminal.clear()
        self.terminal.append("> 🚀 Starting 5-Step Annotation Pipeline...")
        
        if self.db and self.current_project_id:
            self.db.start_analysis(self.current_project_id, "annotation")
            
        self.worker = AnnotationWorker(self.full_file_path)
        self.worker.log_signal.connect(self.terminal.append)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, msg):
        self.btn_run.setEnabled(True)
        self.btn_run.setStyleSheet("background-color: #4318FF; color: white; border: 2px solid #2B3674;")
        if success:
            self.terminal.append("> ✅ Pipeline Complete. Loading Results...")
            self.load_results()
            self.btn_online.setEnabled(True) # ENABLE ONLINE CHECK
            if self.db and self.current_project_id:
                self.db.update_project_status(self.current_project_id, "completed")
        else:
            self.terminal.append(f"> ❌ Error: {msg}")

    # --- ONLINE VERIFICATION LOGIC ---
    def run_online_verification(self):
        # 1. Check if user is on Tab 2 (Annotation)
        if self.tabs.currentIndex() != 1:
            QMessageBox.warning(self, "Wrong Tab", "Please select a row in the '2. Annotation' tab first.")
            self.tabs.setCurrentIndex(1)
            return

        # 2. Get Selected Row
        current_row = self.tab_anno.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please click a gene row in the table first.")
            return
            
        # 3. Get Gene ID (Assuming Column 0 is Gene ID)
        gene_id = self.tab_anno.table.item(current_row, 0).text()
        
        # 4. Fetch Sequence
        sequence = self.fetch_sequence_from_file(gene_id)
        if not sequence:
            QMessageBox.warning(self, "Error", f"Could not find sequence for ID: {gene_id}")
            return

        # 5. Start Worker
        self.btn_online.setEnabled(False)
        self.btn_online.setText("⏳ Connecting...")
        self.terminal.append(f"> 🌍 Checking {gene_id} against NCBI Database...")
        
        self.remote_worker = RemoteBlastWorker(sequence, "blastp", "nr")
        self.remote_worker.log_signal.connect(self.terminal.append)
        self.remote_worker.result_signal.connect(self.show_online_popup)
        self.remote_worker.finished_signal.connect(self.on_online_finished)
        self.remote_worker.start()

    def fetch_sequence_from_file(self, gene_id):
        """Helper to find the sequence string from the .faa file"""
        base = os.path.basename(self.full_file_path).split('.')[0]
        faa_path = os.path.join(os.getcwd(), "results", "annotation", f"{base}.faa")
        
        if not os.path.exists(faa_path): return None
        
        found = False
        seq_parts = []
        with open(faa_path, 'r') as f:
            for line in f:
                if line.startswith(">"):
                    if found: break # End of our gene
                    # Check partial match (Prodigal IDs can vary slightly)
                    if gene_id in line: 
                        found = True
                elif found:
                    seq_parts.append(line.strip())
        
        return "".join(seq_parts) if seq_parts else None

    def show_online_popup(self, data):
        if not data: 
            QMessageBox.information(self, "Online Result", "No matches found.")
            return
        
        msg = f"""
        <h3>NCBI Remote Verification Results</h3>
        <hr>
        <b>Accession:</b> {data.get('accession', 'N/A')}<br>
        <b>Organism:</b> {data.get('organism', 'Unknown')}<br>
        <b>Description:</b> {data.get('description', 'N/A')}<br>
        <br>
        <b>Identity:</b> <span style='color:green'>{data.get('identity', '0%')}</span><br>
        <b>E-Value:</b> {data.get('e_value', 'N/A')}<br>
        <hr>
        <i>Fetched live from NCBI Non-Redundant Database.</i>
        """
        QMessageBox.information(self, "Online Verification", msg)

    def on_online_finished(self):
        self.btn_online.setEnabled(True)
        self.btn_online.setText("🌍 Verify Selected (NCBI)")

    def load_results(self):
        """Parses output files and populates all 5 tabs."""
        base = os.path.basename(self.full_file_path).split('.')[0]
        results_dir = os.path.join(os.getcwd(), "results", "annotation")
        
        gff = os.path.join(results_dir, f"{base}.gff")
        tsv = os.path.join(results_dir, f"{base}_annotation.tsv")
        dom = os.path.join(results_dir, f"{base}_domains.tsv")
        rna = os.path.join(results_dir, f"{base}_rna.tsv")
        png = os.path.join(results_dir, "genome_circle.png")

        # 1. GENES
        genes, lengths = [], []
        if os.path.exists(gff):
            with open(gff) as f:
                for line in f:
                    if "\tCDS\t" in line:
                        parts = line.split('\t')
                        try:
                            start, end = int(parts[3]), int(parts[4])
                            length = end - start
                            strand = parts[6]
                            attr = parts[8].split(';')[0].replace("ID=", "")
                            genes.append((attr, start, end, strand, length))
                            lengths.append(length)
                        except: pass
        
        self.hist_widget.update_data(lengths)
        self.tab_genes.load_safe_data(genes)
        avg_len = sum(lengths)/len(lengths) if lengths else 0
        self.tab_genes.set_report(f"Total Genes: {len(genes)}<br>Avg Length: {avg_len:.2f} bp")

        # 2. ANNOTATION
        tsv_rows, func_counts = [], []
        if os.path.exists(tsv):
            with open(tsv) as f:
                reader = csv.reader(f, delimiter='\t')
                for row in reader:
                    if len(row) >= 5:
                        tsv_rows.append([row[0], row[4], row[2], row[3]])
                        func_counts.append(row[4].split()[0]) 
        
        self.func_chart.update_data(Counter(func_counts).most_common(10))
        self.tab_anno.load_safe_data(tsv_rows)
        self.tab_anno.set_report(f"Annotated: {len(func_counts)}<br>Unknown: {len(genes) - len(func_counts)}")

        # 3. DOMAINS
        dom_rows, dom_counts = [], []
        if os.path.exists(dom):
            with open(dom) as f:
                reader = csv.reader(f, delimiter='\t')
                for row in reader:
                    if len(row) >= 2:
                        dom_rows.append([row[0], row[1], row[2], row[3]])
                        dom_counts.append(row[1].split(',')[0])

        self.domain_chart.update_data(Counter(dom_counts).most_common(10))
        self.tab_domains.load_safe_data(dom_rows)
        self.tab_domains.set_report(f"Domains Found: {len(dom_rows)}")

        # 4. RNA
        rna_rows = []
        if os.path.exists(rna):
            with open(rna) as f:
                reader = csv.reader(f, delimiter='\t')
                for row in reader:
                    if len(row) >= 5:
                        rna_rows.append(["RNA", row[1], row[2], row[3]])
        
        self.rna_visual.setText(f"Found {len(rna_rows)} RNA")
        self.tab_rna.load_safe_data(rna_rows)
        self.tab_rna.set_report(f"Total RNA Hits: {len(rna_rows)}")

        # 5. VISUALIZATION
        if os.path.exists(png):
            pix = QPixmap(png)
            self.circular_plot.setPixmap(pix.scaled(400, 400, Qt.KeepAspectRatio))
        
        map_genes = [{'start': g[1], 'end': g[2], 'strand': g[3]} for g in genes]
        file_size = os.path.getsize(self.full_file_path)
        self.linear_map.update_map(map_genes, file_size)