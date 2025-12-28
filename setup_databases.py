import os
import subprocess
import os
import subprocess

# ... (Keep your existing imports and config) ...

def setup_all_databases():
    base_path = os.getcwd()
    blast_tool = os.path.join(base_path, "tools", "blast", "makeblastdb.exe")
    
    # 1. SPECIAL GENES (rRNA/tRNA) - REQUIRED FOR ANNOTATION MODULE
    rna_dir = os.path.join(base_path, "databases", "blast")
    os.makedirs(rna_dir, exist_ok=True)
    
    rna_fasta = os.path.join(rna_dir, "special_genes.fasta")
    
    # Create dummy reference if it doesn't exist
    if not os.path.exists(rna_fasta):
        with open(rna_fasta, "w") as f:
            f.write(">16S_rRNA_Ecoli\nAAATTGAAGAGTTTGATCATGGCTCAGATTGAACGCTGGCGGCAGGCCTAACACATGCAAGTCGAACGGTAACAGGA\n")
            f.write(">tRNA_Met_Ecoli\nGGGGGUGUGGCGUAGUCGGUAGCGCGCUCCCUUUGCAAGGGAGAGGUCCCCGGUUCAAAUCCGGGCACCCCCA\n")
    
    cmd_rna = [
        blast_tool, "-in", rna_fasta, "-dbtype", "nucl", 
        "-out", os.path.join(rna_dir, "special_genes_db"), 
        "-title", "Special Genes DB"
    ]
    
    print("🧪 Building Special Genes Database...")
    subprocess.run(cmd_rna, check=True)
    print("✅ Special Genes Database created.")

if __name__ == "__main__":
    setup_all_databases()
# CONFIGURATION
BASE_PATH = os.getcwd()
TOOLS_BLAST = os.path.join(BASE_PATH, "tools", "blast", "makeblastdb.exe")
DB_DIR = os.path.join(BASE_PATH, "databases")

# 1. CREATE FOLDERS
os.makedirs(os.path.join(DB_DIR, "amr"), exist_ok=True)
os.makedirs(os.path.join(DB_DIR, "virulence"), exist_ok=True)

# 2. CREATE DUMMY FASTA FILES (For Demonstration)
# In a real scenario, you would download the full CARD/VFDB files here.
# These allow your app to "find" hits immediately during testing.

amr_fasta = os.path.join(DB_DIR, "amr", "card.fasta")
vfdb_fasta = os.path.join(DB_DIR, "virulence", "vfdb.fasta")

# A few known resistance genes (BlaTEM, MecA) for testing
amr_data = """>gnl|CARD|MecA [Staphylococcus aureus]
ATGAAAAAGATAAAAATTGTTCCACTTATTTTAATAGTTGTAGTTGTCGGGTTTGGTATATATTTTTAT
>gnl|CARD|BlaTEM-1 [Escherichia coli]
ATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCCTTTTTTGCGGCATTTTGCCTTCCTGTTTTTGCT
"""

# A few known virulence factors (Shiga toxin, Hemolysin)
vf_data = """>gnl|VFDB|Stx1 [Shigella dysenteriae]
ATGAAAATAATTATTTTTAGAGTGCTAACTTTTTTCTTTGTTATCTTTTCAGTTAATGTGGTGGCGAAG
>gnl|VFDB|HlyA [Escherichia coli]
ATGCCAACAATAACCACTGCACAAATTAAAAGCACACTGCAGTCTGCAAAGCAATCCGCTGCAAATAAA
"""

print("📝 Writing reference FASTA files...")
with open(amr_fasta, "w") as f: f.write(amr_data)
with open(vfdb_fasta, "w") as f: f.write(vf_data)

# 3. COMPILE DATABASES USING BLAST
print("⚙️  Compiling BLAST Databases...")

if not os.path.exists(TOOLS_BLAST):
    print(f"❌ ERROR: makeblastdb.exe not found at {TOOLS_BLAST}")
    print("Please download BLAST+ and place it in tools/blast/")
else:
    # Compile AMR
    cmd_amr = [TOOLS_BLAST, "-in", amr_fasta, "-dbtype", "nucl", "-out", os.path.join(DB_DIR, "amr", "card_db")]
    subprocess.run(cmd_amr, check=True)
    
    # Compile VFDB
    cmd_vf = [TOOLS_BLAST, "-in", vfdb_fasta, "-dbtype", "nucl", "-out", os.path.join(DB_DIR, "virulence", "vfdb_db")]
    subprocess.run(cmd_vf, check=True)
    
    print("✅ Databases successfully created and indexed!")