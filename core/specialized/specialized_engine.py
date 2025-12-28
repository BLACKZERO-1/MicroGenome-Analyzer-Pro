import os
import subprocess
from PySide6.QtCore import QThread, Signal

class SpecializedWorker(QThread):
    # Signals to update the UI
    log_signal = Signal(str)
    progress_signal = Signal(int)
    step_signal = Signal(int)
    result_signal = Signal(dict)
    finished_signal = Signal(bool, str)

    def __init__(self, input_protein_file, db_type):
        """
        input_protein_file: Path to the .faa (Protein) file from Annotation Module.
        db_type: "card" (AMR) or "vfdb" (Virulence).
        """
        super().__init__()
        # Clean up UI artifacts from the path if present
        self.input_file = input_protein_file.replace("📄 ", "").strip()
        self.db_type = db_type.lower()
        
        self.base_path = os.getcwd()
        # FIX 1: Use BLASTP (Protein vs Protein) instead of blastn
        # This matches Blueprint Section 4.4 requirement for protein analysis
        ext = ".exe" if os.name == 'nt' else ""
        self.blast_tool = os.path.join(self.base_path, "tools", "blast", f"blastp{ext}")
        
        # Select Database Path
        if "card" in self.db_type:
            self.db_path = os.path.join(self.base_path, "databases", "amr", "card_db")
        else:
            self.db_path = os.path.join(self.base_path, "databases", "virulence", "vfdb_db")
            
        self.output_dir = os.path.join(self.base_path, "results", "specialized")
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        self.log_signal.emit(f"🚀 Initializing {self.db_type.upper()} Protein Screening...")
        self.progress_signal.emit(5)
        self.step_signal.emit(0)

        # 1. CHECK TOOLS & INPUT
        if not os.path.exists(self.blast_tool):
            self.log_signal.emit(f"❌ CRITICAL: BLASTP tool not found at {self.blast_tool}")
            self.finished_signal.emit(False, "Tool Missing")
            return
            
        if not os.path.exists(self.input_file):
            self.log_signal.emit(f"❌ Input file missing: {self.input_file}")
            self.finished_signal.emit(False, "Input Missing")
            return

        # 2. RUN BLASTP (Step 2)
        self.step_signal.emit(2)
        base_name = os.path.basename(self.input_file).split('.')[0]
        out_file = os.path.join(self.output_dir, f"{base_name}_{self.db_type}.tsv")
        
        self.log_signal.emit(f"💥 Running BLASTP against {self.db_type.upper()} database...")
        
        # FIX 2: Updated Output Format
        # Added 'stitle' to get the descriptive name of the gene (e.g., "blaTEM-1")
        # Added strict evalue (1e-10) to avoid false positives in protein matching
        cmd = [
            self.blast_tool, 
            "-query", self.input_file, 
            "-db", self.db_path, 
            "-out", out_file, 
            "-outfmt", "6 qseqid sseqid pident length evalue bitscore stitle", 
            "-evalue", "1e-10", 
            "-max_target_seqs", "1" # Only keep the best match per protein
        ]
        
        try:
            # Hide the command prompt window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, check=True, startupinfo=startupinfo)
            
            self.progress_signal.emit(60)
            self.log_signal.emit("✅ Scan complete. Parsing biological data...")
        except Exception as e:
            self.finished_signal.emit(False, f"BLASTP Error: {str(e)}")
            return

        # 3. PARSE RESULTS (Step 3)
        self.step_signal.emit(3)
        hits = 0
        gene_names = set()
        drug_classes = set() # For CARD categorization
        
        if os.path.exists(out_file):
            with open(out_file, "r") as f:
                for line in f:
                    cols = line.split("\t")
                    if len(cols) >= 7:
                        hits += 1
                        # The 'stitle' (Column 7) usually contains the full name
                        # e.g., "gb|...|ARO:3000|blaTEM-1|...|Beta-lactamase"
                        full_title = cols[6].strip()
                        
                        # Extract a readable name (heuristic)
                        short_name = self.extract_gene_name(full_title)
                        gene_names.add(short_name)
                        
                        # Basic classification for Risk Assessment
                        if self.db_type == "card":
                            drug_classes.add(self.classify_drug(full_title))

        # 4. REPORT & RISK ASSESSMENT (Step 4)
        self.step_signal.emit(4)
        
        # Calculate Risk Level (Blueprint Requirement)
        risk_level = "LOW"
        if hits > 0: risk_level = "MEDIUM"
        if hits > 5 or (self.db_type == "card" and len(drug_classes) > 2): risk_level = "HIGH"

        results = {
            "total_hits": hits,
            "unique_genes": len(gene_names),
            # Return drug classes for AMR, or specific genes for Virulence
            "classes": list(drug_classes) if self.db_type == "card" else list(gene_names),
            "risk_level": risk_level,
            "file_path": out_file
        }
        
        self.result_signal.emit(results)
        self.progress_signal.emit(100)
        self.log_signal.emit(f"🎉 Analysis Done. Risk Level: {risk_level}")
        self.finished_signal.emit(True, "Success")

    # --- HELPER FUNCTIONS ---

    def extract_gene_name(self, title):
        """Attempts to clean up the BLAST title to get a short gene name."""
        # Example CARD: "ARO:3000|blaTEM-1|..." -> "blaTEM-1"
        if "|" in title:
            parts = title.split("|")
            # Usually the gene name is the 3rd or 4th part in CARD/VFDB headers
            for part in parts:
                if len(part) > 2 and not part.startswith("ARO") and not part.isdigit():
                    return part
        return title[:20] + "..." # Fallback if parsing fails

    def classify_drug(self, title):
        """Classifies CARD hits into drug families for the UI chart."""
        t = title.lower()
        if "beta-lactam" in t or "bla" in t or "mec" in t: return "Beta-Lactam"
        if "aminoglycoside" in t: return "Aminoglycoside"
        if "tetracycline" in t: return "Tetracycline"
        if "fluoroquinolone" in t: return "Fluoroquinolone"
        if "glycopeptide" in t or "van" in t: return "Glycopeptide"
        if "macrolide" in t: return "Macrolide"
        return "Other/Multidrug"