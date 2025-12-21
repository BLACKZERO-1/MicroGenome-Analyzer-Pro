from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

class FooterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #E0E0E0; border-top: 1px solid #CCC;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.lbl_status = QLabel("System Ready")
        self.lbl_status.setStyleSheet("color: #333; font-size: 11px;")
        
        self.lbl_version = QLabel("v1.0.0")
        self.lbl_version.setStyleSheet("color: #666; font-size: 11px;")

        layout.addWidget(self.lbl_status)
        layout.addStretch()
        layout.addWidget(self.lbl_version)