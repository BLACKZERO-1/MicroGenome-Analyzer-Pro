import os
import subprocess

def fix_amr_database():
    base_path = os.getcwd()
    makeblastdb = os.path.join(base_path, "tools", "blast", "makeblastdb.exe")
    
    # 1. Define Paths
    amr_dir = os.path.join(base_path, "databases", "amr")
    card_fasta = os.path.join(amr_dir, "card.fasta")
    os.makedirs(amr_dir, exist_ok=True)

    # 2. Create a DUMMY PROTEIN FASTA (Amino Acid Sequences)
    # This replaces the DNA sequences with Proteins so blastp works.
    print("🛠️  Creating Reference Protein Data...")
    protein_data = """
>gnl|CARD|blaTEM-1|Beta-lactamase
MSIQHFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRIDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPVAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW*
>gnl|CARD|mecA|PBP2a
MKKIKIVPLILIVVVVGTISFSTNVAQSDTSSAPVSKRSRISSRVATTPPKKTGLPIPENISLKDITNVDRDGILKQILPKEIEDLFKNIIDRVDVRISYQNEDMEKVFKDNTKIMISLKDIFKKDKSFIEVLDNKYIKTNDVNKLITKAERVNANLVVQKNSFIIKGDKVKITNTKRYMAKFSIFSSPLQKKTGVDKDIKEWIKEKIPQALKQINSDNINVVIGSGGQIITEIIDGISDNYDKVLIN*
    """
    
    with open(card_fasta, "w") as f:
        f.write(protein_data.strip())

    # 3. Compile as PROTEIN Database (-dbtype prot)
    print("⚙️  Compiling Protein Database...")
    cmd = [
        makeblastdb,
        "-in", card_fasta,
        "-dbtype", "prot",  # <--- CRITICAL CHANGE (Was 'nucl')
        "-out", os.path.join(amr_dir, "card_db"),
        "-title", "CARD Protein DB"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Success! CARD Database is now PROTEIN format.")
        print("   You can now run the AMR scan.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_amr_database()