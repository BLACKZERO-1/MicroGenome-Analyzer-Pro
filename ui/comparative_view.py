import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QSizePolicy, QScrollArea, QListWidget)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from core.comparative.comparative_engine import ComparativeWorker

# ==============================================================================
# 1. WIDGET: ANI IDENTITY GAUGE (Circular Identity Visualization)
# ==============================================================================
class ANIGaugeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(180)
        self.ani_value = 0.0
        self.setStyleSheet("background: transparent;")

    def update_value(self, val):
        self.ani_value = float(val)
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Draw Background Track (Semi-circle)
        rect = QRectF(w/2 - 70, 20, 140, 140)
        painter.setPen(QPen(QColor("#E0E5F2"), 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, -30 * 16, 240 * 16)
        
        # Draw Identity Progress
        if self.ani_value > 0:
            color = "#05CD99" if self.ani_value >= 95 else "#4318FF"
            painter.setPen(QPen(QColor(color), 12, Qt.SolidLine, Qt.RoundCap))
            span = (self.ani_value / 100.0) * 240
            painter.drawArc(rect, 210 * 16, -span * 16)
        
        # Center Text
        painter.setPen(QColor("#2B3674"))
        font = QFont("Segoe UI", 20, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{self.ani_value}%")
        
        font.setPixelSize(11); font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, h-20, w, 20, Qt.AlignCenter, "AVERAGE NUCLEOTIDE IDENTITY")

# ==============================================================================
# 2. MAIN COMPARATIVE DASHBOARD (Seamless & Professional)
# ==============================================================================
class ComparativeView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None 

        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            QLabel#main_title { color: #2B3674; font-size: 26px; font-weight: 900; letter-spacing: 1px; }
            QLabel#sub_title { color: #A3AED0; font-size: 14px; font-weight: 500; }
            
            QFrame#panel_box { background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E0E5F2; }
            
            QLabel#panel_title { 
                color: #2B3674; font-size: 14px; font-weight: 800; text-transform: uppercase;
                border-bottom: 2px solid #F0F0F0; padding-bottom: 15px; margin-bottom: 20px;
            }

            QListWidget { 
                background-color: #F8F9FC; border: 1px solid #E0E5F2; border-radius: 8px; 
                padding: 10px; color: #2B3674; font-weight: 600; font-size: 12px;
            }

            QPushButton#btn_action { background-color: #E9EDF7; color: #4318FF; border-radius: 8px; font-weight: 700; }
            QPushButton#btn_action:hover { background-color: #DCE4F5; }

            QPushButton#btn_run { background: #4318FF; color: white; font-size: 14px; font-weight: 700; border-radius: 8px; }
            QPushButton#btn_run:hover { background: #3311CC; }
            
            QTextEdit#terminal { 
                background-color: #111C44; color: #00E676; font-family: 'Consolas', monospace; 
                font-size: 13px; border-radius: 8px; padding: 20px; border: none; 
            }

            QFrame#stat_card { background: #F8F9FC; border-radius: 12px; border: 1px solid #E0E5F2; }
            QLabel#stat_val { font-size: 26px; font-weight: 900; color: #2B3674; }
            QLabel#stat_title { color: #A3AED0; font-size: 11px; font-weight: 700; text-transform: uppercase; }

            QScrollArea { border: none; background: transparent; }
            QWidget#scroll_content { background: transparent; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # SCROLLABLE VIEWPORT
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("scroll_content")
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(25)

        # BUILD THE DASHBOARD
        self.setup_centered_header()
        self.setup_input_panel()
        self.setup_metrics_panel()
        self.setup_visual_panel()
        self.setup_log_panel()

        self.layout.addStretch()
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)

    def setup_centered_header(self):
        h = QHBoxLayout()
        h.addStretch()
        icon = QLabel("📊"); icon.setStyleSheet("font-size: 40px;")
        v = QVBoxLayout(); v.setSpacing(4)
        t1 = QLabel("Comparative Analysis Dashboard"); t1.setObjectName("main_title"); t1.setAlignment(Qt.AlignCenter)
        t2 = QLabel("Pairwise Average Nucleotide Identity (ANI) Metrics"); t2.setObjectName("sub_title"); t2.setAlignment(Qt.AlignCenter)
        v.addWidget(t1); v.addWidget(t2)
        h.addWidget(icon); h.addSpacing(20); h.addLayout(v)
        h.addStretch()
        self.layout.addLayout(h)

    def setup_input_panel(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(30, 30, 30, 30)

        t = QLabel("📂  Genome Queue Selection"); t.setObjectName("panel_title")
        l.addWidget(t)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        l.addWidget(self.file_list)

        row = QHBoxLayout()
        btn_add = QPushButton("➕ Add Genomes"); btn_add.setObjectName("btn_action"); btn_add.setFixedSize(160, 45)
        btn_add.clicked.connect(self.select_files)
        btn_clear = QPushButton("🗑️ Clear List"); btn_clear.setObjectName("btn_action"); btn_clear.setFixedSize(120, 45)
        btn_clear.clicked.connect(self.file_list.clear)
        row.addWidget(btn_add); row.addWidget(btn_clear); row.addStretch()
        l.addLayout(row)

        self.btn_run = QPushButton("EXECUTE COMPARATIVE PIPELINE"); self.btn_run.setObjectName("btn_run")
        self.btn_run.setFixedHeight(55); self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_process)
        l.addSpacing(15); l.addWidget(self.btn_run)
        
        self.progress = QProgressBar(); self.progress.setFixedHeight(4); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("background: transparent; border: none; QProgressBar::chunk { background: #4318FF; }")
        l.addWidget(self.progress)

        self.layout.addWidget(panel)

    def setup_metrics_panel(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(30, 30, 30, 30)
        t = QLabel("📊  Pairwise Identity Metrics"); t.setObjectName("panel_title")
        l.addWidget(t)

        row = QHBoxLayout(); row.setSpacing(20)
        self.ani_card, self.ani_val = self.create_stat_card("Identity Score (ANI)", "0.00%", "#4318FF")
        self.cov_card, self.cov_val = self.create_stat_card("Alignment Coverage", "0.00%", "#05CD99")
        row.addWidget(self.ani_card); row.addWidget(self.cov_card)
        l.addLayout(row)
        self.layout.addWidget(panel)

    def setup_visual_panel(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(30, 30, 30, 30)
        t = QLabel("🧬  Genomic Similarity Visualization"); t.setObjectName("panel_title")
        l.addWidget(t)

        self.ani_gauge = ANIGaugeWidget()
        l.addWidget(self.ani_gauge)
        
        info = QLabel("95%+ Identity typically indicates the same bacterial species.")
        info.setStyleSheet("color: #A3AED0; font-size: 12px; font-style: italic;")
        info.setAlignment(Qt.AlignCenter)
        l.addWidget(info)
        
        self.layout.addWidget(panel)

    def setup_log_panel(self):
        panel = QFrame(); panel.setObjectName("panel_box")
        l = QVBoxLayout(panel); l.setContentsMargins(30, 30, 30, 30)
        t = QLabel("📝  Pipeline Execution Logs"); t.setObjectName("panel_title")
        l.addWidget(t)

        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        self.terminal.setMinimumHeight(300)
        l.addWidget(self.terminal)
        self.layout.addWidget(panel)

    def create_stat_card(self, title, default, color):
        card = QFrame(); card.setObjectName("stat_card")
        l = QVBoxLayout(card); l.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel(title); lbl.setObjectName("stat_title")
        val = QLabel(default); val.setObjectName("stat_val"); val.setStyleSheet(f"color: {color};")
        l.addWidget(lbl); l.addWidget(val)
        return card, val

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Genomes", "", "FASTA Files (*.fasta *.fa *.fna)")
        if files:
            for f in files: self.file_list.addItem(f"📄 {f}")
            self.btn_run.setEnabled(self.file_list.count() >= 2)

    def log(self, msg):
        self.terminal.append(f"> {msg}"); self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())

    def run_process(self):
        files = [self.file_list.item(i).text().replace("📄 ", "").strip() for i in range(self.file_list.count())]
        self.terminal.clear(); self.progress.setValue(0); self.btn_run.setEnabled(False)
        
        self.worker = ComparativeWorker(files)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        
        # Connect signals to match the Comparative Engine keys
        self.worker.input_stats_signal.connect(lambda d: self.log(f"Comparing Reference: {d.get('ref', 'Unknown')}"))
        self.worker.stats_signal.connect(self.update_results)
        
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_results(self, data):
        ani = data.get('ani', 0.0)
        cov = data.get('coverage', 0.0)
        self.ani_val.setText(f"{ani}%")
        self.cov_val.setText(f"{cov}%")
        self.ani_gauge.update_value(ani)

    def on_finished(self, success, msg):
        self.btn_run.setEnabled(True)
        if success:
            self.log("--- ANALYSIS COMPLETED SUCCESSFULLY ---")
        else:
            self.log(f"❌ ERROR: {msg}")