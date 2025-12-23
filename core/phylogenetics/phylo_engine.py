import os
import subprocess
import matplotlib
# Use Agg backend to prevent freezing
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# Biopython modules
from Bio import AlignIO, Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor

from PySide6.QtCore import QThread, Signal

class PhyloWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    result_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, file_list):
        super().__init__()
        self.files = file_list
        self.base_path = os.getcwd()
        self.output_dir = os.path.join(self.base_path, "results", "phylo")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.output_dir, "mafft_log.txt")

        # Find MAFFT
        self.mafft_exe = self.find_tool("mafft.bat")

    def find_tool(self, filename):
        search_path = os.path.join(self.base_path, "tools")
        # Quick check
        if filename == "mafft.bat":
            standard = os.path.join(search_path, "mafft", "mafft.bat")
            if os.path.exists(standard): return standard
        # Deep Search
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def run(self):
        self.log_signal.emit("🚀 Initializing Hybrid Pipeline...")
        self.progress_signal.emit(5)

        # 1. VALIDATION
        if not self.mafft_exe:
            self.finished_signal.emit(False, "❌ MAFFT not found in tools folder.")
            return
        
        if len(self.files) < 2:
            self.finished_signal.emit(False, "Need at least 2 files to build a tree.")
            return

        # 2. COMBINE SEQUENCES
        self.log_signal.emit("📦 Preparing Sequences...")
        combined_fasta = os.path.join(self.output_dir, "combined_input.fasta")
        
        try:
            with open(combined_fasta, "w") as outfile:
                for fpath in self.files:
                    name = os.path.basename(fpath).split('.')[0]
                    with open(fpath, "r") as infile:
                        # Skip existing headers, just read content
                        lines = infile.readlines()
                        seq = "".join([line.strip() for line in lines if not line.startswith(">")])
                        # Take first 5000bp
                        seq = seq[:5000]
                        if len(seq) == 0:
                            raise Exception(f"File {name} appears empty!")
                        outfile.write(f">{name}\n{seq}\n")
        except Exception as e:
            self.finished_signal.emit(False, f"File Prep Error: {e}")
            return
        self.progress_signal.emit(20)

        # 3. ALIGNMENT (MAFFT)
        self.log_signal.emit("🧬 Running MAFFT Alignment...")
        alignment_file = os.path.join(self.output_dir, "aligned.fasta")
        
        # Ensure we use absolute paths
        cmd_mafft = [os.path.abspath(self.mafft_exe), "--auto", os.path.abspath(combined_fasta)]
        
        try:
            # Capture STDERR to a log file for debugging
            with open(alignment_file, "w") as f_out, open(self.log_file, "w") as f_err:
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.run(
                    cmd_mafft, 
                    stdout=f_out, 
                    stderr=f_err, # Write errors to file
                    startupinfo=startupinfo,
                    text=True
                )
                
                if process.returncode != 0:
                    raise Exception("MAFFT returned error code. Check logs.")

            # CRITICAL CHECK: Did MAFFT actually write anything?
            if os.path.getsize(alignment_file) == 0:
                # Read the error log to tell user why
                with open(self.log_file, 'r') as f:
                    err_msg = f.read()
                raise Exception(f"MAFFT produced empty output!\nLog: {err_msg}")

            self.progress_signal.emit(50)
            self.log_signal.emit("✅ Alignment Complete.")

        except Exception as e:
            self.finished_signal.emit(False, f"MAFFT Error: {e}")
            return

        # 4. TREE BUILDING (Biopython)
        self.log_signal.emit("🌳 Calculating Genetic Distances...")
        
        try:
            alignment = AlignIO.read(alignment_file, "fasta")
            
            calculator = DistanceCalculator('identity')
            dm = calculator.get_distance(alignment)
            
            self.log_signal.emit("🔨 Constructing Tree (NJ)...")
            constructor = DistanceTreeConstructor()
            tree = constructor.nj(dm)
            
            self.progress_signal.emit(80)

            # 5. VISUALIZATION
            self.log_signal.emit("🎨 Rendering Tree Graph...")
            out_img = os.path.join(self.output_dir, "phylo_tree.png")
            
            plt.clf()
            fig = plt.figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(1, 1, 1)
            
            Phylo.draw(tree, axes=ax, do_show=False)
            
            plt.title("Phylogenetic Tree (MAFFT + Biopython)", fontsize=16)
            plt.savefig(out_img, bbox_inches='tight')
            plt.close(fig)
            
            self.result_signal.emit(out_img)
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, "Success")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_signal.emit(False, f"Tree Error: {e}")