import os

# Define the folder structure and the dummy files needed
db_structure = {
    "databases/amr": ["card.fasta", "card.json"],
    "databases/virulence": ["vfdb.fasta"],
    "databases/blast": ["ref_genome.fasta", "blast_db.nin", "blast_db.nhr", "blast_db.nsq"],
    "databases/pathways": ["kegg_modules.tsv"],
    "databases/domains": ["pfam.hmm"],
}

# Dummy content for FASTA files
fasta_content = """>Dummy_Gene_01 | Test Database Entry
ATGCGTACGTAGCTAGCTAGCTAGCTAGCTAGCGTACGTAGCTAG
>Dummy_Gene_02 | Test Database Entry
CGTACGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
"""

# Dummy content for TSV files
tsv_content = """Entry\tName\tDescription
K00001\tE1.1.1.1\tAlcohol dehydrogenase
K00002\tE1.1.1.2\tAlcohol dehydrogenase (NADP+)
"""

def create_databases():
    base_path = os.getcwd()
    print(f"📂 Generating dummy databases in: {base_path}")

    for folder, files in db_structure.items():
        # Create folder if it doesn't exist
        target_dir = os.path.join(base_path, folder)
        os.makedirs(target_dir, exist_ok=True)
        
        for file_name in files:
            file_path = os.path.join(target_dir, file_name)
            
            # Determine content based on extension
            content = "DUMMY BINARY CONTENT"
            if file_name.endswith(".fasta"):
                content = fasta_content
            elif file_name.endswith(".tsv") or file_name.endswith(".json"):
                content = tsv_content
            
            # Write the file
            with open(file_path, "w") as f:
                f.write(content)
            
            print(f"   ✅ Created: {folder}/{file_name}")

    print("\n🎉 Success! Dummy databases are ready. You can now run the software.")

if __name__ == "__main__":
    create_databases()