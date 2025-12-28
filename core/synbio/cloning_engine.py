import re
from Bio.SeqUtils import MeltingTemp as mt
from Bio.Seq import Seq
from PySide6.QtCore import QThread, Signal

class CloningWorker(QThread):
    log_signal = Signal(str)
    result_signal = Signal(dict)
    finished_signal = Signal(bool)

    def __init__(self, sequence, mode="analyze_plasmid", params=None):
        super().__init__()
        self.sequence = sequence.upper()
        self.mode = mode
        self.params = params if params else {}

        # --- EXPANDED ENZYME DATABASE (Top 20 Lab Standards) ---
        self.enzymes_db = {
            "EcoRI": "GAATTC", "BamHI": "GGATCC", "HindIII": "AAGCTT",
            "NotI": "GCGGCCGC", "XhoI": "CTCGAG", "PstI": "CTGCAG",
            "SpeI": "ACTAGT", "XbaI": "TCTAGA", "ClaI": "ATCGAT",
            "EcoRV": "GATATC", "NdeI": "CATATG", "SacI": "GAGCTC",
            "SalI": "GTCGAC", "SmaI": "CCCGGG", "SphI": "GCATGC",
            "KpnI": "GGTACC", "ApaI": "GGGCCC", "BgIII": "AGATCT",
            "DraI": "TTTAAA", "XmaI": "CCCGGG"
        }

        self.features_db = {
            "Promoter (T7)": "TAATACGACTCACTATAGGG",
            "Promoter (CMV)": "CGTTACATAACTTACGGTAAATGGCCC",
            "Antibiotic (AmpR)": "TTACCAATGCTTAATCA", 
            "Antibiotic (KanR)": "ATGAGCCATATTCAACG", 
            "Origin (pUC)": "TTCCATAGGCTCCGCCCCCCTGACGA",
            "GFP Tag": "ATGAGTAAAGGAGAAGAACTTTTC",
            "His-Tag (6x)": "CATCACCATCACCATCAC"
        }

    def run(self):
        try:
            results = {}
            if self.mode == "analyze_plasmid":
                results = self.analyze_map()
            elif self.mode == "crispr":
                results = self.find_crispr()
            elif self.mode == "digest":
                # Handle Multi-Lane Digest
                # params['lanes'] = [['EcoRI'], ['BamHI', 'HindIII']]
                lanes_data = []
                lane_configs = self.params.get('lanes', [])
                
                self.log_signal.emit(f"🧪 Simulating {len(lane_configs)} Gel Lanes...")
                
                for enzymes in lane_configs:
                    frags = self.simulate_digest(enzymes)
                    lanes_data.append({"enzymes": enzymes, "fragments": frags})
                    
                results = {"type": "digest", "lanes": lanes_data}

            self.result_signal.emit(results)
            self.finished_signal.emit(True)

        except Exception as e:
            self.log_signal.emit(f"❌ Error: {str(e)}")
            self.finished_signal.emit(False)

    def analyze_map(self):
        sites = []
        for name, pattern in self.enzymes_db.items():
            for match in re.finditer(pattern, self.sequence):
                sites.append({"name": name, "pos": match.start() + 1})
        
        feats = []
        for name, seq in self.features_db.items():
            if seq in self.sequence:
                start = self.sequence.find(seq)
                feats.append({"name": name, "start": start+1, "end": start+len(seq), "color": "#4318FF"})
        
        return {"type": "plasmid_map", "length": len(self.sequence), "features": feats, "sites": sites}

    def find_crispr(self):
        targets = []
        pattern = r"(?=([ATGC]{20})[ATGC]GG)"
        for match in re.finditer(pattern, self.sequence):
            spacer = match.group(1)
            pam = self.sequence[match.start()+20 : match.start()+23]
            gc = (spacer.count('G') + spacer.count('C')) / 20 * 100
            score = "High" if 40 <= gc <= 60 and "TTTT" not in spacer else "Low"
            targets.append({"pos": match.start()+1, "sequence": spacer, "pam": pam, "gc": round(gc,1), "score": score})
        return {"type": "crispr", "targets": targets}

    def simulate_digest(self, selected_enzymes):
        if not selected_enzymes: return [len(self.sequence)] # Uncut
        
        cut_positions = [0, len(self.sequence)]
        for name in selected_enzymes:
            pattern = self.enzymes_db.get(name)
            if pattern:
                for match in re.finditer(pattern, self.sequence):
                    cut_positions.append(match.start() + 1)
        
        cut_positions = sorted(list(set(cut_positions)))
        fragments = []
        for i in range(len(cut_positions) - 1):
            fragments.append(cut_positions[i+1] - cut_positions[i])
            
        return sorted(fragments, reverse=True)