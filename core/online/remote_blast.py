import ssl
from Bio.Blast import NCBIWWW, NCBIXML
from PySide6.QtCore import QThread, Signal

# FIX: Handle SSL Certificate errors on some Windows machines
ssl._create_default_https_context = ssl._create_unverified_context

class RemoteBlastWorker(QThread):
    # Signals to update the UI safely
    log_signal = Signal(str)
    result_signal = Signal(dict)
    finished_signal = Signal(bool)

    def __init__(self, sequence, blast_type="blastp", db="nr"):
        """
        sequence: The gene sequence string (Amino Acid or DNA)
        blast_type: 'blastp' (Protein) or 'blastn' (DNA)
        db: 'nr' (Non-Redundant Protein) or 'nt' (Nucleotide)
        """
        super().__init__()
        self.sequence = sequence
        self.blast_type = blast_type
        self.db = db

    def run(self):
        self.log_signal.emit("🌍 Connecting to NCBI Remote Server...")
        self.log_signal.emit("⏳ Sending Sequence (This may take 1-3 minutes)...")
        
        try:
            # 1. CALL API (This is the slow part that requires internet)
            # We use Biopython to handle the request automatically
            result_handle = NCBIWWW.qblast(self.blast_type, self.db, self.sequence)
            
            self.log_signal.emit("✅ Response Received. Parsing XML Data...")
            
            # 2. PARSE RESULTS
            blast_record = NCBIXML.read(result_handle)
            result_handle.close()
            
            # 3. EXTRACT TOP HIT
            if len(blast_record.alignments) > 0:
                top_hit = blast_record.alignments[0]
                hsp = top_hit.hsps[0] # High-scoring Segment Pair
                
                # Clean up the title (Organism name is usually in brackets)
                full_title = top_hit.title
                organism = "Unknown"
                description = full_title
                
                if "[" in full_title:
                    parts = full_title.split("[")
                    description = parts[0]
                    organism = parts[-1].replace("]", "")
                
                # Clean up description
                description = description.split(">")[0].strip()
                if len(description) > 60:
                    description = description[:57] + "..."

                data = {
                    "accession": top_hit.accession,
                    "description": description,
                    "organism": organism,
                    "identity": f"{(hsp.identities / hsp.align_length) * 100:.2f}%",
                    "e_value": f"{hsp.expect:.2e}",
                    "score": str(hsp.score)
                }
                
                self.log_signal.emit(f"🎉 Match Found: {data['description']}")
                self.result_signal.emit(data)
                self.finished_signal.emit(True)
            else:
                self.log_signal.emit("⚠️ No significant matches found in NCBI Database.")
                self.result_signal.emit({})
                self.finished_signal.emit(True)

        except Exception as e:
            self.log_signal.emit(f"❌ API Connection Error: {str(e)}")
            self.finished_signal.emit(False)