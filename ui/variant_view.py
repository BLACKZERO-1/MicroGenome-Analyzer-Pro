import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QTextEdit, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont

# IMPORT ENGINE
from core.variant.variant_engine import VariantWorker

# ==============================================================================
# 🎨 MUTATION MAP WIDGET
# ==============================================================================
class MutationMapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(150)
        self.variants = [] 
        self.genome_length = 50000 
        self.setStyleSheet("background: white; border-radius: 12px; border: 2px solid #2B3674;")

    def update_data(self, variant_list, length=50000):
        self.variants = variant_list
        self.genome_length = length if length > 0 else 50000
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        painter.setBrush(QColor("white")); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 12, 12)
        
        painter.setPen(QColor("#2B3674"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(20, 30, "Mutation Density Map")
        
        bar_y = h / 2; bar_margin = 40; bar_width = w - (bar_margin * 2)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor("#E0E5F2"))
        painter.drawRoundedRect(bar_margin, int(bar_y - 10), int(bar_width), 20, 10, 10)
        
        if not self.variants:
            painter.setPen(QColor("#A3AED0")); painter.drawText(self.rect(), Qt.AlignCenter, "No Data / Ready to Analyze")
            return
            
        painter.setPen(QPen(QColor("#E31A1A"), 2))
        scale = bar_width / self.genome_length
        for v in self.variants:
            pos = v.get('pos', 0)
            x = bar_margin + (pos * scale)
            x = min(max(x, bar_margin), w - bar_margin)
            painter.drawLine(int(x), int(bar_y - 15), int(x), int(bar_y + 15))

# ==============================================================================
# 🚀 MAIN VARIANT VIEW
# ==============================================================================
class VariantView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.ref_path = None
        self.query_path = None
        self.current_mutations = []
        
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI'; }
            QFrame { background: white; border-radius: 12px; border: 2px solid #2B3674; }
            QLabel { color: #2B3674; font-weight: bold; border: none; }
            QPushButton { border-radius: 6px; padding: 8px 15px; font-weight: bold; font-size: 13px; border: 2px solid #2B3674; }
            QPushButton:disabled { background: #A3AED0; color: #F4F7FE; border: none; }
        """)
        
        layout = QVBoxLayout(self); layout.setSpacing(20)
        
        # 1. CONTROLS & MAP
        self.setup_controls(layout)
        self.map_widget = MutationMapWidget()
        layout.addWidget(self.map_widget)
        
        # 2. SPLITTER (Table + Inspector + Logs)
        splitter = QSplitter(Qt.Vertical)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Position", "Reference", "Mutation (Alt)", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setRowCount(50); self.table.setShowGrid(True); self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #000000; gridline-color: #9E9E9E; border: 2px solid #2B3674; border-radius: 8px; font-size: 13px; }
            QTableWidget::item { color: #000000; padding: 5px; border-bottom: 1px solid #E0E0E0; }
            QTableWidget::item:hover { background-color: transparent; }
            QTableWidget::item:selected { background-color: #4318FF; color: #FFFFFF; }
            QHeaderView::section { background-color: #2B3674; color: #FFFFFF; font-weight: bold; font-size: 13px; border: 1px solid #FFFFFF; padding: 6px; min-height: 30px; }
        """)
        # Connect Click Event
        self.table.itemClicked.connect(self.show_mutation_details)
        splitter.addWidget(self.table)
        
        # --- NEW INSPECTOR PANEL ---
        self.inspector = QFrame()
        self.inspector.setFixedHeight(130)
        self.inspector.setStyleSheet("background: #1B2559; border-radius: 8px; border: 2px solid #2B3674;")
        insp_layout = QHBoxLayout(self.inspector)
        
        # Context Labels
        self.lbl_ctx_ref = QLabel("Select a mutation to inspect DNA context...")
        self.lbl_ctx_ref.setStyleSheet("font-family: Consolas; font-size: 14px; color: #A3AED0;")
        self.lbl_ctx_query = QLabel("")
        self.lbl_ctx_query.setStyleSheet("font-family: Consolas; font-size: 14px; color: #00E676; font-weight: bold;")
        
        # Stats Label
        self.lbl_stats = QLabel("Ts/Tv Ratio: --")
        self.lbl_stats.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: 1px solid #4318FF; padding: 10px; border-radius: 6px;")
        
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("REFERENCE SEQUENCE:", styleSheet="color:#707EAE; font-size:10px;"))
        vbox.addWidget(self.lbl_ctx_ref)
        vbox.addWidget(QLabel("QUERY SEQUENCE (MUTATED):", styleSheet="color:#707EAE; font-size:10px;"))
        vbox.addWidget(self.lbl_ctx_query)
        
        insp_layout.addLayout(vbox)
        insp_layout.addStretch()
        insp_layout.addWidget(self.lbl_stats)
        splitter.addWidget(self.inspector)
        
        # Logs
        self.terminal = QTextEdit(); self.terminal.setReadOnly(True); self.terminal.setMaximumHeight(80)
        self.terminal.setStyleSheet("background: #111C44; color: #00E676; font-family: Consolas; border: 2px solid #2B3674; border-radius: 6px;")
        splitter.addWidget(self.terminal)
        
        layout.addWidget(splitter)

    def setup_controls(self, parent_layout):
        container = QFrame()
        l = QHBoxLayout(container)
        
        info = QVBoxLayout()
        title = QLabel("🧬 Variant Caller (SNP)")
        title.setStyleSheet("font-size: 16px; border:none;")
        sub = QLabel("Compare two genomes to find mutations")
        sub.setStyleSheet("color: #A3AED0; font-weight: normal; font-size: 11px; border:none;")
        info.addWidget(title); info.addWidget(sub)
        l.addLayout(info); l.addStretch()
        
        self.btn_ref = QPushButton("1. Select Reference")
        self.btn_ref.setStyleSheet("background: #E9EDF7; color: #4318FF; border: 2px solid #D0D7DE;")
        self.btn_ref.clicked.connect(self.select_ref)
        
        self.btn_query = QPushButton("2. Select Query")
        self.btn_query.setStyleSheet("background: #E9EDF7; color: #4318FF; border: 2px solid #D0D7DE;")
        self.btn_query.clicked.connect(self.select_query)
        
        self.btn_run = QPushButton("▶ Run Comparison")
        self.btn_run.setStyleSheet("background: #4318FF; color: white; border: 2px solid #2B3674;")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_analysis)

        self.btn_export = QPushButton("💾 Export VCF")
        self.btn_export.setStyleSheet("background: #FFAB00; color: black; border: 2px solid #E69500;")
        self.btn_export.setEnabled(False) 
        self.btn_export.clicked.connect(self.export_vcf)
        
        l.addWidget(self.btn_ref); l.addWidget(self.btn_query); l.addWidget(self.btn_run); l.addWidget(self.btn_export)
        parent_layout.addWidget(container)

    def select_ref(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Reference", "", "FASTA (*.fasta *.fa)")
        if f:
            self.ref_path = f
            self.btn_ref.setText(f"Ref: {os.path.basename(f)}")
            self.btn_ref.setStyleSheet("background: #05CD99; color: white; border: 2px solid #2B3674;") 
            self.check_ready()

    def select_query(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Query", "", "FASTA (*.fasta *.fa)")
        if f:
            self.query_path = f
            self.btn_query.setText(f"Query: {os.path.basename(f)}")
            self.btn_query.setStyleSheet("background: #05CD99; color: white; border: 2px solid #2B3674;")
            self.check_ready()

    def check_ready(self):
        if self.ref_path and self.query_path: self.btn_run.setEnabled(True)

    def run_analysis(self):
        self.btn_run.setEnabled(False); self.btn_export.setEnabled(False)
        self.table.setRowCount(0); self.terminal.clear()
        
        self.worker = VariantWorker(self.query_path, self.ref_path)
        self.worker.log_signal.connect(self.terminal.append)
        self.worker.result_signal.connect(self.display_results)
        self.worker.finished_signal.connect(lambda: self.btn_run.setEnabled(True))
        self.worker.start()

    def display_results(self, mutations):
        self.current_mutations = mutations
        self.table.setRowCount(len(mutations))
        
        for i, m in enumerate(mutations):
            self.table.setItem(i, 0, QTableWidgetItem(str(m['pos'])))
            self.table.setItem(i, 1, QTableWidgetItem(m['ref']))
            self.table.setItem(i, 2, QTableWidgetItem(m['alt']))
            self.table.setItem(i, 3, QTableWidgetItem(m['type']))
        
        if not mutations: self.table.setRowCount(50)
        else:
            self.btn_export.setEnabled(True)
            # Update Stats Label if stats exist
            if 'stats' in mutations[0]:
                s = mutations[0]['stats']
                self.lbl_stats.setText(f"Transitions: {s['ts']}\nTransversions: {s['tv']}\nTs/Tv Ratio: {s['ratio']}")

        self.map_widget.update_data(mutations, length=50000)

    def show_mutation_details(self, item):
        row = item.row()
        if row < len(self.current_mutations):
            m = self.current_mutations[row]
            
            # Simple HTML formatting
            ref_seq = m.get('ctx_ref', '')
            qry_seq = m.get('ctx_query', '')
            mid = len(ref_seq) // 2
            
            if ref_seq and qry_seq:
                r_html = f"{ref_seq[:mid]}<span style='background-color:#4318FF; color:white;'> {ref_seq[mid]} </span>{ref_seq[mid+1:]}"
                q_html = f"{qry_seq[:mid]}<span style='background-color:#E31A1A; color:white;'> {qry_seq[mid]} </span>{qry_seq[mid+1:]}"
                self.lbl_ctx_ref.setText(r_html)
                self.lbl_ctx_query.setText(q_html)

    def export_vcf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save VCF", "", "VCF Files (*.vcf)")
        if path:
            try:
                with open(path, "w") as f:
                    f.write("##fileformat=VCFv4.2\n")
                    f.write(f"##source=MicroGenomePro\n")
                    f.write("#CHROM\tPOS\tID\tREF\tALT\tINFO\n")
                    for m in self.current_mutations:
                        f.write(f"Genome\t{m['pos']}\t.\t{m['ref']}\t{m['alt']}\tTYPE={m['type']}\n")
                QMessageBox.information(self, "Success", "Export Complete!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed: {e}")