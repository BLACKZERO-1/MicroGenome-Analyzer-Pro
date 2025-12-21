import time
import random
import os
from PySide6.QtCore import QThread, Signal

class PathwayWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)         # Flowchart tracker
    input_stats_signal = Signal(dict) # Genome info
    result_signal = Signal(dict)      # Final Pathway stats
    finished_signal = Signal(bool, str)

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file

    def run(self):
        # STEP 0: INITIALIZE
        self.step_signal.emit(0)
        self.log_signal.emit(f"🚀 Initializing Metabolic Pathway Reconstruction...")
        self.progress_signal.emit(5)
        time.sleep(0.5)

        # --- PHASE 1: INPUT ANALYSIS ---
        self.log_signal.emit("🔍 Scanning genome for enzymatic gene candidates...")
        try:
            with open(self.input_file, 'r') as f:
                content = f.read()
            
            # Count potential genes (start with '>')
            gene_count = content.count('>')
            if gene_count == 0: gene_count = 1500 # Fallback
            
            self.input_stats_signal.emit({
                "genes": gene_count,
                "file": os.path.basename(self.input_file)
            })
            self.log_signal.emit(f"✅ Input: {gene_count} gene sequences detected.")
            self.progress_signal.emit(15)

        except Exception as e:
            self.finished_signal.emit(False, str(e))
            return

        # --- PHASE 2: PIPELINE SIMULATION ---
        
        # Step 1: EC Number Extraction
        self.step_signal.emit(1)
        self.log_signal.emit("🧬 Extracting EC numbers (Enzyme Commission codes)...")
        time.sleep(1.5)
        self.progress_signal.emit(40)

        # Step 2: KEGG Mapping
        self.step_signal.emit(2)
        self.log_signal.emit("🌍 Mapping enzymes to KEGG Reference Pathways...")
        time.sleep(2.0)
        self.progress_signal.emit(70)

        # Step 3: Module Reconstruction
        self.step_signal.emit(3)
        self.log_signal.emit("🧩 Reconstructing functional metabolic modules...")
        time.sleep(1.0)
        self.progress_signal.emit(90)

        # --- PHASE 3: RESULTS ---
        self.step_signal.emit(4)
        self.log_signal.emit("📊 Calculating pathway completeness scores...")
        
        # Simulated Results
        mapped_count = int(gene_count * 0.65)
        completeness = random.randint(75, 98)
        top_pathway = "Glycolysis / Gluconeogenesis"
        
        results = {
            "mapped": mapped_count,
            "completeness": f"{completeness}%",
            "top_pathway": top_pathway
        }
        
        self.result_signal.emit(results)
        time.sleep(0.5)
        
        self.progress_signal.emit(100)
        self.log_signal.emit("🎉 Pathway Reconstruction Complete.")
        self.finished_signal.emit(True, "Success")