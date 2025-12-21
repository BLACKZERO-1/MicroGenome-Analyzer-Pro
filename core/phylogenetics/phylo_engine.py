import os
import subprocess
from PySide6.QtCore import QThread, Signal

class PhyloWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)
    input_stats_signal = Signal(dict)
    result_signal = Signal(dict)
    finished_signal = Signal(bool, str)

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file.replace("📄 ", "").strip()
        
        # DEFINE TOOL PATHS
        base = os.getcwd()
        self.mafft_path = os.path.join(base, "tools", "mafft", "mafft.bat")
        self.fasttree_path = os.path.join(base, "tools", "fasttree", "FastTree.exe")
        self.output_dir = os.path.join(base, "results", "phylogenetics")
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        self.log_signal.emit("🚀 Initializing Phylogenetic Pipeline...")
        self.progress_signal.emit(5)

        # 1. CHECK TOOLS
        if not os.path.exists(self.mafft_path) or not os.path.exists(self.fasttree_path):
            self.log_signal.emit("❌ CRITICAL: Tools missing (MAFFT or FastTree).")
            self.finished_signal.emit(False, "Tools Missing")
            return

        # 2. ANALYZE INPUT (Step 0)
        self.step_signal.emit(0)
        taxa_count = 0
        with open(self.input_file, 'r') as f:
            taxa_count = sum(1 for line in f if line.startswith(">"))
        
        self.log_signal.emit(f"📊 Input loaded: {taxa_count} taxa found.")
        self.input_stats_signal.emit({"taxa": taxa_count, "sites": "Unknown"})
        self.progress_signal.emit(15)

        # 3. ALIGNMENT (MAFFT) (Step 1)
        self.step_signal.emit(1)
        aln_file = os.path.join(self.output_dir, "alignment.fasta")
        self.log_signal.emit("🧬 Running MAFFT Alignment (auto mode)...")
        
        # MAFFT command: mafft.bat --auto input > output
        cmd_mafft = [self.mafft_path, "--auto", self.input_file]
        
        try:
            with open(aln_file, "w") as out_f:
                subprocess.run(cmd_mafft, stdout=out_f, stderr=subprocess.PIPE, check=True, text=True)
            self.log_signal.emit("✅ Alignment completed.")
            self.progress_signal.emit(50)
        except Exception as e:
            self.log_signal.emit(f"❌ MAFFT Failed: {e}")
            self.finished_signal.emit(False, str(e))
            return

        # 4. TREE BUILDING (FastTree) (Step 2)
        self.step_signal.emit(2)
        tree_file = os.path.join(self.output_dir, "tree.nwk")
        self.log_signal.emit("🌳 Building Tree with FastTree (GTR+CAT)...")
        
        # FastTree command: FastTree -gtr -nt alignment > tree
        cmd_tree = [self.fasttree_path, "-gtr", "-nt", aln_file]
        
        try:
            with open(tree_file, "w") as out_f:
                subprocess.run(cmd_tree, stdout=out_f, stderr=subprocess.PIPE, check=True, text=True)
            self.log_signal.emit("✅ Tree construction completed.")
            self.progress_signal.emit(90)
        except Exception as e:
            self.log_signal.emit(f"❌ FastTree Failed: {e}")
            self.finished_signal.emit(False, str(e))
            return

        # 5. RENDER RESULTS
        self.step_signal.emit(4)
        with open(tree_file, "r") as f:
            tree_data = f.read()

        results = {
            "model": "GTR+CAT",
            "tree_view": tree_data  # The Newick string to show in UI
        }
        self.result_signal.emit(results)
        self.progress_signal.emit(100)
        self.log_signal.emit(f"💾 Results saved to: {tree_file}")
        self.finished_signal.emit(True, "Success")