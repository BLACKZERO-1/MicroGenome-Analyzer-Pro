import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QProgressBar, QFrame, QMessageBox, QGridLayout,
    QTabWidget, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath

from core.qc.qc_engine import QCWorker, TrimmingWorker

# ==============================================================================
# 🎨 CUSTOM WIDGET 1: QUALITY GRAPH
# ==============================================================================
class QualityGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []
        self.setStyleSheet("background: white;")

    def set_data(self, data):
        self.data = data
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Margins
        ml, mb = 40, 30
        gw, gh = w - ml - 10, h - mb - 10

        # Background Zones
        green_h = (12/40) * gh; orange_h = (8/40) * gh; red_h = (20/40) * gh
        painter.fillRect(ml, 10, gw, int(green_h), QColor("#E8F5E9"))
        painter.fillRect(ml, 10+int(green_h), gw, int(orange_h), QColor("#FFF3E0"))
        painter.fillRect(ml, 10+int(green_h)+int(orange_h), gw, int(red_h), QColor("#FFEBEE"))

        # Axes
        painter.setPen(QPen(QColor("#707EAE"), 2))
        painter.drawLine(ml, 10, ml, h - mb)
        painter.drawLine(ml, h - mb, w - 10, h - mb)

        if not self.data: return

        # Draw Line
        painter.setPen(QPen(QColor("#4318FF"), 2))
        path = QPainterPath()
        x_step = gw / max(1, len(self.data) - 1)
        
        for i, score in enumerate(self.data):
            x = ml + (i * x_step)
            y = (h - mb) - (score / 40 * gh)
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)
        painter.drawPath(path)

# ==============================================================================
# 🎨 CUSTOM WIDGET 2: BASE CONTENT GRAPH
# ==============================================================================
class BaseContentGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []
        self.setStyleSheet("background: white;")

    def set_data(self, data):
        self.data = data
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        ml, mb = 40, 30
        gw, gh = w - ml - 10, h - mb - 10

        # Axes
        painter.setPen(QPen(QColor("#707EAE"), 2))
        painter.drawLine(ml, 10, ml, h - mb)
        painter.drawLine(ml, h - mb, w - 10, h - mb)
        
        if not self.data: 
            painter.drawText(w//2, h//2, "No Data")
            return

        # Colors: A=Blue, C=Red, G=Green, T=Yellow
        colors = {'A': "#2196F3", 'C': "#F44336", 'G': "#4CAF50", 'T': "#FFEB3B"}
        x_step = gw / max(1, len(self.data) - 1)

        for base, color in colors.items():
            painter.setPen(QPen(QColor(color), 2))
            path = QPainterPath()
            for i, d in enumerate(self.data):
                val = d.get(base, 0)
                x = ml + (i * x_step)
                y = (h - mb) - (val / 100 * gh)
                if i == 0: path.moveTo(x, y)
                else: path.lineTo(x, y)
            painter.drawPath(path)
        
        # Legend
        painter.setPen(Qt.black)
        painter.drawText(w-100, 20, "A (Blue)")
        painter.drawText(w-100, 35, "C (Red)")
        painter.drawText(w-100, 50, "G (Grn)")
        painter.drawText(w-100, 65, "T (Yel)")

# ==============================================================================
# 🚀 MAIN QC DASHBOARD
# ==============================================================================
class QCView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.file_path = ""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30,30,30,30); layout.setSpacing(20)

        # 1. Header & Load
        header = QHBoxLayout()
        header.addWidget(QLabel("📉 Quality Control", styleSheet="font-size:24px; font-weight:bold; color:#1B2559;"))
        header.addStretch()
        self.btn_load = QPushButton("📂 Load FASTQ")
        self.btn_load.setFixedSize(140, 40)
        self.btn_load.setStyleSheet("background:#4318FF; color:white; font-weight:bold; border-radius:8px;")
        self.btn_load.clicked.connect(self.load_file)
        header.addWidget(self.btn_load)
        layout.addLayout(header)

        # 2. Status Cards
        cards = QHBoxLayout(); cards.setSpacing(20)
        self.card_reads = self.create_card("Total Reads", "0", "#E3F2FD", "#1565C0")
        self.card_qual = self.create_card("Avg Quality", "0", "#E8F5E9", "#2E7D32")
        self.card_gc = self.create_card("GC Content", "0%", "#FFF3E0", "#EF6C00")
        cards.addWidget(self.card_reads); cards.addWidget(self.card_qual); cards.addWidget(self.card_gc)
        layout.addLayout(cards)

        # 3. Content Split
        split = QHBoxLayout()
        
        # LEFT: Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E0E5F2; background: white; border-radius: 8px; }
            QTabBar::tab { background: #F4F7FE; padding: 10px; margin-right: 5px; border-radius: 4px; font-weight: bold; color: #707EAE; }
            QTabBar::tab:selected { background: #4318FF; color: white; }
        """)
        self.graph_qual = QualityGraph()
        self.graph_base = BaseContentGraph()
        self.tabs.addTab(self.graph_qual, "Quality Scores")
        self.tabs.addTab(self.graph_base, "Base Composition")
        split.addWidget(self.tabs, 2) 

        # RIGHT: Text Report
        report_frame = QFrame()
        report_frame.setStyleSheet("background:white; border:1px solid #E0E5F2; border-radius:8px;")
        rf_layout = QVBoxLayout(report_frame)
        rf_layout.addWidget(QLabel("📋 Detailed Report", styleSheet="font-weight:bold; font-size: 14px; color:#2B3674;"))
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        # UPDATED STYLE: Large Font, Monospace, Dark Text
        self.report_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E5F2;
                border-radius: 6px;
                background-color: #F9FAFC;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px; 
                color: #1B2559;
                padding: 10px;
            }
        """)
        self.report_text.setText("Load a file to see details...")
        rf_layout.addWidget(self.report_text)
        
        # Tools
        self.btn_trim = QPushButton("✂️ Trim Bad Data")
        self.btn_trim.setEnabled(False)
        self.btn_trim.setStyleSheet("background:#FFB547; color:white; font-weight:bold; padding:8px; border-radius:6px;")
        self.btn_trim.clicked.connect(self.run_trimming)
        rf_layout.addWidget(self.btn_trim)
        
        split.addWidget(report_frame, 1)
        layout.addLayout(split)

        # 4. Progress
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet("QProgressBar{border:none; background:#F4F7FE;} QProgressBar::chunk{background:#05CD99;}")
        layout.addWidget(self.progress)

    def create_card(self, title, val, bg, fg):
        f = QFrame()
        f.setStyleSheet(f"background:{bg}; border-radius:12px; border-left:5px solid {fg};")
        l = QVBoxLayout(f)
        l.addWidget(QLabel(title, styleSheet=f"color:{fg}; font-weight:bold; font-size:12px;"))
        val_lbl = QLabel(val, styleSheet=f"color:#1B2559; font-weight:900; font-size:24px;")
        l.addWidget(val_lbl)
        f.val_label = val_lbl 
        return f

    def load_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open FASTQ", "", "Sequencing (*.fastq *.fq);;All (*.*)")
        if f:
            self.file_path = f
            self.btn_load.setText("Running...")
            self.btn_load.setEnabled(False)
            self.report_text.setText("⏳ Analyzing file structure...\nCalculating Phred scores...\nCounting base distribution...")
            self.progress.setRange(0, 0)
            
            self.worker = QCWorker(f)
            self.worker.result_signal.connect(self.show_results)
            self.worker.start()

    def show_results(self, stats):
        self.progress.setRange(0, 100); self.progress.setValue(100)
        self.btn_load.setText("📂 Load FASTQ"); self.btn_load.setEnabled(True)
        self.btn_trim.setEnabled(True)

        # Update Cards
        self.card_reads.val_label.setText(f"{stats['total_reads']:,}")
        self.card_qual.val_label.setText(str(stats['avg_quality']))
        self.card_gc.val_label.setText(f"{stats['gc_content']}%")

        # Update Graphs
        self.graph_qual.set_data(stats['quality_per_position'])
        self.graph_base.set_data(stats['base_content_per_pos'])

        # Generate Text Report
        report = f""" ANALYSIS COMPLETE 
 ----------------------------
 File: {os.path.basename(self.file_path)}
 Reads: {stats['total_reads']:,}
 GC Content: {stats['gc_content']}%
 Avg Quality: {stats['avg_quality']}

 [ PASS/FAIL CHECKS ]
 """
        if stats['avg_quality'] > 28: report += "✅ Basic Quality: PASS\n"
        elif stats['avg_quality'] > 20: report += "⚠️ Basic Quality: WARN\n"
        else: report += "❌ Basic Quality: FAIL\n"

        if 40 < stats['gc_content'] < 60: report += "✅ GC Distribution: PASS\n"
        else: report += "⚠️ GC Distribution: SKEWED\n"

        if stats['quality_per_position'] and stats['quality_per_position'][-1] < 20: 
            report += "❌ End-Read Quality: FAIL (Trimming Recommended)\n"
        else: 
            report += "✅ End-Read Quality: PASS\n"

        self.report_text.setText(report)

    def run_trimming(self):
        self.btn_trim.setText("✂️ Working..."); self.btn_trim.setEnabled(False)
        self.report_text.append("\n>> STARTED TRIMMING...")
        self.trimmer = TrimmingWorker(self.file_path)
        self.trimmer.finished_signal.connect(lambda p: [
            self.report_text.append(f"✅ DONE. Saved to:\n{p}"),
            self.btn_trim.setText("✂️ Trim Bad Data"),
            self.btn_trim.setEnabled(True)
        ])
        self.trimmer.start()