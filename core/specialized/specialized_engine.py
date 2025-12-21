import os
import subprocess
from PySide6.QtCore import QThread, Signal

class SpecializedWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)
    result_signal = Signal(dict)
    finished_signal = Signal(bool, str)

    def __init__(self, input_file, db_type):
        super().__init__()
        self.input_file = input_file.replace("📄 ", "").strip()
        self.db_type = db_type.lower() # "card" or "vfdb"
        
        base = os.getcwd()
        self.blast_path = os.path.join(base, "tools", "blast", "blastn.exe")
        
        # Select Database Path
        if "card" in self.db_type:
            self.db_path = os.path.join(base, "databases", "amr", "card_db")
        else:
            self.db_path = os.path.join(base, "databases", "virulence", "vfdb_db")
            
        self.output_dir = os.path.join(base, "results", "specialized")
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        self.log_signal.emit(f"🚀 Initializing {self.db_type.upper()} Screening...")
        self.progress_signal.emit(5)
        self.step_signal.emit(0)

        # 1. CHECK TOOLS
        if not os.path.exists(self.blast_path):
            self.log_signal.emit("❌ CRITICAL: 'blastn.exe' not found.")
            self.finished_signal.emit(False, "Tool Missing")
            return

        # 2. RUN BLAST (Step 2)
        self.step_signal.emit(2)
        out_file = os.path.join(self.output_dir, "blast_results.txt")
        self.log_signal.emit(f"💥 Running BLAST against {self.db_type.upper()} database...")
        
        # Command: blastn -query input -db database -outfmt 6 -out output
        cmd = [
            self.blast_path, 
            "-query", self.input_file, 
            "-db", self.db_path, 
            "-out", out_file, 
            "-outfmt", "6 qseqid sseqid pident length evalue bitscore", 
            "-evalue", "1e-5"
        ]
        
        try:
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.progress_signal.emit(60)
            self.log_signal.emit("✅ Scan complete. Analyzing hits...")
        except Exception as e:
            self.finished_signal.emit(False, f"BLAST Error: {e}")
            return

        # 3. PARSE RESULTS (Step 3)
        self.step_signal.emit(3)
        hits = 0
        top_hit = "None"
        classes = set()
        
        if os.path.exists(out_file):
            with open(out_file, "r") as f:
                for line in f:
                    hits += 1
                    cols = line.split("\t")
                    if len(cols) > 1:
                        # Parse Hit Name (e.g., "gnl|CARD|MecA")
                        hit_name = cols[1].split("|")[-1] if "|" in cols[1] else cols[1]
                        classes.add(hit_name)
                        if hits == 1: top_hit = hit_name

        # 4. REPORT (Step 4)
        self.step_signal.emit(4)
        results = {
            "total_hits": hits,
            "classes": f"{len(classes)} Types Detected",
            "top_hit": top_hit
        }
        
        self.result_signal.emit(results)
        self.progress_signal.emit(100)
        self.log_signal.emit(f"🎉 Found {hits} potential threats.")
        self.finished_signal.emit(True, "Success")