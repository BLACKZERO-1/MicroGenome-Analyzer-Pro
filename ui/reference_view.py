import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QComboBox, QProgressBar, QCompleter,
    QListView, QTextEdit, QDialog, QFormLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QStringListModel
from PySide6.QtGui import QColor, QFont

from core.reference.reference_engine import (
    UniversalDownloadEngine, UniversalSearchEngine, 
    MetadataEngine, IndexEngine
)

class ReferenceManagerView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        self.ref_library = []
        self.current_search = None
        self.active_workers = [] 
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)
        self.search_timer.timeout.connect(self.perform_live_search)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15) 
        self.layout.setContentsMargins(15, 15, 15, 15)

        self.create_top_bar()
        self.create_main_content()
        self.create_action_bar()

    def create_top_bar(self):
        container = QFrame()
        container.setStyleSheet("background: white; border: 1px solid #CCC; border-radius: 6px;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(15, 15, 15, 15)
        
        r1 = QHBoxLayout()
        t = QLabel("📚 Universal Data Hub")
        t.setStyleSheet("font-weight: 900; font-size: 18px; color: black; border: none;")
        self.lbl_stats = QLabel("0 Files")
        self.lbl_stats.setStyleSheet("background: #EEE; color: black; padding: 5px; border-radius: 4px;")
        r1.addWidget(t)
        r1.addStretch()
        r1.addWidget(self.lbl_stats)
        
        r2 = QHBoxLayout()
        r2.setSpacing(10)
        self.combo_source = QComboBox()
        self.combo_source.addItems(["NCBI GenBank (DNA)", "NCBI Protein", "RCSB PDB"])
        self.combo_source.setFixedWidth(180)
        self.combo_source.setFixedHeight(40)
        self.combo_source.setStyleSheet("border: 1px solid #888; color: black;")
        
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Search Accession or Organism...")
        self.inp_search.setFixedHeight(40)
        self.inp_search.textChanged.connect(lambda: self.search_timer.start())
        self.inp_search.setStyleSheet("border: 1px solid #888; padding-left: 10px; color: black;")
        
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        popup = QListView()
        popup.setStyleSheet("QListView { background: white; color: black; border: 1px solid #333; }")
        self.completer.setPopup(popup)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.inp_search.setCompleter(self.completer)
        self.completer.activated.connect(self.on_completer_activated)
        
        self.btn_fetch = QPushButton("Download")
        self.btn_fetch.setFixedSize(120, 40)
        self.btn_fetch.clicked.connect(self.start_download)
        self.btn_fetch.setStyleSheet("background: #222; color: white; font-weight: bold;")
        
        self.pbar = QProgressBar()
        self.pbar.setFixedWidth(100); self.pbar.setVisible(False)

        r2.addWidget(QLabel("Source:", styleSheet="border:none; color:black;"))
        r2.addWidget(self.combo_source)
        r2.addWidget(self.inp_search)
        r2.addWidget(self.pbar)
        r2.addWidget(self.btn_fetch)

        lay.addLayout(r1); lay.addLayout(r2)
        self.layout.addWidget(container)

    def create_main_content(self):
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(8)
        
        self.table = QTableWidget(100, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Description", "Type", "Size", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #444; color: black; border: 1px solid #888; }
            QHeaderView::section { background: #DDD; color: black; border: 1px solid #555; }
            QTableWidget::item:hover { background: white; color: black; }
            QTableWidget::item:selected { background: #CCC; color: black; }
        """)
        self.table.itemClicked.connect(self.load_preview)
        
        preview_box = QWidget()
        pl = QVBoxLayout(preview_box); pl.setContentsMargins(0,0,0,0); pl.setSpacing(0)
        lbl = QLabel("File Preview")
        lbl.setStyleSheet("background: #EEE; padding: 5px; border: 1px solid #888; font-weight: bold; color: black;")
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("font-family: Consolas; background: #FAFAFA; color: #222; border: 1px solid #888;")
        self.preview_text.setPlaceholderText("Select a file to preview...")
        
        pl.addWidget(lbl); pl.addWidget(self.preview_text)
        splitter.addWidget(self.table); splitter.addWidget(preview_box)
        splitter.setSizes([400, 200])
        self.layout.addWidget(splitter, 1)

    def create_action_bar(self):
        frame = QFrame()
        frame.setMinimumHeight(80)
        frame.setStyleSheet("background: #E0E0E0; border-top: 2px solid #999;")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(20, 15, 20, 15); lay.setSpacing(20)
        
        btn_del = QPushButton("🗑️ Delete")
        btn_del.clicked.connect(self.delete_file)
        btn_del.setFixedSize(140, 45)
        btn_del.setStyleSheet("background: white; color: #D00; border: 2px solid #D00; font-weight: bold;")
        
        btn_info = QPushButton("ℹ️ Metadata")
        btn_info.clicked.connect(self.show_metadata)
        btn_info.setFixedSize(140, 45)
        btn_info.setStyleSheet("background: white; border: 2px solid #555; font-weight: bold; color: black;")
        
        btn_idx = QPushButton("⚙️ Build Index")
        btn_idx.clicked.connect(self.run_index)
        btn_idx.setFixedSize(140, 45)
        btn_idx.setStyleSheet("background: white; color: #0044CC; border: 2px solid #0044CC; font-weight: bold;")
        
        btn_open = QPushButton("📂 Open Folder")
        btn_open.clicked.connect(lambda: os.startfile("saved_genomes") if os.path.exists("saved_genomes") else None)
        btn_open.setFixedSize(140, 45)
        btn_open.setStyleSheet("background: white; color: #007744; border: 2px solid #007744; font-weight: bold;")
        
        lay.addWidget(btn_del); lay.addWidget(btn_info); lay.addStretch()
        lay.addWidget(btn_idx); lay.addWidget(btn_open)
        self.layout.addWidget(frame, 0)

    # --- LOGIC ---
    def cleanup_worker(self, worker):
        if worker in self.active_workers: self.active_workers.remove(worker)
        worker.deleteLater()

    def on_completer_activated(self, text):
        self.search_timer.stop()
        self.inp_search.setText(text)

    def perform_live_search(self):
        query = self.inp_search.text().strip()
        if len(query) < 3: return
        worker = UniversalSearchEngine(query, self.combo_source.currentText())
        worker.sig_results.connect(lambda r: self.completer_model.setStringList(r) or self.completer.complete())
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()

    def start_download(self):
        query = self.inp_search.text().strip()
        if not query: return
        self.btn_fetch.setEnabled(False); self.pbar.setVisible(True); self.pbar.setValue(0)
        worker = UniversalDownloadEngine(query, self.combo_source.currentText())
        worker.sig_progress.connect(self.pbar.setValue)
        worker.sig_finished.connect(self.on_dl_complete)
        worker.sig_error.connect(self.on_download_error)
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()

    def on_dl_complete(self, rec):
        self.ref_library.append(rec)
        self.refresh_table()
        self.pbar.setVisible(False); self.btn_fetch.setEnabled(True)
        self.inp_search.clear()

    def on_download_error(self, err):
        self.pbar.setVisible(False); self.btn_fetch.setEnabled(True)
        QMessageBox.critical(self, "Error", err)

    def load_preview(self, item):
        row = item.row()
        if row >= len(self.ref_library): return
        path = self.ref_library[row].get('path', '')
        
        if os.path.exists(path):
            try:
                # FIX: Read as raw text, limit to 2000 characters
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(2000) 
                self.preview_text.setPlainText(content)
            except Exception as e:
                self.preview_text.setPlainText(f"Error reading file:\n{e}")
        else:
            self.preview_text.setPlainText("File not found on disk.")

    def show_metadata(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.ref_library): return
        worker = MetadataEngine(self.ref_library[row]['acc'], self.combo_source.currentText())
        worker.sig_data.connect(lambda d: QMessageBox.information(self, "Metadata", str(d)))
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()

    def run_index(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.ref_library): return
        self.table.item(row, 4).setText("Indexing...")
        worker = IndexEngine(None, None)
        worker.sig_finished.connect(lambda s: self.table.item(row, 4).setText(s))
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()

    def delete_file(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.ref_library): return
        path = self.ref_library[row].get('path')
        if os.path.exists(path): os.remove(path)
        del self.ref_library[row]
        self.refresh_table()
        self.preview_text.clear()

    def refresh_table(self):
        self.table.setRowCount(max(100, len(self.ref_library)))
        self.table.clearContents()
        self.lbl_stats.setText(f"{len(self.ref_library)} Files")
        for i, data in enumerate(self.ref_library):
            self.table.setItem(i, 0, QTableWidgetItem(data['acc']))
            self.table.setItem(i, 1, QTableWidgetItem(data['name']))
            self.table.setItem(i, 2, QTableWidgetItem(data.get('type', 'Unknown')))
            self.table.setItem(i, 3, QTableWidgetItem(data['size']))
            self.table.setItem(i, 4, QTableWidgetItem(data['status']))

    def closeEvent(self, event):
        for w in self.active_workers:
            if w.isRunning(): w.terminate()
        event.accept()