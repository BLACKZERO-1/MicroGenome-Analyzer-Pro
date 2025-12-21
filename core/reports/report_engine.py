import time
import random
import os
from PySide6.QtCore import QThread, Signal

class ReportWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)         # Flowchart tracker
    result_signal = Signal(dict)      # Final Report Stats
    finished_signal = Signal(bool, str)

    def __init__(self, format_type="pdf"):
        super().__init__()
        self.format_type = format_type.lower()

    def run(self):
        # STEP 0: INITIALIZE
        self.step_signal.emit(0)
        self.log_signal.emit(f"🚀 Initializing Project Report Generation ({self.format_type.upper()})...")
        self.progress_signal.emit(5)
        time.sleep(0.5)

        # --- PHASE 1: DATA AGGREGATION ---
        self.log_signal.emit("📂 Scanning project directories for analysis results...")
        time.sleep(1.0)
        
        # Simulate finding data from previous modules
        modules_found = ["Annotation", "Phylogenetics", "AMR Screening", "Pathways"]
        self.log_signal.emit(f"✅ Found data from {len(modules_found)} active modules.")
        self.progress_signal.emit(25)

        # --- PHASE 2: PIPELINE SIMULATION ---
        
        # Step 1: Data Merging
        self.step_signal.emit(1)
        self.log_signal.emit("🔄 Merging tables and statistical metrics...")
        time.sleep(1.5)
        self.progress_signal.emit(50)

        # Step 2: Chart Rendering
        self.step_signal.emit(2)
        self.log_signal.emit("📊 Rendering high-resolution summary charts...")
        time.sleep(2.0)
        self.progress_signal.emit(75)

        # Step 3: Document Formatting
        self.step_signal.emit(3)
        self.log_signal.emit(f"📝 Applying styles and layout for {self.format_type.upper()} output...")
        time.sleep(1.5)
        self.progress_signal.emit(90)

        # --- PHASE 3: FINALIZATION ---
        self.step_signal.emit(4)
        self.log_signal.emit("💾 Saving final document to disk...")
        
        # Simulated File Stats
        file_size = f"{random.randint(2, 8)}.4 MB"
        pages = random.randint(12, 25) if self.format_type == "pdf" else "N/A"
        charts = random.randint(8, 15)
        
        results = {
            "modules": len(modules_found),
            "size": file_size,
            "charts": charts,
            "filename": f"Project_Report_Final.{self.format_type}"
        }
        
        self.result_signal.emit(results)
        time.sleep(0.5)
        
        self.progress_signal.emit(100)
        self.log_signal.emit(f"🎉 Report Generated: {results['filename']}")
        self.finished_signal.emit(True, "Success")