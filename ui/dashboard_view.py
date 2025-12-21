import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QGraphicsDropShadowEffect, 
                               QGridLayout, QProgressBar, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()

        # ==========================================================================
        # STYLING (HIGH CONTRAST FIX)
        # ==========================================================================
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI', sans-serif; }
            
            /* HEADERS - Dark Navy for maximum visibility */
            QLabel#dash_title { color: #1B254B; font-size: 26px; font-weight: 900; }
            QLabel#dash_subtitle { color: #4A5568; font-size: 14px; font-weight: 600; } /* Dark Grey */
            QLabel#section_title { color: #1B254B; font-size: 18px; font-weight: 800; margin-bottom: 10px; }

            /* CARDS */
            QFrame#white_card { 
                background-color: #FFFFFF; 
                border-radius: 20px; 
                border: 1px solid #E0E5F2; /* Subtle border for definition */
            }
            
            /* STAT TEXT */
            QLabel#card_label { color: #4A5568; font-size: 12px; font-weight: 700; } /* Dark Grey */
            QLabel#card_value { color: #1B254B; font-size: 28px; font-weight: 900; } /* Dark Navy */
            
            /* TABLE */
            QTableWidget {
                background-color: white; border: none; gridline-color: #E0E5F2;
                color: #1B254B; font-weight: 600;
            }
            QHeaderView::section {
                background-color: #F4F7FE; border: none; 
                color: #1B254B; /* Dark Navy Headers */
                font-weight: 700; padding: 10px;
            }
            
            /* QUICK ACTION BUTTONS */
            QPushButton#action_btn {
                background-color: #FFFFFF; /* White background */
                color: #2B3674; /* Dark Blue Text */
                border: 2px solid #E0E5F2;
                border-radius: 15px; 
                font-weight: 700; font-size: 13px; text-align: left; padding: 20px;
            }
            QPushButton#action_btn:hover {
                background-color: #F4F7FE; border: 2px solid #4318FF; color: #4318FF;
            }
            
            /* USER BADGE */
            QLabel#user_badge {
                background-color: #FFFFFF; color: #2B3674; font-weight: 700;
                padding: 10px 20px; border-radius: 20px; border: 1px solid #E0E5F2;
            }

            /* SYSTEM BARS */
            QProgressBar { background: #E0E5F2; border-radius: 4px; height: 8px; text-align: center; }
            QProgressBar::chunk { background: #4318FF; border-radius: 4px; }
        """)

        # Scrollable Main Area
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(30)

        # --- BUILD UI ---
        self.setup_header()
        self.setup_stats_row()
        
        split_layout = QHBoxLayout()
        split_layout.setSpacing(30)
        
        self.setup_recent_projects(split_layout)
        self.setup_quick_actions(split_layout)
        
        self.layout.addLayout(split_layout)
        self.layout.addStretch()

        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)

    def setup_header(self):
        h = QHBoxLayout()
        v = QVBoxLayout()
        
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        t1 = QLabel("Dashboard Overview"); t1.setObjectName("dash_title")
        t2 = QLabel(f"MicroGenome Analyzer Pro • {date_str}"); t2.setObjectName("dash_subtitle")
        
        v.addWidget(t1); v.addWidget(t2)
        h.addLayout(v); h.addStretch()
        
        # User Profile
        user = QLabel("👤 Admin User"); user.setObjectName("user_badge")
        h.addWidget(user)
        
        self.layout.addLayout(h)

    def setup_stats_row(self):
        """Row of 4 white cards"""
        row = QHBoxLayout(); row.setSpacing(20)
        
        c1 = self.create_metric_card("Genomes Processed", "1,240", "🧬", "#4318FF")
        c2 = self.create_metric_card("Analysis Hours", "342h", "⏱️", "#05CD99")
        c3 = self.create_metric_card("Critical Alerts", "5 New", "🛡️", "#FF5B5B")
        c4 = self.create_metric_card("Storage Used", "12 GB", "💾", "#FFAB00")
        
        row.addWidget(c1); row.addWidget(c2); row.addWidget(c3); row.addWidget(c4)
        self.layout.addLayout(row)

    def setup_recent_projects(self, parent_layout):
        """Table styled list"""
        container = QWidget()
        l = QVBoxLayout(container); l.setContentsMargins(0,0,0,0)
        
        lbl = QLabel("Recent Analysis Projects"); lbl.setObjectName("section_title")
        l.addWidget(lbl)
        
        card = QFrame(); card.setObjectName("white_card"); self.apply_shadow(card)
        cl = QVBoxLayout(card); cl.setContentsMargins(20,20,20,20)
        
        # Table
        table = QTableWidget(5, 3)
        table.setHorizontalHeaderLabels(["Filename", "Module", "Status"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.NoFocus)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFixedHeight(250)

        # Fake Data
        data = [
            ("E_coli_K12.fasta", "Annotation", "Completed"),
            ("Sample_042.fna", "AMR Screen", "Threat Found"),
            ("Unknown_Isolate.fa", "Phylogenetics", "Processing..."),
            ("Batch_Run_09.fasta", "Comparative", "Completed"),
            ("Metabolic_Map_A.txt", "Pathways", "Completed")
        ]
        
        for r, (name, mod, status) in enumerate(data):
            table.setItem(r, 0, QTableWidgetItem(name))
            table.setItem(r, 1, QTableWidgetItem(mod))
            
            # Status Badge Logic
            item = QTableWidgetItem(status)
            if "Threat" in status: item.setForeground(QColor("#FF5B5B"))
            elif "Processing" in status: item.setForeground(QColor("#FFAB00"))
            else: item.setForeground(QColor("#05CD99"))
            table.setItem(r, 2, item)

        cl.addWidget(table)
        l.addWidget(card)
        
        parent_layout.addWidget(container, 2)

    def setup_quick_actions(self, parent_layout):
        """Right side buttons"""
        container = QWidget()
        l = QVBoxLayout(container); l.setContentsMargins(0,0,0,0)
        
        lbl = QLabel("Quick Actions"); lbl.setObjectName("section_title")
        l.addWidget(lbl)
        
        card = QFrame(); card.setObjectName("white_card"); self.apply_shadow(card)
        cl = QVBoxLayout(card); cl.setContentsMargins(20,20,20,20); cl.setSpacing(15)
        
        b1 = QPushButton("⚡  Start New Annotation")
        b1.setObjectName("action_btn"); b1.setCursor(Qt.PointingHandCursor)
        
        b2 = QPushButton("📂  Import Batch Genomes")
        b2.setObjectName("action_btn"); b2.setCursor(Qt.PointingHandCursor)
        
        b3 = QPushButton("⚙️  System Settings")
        b3.setObjectName("action_btn"); b3.setCursor(Qt.PointingHandCursor)

        # System Load Mini
        sys_lbl = QLabel("System Load"); sys_lbl.setStyleSheet("color: #4A5568; font-weight: 700; margin-top: 10px;")
        bar = QProgressBar(); bar.setValue(24); bar.setTextVisible(False)

        cl.addWidget(b1); cl.addWidget(b2); cl.addWidget(b3)
        cl.addWidget(sys_lbl); cl.addWidget(bar)
        cl.addStretch()
        
        l.addWidget(card)
        parent_layout.addWidget(container, 1)

    # --- HELPERS ---
    def create_metric_card(self, title, value, icon, color):
        card = QFrame(); card.setObjectName("white_card"); self.apply_shadow(card)
        l = QHBoxLayout(card); l.setContentsMargins(20, 20, 20, 20)
        
        # Icon
        ico = QLabel(icon); ico.setFixedSize(50, 50); ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet(f"background-color: {color}15; color: {color}; border-radius: 25px; font-size: 22px;")
        
        v = QVBoxLayout()
        t = QLabel(title); t.setObjectName("card_label")
        val = QLabel(value); val.setObjectName("card_value"); val.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 900;")
        
        v.addWidget(t); v.addWidget(val)
        l.addWidget(ico); l.addSpacing(15); l.addLayout(v)
        return card

    def apply_shadow(self, w):
        e = QGraphicsDropShadowEffect(); e.setBlurRadius(20); e.setColor(QColor(112, 144, 176, 20)); e.setOffset(0, 5); w.setGraphicsEffect(e)