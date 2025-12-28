import os
import csv
from collections import Counter
import matplotlib
# CRITICAL: Agg backend to prevent GUI freezing
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PySide6.QtCore import QThread, Signal

class PathwayWorker(QThread):
    log_signal = Signal(str)
    # Returns: Success (bool), Image Path (str), Table Data (list of dicts)
    finished_signal = Signal(bool, str, list)

    def __init__(self, annotation_file):
        super().__init__()
        self.annot_file = annotation_file
        self.base_path = os.getcwd()
        self.output_dir = os.path.join(self.base_path, "results", "pathways")
        os.makedirs(self.output_dir, exist_ok=True)

        # KEYWORD DICTIONARY
        self.pathway_db = {
            "Glycolysis": ["pfk", "pyk", "gap", "eno", "pgk", "fba", "tpi", "glucose", "pyruvate", "kinase"],
            "TCA Cycle": ["citrate", "isocitrate", "succinyl", "fumarate", "malate", "oxaloacetate", "dehydrogenase"],
            "Respiration": ["atp synthase", "nadh", "cytochrome", "quinone", "oxidative", "reductase"],
            "Fatty Acid": ["acyl-coa", "acetyl-coa", "fatty acid", "lipid", "beta-oxidation", "lipase"],
            "Amino Acid": ["tryptophan", "histidine", "arginine", "leucine", "glutamine", "synthase", "aminotransferase"],
            "DNA Repair": ["polymerase", "helicase", "ligase", "gyrase", "recombinase", "topoisomerase", "nuclease"],
            "Translation": ["ribosom", "trna", "elongation factor", "initiation factor", "synthetase"],
            "Cell Wall": ["peptidoglycan", "penicillin", "murein", "membrane", "multidrug", "lactamase"],
            "Transporters": ["transporter", "permease", "efflux", "pump", "channel", "porter"]
        }

    def run(self):
        self.log_signal.emit("🚀 Initializing Data Mining...")
        
        try:
            if not os.path.exists(self.annot_file):
                self.finished_signal.emit(False, "File not found.", [])
                return

            self.log_signal.emit(f"📖 Mining file: {os.path.basename(self.annot_file)}")
            
            pathway_counts = {k: 0 for k in self.pathway_db.keys()}
            detailed_hits = [] 
            
            lines_read = 0
            
            with open(self.annot_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    lines_read += 1
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("#"): continue
                    
                    line_lower = line_clean.lower()
                    matched_cat = None
                    matched_key = None

                    # Search keywords
                    for category, keywords in self.pathway_db.items():
                        for k in keywords:
                            if k in line_lower:
                                matched_cat = category
                                matched_key = k
                                break
                        if matched_cat: break
                    
                    if matched_cat:
                        pathway_counts[matched_cat] += 1
                        
                        parts = line_clean.split('\t')
                        gene_id = parts[0] if len(parts) > 1 else f"Line {lines_read}"
                        
                        detailed_hits.append({
                            "Pathway": matched_cat,
                            "Enzyme/Keyword": matched_key.upper(),
                            "Gene ID / Location": gene_id,
                            "Full Annotation": line_clean[:100] + "..."
                        })

            total_matches = len(detailed_hits)
            self.log_signal.emit(f"✅ Extracted {total_matches} records.")

            if total_matches == 0:
                self.finished_signal.emit(False, "0 Matches Found.", [])
                return

            # --- GENERATE CHART (Standard Matplotlib) ---
            self.log_signal.emit("🎨 Rendering Chart...")
            output_img = os.path.join(self.output_dir, "metabolic_profile.png")
            
            plt.style.use('bmh') # Use built-in style, no seaborn needed
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = list(pathway_counts.keys())
            counts = list(pathway_counts.values())
            
            # Create horizontal bar chart
            bars = ax.barh(categories, counts, color='#4318FF')
            ax.set_xlabel('Gene Count')
            ax.set_title(f"Metabolic Profile: {os.path.basename(self.annot_file)}")
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                        f"{int(width)}", va='center', fontweight='bold')

            plt.tight_layout()
            plt.savefig(output_img, dpi=120, bbox_inches='tight')
            plt.close(fig)
            
            self.finished_signal.emit(True, output_img, detailed_hits)

        except Exception as e:
            self.log_signal.emit(f"❌ Error: {str(e)}")
            self.finished_signal.emit(False, str(e), [])