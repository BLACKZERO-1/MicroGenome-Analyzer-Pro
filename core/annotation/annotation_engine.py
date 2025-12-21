import os
import subprocess
import time
from PySide6.QtCore import QThread, Signal

class AnnotationWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    stats_signal = Signal(dict)
    finished_signal = Signal(bool, str)

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file.replace("📄 ", "").strip()
        
        base_path = os.getcwd()
        self.tool_path = os.path.join(base_path, "tools", "prodigal", "prodigal.exe")
        self.output_dir = os.path.join(base_path, "results", "annotation")
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        self.log_signal.emit("🚀 Initializing Annotation Engine...")
        self.progress_signal.emit(5)
        
        if not os.path.exists(self.tool_path):
            self.log_signal.emit(f"❌ CRITICAL ERROR: Tool not found at {self.tool_path}")
            self.finished_signal.emit(False, "Tool Missing")
            return

        # 2. CALCULATE GC & SIZE
        self.log_signal.emit("📊 Analyzing sequence composition...")
        try:
            gc_percent, total_len = self.calculate_gc(self.input_file)
            self.log_signal.emit(f"✅ Genome Size: {total_len:,} bp | GC Content: {gc_percent:.2f}%")
            self.progress_signal.emit(25)
        except Exception as e:
            self.finished_signal.emit(False, f"File Error: {str(e)}")
            return

        # 3. SMART MODE SELECTION
        # Prodigal crashes on files < 20,000bp in "single" mode.
        # We switch to "meta" (metagenomic) mode for small fragments.
        mode = "single"
        if total_len < 20000:
            mode = "meta"
            self.log_signal.emit("⚠️ Input is small (<20kb). Switching to Metagenomic Mode.")
        else:
            self.log_signal.emit("✅ Input is large. Using Standard Single-Genome Mode.")

        # 4. CONSTRUCT COMMAND
        base_name = os.path.basename(self.input_file).split('.')[0]
        out_gff = os.path.join(self.output_dir, f"{base_name}.gff")
        out_proteins = os.path.join(self.output_dir, f"{base_name}.faa")
        
        # -p mode : Uses our smart variable
        # -q : Runs quietly (less noise)
        cmd = [self.tool_path, "-i", self.input_file, "-o", out_gff, "-a", out_proteins, "-f", "gff", "-p", mode]
        
        self.log_signal.emit(f"⚙️ Executing Prodigal ({mode} mode)...")
        
        # 5. EXECUTE
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            
            # Read logs
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_signal.emit(f"  [PRODIGAL] {line.strip()}")

            self.progress_signal.emit(85)
            
            # 6. RESULTS
            gene_count = self.count_genes(out_proteins)
            
            results = {
                "gc": round(gc_percent, 2),
                "genes": gene_count,
                "orfs": gene_count
            }
            self.stats_signal.emit(results)
            self.progress_signal.emit(100)
            self.log_signal.emit(f"🎉 Success! Found {gene_count} genes.")
            self.finished_signal.emit(True, "Success")

        except Exception as e:
            self.log_signal.emit(f"❌ Execution Failed: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def calculate_gc(self, file_path):
        total_bases = 0
        gc_bases = 0
        with open(file_path, 'r') as f:
            for line in f:
                if not line.startswith(">"):
                    seq = line.strip().upper()
                    total_bases += len(seq)
                    gc_bases += seq.count('G') + seq.count('C')
        if total_bases == 0: return 0, 0
        return (gc_bases / total_bases) * 100, total_bases

    def count_genes(self, protein_file):
        count = 0
        if os.path.exists(protein_file):
            with open(protein_file, 'r') as f:
                for line in f:
                    if line.startswith(">"):
                        count += 1
        return count