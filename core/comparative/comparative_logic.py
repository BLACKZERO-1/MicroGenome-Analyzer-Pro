import pandas as pd
import os
from utils.parsers import parse_gff3

class ComparativeManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.output_dir = os.path.join(self.project_dir, "comparative_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_matrix(self, gff_files):
        """
        Takes a list of GFF file paths and creates a 
        Gene Presence/Absence Matrix using Pandas.
        """
        all_data = {}

        for gff in gff_files:
            strain_name = os.path.basename(gff).split('_')[0]
            genes = parse_gff3(gff)
            # Create a set of gene IDs for this strain
            all_data[strain_name] = {gene['id']: 1 for gene in genes}

        # Create DataFrame: Rows = Genes, Columns = Strains
        df = pd.DataFrame(all_data).fillna(0).astype(int)
        
        # Save the matrix as CSV
        matrix_path = os.path.join(self.output_dir, "pangenome_matrix.csv")
        df.to_csv(matrix_path)

        # Calculate Statistics
        core_genes = df[df.all(axis=1)].shape[0]
        total_genes = df.shape[0]

        return {
            "matrix_path": matrix_path,
            "core_count": core_genes,
            "accessory_count": total_genes - core_genes,
            "total_count": total_genes
        }