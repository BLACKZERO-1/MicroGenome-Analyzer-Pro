import os
import subprocess
import matplotlib.pyplot as plt
from PySide6.QtCore import QThread, Signal

class ComparativeWorker(QThread):
    # Signals for UI updates
    log_signal = Signal(str)
    progress_signal = Signal(int)
    result_signal = Signal(dict)       # Sends Plot Path & Stats to UI
    finished_signal = Signal(bool, str)

    def __init__(self, query_file, ref_file):
        """
        query_file: The User's Genome (FASTA)
        ref_file: The Reference Genome (FASTA) e.g., E. coli K12
        """
        super().__init__()
        self.query_file = query_file
        self.ref_file = ref_file
        
        self.base_path = os.getcwd()
        self.output_dir = os.path.join(self.base_path, "results", "comparative")
        os.makedirs(self.output_dir, exist_ok=True)

        # Tools
        self.blastn_path = os.path.join(self.base_path, "tools", "blast", "blastn.exe")
        self.makeblastdb_path = os.path.join(self.base_path, "tools", "blast", "makeblastdb.exe")

    def run(self):
        self.log_signal.emit("🚀 Initializing Comparative Genomics Engine...")
        self.progress_signal.emit(5)

        # 1. VALIDATION
        if not os.path.exists(self.query_file):
            self.finished_signal.emit(False, "Query file missing.")
            return
        if not os.path.exists(self.ref_file):
            self.finished_signal.emit(False, "Reference file missing.")
            return
        if not os.path.exists(self.blastn_path):
            self.finished_signal.emit(False, "CRITICAL: blastn.exe not found.")
            return

        # 2. BUILD REFERENCE DATABASE (Step 1)
        # We need to turn the Reference Genome into a BLAST DB so we can search it.
        self.log_signal.emit("📦 Building Reference Database...")
        ref_db_name = os.path.join(self.output_dir, "temp_ref_db")
        
        # Command: makeblastdb -in reference.fasta -dbtype nucl ...
        cmd_db = [
            self.makeblastdb_path, 
            "-in", self.ref_file, 
            "-dbtype", "nucl", 
            "-out", ref_db_name,
            "-title", "ReferenceDB"
        ]
        
        try:
            self.run_subprocess(cmd_db)
            self.progress_signal.emit(30)
            self.log_signal.emit("✅ Reference Database Built.")
        except Exception as e:
            self.finished_signal.emit(False, f"DB Error: {str(e)}")
            return

        # 3. RUN SYNTENY ALIGNMENT (Step 2)
        # Compares Input vs Reference to find matching regions
        self.log_signal.emit("⚔️  Running Whole Genome Alignment (BLASTN)...")
        alignment_file = os.path.join(self.output_dir, "alignment.tsv")
        
        # Command: blastn -query input -db ref -outfmt 6 ...
        # Output columns: qstart qend sstart send pident length
        cmd_blast = [
            self.blastn_path,
            "-query", self.query_file,
            "-db", ref_db_name,
            "-out", alignment_file,
            "-outfmt", "6 qstart qend sstart send pident length",
            "-evalue", "1e-10",
            "-perc_identity", "95" # Strict matching for synteny
        ]

        try:
            self.run_subprocess(cmd_blast)
            self.progress_signal.emit(70)
            self.log_signal.emit("✅ Alignment Complete.")
        except Exception as e:
            self.finished_signal.emit(False, f"Alignment Error: {str(e)}")
            return

        # 4. GENERATE DOTPLOT (Step 3)
        self.log_signal.emit("🎨 Generating Synteny Dotplot...")
        try:
            plot_path, match_count = self.create_dotplot(alignment_file)
            
            # Final Results Package
            results = {
                "plot_path": plot_path,
                "matches": match_count,
                "ref_name": os.path.basename(self.ref_file)
            }
            
            self.result_signal.emit(results)
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, "Success")
            
        except Exception as e:
            self.finished_signal.emit(False, f"Plotting Error: {str(e)}")

    def create_dotplot(self, tsv_file):
        """
        Reads BLAST results and plots a Diagonal Synteny Map using Matplotlib.
        This visualizes large-scale genomic rearrangements (Synteny).
        """
        x_coords = [] # Query positions
        y_coords = [] # Reference positions
        colors = []   # Blue = Forward, Red = Inverted
        count = 0

        if not os.path.exists(tsv_file): return None, 0

        with open(tsv_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    count += 1
                    # Parse BLAST coords
                    q_start, q_end = int(parts[0]), int(parts[1])
                    s_start, s_end = int(parts[2]), int(parts[3])
                    
                    x_coords.append([q_start, q_end])
                    y_coords.append([s_start, s_end])
                    
                    # Color logic: Forward match vs Reverse Complement (Inversion)
                    if s_start < s_end:
                        colors.append('#4318FF') # Blue (Forward)
                    else:
                        colors.append('#E04F5F') # Red (Inversion)

        # Plotting
        plt.figure(figsize=(10, 8), dpi=100)
        for i in range(len(x_coords)):
            plt.plot(x_coords[i], y_coords[i], color=colors[i], linewidth=1.5, alpha=0.8)
            
        plt.title(f"Genome Synteny: Input vs {os.path.basename(self.ref_file)}", fontsize=14, fontweight='bold')
        plt.xlabel("Query Genome Position (bp)", fontsize=12)
        plt.ylabel("Reference Genome Position (bp)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.3)
        
        # Save Plot
        out_png = os.path.join(self.output_dir, "synteny_plot.png")
        plt.savefig(out_png, bbox_inches='tight')
        plt.close()
        
        return out_png, count

    def run_subprocess(self, cmd):
        """Runs command line tools silently on Windows."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(stderr.strip() or "Process failed")