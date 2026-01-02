from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

class FooterWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(35)
        self.setStyleSheet("""
            QFrame { background-color: #ffffff; border-top: 1px solid #E0E5F2; }
            QLabel { color: #707EAE; font-size: 11px; font-weight: 500; font-family: 'Segoe UI'; }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # ZONE 1: DATABASE STATUS (Left)
        self.db_status = QLabel("🟢 BLAST DB: Connected (v2.14)  |  🟢 Pfam: Loaded")
        layout.addWidget(self.db_status)
        
        layout.addStretch()
        
        # ZONE 2: CITATION (Center)
        center_box = QHBoxLayout()
        ver = QLabel("MicroGenome Pro v3.0  |  © 2025 Research Team")
        ver.setStyleSheet("font-weight: bold; color: #2B3674;")
        center_box.addWidget(ver)
        
        # Cite Button
        btn_cite = QPushButton("Cite This")
        btn_cite.setCursor(Qt.PointingHandCursor)
        btn_cite.setStyleSheet("""
            QPushButton { 
                background: #F4F7FE; border: none; color: #4318FF; 
                border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #4318FF; color: white; }
        """)
        btn_cite.clicked.connect(self.copy_citation)
        center_box.addWidget(btn_cite)
        layout.addLayout(center_box)
        
        layout.addStretch()
        
        # ZONE 3: RESOURCES (Right - Live Update)
        self.res_label = QLabel("RAM: 450MB  |  CPU: 2%")
        layout.addWidget(self.res_label)

        # Timer to simulate live resource updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_resources)
        self.timer.start(2000)

    def update_resources(self):
        # In a real app, use 'psutil' here. For now, we simulate "Live" behavior.
        import random
        cpu = random.randint(1, 15)
        ram = random.randint(400, 550)
        self.res_label.setText(f"RAM: {ram}MB  |  CPU: {cpu}%")

    def copy_citation(self):
        clipboard = QApplication.clipboard()
        clipboard.setText("MicroGenome Analyzer Pro v3.0 (2025). High-performance genomics platform.")
        # Visual feedback could be added here