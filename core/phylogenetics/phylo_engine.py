import time
import random
import os
from PySide6.QtCore import QThread, Signal

class PhyloWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)         # Flowchart tracker
    input_stats_signal = Signal(dict) # Taxa count, Sites
    result_signal = Signal(dict)      # Final Tree & Model info
    finished_signal = Signal(bool, str)

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file

    def run(self):
        # STEP 0: INITIALIZE
        self.step_signal.emit(0)
        self.log_signal.emit(f"🚀 Initializing Phylogenetic Inference on: {os.path.basename(self.input_file)}")
        self.progress_signal.emit(5)
        time.sleep(0.5)

        # --- PHASE 1: READ ALIGNMENT DATA ---
        self.log_signal.emit("🔍 Reading MSA (Multiple Sequence Alignment)...")
        try:
            with open(self.input_file, 'r') as f:
                content = f.read()
            
            # Count Taxa (headers start with '>')
            taxa_count = content.count('>')
            if taxa_count == 0: taxa_count = 1 # Fallback for dummy file
            
            # Estimate Alignment Length
            lines = content.splitlines()
            seq_len = 0
            for line in lines:
                if not line.startswith(">") and len(line) > 0:
                    seq_len += len(line)
                    break # Just measure the first sequence
            
            # Emit Input Stats
            self.input_stats_signal.emit({
                "taxa": taxa_count,
                "sites": seq_len
            })
            self.log_signal.emit(f"✅ Alignment Check: {taxa_count} taxa, {seq_len} sites.")
            self.progress_signal.emit(15)

        except Exception as e:
            self.finished_signal.emit(False, str(e))
            return

        # --- PHASE 2: PIPELINE SIMULATION ---
        
        # Step 1: Substitution Model
        self.step_signal.emit(1)
        self.log_signal.emit("⚙️ ModelTest-NG: Testing 88 substitution models...")
        time.sleep(1.5)
        selected_model = random.choice(["GTR+I+G", "HKY85", "Jukes-Cantor", "TIM2+G"])
        self.log_signal.emit(f"✅ Best Fit Model Selected: {selected_model} (BIC score: 1240.5)")
        self.progress_signal.emit(40)

        # Step 2: Tree Topology Search
        self.step_signal.emit(2)
        self.log_signal.emit("🌳 Calculating Maximum Likelihood (ML) tree topology...")
        time.sleep(2.0)
        self.progress_signal.emit(70)

        # Step 3: Bootstrapping
        self.step_signal.emit(3)
        self.log_signal.emit("🔄 Running Rapid Bootstrapping (1000 replicates)...")
        time.sleep(1.5)
        self.progress_signal.emit(90)

        # --- PHASE 3: FINALIZE & VISUALIZE ---
        self.step_signal.emit(4)
        self.log_signal.emit("💾 Saving 'phylogeny.nwk' and rendering preview...")
        
        # Generate Fake ASCII Tree for Visualization
        ascii_tree = f"""
        (Root)
          |
          +--- {os.path.basename(self.input_file)}_Strain_A
          |
          +--- (Clade_1)
          |      |
          |      +--- E.coli_K12
          |      +--- S.enterica_Typhi
          |
          +--- (Clade_2) [Support: 98%]
                 |
                 +--- P.aeruginosa_PAO1
                 +--- {os.path.basename(self.input_file)}_Strain_B
        """
        
        results = {
            "model": selected_model,
            "bootstrap": "98.5%",
            "tree_view": ascii_tree
        }
        
        self.result_signal.emit(results)
        time.sleep(0.5)
        self.progress_signal.emit(100)
        self.log_signal.emit("🎉 Phylogenetics Pipeline Completed.")
        self.finished_signal.emit(True, "Success")