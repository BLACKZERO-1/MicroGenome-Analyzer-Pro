import os
import subprocess

def fix_virulence_database():
    base_path = os.getcwd()
    makeblastdb = os.path.join(base_path, "tools", "blast", "makeblastdb.exe")
    
    # 1. Define Paths
    vir_dir = os.path.join(base_path, "databases", "virulence")
    vfdb_fasta = os.path.join(vir_dir, "vfdb.fasta")
    os.makedirs(vir_dir, exist_ok=True)

    # 2. Create DUMMY PROTEIN FASTA (Virulence Factors)
    # Includes: Staphylococcus Enterotoxin (Toxin) and E. coli Adhesin
    print("☣️  Creating Reference Virulence Protein Data...")
    protein_data = """
>gnl|VFDB|VFG0001|Enterotoxin_Type_A
MKLFKKKSVLCFSTVALSAFVPTYAKSEKSEEINEKDLRKKSELQGTALGNLKQIYYYNEKAKTENKESHDQFLQHTILFKGFFTDHSWYNDLLVDFDSKDIVDKYKGKKVDLYGAYYGYQCAGGTPNKTACMYGGVTLHDNNRLTEEKKVPINLWLDGKQNTVPLETVKTNKKNVTVQELDLQARRYLQEKYNLYNSDVFDGKVQRGLIVFHTSTEPSVNYDLFGAQGQYSNTLLRIYRDNKTINSENMHIDIYLYTS
>gnl|VFDB|VFG0002|Hemolysin_A
MSISAITSPTKVYAIGAGLLGLSLAALGAAGGVLGGVFQGGLGGLGNQIIGGAGGQAGLGGGVGGLGGLIGGVGGLGGVAQGGLGGLGNQIIGGAGGQAGLGGGVGGLGGLIGGVGGLGGVAQGGLGGLGNQIIGGAGGQAGLGGGVGGLGGLIGGVGGLGGVAQGGLGGLGNQIIGGAGQGGLIGGAGGQAGLGGGVGGLGGLIGGVGGLGGVAQ
    """
    
    with open(vfdb_fasta, "w") as f:
        f.write(protein_data.strip())

    # 3. Compile as PROTEIN Database (-dbtype prot)
    print("⚙️  Compiling VFDB Protein Database...")
    cmd = [
        makeblastdb,
        "-in", vfdb_fasta,
        "-dbtype", "prot",  # <--- CRITICAL CHANGE (Was 'nucl')
        "-out", os.path.join(vir_dir, "vfdb_db"),
        "-title", "VFDB Protein DB"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Success! VFDB Database is now PROTEIN format.")
        print("   You can now run the Virulence scan.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_virulence_database()