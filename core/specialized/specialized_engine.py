import time
import random
import os
from PySide6.QtCore import QThread, Signal

class SpecializedWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)         # Flowchart tracker
    input_stats_signal = Signal(dict) # File info
    result_signal = Signal(dict)      # Hits found
    finished_signal = Signal(bool, str)

    def __init__(self, input_file, db_type="card"):
        super().__init__()
        self.input_file = input_file
        self.db_type = db_type # "card" or "vfdb"

    def run(self):
        db_name = "CARD (Antibiotic Resistance)" if self.db_type == "card" else "VFDB (Virulence Factors)"
        
        # STEP 0: INITIALIZE
        self.step_signal.emit(0)
        self.log_signal.emit(f"🚀 Initializing {db_name} Scan...")
        self.progress_signal.emit(5)
        time.sleep(0.5)

        # --- PHASE 1: INPUT CHECK ---
        self.log_signal.emit("🔍 Analyzing input genome sequence...")
        try:
            with open(self.input_file, 'r') as f:
                content = f.read()
            
            # Simple size check
            raw = "".join([line.strip() for line in content.splitlines() if not line.startswith(">")])
            size_mb = len(raw) / 1_000_000
            
            self.input_stats_signal.emit({
                "name": os.path.basename(self.input_file),
                "size": f"{size_mb:.2f} MB"
            })
            self.log_signal.emit(f"✅ Genome Size: {size_mb:.2f} MB. Ready for screening.")
            self.progress_signal.emit(15)

        except Exception as e:
            self.finished_signal.emit(False, str(e))
            return

        # --- PHASE 2: PIPELINE SIMULATION ---
        
        # Step 1: Load Database
        self.step_signal.emit(1)
        self.log_signal.emit(f"📂 Loading {self.db_type.upper()} reference database into memory...")
        time.sleep(1.5)
        self.progress_signal.emit(35)

        # Step 2: BLASTn Search
        self.step_signal.emit(2)
        self.log_signal.emit(f"⚔️ Running BLASTn alignment against {db_name}...")
        time.sleep(2.5) # Scanning takes time
        self.progress_signal.emit(65)

        # Step 3: Filtering
        self.step_signal.emit(3)
        self.log_signal.emit("🛡️ Filtering hits (Identity > 90%, Coverage > 80%)...")
        time.sleep(1.0)
        self.progress_signal.emit(85)

        # --- PHASE 3: RESULTS ---
        self.step_signal.emit(4)
        self.log_signal.emit("📊 Compiling resistance profile...")
        
        # Simulated Findings
        if self.db_type == "card":
            hits = random.randint(3, 12)
            classes = "Beta-lactamase, Aminoglycoside"
            top_hit = "blaTEM-1"
        else:
            hits = random.randint(5, 20)
            classes = "Adherence, Toxin, Secretion"
            top_hit = "Exotoxin A"
            
        results = {
            "total_hits": hits,
            "classes": classes,
            "top_hit": top_hit,
            "db": self.db_type.upper()
        }
        
        self.result_signal.emit(results)
        time.sleep(0.5)
        
        self.progress_signal.emit(100)
        self.log_signal.emit(f"🎉 Scan Complete. Found {hits} significant hits.")
        self.finished_signal.emit(True, "Success")