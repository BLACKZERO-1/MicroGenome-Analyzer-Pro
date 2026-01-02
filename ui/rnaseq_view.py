import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('QtAgg')

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QFrame, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import the Engine
# Make sure you have created 'core/rnaseq/rnaseq_engine.py' before running this!
from core.rnaseq.rnaseq_engine import RNASeqEngine

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

class RNASeqView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.engine = RNASeqEngine(db_manager)
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.create_header()
        self.create_workspace()

    def create_header(self):
        header = QFrame()
        header.setStyleSheet("background: white; border: 1px solid #CCC; border-radius: 6px;")
        header.setFixedHeight(70)
        
        lay = QHBoxLayout(header)
        
        lbl_title = QLabel("📊 Transcriptomics (RNA-Seq)")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        
        self.btn_load = QPushButton("📂 Load DESeq2 Results (.csv)")
        self.btn_load.setStyleSheet("background: #2980B9; color: white; font-weight: bold; padding: 6px;")
        self.btn_load.clicked.connect(self.load_data)

        lay.addWidget(lbl_title)
        lay.addStretch()
        lay.addWidget(self.btn_load)
        
        self.layout.addWidget(header)

    def create_workspace(self):
        splitter = QSplitter(Qt.Horizontal)
        
        # --- LEFT: Table ---
        table_grp = QGroupBox("Top Significant Genes")
        v_table = QVBoxLayout(table_grp)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Gene", "Log2FC", "P-Adj"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v_table.addWidget(self.table)
        
        # --- RIGHT: Plot ---
        plot_grp = QGroupBox("Differential Expression Analysis")
        v_plot = QVBoxLayout(plot_grp)
        
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        v_plot.addWidget(self.canvas)
        
        splitter.addWidget(table_grp)
        splitter.addWidget(plot_grp)
        splitter.setSizes([350, 700])
        
        self.layout.addWidget(splitter)

    def load_data(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not fname: return
        
        # 1. Load via Engine
        result = self.engine.load_expression_data(fname)
        
        if result.get("status") == "error":
            QMessageBox.critical(self, "Load Error", result.get("message"))
            return
            
        # 2. Update Table
        self.update_table()
        
        # 3. Update Plot
        self.update_plot()

    def update_table(self):
        top_genes = self.engine.get_top_genes(100)
        self.table.setRowCount(len(top_genes))
        
        for i, row in enumerate(top_genes):
            self.table.setItem(i, 0, QTableWidgetItem(row['gene']))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['fc']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row['pval']:.4e}"))
            
            # Color coding
            if row['fc'] > 1 and row['pval'] < 0.05:
                self.table.item(i, 1).setForeground(Qt.red)
            elif row['fc'] < -1 and row['pval'] < 0.05:
                self.table.item(i, 1).setForeground(Qt.blue)

    def update_plot(self):
        data = self.engine.get_volcano_data()
        if not data: return
        
        ax = self.canvas.axes
        ax.clear()
        
        # Scatter Plot
        # Colors: Red (UP), Blue (DOWN), Grey (Neutral)
        colors = []
        for status in data['status']:
            if status == 'UP': colors.append('#E74C3C')
            elif status == 'DOWN': colors.append('#3498DB')
            else: colors.append('#95A5A6')
            
        ax.scatter(data['x'], data['y'], c=colors, s=15, alpha=0.6)
        
        # Labels and Lines
        ax.set_title("Volcano Plot", fontsize=10, fontweight='bold')
        ax.set_xlabel("Log2 Fold Change")
        ax.set_ylabel("-Log10 P-Value")
        
        # Threshold lines
        ax.axvline(x=1, color='black', linestyle='--', linewidth=0.5)
        ax.axvline(x=-1, color='black', linestyle='--', linewidth=0.5)
        ax.axhline(y=-np.log10(0.05), color='black', linestyle='--', linewidth=0.5)
        
        self.canvas.draw()