import math
import os
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QTextEdit, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, 
    QAbstractItemView, QGroupBox, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QPointF, QRectF, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QLinearGradient

from core.synbio.cloning_engine import CloningWorker

# ==============================================================================
# 🎨 WIDGET 1: ADVANCED VIRTUAL GEL (Physics + Multi-Lane)
# ==============================================================================
class AdvancedGelWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(500)
        self.lanes = [] 
        # Deep dark background for high contrast bands
        self.setStyleSheet("background-color: #000000; border-radius: 8px; border: 4px solid #333;")

    def update_data(self, lanes_data):
        self.lanes = lanes_data
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#111111"))
        
        # Lane 1: Ladder
        ladder_frags = [10000, 8000, 6000, 5000, 4000, 3000, 2000, 1500, 1000, 500]
        self.draw_lane(painter, 0, "Ladder", ladder_frags, h, w, is_ladder=True)
        
        # User Lanes
        for i, lane in enumerate(self.lanes):
            label = "\n".join(lane['enzymes']) if lane['enzymes'] else "Uncut"
            self.draw_lane(painter, i + 1, label, lane['fragments'], h, w)

    def draw_lane(self, painter, lane_idx, label, fragments, h, total_w, is_ladder=False):
        num_lanes = max(5, len(self.lanes) + 2)
        lane_width = total_w / num_lanes
        x_center = (lane_idx * lane_width) + (lane_width / 2)
        well_y = 30
        gel_bottom = h - 50
        run_length = gel_bottom - well_y
        
        # Well
        painter.setBrush(QColor("#222")); painter.setPen(QColor("#444"))
        painter.drawRect(int(x_center - 20), 10, 40, 15)
        
        # Label
        painter.setPen(QColor("#AAA")); painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(x_center-40, h-40, 80, 40), Qt.AlignCenter, label)

        max_log = math.log(12000); min_log = math.log(100)
        
        for size in fragments:
            if size <= 0: continue
            val = math.log(size)
            norm_dist = (max_log - val) / (max_log - min_log)
            y_pos = well_y + (norm_dist * run_length)
            
            # Physics: Brightness based on Mass
            intensity = min(255, max(80, int((math.log(size)/10) * 255)))
            
            if is_ladder: color = QColor(200, 200, 200, intensity)
            else: color = QColor(0, 255, 120, intensity) # Neon Green
            
            # Physics: Band Spread
            spread = 4 + (1 - norm_dist) * 3 
            
            grad = QLinearGradient(0, y_pos, 0, y_pos + spread)
            grad.setColorAt(0, color.lighter(150)); grad.setColorAt(0.5, color); grad.setColorAt(1, color.darker(150))
            
            painter.setBrush(QBrush(grad)); painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x_center - 15), int(y_pos), 30, int(spread), 2, 2)
            
            if is_ladder:
                painter.setPen(QColor("#666"))
                painter.drawText(int(x_center - 45), int(y_pos)+5, f"{size}")

# ==============================================================================
# 🎨 WIDGET 2: CIRCULAR PLASMID MAP (Zoomable)
# ==============================================================================
class CircularPlasmidWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(450)
        self.features = []; self.sites = []; self.genome_len = 1000
        self.scale_factor = 1.0; self.offset = QPoint(0, 0); self.is_dragging = False
        self.setStyleSheet("background-color: white; border-radius: 12px; border: 2px solid #E0E5F2;")

    def update_map(self, length, features, sites):
        self.genome_len = max(1, length); self.features = features; self.sites = sites
        self.scale_factor = 1.0; self.offset = QPoint(0, 0); self.repaint()

    def wheelEvent(self, e):
        self.scale_factor *= 1.1 if e.angleDelta().y() > 0 else 0.9
        self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.is_dragging = True; self.last = e.pos()
    def mouseMoveEvent(self, e):
        if self.is_dragging: self.offset += e.pos() - self.last; self.last = e.pos(); self.update()
    def mouseReleaseEvent(self, e): self.is_dragging = False

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w/2 + self.offset.x(), h/2 + self.offset.y()
        p.translate(cx, cy); p.scale(self.scale_factor, self.scale_factor)
        r = min(w, h)/3
        
        p.setPen(QPen(QColor("#2B3674"), 3)); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(0,0), r, r)
        
        for f in self.features:
            start = (90*16) - ((f['start']/self.genome_len)*360*16)
            span = -((f['end']-f['start'])/self.genome_len)*360*16
            col = QColor(f['color']); col.setAlpha(150)
            p.setPen(QPen(col, 12, cap=Qt.FlatCap))
            p.drawArc(QRectF(-r, -r, r*2, r*2), int(start), int(span))

        p.setPen(QPen(QColor("black"), 1))
        font_size = max(6, int(9 / self.scale_factor)) 
        p.setFont(QFont("Segoe UI", font_size, QFont.Bold))
        
        for s in self.sites:
            ang = math.radians((s['pos']/self.genome_len)*360 - 90)
            p1 = QPointF(r*math.cos(ang), r*math.sin(ang))
            p2 = QPointF((r+15)*math.cos(ang), (r+15)*math.sin(ang))
            p.drawLine(p1, p2)
            t_pos = QPointF((r+25)*math.cos(ang), (r+25)*math.sin(ang))
            if t_pos.x() < 0: t_pos.setX(t_pos.x()-40)
            p.drawText(t_pos, s['name'])
            
        p.setPen(QColor("#2B3674")); p.setFont(QFont("Segoe UI", 14, QFont.Bold))
        p.drawText(QRectF(-100, -20, 200, 40), Qt.AlignCenter, f"{self.genome_len} bp")

# ==============================================================================
# 🚀 MAIN VIEW
# ==============================================================================
class SynBioView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.lane_queue = []
        
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI'; }
            
            /* BUTTONS */
            QPushButton { 
                background-color: #4318FF; color: white; border-radius: 6px; 
                padding: 10px; font-weight: bold; font-size: 13px; 
                border: 2px solid #2B3674; min-height: 25px;
            }
            QPushButton:hover { background-color: #3311CC; border-color: #FFFFFF; }
            QPushButton:pressed { background-color: #111111; }
            
            /* INPUTS & LISTS */
            QTextEdit, QListWidget { 
                background: white; border: 2px solid #A3AED0; border-radius: 4px; 
                color: black; font-family: Consolas; font-size: 13px;
            }
            
            /* LIST SELECTION (Light Blue) */
            QListWidget::item:selected {
                background-color: #E9EDF7;
                color: #4318FF;
                border: 1px solid #4318FF;
            }
            QListWidget::item:hover {
                background-color: #F4F7FE;
            }
            
            /* TABS */
            QTabWidget::pane { border: 2px solid #2B3674; background: white; }
            QTabBar::tab { background: #E9EDF7; color: #2B3674; padding: 10px 20px; font-weight: bold; }
            QTabBar::tab:selected { background: #4318FF; color: white; }

            /* --- FIXED TABLE STYLE (NO BROWN HOVER) --- */
            QTableWidget { 
                background-color: #FFFFFF; 
                color: #000000; 
                gridline-color: #555555; /* Visible grid */
                border: 1px solid #888888;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            /* Explicitly set item background to transparent on hover to kill brown */
            QTableWidget::item { 
                color: #000000; 
                padding: 5px; 
            }
            QTableWidget::item:hover { 
                background-color: white; 
                color: #000000;
            }
            QTableWidget::item:selected { 
                background-color: #4318FF; 
                color: #FFFFFF; 
            }
            QHeaderView::section { 
                background-color: #2B3674; 
                color: white; 
                padding: 5px; 
                font-weight: bold; 
                border: 1px solid white;
            }
            
            /* GROUP BOX FIX */
            QGroupBox {
                border: 2px solid #2B3674; 
                border-radius: 8px; 
                margin-top: 10px; 
                padding: 15px;
                background-color: white; 
                font-weight: bold; 
                color: #2B3674;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)

        layout = QHBoxLayout(self)
        
        # --- LEFT PANEL (SCROLLABLE) ---
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(360)
        left_content = QWidget()
        left_scroll.setWidget(left_content)
        
        l_layout = QVBoxLayout(left_content)
        l_layout.setSpacing(15)
        
        # Header
        l_layout.addWidget(QLabel("🧬 SynBio Workbench", styleSheet="font-size: 18px; color:#2B3674; font-weight:900;"))
        
        # Input Section
        l_layout.addWidget(QLabel("1. Sequence Input:", styleSheet="color:#2B3674; font-weight:bold;"))
        self.txt_seq = QTextEdit(); self.txt_seq.setMinimumHeight(80)
        self.txt_seq.setPlaceholderText("Paste DNA sequence here...")
        l_layout.addWidget(self.txt_seq)
        
        btn_row = QHBoxLayout()
        btn_up = QPushButton("📂 Upload File"); btn_up.setStyleSheet("background: #05CD99; color: black;")
        btn_up.clicked.connect(self.upload_file)
        btn_load = QPushButton("📥 Demo Data"); btn_load.setStyleSheet("background: #E9EDF7; color: #4318FF;")
        btn_load.clicked.connect(self.load_demo)
        btn_row.addWidget(btn_up); btn_row.addWidget(btn_load)
        l_layout.addLayout(btn_row)
        
        # Analysis Tools
        l_layout.addSpacing(10)
        l_layout.addWidget(QLabel("2. Standard Tools:", styleSheet="color:#2B3674; font-weight:bold;"))
        b_map = QPushButton("🔬 Plasmid Map"); b_map.clicked.connect(lambda: self.run("analyze_plasmid"))
        b_crispr = QPushButton("✂️ CRISPR Scan"); b_crispr.clicked.connect(lambda: self.run("crispr"))
        l_layout.addWidget(b_map); l_layout.addWidget(b_crispr)
        
        # Gel Controls
        gel_group = QGroupBox("3. Multi-Lane Gel Config")
        gl = QVBoxLayout(gel_group)
        gl.setSpacing(10)
        
        # FIXED LABEL VISIBILITY
        lbl_enz = QLabel("Select Enzymes (Ctrl+Click):")
        lbl_enz.setStyleSheet("color: #2B3674; background: transparent; font-weight: bold;")
        gl.addWidget(lbl_enz)
        
        self.enz_list = QListWidget()
        self.enz_list.setSelectionMode(QAbstractItemView.ExtendedSelection) # Ctrl+Click Enabled
        self.enz_list.addItems(["EcoRI", "BamHI", "HindIII", "NotI", "XhoI", "PstI", "SpeI", "XbaI", "ClaI", "NdeI", "SalI"])
        self.enz_list.setFixedHeight(120)
        gl.addWidget(self.enz_list)
        
        btn_add = QPushButton("➕ Add Selection to Gel"); btn_add.clicked.connect(self.add_lane)
        btn_add.setStyleSheet("background: #FFAB00; color: black;")
        gl.addWidget(btn_add)
        
        btn_run = QPushButton("▶ Run Gel Simulation"); btn_run.clicked.connect(self.run_gel)
        gl.addWidget(btn_run)
        
        l_layout.addWidget(gel_group)
        l_layout.addStretch()
        
        # Log
        self.log = QTextEdit(); self.log.setMaximumHeight(80); self.log.setReadOnly(True)
        self.log.setStyleSheet("background:#111; color:#0F0;")
        l_layout.addWidget(self.log)
        
        layout.addWidget(left_scroll)
        
        # --- RIGHT TABS ---
        self.tabs = QTabWidget()
        
        # Tab 1: Map
        self.map_wid = CircularPlasmidWidget()
        self.tabs.addTab(self.map_wid, "⭕ Map")
        
        # Tab 2: CRISPR (Excel Style Table)
        self.crispr_tab = QTableWidget()
        self.crispr_tab.setColumnCount(5) 
        self.crispr_tab.setHorizontalHeaderLabels(["Pos", "Spacer", "PAM", "GC%", "Score"])
        self.crispr_tab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # FORCE EXCEL LOOK
        self.crispr_tab.setShowGrid(True)
        self.crispr_tab.setRowCount(50) # Default empty rows
        self.crispr_tab.setAlternatingRowColors(True)
        
        self.tabs.addTab(self.crispr_tab, "✂️ CRISPR")
        
        # Tab 3: Gel
        self.gel_wid = AdvancedGelWidget()
        gc = QWidget(); gc.setStyleSheet("background:#222;")
        gcl = QVBoxLayout(gc)
        gcl.addWidget(QLabel("Physics-Based Agarose Gel Simulation", styleSheet="color:white; font-weight:bold;"))
        gcl.addWidget(self.gel_wid)
        self.tabs.addTab(gc, "⚗️ Virtual Gel")
        
        # Tab 4: Report (Restored)
        self.report_box = QTextEdit()
        self.report_box.setReadOnly(True)
        self.report_box.setStyleSheet("background: white; color: black; font-family: 'Segoe UI'; padding: 20px;")
        self.report_box.setHtml("<h3>📄 Detailed Report</h3><p>Results will appear here.</p>")
        self.tabs.addTab(self.report_box, "📄 Detailed Report")
        
        layout.addWidget(self.tabs)

    # --- LOGIC ---
    def upload_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Load DNA", "", "FASTA (*.fasta *.txt)")
        if f:
            with open(f) as file:
                data = "".join([l.strip() for l in file if not l.startswith(">")])
                self.txt_seq.setText(data)
                self.log.append(f"Loaded {len(data)} bp from {os.path.basename(f)}")

    def load_demo(self):
        self.txt_seq.setText("GACGAAAGGGCCTCGTGATACGCCTATTTTTATAGGTTAATGTCATGATAATAATGGTTTCTTAGACGTCAGGTGGCACTTTTCGGGGAAATGTGCGCGGAACCCCTATTTGTTTATTTTTCTAAATACATTCAAATATGTATCCGCTCATGAGACAATAACCCTGATAAATGCTTCAATAATATTGAAAAAGGAAGAGTATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCCTTTTTTGCGGCATTTTGCCTTCCTGTTTTTGCTCACCCAGAAACGCTGGTGAAAGTAAAAGATGCTGAAGATCAGTTGGGTGCACGAGTGGGTTACATCGAACTGGATCTCAACAGCGGTAAGATCCTTGAGAGTTTTCGCCCCGAAGAACGTTTTCCAATGATGAGCACTTTTAAAGTTCTGCTATGTGGCGCGGTATTATCCCGTATTGACGCCGGGCAAGAGCAACTCGGTCGCCGCATACACTATTCTCAGAATGACTTGGTTGAGTACTCACCAGTCACAGAAAAGCATCTTACGGATGGCATGACAGTAAGAGAATTATGCAGTGCTGCCATAACCATGAGTGATAACACTGCGGCCAACTTACTTCTGACAACGATCGGAGGACCGAAGGAGCTAACCGCTTTTTTGCACAACATGGGGGATCATGTAACTCGCCTTGATCGTTGGGAACCGGAGCTGAATGAAGCCATACCAAACGACGAGCGTGACACCACGATGCCTGTAGCAATGGCAACAACGTTGCGCAAACTATTAACTGGCGAACTACTTACTCTAGCTTCCCGGCAACAATTAATAGACTGGATGGAGGCGGATAAAGTTGCAGGACCACTTCTGCGCTCGGCCCTTCCGGCTGGCTGGTTTATTGCTGATAAATCTGGAGCCGGTGAGCGTGGGTCTCGCGGTATCATTGCAGCACTGGGGCCAGATGGTAAGCCCTCCCGTATCGTAGTTATCTACACGACGGGGAGTCAGGCAACTATGGATGAACGAAATAGACAGATCGCTGAGATAGGTGCCTCACTGATTAAGCATTGGTAACTGTCAGACCAAGTTTACTCATATATACTTTAGATTGATTTAAAACTTCATTTTTAATTTAAAAGGATCTAGGTGAAGATCCTTTTTGATAATCTCATGACCAAAATCCCTTAACGTGAGTTTTCGTTCCACTGAGCGTCAGACCCCGTAGAAAAGATCAAAGGATCTTCTTGAGATCCTTTTTTTCTGCGCGTAATCTGCTGCTTGCAAACAAAAAAACCACCGCTACCAGCGGTGGTTTGTTTGCCGGATCAAGAGCTACCAACTCTTTTTCCGAAGGTAACTGGCTTCAGCAGAGCGCAGATACCAAATACTGTCCTTCTAGTGTAGCCGTAGTTAGGCCACCACTTCAAGAACTCTGTAGCACCGCCTACATACCTCGCTCTGCTAATCCTGTTACCAGTGGCTGCTGCCAGTGGCGATAAGTCGTGTCTTACCGGGTTGGACTCAAGACGATAGTTACCGGATAAGGCGCAGCGGTCGGGCTGAACGGGGGGTTCGTGCACACAGCCCAGCTTGGAGCGAACGACCTACACCGAACTGAGATACCTACAGCGTGAGCTATGAGAAAGCGCCACGCTTCCCGAAGGGAGAAAGGCGGACAGGTATCCGGTAAGCGGCAGGGTCGGAACAGGAGAGCGCACGAGGGAGCTTCCAGGGGGAAACGCCTGGTATCTTTATAGTCCTGTCGGGTTTCGCCACCTCTGACTTGAGCGTCGATTTTTGTGATGCTCGTCAGGGGGGCGGAGCCTATGGAAAAACGCCAGCAACGCGGCCTTTTTACGGTTCCTGGCCTTTTGCTGGCCTTTTGCTCACATGTTCTTTCCTGCGTTATCCCCTGATTCTGTGGATAACCGTATTACCGCCTTTGAGTGAGCTGATACCGCTCGCCGCAGCCGAACGACCGAGCGCAGCGAGTCAGTGAGCGAGGAAGCGGAAGAGCGCCCAATACGCAAACCGCCTCTCCCCGCGCGTTGGCCGATTCATTAATGCAGCTGGCACGACAGGTTTCCCGACTGGAAAGCGGGCAGTGAGCGCAACGCAATTAATGTGAGTTAGCTCACTCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATGTTGTGTGGAATTGTGAGCGGATAACAATTTCACACAGGAAACAGCTATGACCATGATTACGCCAAGCTTGCATGCCTGCAGGTCGACTCTAGAGGATCCCCGGGTACCGAGCTCGAATTCACTGGCCGTCGTTTTACAACGTCGTGACTGGGAAAACCCTGGCGTTACCCAACTTAATCGCCTTGCAGCACATCCCCCTTTCGCCAGCTGGCGTAATAGCGAAGAGGCCCGCACCGATCGCCCTTCCCAACAGTTGCGCAGCCTGAATGGCGAATGGCGCCTGATGCGGTATTTTCTCCTTACGCATCTGTGCGGTATTTCACACCGCATATGGTGCACTCTCAGTACAATCTGCTCTGATGCCGCATAGTTAAGCCAGCCCCGACACCCGCCAACACCCGCTGACGCGCCCTGACGGGCTTGTCTGCTCCCGGCATCCGCTTACAGACAAGCTGTGACCGTCTCCGGGAGCTGCATGTGTCAGAGGTTTTCACCGTCATCACCGAAACGCGCGAG")
        self.log.append("Loaded Demo pUC19")

    def run(self, mode):
        seq = self.txt_seq.toPlainText().strip()
        if not seq: return
        self.worker = CloningWorker(seq, mode)
        self.worker.result_signal.connect(self.handle_res)
        self.worker.start()

    def add_lane(self):
        selected = [i.text() for i in self.enz_list.selectedItems()]
        if not selected: return
        self.lane_queue.append(selected)
        self.log.append(f"Added Lane: {', '.join(selected)}")
        
    def run_gel(self):
        seq = self.txt_seq.toPlainText().strip()
        if not seq or not self.lane_queue: 
            QMessageBox.warning(self, "Error", "Load sequence and add at least one lane.")
            return
        self.worker = CloningWorker(seq, "digest", {"lanes": self.lane_queue})
        self.worker.result_signal.connect(self.handle_res)
        self.worker.start()
        self.lane_queue = []

    def handle_res(self, data):
        t = data.get("type")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # --- GENERATE PROFESSIONAL HTML REPORT ---
        report = f"""
        <div style='font-family:Segoe UI; padding:20px;'>
            <h1 style='color:#2B3674; border-bottom:2px solid #2B3674;'>🧬 Molecular Analysis Report</h1>
            <p><b>Date:</b> {timestamp}</p>
            <p><b>Tool Used:</b> {t.upper().replace('_', ' ')}</p>
            <hr>
        """
        
        if t == "plasmid_map":
            self.map_wid.update_map(data['length'], data['features'], data['sites'])
            self.tabs.setCurrentIndex(0)
            
            report += f"""
            <h3>1. Plasmid Summary</h3>
            <p>The analyzed sequence has a total length of <b>{data['length']} bp</b>.</p>
            
            <h3>2. Detected Features</h3>
            <table width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse:collapse;'>
                <tr style='background:#E9EDF7;'><th>Feature Name</th><th>Start</th><th>End</th><th>Color</th></tr>
            """
            for f in data['features']:
                report += f"<tr><td>{f['name']}</td><td>{f['start']}</td><td>{f['end']}</td><td>{f['color']}</td></tr>"
            report += "</table>"
            
            report += """
            <h3>3. Restriction Sites</h3>
            <p>The following restriction enzymes have cut sites in this sequence:</p>
            <ul>
            """
            for s in data['sites']:
                report += f"<li><b>{s['name']}</b> at position {s['pos']}</li>"
            report += "</ul>"
            
        elif t == "crispr":
            self.crispr_tab.setRowCount(0)
            self.crispr_tab.setRowCount(len(data['targets']))
            self.tabs.setCurrentIndex(1)
            
            report += f"""
            <h3>1. CRISPR Scan Results</h3>
            <p>A total of <b>{len(data['targets'])}</b> potential gRNA targets were identified using the NGG PAM search.</p>
            
            <h3>2. Top Targets (Score: High)</h3>
            <table width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse:collapse;'>
                <tr style='background:#E9EDF7;'><th>Position</th><th>Spacer Sequence (20bp)</th><th>PAM</th><th>GC Content</th><th>Score</th></tr>
            """
            for i, row in enumerate(data['targets']):
                # Update visual table
                self.crispr_tab.setItem(i, 0, QTableWidgetItem(str(row['pos'])))
                self.crispr_tab.setItem(i, 1, QTableWidgetItem(row['sequence']))
                self.crispr_tab.setItem(i, 2, QTableWidgetItem(row['pam']))
                self.crispr_tab.setItem(i, 3, QTableWidgetItem(str(row['gc'])))
                self.crispr_tab.setItem(i, 4, QTableWidgetItem(row['score']))
                
                # Add to text report
                report += f"<tr><td>{row['pos']}</td><td style='font-family:Consolas'>{row['sequence']}</td><td>{row['pam']}</td><td>{row['gc']}%</td><td>{row['score']}</td></tr>"
            report += "</table>"
            if not data['targets']: self.crispr_tab.setRowCount(50)
            
        elif t == "digest":
            self.gel_wid.update_data(data['lanes'])
            self.tabs.setCurrentIndex(2)
            
            report += f"""
            <h3>1. Virtual Digest Configuration</h3>
            <p>This simulation modeled an agarose gel electrophoresis run with <b>{len(data['lanes'])}</b> sample lanes plus a 1kb ladder.</p>
            
            <h3>2. Fragment Analysis</h3>
            <table width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse:collapse;'>
                <tr style='background:#E9EDF7;'><th>Lane #</th><th>Enzymes Used</th><th>Fragment Sizes (bp)</th></tr>
            """
            for i, lane in enumerate(data['lanes']):
                enz = ', '.join(lane['enzymes']) if lane['enzymes'] else 'Uncut'
                frags = ', '.join([str(f) for f in lane['fragments']])
                report += f"<tr><td>Lane {i+2}</td><td>{enz}</td><td>{frags}</td></tr>"
            report += "</table>"

        report += "</div>"
        self.report_box.setHtml(report)