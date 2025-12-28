import os
import subprocess
import numpy as np
import matplotlib
# CRITICAL: Use non-interactive backend to prevent GUI thread crashes
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from PySide6.QtCore import QThread, Signal

# ==============================================================================
# 1. VISUALIZATION ENGINE (FIXED)
# ==============================================================================
class GenomePlotter:
    def __init__(self, gff_file, output_dir):
        self.gff_file = gff_file
        self.output_dir = output_dir
        self.genome_length = 0
        self.genes = []

    def parse_gff(self):
        """
        Reads Prodigal GFF file to get gene positions.
        Improved to handle standard Prodigal output format robustly.
        """
        self.genes = []
        try:
            with open(self.gff_file, 'r') as f:
                for line in f:
                    # 1. Try to find genome length from comments
                    if "sequence-region" in line:
                        try:
                            parts = line.split()
                            # format: ##sequence-region header start end
                            self.genome_length = int(parts[3]) 
                        except: pass
                    
                    if line.startswith("#") or not line.strip(): 
                        continue
                        
                    parts = line.split('\t')
                    if len(parts) < 9: continue
                    
                    try:
                        # GFF columns: 3=start, 4=end, 6=strand
                        start, end = int(parts[3]), int(parts[4])
                        strand = parts[6]
                        self.genes.append({'start': start, 'end': end, 'strand': strand})
                    except: continue
            
            # Fallback: if genome length wasn't found in header, use last gene position
            if self.genome_length == 0 and self.genes:
                # Add 2% buffer to the end
                self.genome_length = int(self.genes[-1]['end'] * 1.02)
                
        except Exception as e:
            print(f"Error parsing GFF: {e}")

    def create_circular_plot(self, filename="genome_circle.png"):
        """Generates a circular plot of the genome."""
        if not self.genes or self.genome_length == 0: 
            return None

        try:
            fig = plt.figure(figsize=(10, 10), dpi=300)
            ax = fig.add_subplot(111, polar=True)
            
            # Setup Polar Axes
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.grid(False)
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.spines['polar'].set_visible(False)
            
            # Plot Genes
            base_radius = 10
            width = 0.8
            
            # Use arrays for faster plotting
            starts = np.array([g['start'] for g in self.genes])
            ends = np.array([g['end'] for g in self.genes])
            strands = np.array([g['strand'] for g in self.genes])
            
            # Calculate angles
            start_angles = (starts / self.genome_length) * 2 * np.pi
            end_angles = (ends / self.genome_length) * 2 * np.pi
            
            # Handle wrap-around or simple duration calculation
            durations = np.where(
                end_angles < start_angles, 
                (2 * np.pi) - start_angles + end_angles, 
                end_angles - start_angles
            )
            
            # Colors and Offsets
            colors = np.where(strands == '+', '#2ecc71', '#e74c3c')
            radii = np.where(strands == '+', base_radius + 0.4, base_radius - 0.4)
            
            ax.bar(x=start_angles, height=width, width=durations, bottom=radii, 
                   color=colors, align='edge', alpha=0.9)

            # Center Text
            size_kb = self.genome_length / 1000
            plt.text(0, 0, f"Microbial Genome\n{size_kb:.1f} kb", 
                     ha='center', va='center', fontsize=14, fontweight='bold', color='#2c3e50')
            
            # Save Output
            out_path = os.path.join(self.output_dir, filename)
            plt.savefig(out_path, transparent=True, bbox_inches='tight')
            plt.close(fig) # Explicitly close to free memory
            return out_path
            
        except Exception as e:
            print(f"Plotting Error: {e}")
            return None

# ==============================================================================
# 2. ANNOTATION WORKER
# ==============================================================================
class AnnotationWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    stats_signal = Signal(dict)
    finished_signal = Signal(bool, str)

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file
        self.base_path = os.getcwd() 
        self.output_dir = os.path.join(self.base_path, "results", "annotation")
        os.makedirs(self.output_dir, exist_ok=True)

        # --- TOOL PATHS ---
        # Ensure extensions are correct for Windows
        ext = ".exe" if os.name == 'nt' else ""
        self.prodigal_path = os.path.join(self.base_path, "tools", "prodigal", f"prodigal{ext}")
        self.diamond_path = os.path.join(self.base_path, "tools", "diamond", f"diamond{ext}")
        self.rpsblast_path = os.path.join(self.base_path, "tools", "blast", f"rpsblast{ext}")
        self.blastn_path = os.path.join(self.base_path, "tools", "blast", f"blastn{ext}")

        # --- DATABASE PATHS ---
        self.protein_db_path = os.path.join(self.base_path, "databases", "blast", "core_proteins.dmnd")
        self.domain_db_path = os.path.join(self.base_path, "databases", "domains", "Pfam") 
        self.rna_db_path = os.path.join(self.base_path, "databases", "blast", "special_genes_db")

    def run(self):
        self.log_signal.emit("🚀 Initializing Annotation Engine...")
        self.progress_signal.emit(5)
        
        if not os.path.exists(self.prodigal_path):
            self.finished_signal.emit(False, f"Prodigal Tool Missing at: {self.prodigal_path}")
            return
            
        # 1. GC CALCULATION
        try:
            gc_percent, total_len = self.calculate_gc(self.input_file)
            self.log_signal.emit(f"📊 Genome Size: {total_len:,} bp | GC: {gc_percent:.2f}%")
        except Exception as e:
            self.finished_signal.emit(False, f"File Error: {str(e)}"); return
        
        # 2. PRODIGAL
        self.log_signal.emit("🧬 [Step 1/5] Predicting Genes (Prodigal)...")
        # Use 'meta' for small contigs/metagenomes, 'single' for complete genomes
        mode = "meta" if total_len < 100000 else "single"
        
        base_name = os.path.basename(self.input_file).split('.')[0]
        out_gff = os.path.join(self.output_dir, f"{base_name}.gff")
        out_proteins = os.path.join(self.output_dir, f"{base_name}.faa")
        
        cmd_prodigal = [self.prodigal_path, "-i", self.input_file, "-o", out_gff, "-a", out_proteins, "-f", "gff", "-p", mode, "-q"]
        try:
            self.run_subprocess(cmd_prodigal, "PRODIGAL")
            gene_count = self.count_genes(out_proteins)
            self.log_signal.emit(f"✅ Found {gene_count} genes.")
            self.progress_signal.emit(30)
        except Exception as e:
            self.finished_signal.emit(False, f"Prodigal Error: {str(e)}"); return

        # 3. DIAMOND
        self.log_signal.emit("🔍 [Step 2/5] Annotating Proteins (DIAMOND)...")
        annotated_count = 0
        if os.path.exists(self.protein_db_path) and os.path.exists(self.diamond_path):
            annotated_count = self.annotate_local(out_proteins, base_name)
        else:
            self.log_signal.emit("⚠️ Skipping Protein Annotation (DB/Tool missing)")
        self.progress_signal.emit(50)

        # 4. RPS-BLAST (DOMAINS)
        self.log_signal.emit("🛡️ [Step 3/5] Finding Domains (RPS-BLAST)...")
        domain_count = 0
        # Check for either single volume (.rps) or multi-volume alias (.pal)
        has_domain_db = os.path.exists(self.domain_db_path + ".rps") or os.path.exists(self.domain_db_path + ".pal")
        
        if os.path.exists(self.rpsblast_path) and has_domain_db:
             domain_count = self.find_domains(out_proteins, base_name)
        else:
             self.log_signal.emit("⚠️ Skipping Domains (Tool or Pfam.pal/.rps missing)")
        self.progress_signal.emit(70)

        # 5. BLASTN (SPECIAL GENES)
        self.log_signal.emit("🧪 [Step 4/5] Detecting rRNA/tRNA (BLASTN)...")
        rna_count = 0
        has_rna_db = os.path.exists(self.rna_db_path + ".nhr") or os.path.exists(self.rna_db_path + ".nal")
        
        if os.path.exists(self.blastn_path) and has_rna_db:
            rna_count = self.detect_special_genes(base_name)
        else:
             self.log_signal.emit("⚠️ Skipping Special Genes (BLASTN or RNA DB missing)")
        self.progress_signal.emit(85)

        # 6. VISUALIZATION
        self.log_signal.emit("🎨 [Step 5/5] Generating Visualization...")
        try:
            plotter = GenomePlotter(out_gff, self.output_dir)
            plotter.parse_gff()
            plot_path = plotter.create_circular_plot()
            if plot_path:
                self.log_signal.emit("✅ Visualization created.")
            else:
                self.log_signal.emit("⚠️ Visualization skipped (no genes found or parse error).")
        except Exception as e:
            self.log_signal.emit(f"⚠️ Visualization Error: {e}")
        
        # FINISH
        results = {
            "genes": gene_count, 
            "annotated": annotated_count, 
            "gc": gc_percent, 
            "domains": domain_count, 
            "rna": rna_count,
            "genome_length": total_len # Added for database
        }
        self.stats_signal.emit(results)
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Success")

    # --- WORKER FUNCTIONS ---

    def annotate_local(self, protein_file, base_name):
        out_diamond = os.path.join(self.output_dir, f"{base_name}_annotation.tsv")
        cmd = [
            self.diamond_path, "blastp", "-q", protein_file, "-d", self.protein_db_path,
            "-o", out_diamond, "-f", "6", "qseqid", "sseqid", "pident", "evalue", "stitle",
            "-k", "1", "--quiet"
        ]
        self.run_subprocess(cmd, "DIAMOND")
        return self.count_lines(out_diamond)

    def find_domains(self, protein_file, base_name):
        out_domains = os.path.join(self.output_dir, f"{base_name}_domains.tsv")
        cmd = [
            self.rpsblast_path, "-query", protein_file, "-db", self.domain_db_path,
            "-out", out_domains, "-outfmt", "6 qseqid stitle pident evalue", "-evalue", "0.01"
        ]
        try:
            self.run_subprocess(cmd, "RPS-BLAST")
            count = self.count_lines(out_domains)
            self.log_signal.emit(f"✅ Domains identified: {count}")
            return count
        except Exception as e:
            self.log_signal.emit(f"⚠️ RPS-BLAST Failed: {e}")
            return 0

    def detect_special_genes(self, base_name):
        out_rna = os.path.join(self.output_dir, f"{base_name}_rna.tsv")
        cmd = [
            self.blastn_path, "-query", self.input_file, "-db", self.rna_db_path,
            "-out", out_rna, "-outfmt", "6 qseqid sseqid pident length evalue", 
            "-evalue", "1e-5", "-perc_identity", "90"
        ]
        try:
            self.run_subprocess(cmd, "BLASTN")
            count = self.count_lines(out_rna)
            self.log_signal.emit(f"✅ Special Genes (rRNA/tRNA) found: {count}")
            return count
        except Exception as e:
            self.log_signal.emit(f"⚠️ BLASTN Failed: {e}")
            return 0

    # --- HELPERS ---

    def run_subprocess(self, cmd, tool_name):
        # Hide console window on Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None: break
            if line: self.log_signal.emit(f"  [{tool_name}] {line.strip()}")
        if process.returncode != 0: raise Exception(f"Failed code {process.returncode}")

    def calculate_gc(self, file_path):
        total, gc = 0, 0
        with open(file_path, 'r') as f:
            for line in f:
                if not line.startswith(">"):
                    s = line.strip().upper(); total += len(s); gc += s.count('G') + s.count('C')
        return ((gc/total)*100, total) if total > 0 else (0,0)

    def count_genes(self, f_path):
        return sum(1 for line in open(f_path) if line.startswith(">")) if os.path.exists(f_path) else 0

    def count_lines(self, f_path):
        return sum(1 for _ in open(f_path)) if os.path.exists(f_path) else 0