import os
import json
import time
import urllib.request
import urllib.parse
from PySide6.QtCore import QThread, Signal

# Safe Biopython Import
try:
    from Bio import Entrez
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False

# ==========================================
# 1. SEARCH ENGINE (Safe Mode)
# ==========================================
class UniversalSearchEngine(QThread):
    sig_results = Signal(list) 

    def __init__(self, search_term, source="NCBI GenBank", email="user@example.com"):
        super().__init__()
        self.term = search_term
        self.source = source
        self.email = email

    def run(self):
        if not self.term or len(self.term) < 3: return

        try:
            if "PDB" in self.source:
                self.search_pdb()
            else:
                self.search_ncbi()
        except Exception as e:
            print(f"Global Search Error: {e}") 

    def search_ncbi(self):
        if not HAS_BIOPYTHON: return
        Entrez.email = self.email
        
        db_target = "protein" if "Protein" in self.source else "nucleotide"
        
        # STRICTER FILTERS (Reduces "Fake" Data)
        if db_target == "protein":
            query = f"{self.term} AND srcdb_swiss_prot[PROP]"
        else:
            query = f"{self.term} AND (RefSeq[filter] OR \"complete genome\"[Title])"

        try:
            handle = Entrez.esearch(db=db_target, term=query, retmax=50, sort="relevance")
            results = Entrez.read(handle)
            handle.close()
            
            id_list = results.get('IdList', [])
            if not id_list: return

            handle = Entrez.esummary(db=db_target, id=",".join(id_list))
            summaries = Entrez.read(handle)
            handle.close()

            formatted = []
            for item in summaries:
                acc = item.get('Caption', 'N/A')
                title = item.get('Title', 'Unknown')
                if len(title) > 90: title = title[:87] + "..."
                formatted.append(f"{acc} | {title}")
            
            self.sig_results.emit(formatted)

        except Exception as e:
            print(f"NCBI Error: {e}")

    def search_pdb(self):
        try:
            encoded = urllib.parse.quote(self.term)
            url = f"https://search.rcsb.org/rcsbsearch/v2/suggest?q={encoded}&type=entry"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    formatted = []
                    if "suggestions" in data:
                        for key in data["suggestions"]:
                            formatted.append(f"{key} | PDB Structure")
                    self.sig_results.emit(formatted)
        except: pass

# ==========================================
# 2. DOWNLOAD ENGINE (With Smart Resolver)
# ==========================================
class UniversalDownloadEngine(QThread):
    sig_status = Signal(str)
    sig_progress = Signal(int)
    sig_finished = Signal(dict)
    sig_error = Signal(str)

    def __init__(self, query_str, source, email="user@example.com"):
        super().__init__()
        self.query_str = query_str
        self.source = source
        self.email = email
        
        if "Protein" in self.source: self.save_folder = "saved_proteins"
        elif "PDB" in self.source: self.save_folder = "saved_structures"
        else: self.save_folder = "saved_genomes"
        
        if not os.path.exists(self.save_folder): os.makedirs(self.save_folder)

    def run(self):
        try:
            # --- LOGIC UPGRADE: SMART ID RESOLUTION ---
            if "|" in self.query_str:
                # Case A: User selected from dropdown (Safe)
                parts = self.query_str.split("|")
                acc_id = parts[0].strip()
                name_guess = parts[1].strip() if len(parts) > 1 else acc_id
            else:
                # Case B: User typed a name (e.g. "Salmonella") -> We must find the ID first
                self.sig_status.emit("Resolving Name to ID...")
                acc_id = self.resolve_id_from_name(self.query_str.strip())
                
                if not acc_id:
                    self.sig_error.emit(f"Could not find any ID for '{self.query_str}'")
                    return
                name_guess = f"Auto-Resolved: {self.query_str}"

            # Start Download with the valid ID
            if "PDB" in self.source:
                self.download_pdb(acc_id, name_guess)
            else:
                self.download_ncbi(acc_id, name_guess)
                
        except Exception as e:
            self.sig_error.emit(f"Critical Download Error: {str(e)}")

    def resolve_id_from_name(self, term):
        """Helper to find an Accession ID if the user provided a name."""
        if "PDB" in self.source: return term # PDB IDs are usually typed directly (4 chars)
        if not HAS_BIOPYTHON: return None
        
        Entrez.email = self.email
        db = "protein" if "Protein" in self.source else "nucleotide"
        try:
            # Search for the top result
            handle = Entrez.esearch(db=db, term=term, retmax=1, sort="relevance")
            record = Entrez.read(handle)
            handle.close()
            ids = record.get("IdList", [])
            return ids[0] if ids else None
        except:
            return None

    def download_ncbi(self, acc_id, name):
        if not HAS_BIOPYTHON:
            self.sig_error.emit("Biopython not found.")
            return

        Entrez.email = self.email
        db = "protein" if "Protein" in self.source else "nucleotide"
        ext = ".fasta" if db == "protein" else ".gbk"
        rtype = "fasta" if db == "protein" else "gb"

        self.sig_status.emit(f"Downloading {acc_id}...")
        self.sig_progress.emit(10)

        try:
            handle = Entrez.efetch(db=db, id=acc_id, rettype=rtype, retmode="text")
            
            # STREAMING DOWNLOAD (Prevents Freezing on Large Files)
            path = os.path.join(self.save_folder, f"{acc_id}{ext}")
            with open(path, "w", encoding="utf-8") as f:
                while True:
                    chunk = handle.read(4096)
                    if not chunk: break
                    f.write(chunk)
            
            handle.close()
            
            # Verify File
            if os.path.getsize(path) < 50:
                self.sig_error.emit("NCBI returned empty/invalid data.")
                os.remove(path)
                return

            self.finish(acc_id, name, path)

        except Exception as e:
            self.sig_error.emit(f"NCBI Error: {str(e)}")

    def download_pdb(self, pdb_id, name):
        self.sig_status.emit(f"Fetching {pdb_id}...")
        self.sig_progress.emit(10)
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        path = os.path.join(self.save_folder, f"{pdb_id}.pdb")
        
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read()
                if len(data) < 100:
                    self.sig_error.emit("PDB File too small or invalid ID.")
                    return
                with open(path, 'wb') as f: f.write(data)
            
            self.finish(pdb_id, name, path)
        except Exception as e:
            self.sig_error.emit(str(e))

    def finish(self, acc, name, path):
        self.sig_progress.emit(100)
        size_str = "0 KB"
        if os.path.exists(path):
            size_bytes = os.path.getsize(path)
            if size_bytes > 1024 * 1024: size_str = f"{size_bytes/(1024*1024):.2f} MB"
            else: size_str = f"{size_bytes/1024:.2f} KB"
        
        self.sig_finished.emit({
            "acc": acc, "name": name, "size": size_str, 
            "status": "Ready", "path": path, "type": self.source
        })

# --- METADATA & INDEX ENGINES ---
class MetadataEngine(QThread):
    sig_data = Signal(dict)
    def __init__(self, acc, source): super().__init__(); self.acc=acc; self.src=source
    def run(self): 
        self.sig_data.emit({"ID": self.acc, "Status": "Live (Simulated)"})

class IndexEngine(QThread):
    sig_finished = Signal(str)
    def __init__(self, p, t): super().__init__(); self.p=p
    def run(self): time.sleep(0.5); self.sig_finished.emit("Indexed")