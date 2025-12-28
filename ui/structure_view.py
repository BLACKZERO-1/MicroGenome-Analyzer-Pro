import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QTextEdit, QMessageBox, QComboBox, QFileDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView 
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QColor, QPixmap

# IMPORT ENGINE
from core.structure.structure_engine import StructureWorker

class StructureView(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db = db_manager
        self.pdb_path = None
        
        self.setStyleSheet("""
            QWidget { background-color: #F4F7FE; font-family: 'Segoe UI'; }
            
            QFrame { background: white; border-radius: 12px; border: 1px solid #E0E5F2; }
            
            QLabel { color: #2B3674; font-weight: bold; border: none; }
            
            QPushButton { 
                background: #4318FF; color: white; border-radius: 6px; 
                padding: 10px; font-weight: bold; border: 1px solid #2B3674;
            }
            QPushButton:hover { background: #3311CC; }
            QPushButton:disabled { background: #A3AED0; border: none; }
            
            /* DROPDOWN STYLE */
            QComboBox {
                background-color: white; color: #2B3674; border: 1px solid #E0E5F2;
                border-radius: 6px; padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white; color: #2B3674; selection-background-color: #4318FF;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(20)
        
        # --- LEFT PANEL (Controls) ---
        left_panel = QFrame(); left_panel.setFixedWidth(300)
        l_layout = QVBoxLayout(left_panel)
        
        # Header
        l_layout.addWidget(QLabel("🧪 3D Structure Viewer", styleSheet="font-size: 18px;"))
        l_layout.addWidget(QLabel("Molecular visualization & docking analysis.", styleSheet="color: #A3AED0; font-weight: normal; font-size:11px;"))
        l_layout.addSpacing(20)
        
        # Input
        l_layout.addWidget(QLabel("Target Protein:"))
        self.combo_protein = QComboBox()
        self.combo_protein.addItems(["Sample: Ubiquitin (1UBQ)", "Sample: Hemoglobin (1A3N)", "Sample: Insulin (4INS)"])
        l_layout.addWidget(self.combo_protein)
        
        self.btn_fetch = QPushButton("⬇️ Fetch Structure")
        self.btn_fetch.clicked.connect(self.run_fetch)
        l_layout.addWidget(self.btn_fetch)
        
        l_layout.addSpacing(20)
        l_layout.addWidget(QLabel("Visualization Mode:"))
        
        # Style Buttons
        row1 = QHBoxLayout()
        self.btn_cartoon = QPushButton("Cartoon")
        self.btn_cartoon.setStyleSheet("background: #E9EDF7; color: #4318FF; border: 1px solid #D0D7DE;")
        self.btn_cartoon.clicked.connect(lambda: self.update_style("cartoon"))
        
        self.btn_surface = QPushButton("Surface (Skin)")
        self.btn_surface.setStyleSheet("background: #E9EDF7; color: #4318FF; border: 1px solid #D0D7DE;")
        self.btn_surface.clicked.connect(lambda: self.update_style("surface"))
        row1.addWidget(self.btn_cartoon); row1.addWidget(self.btn_surface)
        l_layout.addLayout(row1)
        
        # Advanced Buttons
        self.btn_ligand = QPushButton("💊 Highlight Ligands")
        self.btn_ligand.setStyleSheet("background: #05CD99; color: white; border: none;")
        self.btn_ligand.clicked.connect(lambda: self.update_style("ligand"))
        l_layout.addWidget(self.btn_ligand)

        l_layout.addStretch()
        
        # Snapshot
        self.btn_snap = QPushButton("📷 Take Snapshot")
        self.btn_snap.setStyleSheet("background: #FFAB00; color: black; border: none;")
        self.btn_snap.clicked.connect(self.take_snapshot)
        l_layout.addWidget(self.btn_snap)
        
        # Logs
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True); self.terminal.setMaximumHeight(100)
        self.terminal.setStyleSheet("background: #111C44; color: #00E676; font-family: Consolas; border-radius: 6px; margin-top: 10px;")
        l_layout.addWidget(self.terminal)
        
        layout.addWidget(left_panel)
        
        # --- RIGHT PANEL (Web Engine) ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background: black; border: 4px solid #2B3674; border-radius: 8px;")
        r_layout = QVBoxLayout(right_panel); r_layout.setContentsMargins(0,0,0,0)
        
        self.webview = QWebEngineView()
        self.webview.setStyleSheet("background: black;")
        r_layout.addWidget(self.webview)
        
        self.set_placeholder()
        layout.addWidget(right_panel)

    # --- LOGIC ---

    def set_placeholder(self):
        html = """
        <html><body style="background:black; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
            <div style="text-align:center;">
                <h1 style="color:#4318FF;">🧬 Ready to Render</h1>
                <p>Select a protein ID to visualize 3D structure.</p>
            </div>
        </body></html>
        """
        self.webview.setHtml(html)

    def run_fetch(self):
        self.btn_fetch.setEnabled(False)
        self.terminal.clear()
        
        selection = self.combo_protein.currentText()
        search_id = "1UBQ"
        if "Hemoglobin" in selection: search_id = "1A3N"
        if "Insulin" in selection: search_id = "4INS"
        
        self.worker = StructureWorker(uniprot_id=search_id)
        self.worker.log_signal.connect(self.terminal.append)
        self.worker.result_signal.connect(self.render_structure)
        self.worker.finished_signal.connect(lambda: self.btn_fetch.setEnabled(True))
        self.worker.start()

    def render_structure(self, pdb_path):
        self.pdb_path = pdb_path
        with open(pdb_path, "r") as f:
            pdb_data = f.read().replace("\n", "\\n")
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
            <style>
                html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:black; }}
                #container {{ width:100%; height:100%; position:relative; }}
                #tooltip {{
                    position: absolute; background: rgba(0, 0, 0, 0.85); color: #00E676;
                    padding: 8px; border-radius: 4px; font-family: sans-serif; font-size: 12px;
                    pointer-events: none; display: none; border: 1px solid #4318FF; z-index: 100;
                }}
            </style>
        </head>
        <body>
            <div id="tooltip"></div>
            <div id="container"></div>
            <script>
                let element = document.getElementById('container');
                let tooltip = document.getElementById('tooltip');
                let viewer = $3Dmol.createViewer(element, {{ backgroundColor: 'black' }});
                let pdbData = "{pdb_data}";
                
                viewer.addModel(pdbData, "pdb");
                viewer.setStyle({{}}, {{cartoon: {{color: 'spectrum'}}}});
                viewer.zoomTo();
                
                // HOVER INTERACTION
                viewer.setHoverable({{}}, true,
                    function(atom, viewer, event, container) {{
                        if(!atom.label) {{
                            tooltip.style.display = 'block';
                            tooltip.style.left = event.x + 10 + 'px';
                            tooltip.style.top = event.y + 10 + 'px';
                            tooltip.innerHTML = '<b>' + atom.resn + ' ' + atom.resi + '</b><br>' + atom.atom;
                        }}
                    }},
                    function(atom) {{ tooltip.style.display = 'none'; }}
                );
                
                viewer.render();

                // EXPOSED FUNCTIONS FOR PYTHON
                window.setCartoon = function() {{
                    viewer.removeAllSurfaces();
                    viewer.setStyle({{}}, {{cartoon: {{color: 'spectrum'}}}});
                    viewer.render();
                }}
                
                window.setSurface = function() {{
                    viewer.setStyle({{}}, {{cartoon: {{color: 'spectrum', opacity:0.5}}}});
                    viewer.addSurface($3Dmol.SurfaceType.VDW, {{opacity:0.6, color:'spectrum'}});
                    viewer.render();
                }}
                
                window.showLigands = function() {{
                    viewer.removeAllSurfaces();
                    // Make main protein Ghost
                    viewer.setStyle({{}}, {{cartoon: {{color: 'white', opacity: 0.3}}}});
                    // Highlight Ligands (HETATM) in Green Stick
                    viewer.setStyle({{hetflag:true}}, {{stick:{{colorscheme:'greenCarbon', radius:0.3}}}});
                    viewer.zoomTo({{hetflag:true}});
                    viewer.render();
                }}
            </script>
        </body>
        </html>
        """
        self.webview.setHtml(html)

    def update_style(self, style):
        if not self.pdb_path: return
        
        if style == "cartoon":
            self.webview.page().runJavaScript("window.setCartoon();")
        elif style == "surface":
            self.webview.page().runJavaScript("window.setSurface();")
        elif style == "ligand":
            self.webview.page().runJavaScript("window.showLigands();")

    def take_snapshot(self):
        if not self.pdb_path: return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", "protein_structure.png", "Images (*.png)")
        if file_path:
            # Captures the current state of the WebEngine Widget
            self.webview.grab().save(file_path)
            self.terminal.append(f"✅ Snapshot saved to {os.path.basename(file_path)}")