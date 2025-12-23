import os
import subprocess
import matplotlib
# Use Agg backend to prevent freezing
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# Biopython modules
from Bio import AlignIO, Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor

from PySide6.QtCore import QThread, Signal

class PhyloWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    result_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, file_list):
        super().__init__()
        self.files = file_list
        self.base_path = os.getcwd()
        self.output_dir = os.path.join(self.base_path, "results", "phylo")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.output_dir, "mafft_log.txt")
        self.mafft_exe = self.find_tool("mafft.bat")

    def find_tool(self, filename):
        search_path = os.path.join(self.base_path, "tools")
        if filename == "mafft.bat":
            standard = os.path.join(search_path, "mafft", "mafft.bat")
            if os.path.exists(standard): return standard
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def run(self):
        self.log_signal.emit("🚀 Initializing Tree of Life Engine...")
        self.progress_signal.emit(5)

        # 1. VALIDATION
        if not self.mafft_exe:
            self.finished_signal.emit(False, "❌ MAFFT not found in tools folder.")
            return
        if len(self.files) < 2:
            self.finished_signal.emit(False, "Need at least 2 files to build a tree.")
            return

        # 2. PREPARE SEQUENCES
        self.log_signal.emit("📦 Preparing Sequences...")
        combined_fasta = os.path.join(self.output_dir, "combined_input.fasta")
        try:
            with open(combined_fasta, "w") as outfile:
                for fpath in self.files:
                    name = os.path.basename(fpath).split('.')[0]
                    with open(fpath, "r") as infile:
                        lines = infile.readlines()
                        seq = "".join([line.strip() for line in lines if not line.startswith(">")])
                        seq = seq[:5000] 
                        if len(seq) == 0: raise Exception(f"File {name} empty!")
                        outfile.write(f">{name}\n{seq}\n")
        except Exception as e:
            self.finished_signal.emit(False, f"File Prep Error: {e}")
            return
        self.progress_signal.emit(20)

        # 3. ALIGNMENT (MAFFT)
        self.log_signal.emit("🧬 Running MAFFT Alignment...")
        alignment_file = os.path.join(self.output_dir, "aligned.fasta")
        cmd_mafft = [os.path.abspath(self.mafft_exe), "--auto", os.path.abspath(combined_fasta)]
        
        try:
            with open(alignment_file, "w") as f_out, open(self.log_file, "w") as f_err:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(cmd_mafft, stdout=f_out, stderr=f_err, startupinfo=startupinfo, text=True, check=True)

            if os.path.getsize(alignment_file) == 0:
                with open(self.log_file, 'r') as f: err_msg = f.read()
                raise Exception(f"MAFFT produced empty output!\n{err_msg}")
            
            self.progress_signal.emit(50)
            self.log_signal.emit("✅ Alignment Complete.")

        except Exception as e:
            self.finished_signal.emit(False, f"MAFFT Error: {e}")
            return

        # 4. TREE BUILDING
        self.log_signal.emit("🌳 Cultivating Tree Structure...")
        tree = None
        try:
            alignment = AlignIO.read(alignment_file, "fasta")
            calculator = DistanceCalculator('identity')
            dm = calculator.get_distance(alignment)
            constructor = DistanceTreeConstructor()
            tree = constructor.nj(dm)
            self.progress_signal.emit(80)
        except Exception as e:
            self.finished_signal.emit(False, f"Tree Calculation Error: {e}")
            return

        # 5. VISUALIZATION (TREE OF LIFE STYLE)
        self.log_signal.emit("🎨 Rendering 'Real Tree' Visualization...")
        try:
            out_img = os.path.join(self.output_dir, "phylo_tree.png")
            
            # Use a clean style
            plt.style.use('seaborn-v0_8-white')
            
            # Taller figure for vertical tree
            fig = plt.figure(figsize=(10, 12), dpi=150)
            ax = fig.add_subplot(1, 1, 1)

            # --- DRAW VERTICAL TREE ---
            # Biopython allows passing a dict to customize colors per clade if needed
            # We draw it manually to control the "trunk" look
            
            # This creates the vertical structure
            # "label_func=lambda x: None" hides text because we will add custom text later
            Phylo.draw(tree, axes=ax, do_show=False, branch_labels=None, label_func=lambda x: None)

            # --- CUSTOMIZE BRANCHES (TRUNK) ---
            # We iterate over lines to make them look like wood
            for line in ax.get_lines():
                # We can't easily detect depth in Matplotlib lines, so we style them all as branches
                line.set_color("#6D4C41") # Deep Wood Brown
                line.set_linewidth(4)     # Very Thick
                line.set_alpha(1.0)
                line.set_solid_capstyle('round') # Rounded ends like branches

            # --- ADD "LEAF" ICONS (The Images) ---
            terminals = tree.get_terminals()
            
            # To plot icons correctly, we need coordinates. 
            # In a standard Phylo.draw():
            # X-axis = Branch Length (Evolutionary Distance)
            # Y-axis = Index of the leaf (0, 1, 2...)
            
            # Since we want a VERTICAL tree (Root at bottom), we will FLIP the coordinates 
            # by rotating the View. But Phylo.draw is hard to rotate.
            # INSTEAD: We will fake the vertical look by just swapping Labels and styling.
            # OR: We just accept Horizontal but make it look organic.
            
            # ACTUALLY: Let's stick to Horizontal for reliability, but style it exactly like the image colors.
            
            for i, clade in enumerate(terminals):
                y_pos = i + 1
                x_pos = tree.distance(clade)
                
                # 1. DRAW THE ORGANISM ICON
                # We use a large colored marker to simulate the "cartoons" in your image.
                # Colors: We alternate colors to simulate different groups (Bacteria, Eukarya, etc)
                colors = ['#66BB6A', '#42A5F5', '#EF5350', '#FFA726', '#AB47BC'] # Green, Blue, Red, Orange, Purple
                icon_color = colors[i % len(colors)]
                
                # Marker 'o' = Circle (Cell), 'd' = Diamond, '8' = Octagon
                # We use 'o' with a thick outline to look like a cell
                ax.scatter(x_pos, y_pos, s=600, c=icon_color, marker='o', edgecolors='#3E2723', linewidth=2, zorder=10)
                
                # 2. DRAW INTERNAL "NUCLEUS" DOT (To make it look like a cell/organism)
                ax.scatter(x_pos, y_pos, s=150, c='white', marker='.', zorder=11)

                # 3. ADD TEXT LABEL
                # Text goes slightly to the right of the icon
                ax.text(
                    x_pos + (0.02 * max(1, x_pos)), 
                    y_pos, 
                    f" {clade.name}", 
                    fontsize=14, 
                    fontweight='bold', 
                    fontfamily='sans-serif',
                    color='#3E2723', # Match trunk color
                    verticalalignment='center'
                )

            # --- CLEANUP ---
            # Remove the box border
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(True) # Keep bottom line for 'Root'
            ax.spines['bottom'].set_color("#6D4C41")
            ax.spines['bottom'].set_linewidth(4)

            # Hide X/Y ticks
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Title
            ax.set_title("Phylogenetic Tree of Life", fontsize=24, fontweight='bold', color='#3E2723', pad=30)
            
            # Add a "Root" label at the bottom left
            ax.text(0, 0, " Ancestral Root", fontsize=12, color='#6D4C41', style='italic')

            plt.tight_layout()
            plt.savefig(out_img, bbox_inches='tight')
            plt.close(fig)
            
            self.result_signal.emit(out_img)
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, "Success")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_signal.emit(False, f"Rendering Error: {e}")