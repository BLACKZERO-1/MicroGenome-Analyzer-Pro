from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QProgressBar, QTextEdit, 
                               QFrame, QGraphicsDropShadowEffect, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from core.annotation.annotation_engine import AnnotationWorker

class AnnotationView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None 

        # ==========================================================================
        # 1. PROFESSIONAL STYLING (Soft UI + Tech Terminal)
        # ==========================================================================
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            
            /* Main Container */
            QFrame#main_card { 
                background-color: #FFFFFF; 
                border-radius: 20px; 
                border: 1px solid #F0F0F0;
            }

            /* Headers */
            QLabel#section_header { 
                color: #2B3674; font-size: 14px; font-weight: 800; 
                letter-spacing: 1px; margin-bottom: 5px; margin-top: 10px;
            }

            /* Input Field */
            QLabel#path_display {
                background-color: #F8F9FC; color: #A3AED0; font-weight: 600; 
                border-radius: 12px; padding-left: 15px; border: 1px solid #E0E5F2;
            }
            QLabel#path_display[active="true"] {
                background-color: #E9FAF5; color: #05CD99; border: 1px solid #05CD99;
            }

            /* Buttons */
            QPushButton { border-radius: 12px; font-weight: 700; font-size: 14px; border: none; }
            QPushButton#btn_browse { background-color: #E9EDF7; color: #4318FF; }
            QPushButton#btn_browse:hover { background-color: #DCE4F5; }
            
            QPushButton#btn_run {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4318FF, stop:1 #868CFF);
                color: white; font-size: 15px;
            }
            QPushButton#btn_run:hover { margin-top: -2px; }
            QPushButton#btn_run:disabled { background: #A3AED0; }

            /* TERMINAL (Bottom) */
            QTextEdit#terminal {
                background-color: #111C44; color: #00E676; 
                font-family: 'Consolas', monospace; font-size: 12px;
                border-radius: 15px; padding: 15px; border: none;
            }

            /* STAT CARDS */
            QFrame#stat_card { background: #FFFFFF; border-radius: 15px; border: 1px solid #F4F7FE; }
            QLabel#stat_val { font-size: 28px; font-weight: 900; }
            QLabel#stat_title { color: #A3AED0; font-size: 12px; font-weight: 700; }
        """)

        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)

        # The Floating White Card
        self.card = QFrame()
        self.card.setObjectName("main_card")
        self.apply_shadow(self.card)
        
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(30, 30, 30, 30)
        self.card_layout.setSpacing(15)

        # --- BUILD UI SECTIONS ---
        self.setup_header()
        self.setup_controls()
        
        # Divider
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background: #F0F0F0;")
        self.card_layout.addWidget(line)

        # SECTION 1: VISUAL DASHBOARD (Top)
        self.setup_visuals()

        # SECTION 2: TEXT TERMINAL (Bottom)
        self.setup_terminal()

        self.layout.addWidget(self.card)


    # ==========================================================================
    # UI COMPONENTS
    # ==========================================================================
    def setup_header(self):
        h = QHBoxLayout()
        icon = QLabel("🧬"); icon.setStyleSheet("font-size: 32px; background: transparent;")
        
        v = QVBoxLayout()
        t1 = QLabel("Genome Annotation Engine"); t1.setStyleSheet("color: #2B3674; font-size: 22px; font-weight: 900;")
        t2 = QLabel("Prodigal-based ORF Prediction System"); t2.setStyleSheet("color: #A3AED0; font-weight: 600; font-size: 12px;")
        v.addWidget(t1); v.addWidget(t2)
        
        h.addWidget(icon); h.addSpacing(15); h.addLayout(v); h.addStretch()
        self.card_layout.addLayout(h)

    def setup_controls(self):
        h = QHBoxLayout()
        
        self.path_lbl = QLabel("  No Input File Selected"); self.path_lbl.setObjectName("path_display"); self.path_lbl.setFixedHeight(50)
        
        btn_browse = QPushButton("📂 Load FASTA"); btn_browse.setObjectName("btn_browse"); btn_browse.setFixedSize(140, 50)
        btn_browse.setCursor(Qt.PointingHandCursor); btn_browse.clicked.connect(self.select_file)

        h.addWidget(self.path_lbl); h.addSpacing(10); h.addWidget(btn_browse)
        self.card_layout.addLayout(h)

        # Run Button & Progress Bar
        self.btn_run = QPushButton("START ANALYSIS PIPELINE"); self.btn_run.setObjectName("btn_run"); self.btn_run.setFixedHeight(50)
        self.btn_run.setCursor(Qt.PointingHandCursor); self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_process)

        self.progress = QProgressBar(); self.progress.setFixedHeight(6); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("background: #F4F7FE; border-radius: 3px; QProgressBar::chunk { background: #4318FF; border-radius: 3px; }")

        self.card_layout.addWidget(self.btn_run)
        self.card_layout.addWidget(self.progress)

    def setup_visuals(self):
        """Top Section: Charts and Stats"""
        self.vis_container = QWidget()
        # Visuals are dimmed until run starts
        self.vis_container.setEnabled(False) 
        self.vis_container.setStyleSheet("QWidget:disabled { opacity: 0.6; }")
        
        vl = QVBoxLayout(self.vis_container); vl.setContentsMargins(0,0,0,0)
        
        lbl = QLabel("REAL-TIME METRICS DASHBOARD"); lbl.setObjectName("section_header")
        vl.addWidget(lbl)

        # --- STATS ROW ---
        row = QHBoxLayout(); row.setSpacing(15)
        
        # 1. GC Content
        self.gc_card, self.gc_val, self.gc_bar = self.create_stat_card("GC Content", "📊", "#4318FF")
        # 2. Gene Count
        self.gene_card, self.gene_val, self.gene_bar = self.create_stat_card("Predicted Genes", "🧬", "#05CD99")
        # 3. ORFs
        self.orf_card, self.orf_val, self.orf_bar = self.create_stat_card("Total ORFs", "🔬", "#FFAB00")

        row.addWidget(self.gc_card); row.addWidget(self.gene_card); row.addWidget(self.orf_card)
        vl.addLayout(row)

        # --- GENOME TRACK VISUALIZATION ---
        t_lbl = QLabel("GENOME DENSITY MAP"); t_lbl.setObjectName("section_header")
        vl.addWidget(t_lbl)

        self.track = QFrame(); self.track.setFixedHeight(30)
        self.track.setStyleSheet("background: #F4F7FE; border-radius: 5px;")
        vl.addWidget(self.track)
        
        self.card_layout.addWidget(self.vis_container)

    def setup_terminal(self):
        """Bottom Section: Text Logs"""
        lbl = QLabel("SYSTEM EXECUTION LOGS"); lbl.setObjectName("section_header")
        self.card_layout.addWidget(lbl)

        self.terminal = QTextEdit(); self.terminal.setObjectName("terminal"); self.terminal.setReadOnly(True)
        self.terminal.setPlaceholderText("Waiting for execution command...")
        
        # --- FIX: USE CORRECT QSizePolicy IMPORT ---
        self.terminal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.card_layout.addWidget(self.terminal)

    # ==========================================================================
    # HELPER FUNCTIONS
    # ==========================================================================
    def create_stat_card(self, title, icon, color):
        card = QFrame(); card.setObjectName("stat_card")
        self.apply_shadow(card)
        l = QVBoxLayout(card); l.setContentsMargins(20, 15, 20, 15)

        # Header
        top = QHBoxLayout()
        ico = QLabel(icon); ico.setStyleSheet(f"color: {color}; font-size: 18px; background: transparent;")
        txt = QLabel(title); txt.setObjectName("stat_title")
        top.addWidget(ico); top.addSpacing(8); top.addWidget(txt); top.addStretch()

        # Value
        val = QLabel("0"); val.setObjectName("stat_val"); val.setStyleSheet(f"color: {color};")
        
        # Mini Bar
        bar = QProgressBar(); bar.setFixedHeight(4); bar.setTextVisible(False)
        bar.setStyleSheet(f"background: #F4F7FE; border-radius: 2px; QProgressBar::chunk {{ background: {color}; }}")
        bar.setValue(0)

        l.addLayout(top); l.addWidget(val); l.addSpacing(5); l.addWidget(bar)
        return card, val, bar

    def apply_shadow(self, widget):
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(20); eff.setColor(QColor(112, 144, 176, 20)); eff.setOffset(0, 5)
        widget.setGraphicsEffect(eff)

    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Genome", "", "FASTA Files (*.fasta *.fa *.fna)")
        if f:
            self.path_lbl.setText(f"  📄 {f}")
            self.path_lbl.setProperty("active", True) # Triggers green style
            self.path_lbl.style().unpolish(self.path_lbl); self.path_lbl.style().polish(self.path_lbl)
            self.btn_run.setEnabled(True)
            self.log(f"Input source loaded: {f}")

    def log(self, msg):
        self.terminal.append(f"> {msg}")
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())

    # ==========================================================================
    # LOGIC CONNECTION
    # ==========================================================================
    def run_process(self):
        raw_path = self.path_lbl.text().replace("  📄 ", "").strip()
        
        # Reset UI
        self.terminal.clear(); self.progress.setValue(0); self.btn_run.setEnabled(False)
        self.vis_container.setEnabled(True); self.vis_container.setStyleSheet("") # Undim visuals
        
        # Reset Values
        self.gc_val.setText("0%"); self.gc_bar.setValue(0)
        self.gene_val.setText("0"); self.gene_bar.setValue(0)
        self.orf_val.setText("0"); self.orf_bar.setValue(0)
        self.track.setStyleSheet("background: #F4F7FE; border-radius: 5px;")

        self.log("Initializing Worker Thread...")

        self.worker = AnnotationWorker(raw_path)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        
        # CRITICAL: Receive Real Stats
        self.worker.stats_signal.connect(self.update_stats)
        
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_stats(self, data):
        """This function receives REAL numbers from the backend"""
        self.log(f"Received Analysis Data: GC={data['gc']}% | Genes={data['genes']}")
        
        # Update GC
        self.gc_val.setText(f"{data['gc']}%")
        self.gc_bar.setValue(int(data['gc']))

        # Update Genes (Normalize bar to max 5000 for visual effect)
        self.gene_val.setText(f"{data['genes']:,}")
        self.gene_bar.setValue(min(100, int(data['genes']/50))) 

        # Update ORFs
        self.orf_val.setText(f"{data['orfs']:,}")
        self.orf_bar.setValue(min(100, int(data['orfs']/50)))

        # Activate The "DNA Barcode" Visual
        self.track.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
            stop:0 #4318FF, stop:0.1 #F4F7FE, stop:0.2 #4318FF, 
            stop:0.4 #05CD99, stop:0.6 #4318FF, stop:0.8 #FFAB00, stop:1 #4318FF);
            border-radius: 5px;
        """)

    def on_finished(self, success, msg):
        self.btn_run.setEnabled(True)
        if success:
            self.log("--- PIPELINE FINISHED SUCCESSFULLY ---")
        else:
            self.log(f"ERROR: {msg}")