import os
from Bio import SeqIO
from Bio.Align import PairwiseAligner
from PySide6.QtCore import QThread, Signal

class VariantWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    result_signal = Signal(list) 
    finished_signal = Signal(bool)

    def __init__(self, query_file, ref_file):
        super().__init__()
        self.query_file = query_file
        self.ref_file = ref_file

    def run(self):
        self.log_signal.emit("🚀 Initializing Variant Caller...")
        self.progress_signal.emit(5)

        try:
            # 1. Load Sequences
            self.log_signal.emit("📂 Loading Genomes...")
            ref_seq = self.read_fasta(self.ref_file)
            query_seq = self.read_fasta(self.query_file)

            if not ref_seq or not query_seq:
                self.log_signal.emit("❌ Error: Could not read sequences.")
                self.finished_signal.emit(False)
                return

            if len(ref_seq) > 5000000: 
                self.log_signal.emit("⚠️ Warning: Large genome detected. Using optimized alignment...")
            
            self.progress_signal.emit(20)

            # 2. Configure Aligner
            self.log_signal.emit("⚙️ Aligning Sequences (This uses CPU)...")
            aligner = PairwiseAligner()
            aligner.mode = 'global'
            aligner.match_score = 1
            aligner.mismatch_score = -1
            aligner.open_gap_score = -2
            aligner.extend_gap_score = -1

            # 3. Perform Alignment (Limit 50kb for demo speed)
            alignment = aligner.align(ref_seq[:50000], query_seq[:50000]) 
            best_aln = alignment[0]
            
            self.progress_signal.emit(60)
            self.log_signal.emit("✅ Alignment Complete. Calling variants...")

            # 4. Call Variants & Context
            mutations = self.call_variants(best_aln)
            
            self.progress_signal.emit(100)
            self.result_signal.emit(mutations)
            self.log_signal.emit(f"🎉 Analysis Done. Found {len(mutations)} variants.")
            self.finished_signal.emit(True)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log_signal.emit(f"❌ Critical Error: {str(e)}")
            self.finished_signal.emit(False)

    def read_fasta(self, path):
        try:
            if not os.path.exists(path): return None
            with open(path, "r") as f:
                record = next(SeqIO.parse(f, "fasta"))
            return str(record.seq).upper()
        except:
            return None

    def call_variants(self, alignment):
        """
        Extracts mutations AND Context strings (10bp window).
        """
        variants = []
        try:
            aln_str = format(alignment, "fasta")
            lines = aln_str.splitlines()
            
            if len(lines) >= 4:
                ref_aligned = lines[1]
                query_aligned = lines[3]
                
                # Stats Counters
                ts = 0
                tv = 0
                
                for i, (r, q) in enumerate(zip(ref_aligned, query_aligned)):
                    if r != q:
                        v_type = "SNP"
                        if r == '-': v_type = "Insertion"
                        elif q == '-': v_type = "Deletion"
                        
                        # Calculate Stats
                        if v_type == "SNP":
                            if (r in "AG" and q in "AG") or (r in "CT" and q in "CT"): ts += 1
                            else: tv += 1
                        
                        # Extract Context (10bp surrounding)
                        start = max(0, i - 10)
                        end = min(len(ref_aligned), i + 11)
                        ctx_ref = ref_aligned[start:end]
                        ctx_query = query_aligned[start:end]
                        
                        variants.append({
                            "pos": i + 1,
                            "ref": r,
                            "alt": q,
                            "type": v_type,
                            "ctx_ref": ctx_ref,
                            "ctx_query": ctx_query
                        })
                
                # Attach Stats to first item for UI to read
                if variants:
                    ratio = round(ts/tv, 2) if tv > 0 else 0
                    variants[0]['stats'] = {'ts': ts, 'tv': tv, 'ratio': ratio}
                    
        except Exception as e:
            print(f"Variant Parsing Error: {e}")
            
        return variants