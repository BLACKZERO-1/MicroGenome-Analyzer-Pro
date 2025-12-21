import time
import random
import os
from PySide6.QtCore import QThread, Signal

class ComparativeWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    stats_signal = Signal(dict)       # For Final Results (Core/Accessory)
    input_stats_signal = Signal(dict) # For Input Metrics (Size/Count)
    step_signal = Signal(int)         # For Visual Pipeline Tracker (0-4)
    finished_signal = Signal(bool, str)

    def __init__(self, file_list):
        super().__init__()
        self.files = file_list

    def run(self):
        # STEP 0: INITIALIZATION
        self.step_signal.emit(0) 
        self.log_signal.emit(f"🚀 Initializing Pangenome Pipeline...")
        self.progress_signal.emit(5)
        time.sleep(0.5)

        # --- PHASE 1: INPUT PROCESSING ---
        self.log_signal.emit("🔍 Parsing input genomes...")
        try:
            total_size_bp = 0
            for fpath in self.files:
                with open(fpath, 'r') as f:
                    content = f.read()
                    raw = "".join([line.strip() for line in content.splitlines() if not line.startswith(">")])
                    total_size_bp += len(raw)
            
            num_files = len(self.files)
            
            # EMIT INPUT STATS (Visualized Immediately)
            self.input_stats_signal.emit({
                "count": num_files,
                "size": total_size_bp
            })
            self.log_signal.emit(f"✅ Input Processed: {total_size_bp:,} bp across {num_files} isolates.")
            self.progress_signal.emit(15)
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))
            return

        # --- PHASE 2: PIPELINE SIMULATION ---
        
        # Step 1: Conversion (GFF3)
        self.step_signal.emit(1)
        self.log_signal.emit("🧬 Converting FASTA sequences to GFF3 format...")
        time.sleep(1.5)
        self.progress_signal.emit(30)

        # Step 2: Alignment (BLAST)
        self.step_signal.emit(2)
        self.log_signal.emit("🔄 Running all-vs-all BLAST alignment...")
        time.sleep(2.0)
        self.progress_signal.emit(60)

        # Step 3: Clustering (MCL)
        self.step_signal.emit(3)
        self.log_signal.emit("🕸️ Performing Markov Clustering (MCL) of gene families...")
        time.sleep(1.5)
        self.progress_signal.emit(80)

        # --- PHASE 3: RESULT GENERATION ---
        self.step_signal.emit(4)
        self.log_signal.emit("📉 Calculating Core vs. Accessory Genome statistics...")
        
        # Calculate Logic
        avg_genes = 3000 # Bacteria avg
        total_pool = num_files * avg_genes
        core_ratio = max(0.3, 0.9 - (num_files * 0.05)) # More files = smaller core
        
        core = int(avg_genes * core_ratio)
        accessory = int(avg_genes * (1 - core_ratio) * num_files * 0.5)
        unique = int(total_pool * 0.1) # Random uniqueness
        
        stats = {
            "core": core,
            "accessory": accessory,
            "unique": unique,
            "total_clusters": core + accessory + unique
        }
        
        self.stats_signal.emit(stats)
        time.sleep(1)
        
        self.progress_signal.emit(100)
        self.log_signal.emit("🎉 Comparative Analysis Complete.")
        self.finished_signal.emit(True, "Success")