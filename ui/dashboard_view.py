import random
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, 
    QListWidget, QListWidgetItem, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QTime, Slot
from PySide6.QtGui import QColor, QFont, QBrush, QLinearGradient, QGradient

# --- CONFIGURATION & COLORS ---
COLORS = {
    "header_start": "#4318FF",
    "header_end": "#7c3aed",
    "bg_metrics": "#F4F7FE",
    "bg_main": "#FAFBFC",
    "bg_right": "#F8F7FF",
    "footer": "#2D3748",
    "card_bg": "#FFFFFF",
    "text_dark": "#1B2559",
    "text_gray": "#A3AED0",
    "accent_purple": "#4318FF",
    "accent_green": "#05CD99",
    "accent_red": "#FF5B5B",
    "accent_orange": "#FFAB00",
}

STYLES = {
    "card": f"""
        QFrame {{
            background-color: {COLORS['card_bg']};
            border-radius: 15px;
            border: 1px solid #E0E5F2;
        }}
    """,
    "metric_card": f"""
        QFrame {{
            background-color: {COLORS['card_bg']};
            border-radius: 15px;
            border-bottom: 3px solid #E0E5F2;
        }}
        QFrame:hover {{
            border-bottom: 3px solid {COLORS['accent_purple']};
            margin-top: -3px; 
        }}
    """,
    "btn_action": f"""
        QPushButton {{
            background-color: {COLORS['accent_purple']};
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-weight: bold;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: #3311CC;
        }}
    """
}

# --- CUSTOM WIDGETS ---

class MetricCard(QFrame):
    def __init__(self, title, value, icon, accent_color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border-left: 6px solid {accent_color};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        self.setFixedSize(220, 100)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        
        # Header Row
        h_layout = QHBoxLayout()
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setStyleSheet(f"font-size: 24px; color: {accent_color};")
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 14px; font-weight: 500;")
        h_layout.addWidget(self.icon_lbl)
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()
        
        # Value Row
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color: {COLORS['text_dark']}; font-size: 24px; font-weight: bold;")
        
        # Trend (Simulated)
        self.trend_lbl = QLabel("↗ +12%")
        self.trend_lbl.setStyleSheet("color: #05CD99; font-size: 12px; font-weight: bold;")
        
        layout.addLayout(h_layout)
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.trend_lbl)

    def update_data(self, new_value, is_up):
        self.value_lbl.setText(new_value)
        if is_up:
            self.trend_lbl.setText("↗ Rising")
            self.trend_lbl.setStyleSheet("color: #05CD99; font-size: 12px; font-weight: bold;")
        else:
            self.trend_lbl.setText("↘ Falling")
            self.trend_lbl.setStyleSheet("color: #FF5B5B; font-size: 12px; font-weight: bold;")

class LiveProgressBar(QProgressBar):
    def __init__(self, color):
        super().__init__()
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #E9EDF7;
                border-radius: 4px;
                height: 8px;
                text-align: center; 
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        self.setTextVisible(False)
        self.setValue(random.randint(20, 80))

class DashboardView(QWidget):
    # --- UPDATED INIT METHOD TO FIX CRASH ---
    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db = db_manager  # Store the database manager reference
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. BUILD HEADER (Deep Purple Gradient)
        self.build_header()
        
        # 2. BUILD METRICS BANNER (Light Blue)
        self.build_metrics()
        
        # 3. BUILD MAIN CONTENT (Split View)
        self.build_main_content()
        
        # 4. BUILD FOOTER (Dark Slate)
        self.build_footer()
        
        # --- TIMERS FOR LIVE EFFECTS ---
        self.setup_live_data()

    def build_header(self):
        header = QFrame()
        header.setFixedHeight(85)
        # Gradient background using CSS
        header.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                                  stop:0 {COLORS['header_start']}, stop:1 {COLORS['header_end']});
                border: none;
            }}
            QLabel {{ color: white; background: transparent; }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 0, 40, 0)
        
        # Logo Area
        logo = QLabel("🧬")
        logo.setFont(QFont("Segoe UI", 24))
        title_box = QVBoxLayout()
        title = QLabel("Dashboard Overview")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        subtitle = QLabel(f"Live Monitor • {datetime.date.today().strftime('%b %d, %Y')}")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        
        layout.addWidget(logo)
        layout.addSpacing(10)
        layout.addLayout(title_box)
        layout.addStretch()
        
        # Right Side Icons
        search_btn = QPushButton("🔍 Search")
        search_btn.setStyleSheet("background: rgba(255,255,255,0.2); border-radius: 15px; color: white; padding: 5px 15px;")
        
        self.notif_btn = QPushButton("🔔 3")
        self.notif_btn.setStyleSheet("border: 1px solid white; border-radius: 15px; color: white; padding: 5px 15px;")
        
        user_lbl = QLabel("👤 Admin")
        
        layout.addWidget(search_btn)
        layout.addSpacing(10)
        layout.addWidget(self.notif_btn)
        layout.addSpacing(15)
        layout.addWidget(user_lbl)
        
        self.main_layout.addWidget(header)

    def build_metrics(self):
        banner = QFrame()
        banner.setStyleSheet(f"background-color: {COLORS['bg_metrics']};")
        banner.setFixedHeight(160)
        
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(25)
        
        # Create Cards
        self.card_genomes = MetricCard("Total Genomes", "1,240", "🧬", COLORS['accent_purple'])
        self.card_hours = MetricCard("Compute Hours", "342h", "⏱️", COLORS['accent_green'])
        self.card_alerts = MetricCard("Active Alerts", "5", "🛡️", COLORS['accent_red'])
        self.card_storage = MetricCard("Storage Used", "12GB", "💾", COLORS['accent_orange'])
        
        layout.addWidget(self.card_genomes)
        layout.addWidget(self.card_hours)
        layout.addWidget(self.card_alerts)
        layout.addWidget(self.card_storage)
        layout.addStretch()
        
        # Live Indicator
        live_lbl = QLabel("🔴 LIVE UPDATES")
        live_lbl.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        
        # Put live label in a vertical box at the end
        v_box = QVBoxLayout()
        v_box.addStretch()
        v_box.addWidget(live_lbl)
        v_box.addStretch()
        layout.addLayout(v_box)
        
        self.main_layout.addWidget(banner)

    def build_main_content(self):
        content_wrapper = QWidget()
        content_layout = QHBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # --- LEFT PANEL (60% White/Gray) ---
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 30, 20, 30)
        left_layout.setSpacing(20)
        
        # Section 1: Active Projects Table
        lbl_projects = QLabel("📊 ACTIVE PROJECTS")
        lbl_projects.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 14px;")
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Project ID", "Module", "Progress", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid #E0E5F2;
                gridline-color: transparent;
                padding: 10px;
            }}
            QHeaderView::section {{
                background-color: white;
                color: {COLORS['text_gray']};
                border: none;
                font-weight: bold;
                padding: 5px;
            }}
            QTableWidget::item {{
                padding: 5px;
                color: {COLORS['text_dark']};
            }}
        """)
        
        # Populate initial table
        data = [
            ("PRJ-1024", "AMR Detection", 75, "Running"),
            ("PRJ-1025", "Phylogenetics", 10, "Queued"),
            ("PRJ-1021", "Virulence", 100, "Completed"),
        ]
        self.table.setRowCount(len(data))
        for r, (pid, mod, prog, stat) in enumerate(data):
            self.table.setItem(r, 0, QTableWidgetItem(pid))
            self.table.setItem(r, 1, QTableWidgetItem(mod))
            
            # Progress Bar in Cell
            p_bar = QProgressBar()
            p_bar.setValue(prog)
            if prog == 100:
                p_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['accent_green']}; border-radius: 4px; }} QProgressBar {{ background: #E9EDF7; border-radius: 4px; height: 6px; border: none; }}")
            else:
                p_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['accent_purple']}; border-radius: 4px; }} QProgressBar {{ background: #E9EDF7; border-radius: 4px; height: 6px; border: none; }}")
            p_bar.setTextVisible(False)
            self.table.setCellWidget(r, 2, p_bar)
            
            # Status Badge
            item_stat = QTableWidgetItem(stat)
            if stat == "Running": item_stat.setForeground(QBrush(QColor(COLORS['accent_orange'])))
            elif stat == "Completed": item_stat.setForeground(QBrush(QColor(COLORS['accent_green'])))
            else: item_stat.setForeground(QBrush(QColor(COLORS['text_gray'])))
            self.table.setItem(r, 3, item_stat)
            
        left_layout.addWidget(lbl_projects)
        left_layout.addWidget(self.table)
        
        # Section 2: Module Usage (Simple Visualization)
        chart_frame = QFrame()
        chart_frame.setStyleSheet(STYLES['card'])
        chart_layout = QVBoxLayout(chart_frame)
        
        lbl_chart = QLabel("📈 MODULE USAGE DISTRIBUTION")
        lbl_chart.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        chart_layout.addWidget(lbl_chart)
        
        modules = [("AMR Analysis", 80, COLORS['accent_red']), 
                   ("Virulence", 65, COLORS['accent_purple']), 
                   ("Plasmid", 40, COLORS['accent_orange'])]
        
        for name, val, col in modules:
            h = QHBoxLayout()
            l = QLabel(name)
            l.setFixedWidth(100)
            p = QProgressBar()
            p.setValue(val)
            p.setTextVisible(False)
            p.setStyleSheet(f"QProgressBar::chunk {{ background-color: {col}; border-radius: 4px; }} QProgressBar {{ background: #E9EDF7; border-radius: 4px; height: 10px; border: none; }}")
            h.addWidget(l)
            h.addWidget(p)
            chart_layout.addLayout(h)
            
        left_layout.addWidget(chart_frame)

        # --- RIGHT PANEL (40% Lavender Tint) ---
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {COLORS['bg_right']}; border-left: 1px solid #E0E5F2;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 30, 40, 30)
        right_layout.setSpacing(20)
        
        # Quick Actions
        lbl_actions = QLabel("⚡ QUICK ACTIONS")
        lbl_actions.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        right_layout.addWidget(lbl_actions)
        
        act_box = QFrame()
        act_box.setStyleSheet(f"background-color: white; border-radius: 15px; border: 1px solid #E9D5FF; padding: 15px;")
        act_layout = QVBoxLayout(act_box)
        
        btn1 = QPushButton("➕ Start New Analysis")
        btn1.setStyleSheet(STYLES['btn_action'])
        btn2 = QPushButton("📂 Import FASTQ Files")
        btn2.setStyleSheet(f"background-color: white; color: {COLORS['accent_purple']}; border: 1px solid {COLORS['accent_purple']}; border-radius: 10px; padding: 10px; font-weight: bold;")
        
        act_layout.addWidget(btn1)
        act_layout.addWidget(btn2)
        right_layout.addWidget(act_box)
        
        # Activity Feed
        lbl_feed = QLabel("⏱️ LIVE ACTIVITY")
        lbl_feed.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        right_layout.addWidget(lbl_feed)
        
        self.feed_list = QListWidget()
        self.feed_list.setStyleSheet(f"""
            QListWidget {{ background-color: white; border-radius: 15px; border: 1px solid #D1FAE5; padding: 10px; outline: none; }}
            QListWidget::item {{ padding: 10px; border-bottom: 1px solid #F3F4F6; color: {COLORS['text_dark']}; }}
        """)
        initial_feed = ["✅ System initialized", "ℹ️ Database connected (Local)", "⚠️ High memory usage detected"]
        for f in initial_feed:
            self.feed_list.addItem(f)
            
        right_layout.addWidget(self.feed_list)
        
        # System Pulse
        lbl_sys = QLabel("💻 SYSTEM HEALTH")
        lbl_sys.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        right_layout.addWidget(lbl_sys)
        
        sys_box = QFrame()
        sys_box.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #FED7AA; padding: 15px;")
        sys_layout = QVBoxLayout(sys_box)
        
        self.cpu_bar = LiveProgressBar(COLORS['accent_red'])
        self.ram_bar = LiveProgressBar(COLORS['accent_purple'])
        
        sys_layout.addWidget(QLabel("CPU Load"))
        sys_layout.addWidget(self.cpu_bar)
        sys_layout.addWidget(QLabel("RAM Usage"))
        sys_layout.addWidget(self.ram_bar)
        
        right_layout.addWidget(sys_box)
        right_layout.addStretch()

        # Add panels to content layout
        content_layout.addWidget(left_panel, 60)
        content_layout.addWidget(right_panel, 40)
        
        self.main_layout.addWidget(content_wrapper)

    def build_footer(self):
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"background-color: {COLORS['footer']}; border-top: 1px solid #4B5563;")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 0, 20, 0)
        
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet("color: #E5E7EB; font-family: monospace;")
        
        db_status = QLabel("● Database: Connected")
        db_status.setStyleSheet(f"color: {COLORS['accent_green']}; font-weight: bold;")
        
        refresh_lbl = QLabel("Auto-refresh: 2s")
        refresh_lbl.setStyleSheet("color: #A0AEC0;")
        
        layout.addWidget(self.time_lbl)
        layout.addSpacing(20)
        layout.addWidget(db_status)
        layout.addStretch()
        layout.addWidget(refresh_lbl)
        
        self.main_layout.addWidget(footer)

    # --- LIVE DATA LOGIC ---
    
    def setup_live_data(self):
        # 1. Clock & System (Fast - 1s)
        self.timer_fast = QTimer()
        self.timer_fast.timeout.connect(self.update_fast)
        self.timer_fast.start(1000)
        
        # 2. Metrics & Table (Medium - 3s)
        self.timer_med = QTimer()
        self.timer_med.timeout.connect(self.update_metrics)
        self.timer_med.start(3000)
        
        # 3. Activity Feed (Random)
        self.timer_feed = QTimer()
        self.timer_feed.timeout.connect(self.add_activity)
        self.timer_feed.start(5000)

    def update_fast(self):
        # Update Time
        now = QTime.currentTime()
        self.time_lbl.setText(f"Last Update: {now.toString('HH:mm:ss')}")
        
        # Jiggle System Bars
        cpu = self.cpu_bar.value() + random.randint(-5, 5)
        ram = self.ram_bar.value() + random.randint(-3, 3)
        self.cpu_bar.setValue(max(0, min(100, cpu)))
        self.ram_bar.setValue(max(0, min(100, ram)))

    def update_metrics(self):
        # Randomly change one metric to simulate data flow
        target = random.choice([self.card_genomes, self.card_hours, self.card_storage])
        
        if target == self.card_genomes:
            # Simple string parsing for the demo
            try:
                val = int(target.value_lbl.text().replace(",","")) + random.randint(0, 5)
                target.update_data(f"{val:,}", True)
            except:
                pass
        
        # Update Running Progress in Table
        running_bar = self.table.cellWidget(0, 2) # Assuming row 0 is running
        if running_bar:
            new_val = running_bar.value() + 2
            if new_val > 100: new_val = 0
            running_bar.setValue(new_val)

    def add_activity(self):
        actions = [
            ("ℹ️ Analysis step completed", "#3B82F6"),
            ("✅ New genome indexed", COLORS['accent_green']),
            ("⚠️ Connection latency", COLORS['accent_orange']),
            ("📂 Batch export started", COLORS['accent_purple'])
        ]
        text, col = random.choice(actions)
        
        item = QListWidgetItem(f"{text} ({QTime.currentTime().toString('HH:mm')})")
        self.feed_list.insertItem(0, item)
        if self.feed_list.count() > 8:
            self.feed_list.takeItem(8)
            
        # Flash notification badge
        try:
            current = int(self.notif_btn.text().split()[-1])
            self.notif_btn.setText(f"🔔 {current + 1}")
            self.notif_btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 15px; border: none;")
            QTimer.singleShot(500, lambda: self.notif_btn.setStyleSheet("border: 1px solid white; border-radius: 15px; color: white; background: transparent;"))
        except:
            pass
        