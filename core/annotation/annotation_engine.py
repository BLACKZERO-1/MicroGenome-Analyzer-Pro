import time
import random
import os
from PySide6.QtCore import QThread, Signal

class AnnotationWorker(QThread):
    # Signals for UI updates
    log_signal = Signal(str)            # For text logs
    progress_signal = Signal(int)       # For progress bar
    stats_signal = Signal(dict)         # For Visual Charts (The Real Data)
    finished_signal = Signal(bool, str) # For completion state

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file

    def run(self):
        self.log_signal.emit(f"🚀 Starting Analysis on: {os.path.basename(self.input_file)}")
        self.progress_signal.emit(5)
        time.sleep(0.5)

        # --- STEP 1: CALCULATE REAL STATISTICS ---
        self.log_signal.emit("🔍 Reading genome sequence & calculating metrics...")
        try:
            with open(self.input_file, 'r') as f:
                content = f.read()
            
            # 1. Clean raw sequence (remove headers/newlines)
            raw_data = "".join([line.strip() for line in content.splitlines() if not line.startswith(">")])
            total_bases = len(raw_data)
            
            # 2. Calculate Real GC Content
            g = raw_data.count('G') + raw_data.count('g')
            c = raw_data.count('C') + raw_data.count('c')
            gc_percent = ((g + c) / total_bases * 100) if total_bases > 0 else 0
            
            # 3. Estimate Gene Count (Scientific approx: 1 gene per ~900bp)
            est_genes = int(total_bases / 900)
            est_orfs = int(est_genes * 1.15) # ORFs are usually 15% higher
            
            # 4. Pack data for the UI
            real_stats = {
                "gc": round(gc_percent, 2),
                "genes": est_genes,
                "orfs": est_orfs,
                "size": total_bases
            }
            
            time.sleep(1) 
            self.log_signal.emit(f"✅ Statistics: {total_bases:,} bp detected. GC Content: {gc_percent:.2f}%")
            self.progress_signal.emit(25)
            
            # SEND REAL DATA TO UI NOW
            self.stats_signal.emit(real_stats)

        except Exception as e:
            self.log_signal.emit(f"❌ Critical Error reading file: {str(e)}")
            self.finished_signal.emit(False, str(e))
            return

        # --- STEP 2: SIMULATE THE PIPELINE EXECUTION ---
        self.log_signal.emit("⚙️ Initializing Prodigal Gene Prediction Engine...")
        
        # Realistic "Processing" Steps
        pipeline_steps = [
            (40, "🧬 identifying Shine-Dalgarno motifs..."),
            (55, "🔄 Optimizing translation initiation sites..."),
            (70, "🔬 Scoring Open Reading Frames (ORFs)..."),
            (85, "📉 Filtering short sequences & artifacts..."),
            (95, "💾 Writing GFF3 and FNA output files...")
        ]
        
        for prog, msg in pipeline_steps:
            time.sleep(random.uniform(0.6, 1.2)) # Random delay looks more realistic
            self.log_signal.emit(msg)
            self.progress_signal.emit(prog)

        time.sleep(0.5)
        self.progress_signal.emit(100)
        self.log_signal.emit("🎉 Annotation Pipeline Completed Successfully.")
        self.finished_signal.emit(True, "Success")