from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QGraphicsDropShadowEffect, QSizePolicy, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from core.specialized.specialized_engine import SpecializedWorker

class SpecializedView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None 
        self.step_widgets = []

        # UNIFIED BLUE THEME FOR UI ELEMENTS
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            QFrame#main_card { background-color: #FFFFFF; border-radius: 20px; border: 1px solid #F0F0F0; }
            QLabel#section_header { color: #2B3674; font-size: 14px; font-weight: 800; margin-top: 15px; }
            
            /* PIPELINE TRACKER (BLUE) */
            QLabel#step_label { color: #A3AED0; font-weight: 600; font-size: 11px; }
            QLabel#step_label[status="active"] { color: #4318FF; font-weight: 800; }
            QFrame#step_dot { background: #E0E5F2; border-radius: 8px; }
            QFrame#step_dot[status="active"] { background: #4318FF; border: 2px solid #DCE4F5; }
            QFrame#step_line { background: #E0E5F2; }
            QFrame#step_line[status="active"] { background: #4318FF; }

            /* CONTROLS */
            QLabel#path_display { background-color: #F8F9FC; color: #A3AED0; font-weight: 600; border-radius: 12px; padding-left: 15px; border: 1px solid #E0E5F2; }
            QLabel#path_display[active="true"] { background-color: #F2F0FF; color: #4318FF; border: 1px solid #4318FF; }

            QPushButton#btn_browse { background-color: #E9EDF7; color: #4318FF; font-weight: 700; border-radius: 12px; border: none; }
            QPushButton#btn_browse:hover { background-color: #DCE4F5; }
            
            /* PRIMARY BUTTON (BLUE) */
            QPushButton#btn_run { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4318FF, stop:1 #868CFF); color: white; font-size: 15px; font-weight: 700; border-radius: 12px; border: none; }
            QPushButton#btn_run:hover { margin-top: -2px; }
            QPushButton#btn_run:disabled { background: #A3AED0; }
            
            QComboBox { padding: 10px; border-radius: 10px; border: 1px solid #E0E5F2; background: white; font-weight: 600; color: #2B3674; }

            /* Terminal keeps RED text to signal Threat Analysis context */
            QTextEdit#terminal { background-color: #111C44; color: #FF5B5B; font-family: 'Consolas', monospace; font-size: 12px; border-radius: 15px; padding: 15px; border: none; }
            
            QFrame#stat_card { background: #FFFFFF; border-radius: 15px; border: 1px solid #F4F7FE; }
            QLabel#stat_val { font-size: 24px; font-weight: 900; }
            QLabel#stat_title { color: #A3AED0; font-size: 11px; font-weight: 700; }
            QProgressBar { background: #F4F7FE; border-radius: 3px; height: 6px; text-align: center; }
            QProgressBar::chunk { background: #4318FF; border-radius: 3px; }
        """)

        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(30,30,30,30)
        self.card = QFrame(); self.card.setObjectName("main_card"); self.apply_shadow(self.card)
        self.card_layout = QVBoxLayout(self.card); self.card_layout.setContentsMargins(30,30,30,30); self.card_layout.setSpacing(10)
        self.setup_header(); self.setup_pipeline_tracker(); self.setup_controls()
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background: #F0F0F0;"); self.card_layout.addWidget(line)
        self.setup_visuals(); self.setup_terminal(); self.layout.addWidget(self.card)

    def setup_header(self):
        h = QHBoxLayout(); icon = QLabel("🛡️"); icon.setStyleSheet("font-size: 32px; background: transparent;")
        v = QVBoxLayout(); t1 = QLabel("Specialized Screening Module"); t1.setStyleSheet("color: #2B3674; font-size: 22px; font-weight: 900;")
        t2 = QLabel("Antibiotic Resistance (AMR) & Virulence Factor Detection"); t2.setStyleSheet("color: #A3AED0; font-weight: 600; font-size: 12px;")
        v.addWidget(t1); v.addWidget(t2); h.addWidget(icon); h.addSpacing(15); h.addLayout(v); h.addStretch(); self.card_layout.addLayout(h)

    def setup_pipeline_tracker(self):
        self.track_container = QWidget(); l = QHBoxLayout(self.track_container); l.setContentsMargins(10,10,10,10)
        steps = ["GENOME CHECK", "LOAD DB", "BLAST SCAN", "FILTER HITS", "REPORT"]
        for i, text in enumerate(steps):
            dot = QFrame(); dot.setObjectName("step_dot"); dot.setFixedSize(16, 16)
            lbl = QLabel(text); lbl.setObjectName("step_label"); lbl.setAlignment(Qt.AlignCenter)
            v = QVBoxLayout(); v.setSpacing(5); v.setAlignment(Qt.AlignCenter)
            v.addWidget(dot, 0, Qt.AlignCenter); v.addWidget(lbl); l.addLayout(v)
            if i < len(steps) - 1:
                line = QFrame(); line.setObjectName("step_line"); line.setFixedHeight(4); line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed); l.addWidget(line)
            self.step_widgets.append({"dot": dot, "lbl": lbl, "line": line})
        self.card_layout.addWidget(self.track_container)

    def setup_controls(self):
        h = QHBoxLayout()
        self.db_selector = QComboBox(); self.db_selector.addItems(["CARD (Antibiotic Resistance)", "VFDB (Virulence Factors)"]); self.db_selector.setFixedSize(220, 50)
        self.path_lbl = QLabel("  No Genome Selected"); self.path_lbl.setObjectName("path_display"); self.path_lbl.setFixedHeight(50)
        btn_browse = QPushButton("📂 Load File"); btn_browse.setObjectName("btn_browse"); btn_browse.setFixedSize(120, 50)
        btn_browse.setCursor(Qt.PointingHandCursor); btn_browse.clicked.connect(self.select_file)
        h.addWidget(self.db_selector); h.addSpacing(10); h.addWidget(self.path_lbl); h.addSpacing(10); h.addWidget(btn_browse)
        self.card_layout.addLayout(h)
        self.btn_run = QPushButton("START SCREENING SCAN"); self.btn_run.setObjectName("btn_run"); self.btn_run.setFixedHeight(50)
        self.btn_run.setCursor(Qt.PointingHandCursor); self.btn_run.setEnabled(False); self.btn_run.clicked.connect(self.run_process)
        self.progress = QProgressBar(); self.card_layout.addWidget(self.btn_run); self.card_layout.addWidget(self.progress)

    def setup_visuals(self):
        self.vis_container = QWidget(); self.vis_container.setEnabled(False); self.vis_container.setStyleSheet("QWidget:disabled { opacity: 0.6; }")
        vl = QVBoxLayout(self.vis_container); vl.setContentsMargins(0,0,0,0)
        l1 = QLabel("DETECTION RESULTS"); l1.setObjectName("section_header"); vl.addWidget(l1)
        r1 = QHBoxLayout(); r1.setSpacing(15)
        # KEEP DATA CARDS RED (ALERT STYLE)
        self.hits_card = self.create_stat_card("Total Hits", "⚠️", "#FF5B5B")
        self.class_card = self.create_stat_card("Target Classes", "💊", "#2B3674")
        self.top_card = self.create_stat_card("Highest Threat", "☠️", "#FFAB00")
        r1.addWidget(self.hits_card[0]); r1.addWidget(self.class_card[0]); r1.addWidget(self.top_card[0]); vl.addLayout(r1)
        self.card_layout.addWidget(self.vis_container)

    def setup_terminal(self):
        l = QLabel("SCANNER LOGS"); l.setObjectName("section_header"); self.card_layout.addWidget(l)
        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        self.terminal.setPlaceholderText("System ready..."); self.terminal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.card_layout.addWidget(self.terminal)

    def create_stat_card(self, title, icon, color):
        card = QFrame(); card.setObjectName("stat_card"); self.apply_shadow(card)
        l = QVBoxLayout(card); l.setContentsMargins(20, 15, 20, 15); top = QHBoxLayout()
        ico = QLabel(icon); ico.setStyleSheet(f"color: {color}; font-size: 18px; background: transparent;")
        txt = QLabel(title); txt.setObjectName("stat_title"); top.addWidget(ico); top.addSpacing(8); top.addWidget(txt); top.addStretch()
        val = QLabel("-"); val.setObjectName("stat_val"); val.setStyleSheet(f"color: {color};"); l.addLayout(top); l.addWidget(val)
        return card, val, l

    def apply_shadow(self, w):
        e = QGraphicsDropShadowEffect(); e.setBlurRadius(20); e.setColor(QColor(112, 144, 176, 20)); e.setOffset(0, 5); w.setGraphicsEffect(e)
    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Genome", "", "FASTA Files (*.fasta *.fa *.fna)")
        if f:
            self.path_lbl.setText(f"  📄 {f}"); self.path_lbl.setProperty("active", True); self.path_lbl.style().unpolish(self.path_lbl); self.path_lbl.style().polish(self.path_lbl); self.btn_run.setEnabled(True); self.log(f"Genome loaded: {f}")
    def log(self, msg):
        self.terminal.append(f"> {msg}"); self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())
    def update_step(self, step_idx):
        for i, w in enumerate(self.step_widgets):
            status = "active" if i <= step_idx else ""
            w["dot"].setProperty("status", status); w["lbl"].setProperty("status", status); w["dot"].style().unpolish(w["dot"]); w["dot"].style().polish(w["dot"]); w["lbl"].style().unpolish(w["lbl"]); w["lbl"].style().polish(w["lbl"])
            if w["line"] and i < step_idx:
                w["line"].setProperty("status", "active"); w["line"].style().unpolish(w["line"]); w["line"].style().polish(w["line"])
    def run_process(self):
        raw = self.path_lbl.text().replace("  📄 ", "").strip(); db_choice = "card" if "CARD" in self.db_selector.currentText() else "vfdb"
        self.terminal.clear(); self.progress.setValue(0); self.btn_run.setEnabled(False); self.vis_container.setEnabled(True); self.vis_container.setStyleSheet(""); self.update_step(-1)
        self.worker = SpecializedWorker(raw, db_choice)
        self.worker.log_signal.connect(self.log); self.worker.progress_signal.connect(self.progress.setValue); self.worker.step_signal.connect(self.update_step)
        self.worker.result_signal.connect(self.update_results); self.worker.finished_signal.connect(self.on_finished); self.worker.start()
    def update_results(self, data):
        self.hits_card[1].setText(f"{data['total_hits']}"); self.class_card[1].setText(data['classes']); self.class_card[1].setStyleSheet("font-size: 14px; font-weight: 700; color: #2B3674;"); self.top_card[1].setText(data['top_hit']); self.top_card[1].setStyleSheet("font-size: 18px; font-weight: 800; color: #FFAB00;")
    def on_finished(self, s, m):
        self.btn_run.setEnabled(True); self.log("--- DONE ---" if s else f"ERROR: {m}")