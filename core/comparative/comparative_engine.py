import os
import subprocess
import matplotlib
# CRITICAL: Use non-interactive backend to prevent GUI thread crashes
matplotlib.use('Agg') 
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
        ext = ".exe" if os.name == 'nt' else ""
        self.blastn_path = os.path.join(self.base_path, "tools", "blast", f"blastn{ext}")
        self.makeblastdb_path = os.path.join(self.base_path, "tools", "blast", f"makeblastdb{ext}")

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
            self.finished_signal.emit(False, f"CRITICAL: blastn tool not found at {self.blastn_path}")
            return

        # 2. BUILD REFERENCE DATABASE (Step 1)
        # We need to turn the Reference Genome into a BLAST DB so we can search it.
        self.log_signal.emit("📦 Building Reference Database...")
        ref_name_base = os.path.basename(self.ref_file).split('.')[0]
        ref_db_name = os.path.join(self.output_dir, f"{ref_name_base}_db")
        
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
            "-perc_identity", "90" # Strict matching for synteny
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
                    try:
                        q_start, q_end = int(parts[0]), int(parts[1])
                        s_start, s_end = int(parts[2]), int(parts[3])
                        
                        # Store segments (Start -> End)
                        x_coords.append([q_start, q_end])
                        y_coords.append([s_start, s_end])
                        
                        # Color logic: Forward match vs Reverse Complement (Inversion)
                        if s_start < s_end:
                            colors.append('#4318FF') # Blue (Forward)
                        else:
                            colors.append('#E04F5F') # Red (Inversion)
                    except: pass

        if count == 0:
            return None, 0

        # Plotting
        fig = plt.figure(figsize=(10, 8), dpi=150)
        ax = fig.add_subplot(111)
        
        for i in range(len(x_coords)):
            ax.plot(x_coords[i], y_coords[i], color=colors[i], linewidth=1.5, alpha=0.8)
            
        ax.set_title(f"Genome Synteny: Input vs {os.path.basename(self.ref_file)}", fontsize=14, fontweight='bold')
        ax.set_xlabel("Query Genome Position (bp)", fontsize=12)
        ax.set_ylabel("Reference Genome Position (bp)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.3)
        
        out_png = os.path.join(self.output_dir, "synteny_plot.png")
        plt.savefig(out_png, bbox_inches='tight')
        plt.close(fig) # Explicitly close to free memory
        
        return out_png, count

    def run_subprocess(self, cmd):
        """Runs command line tools silently on Windows."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(stderr.strip() or "Process failed")