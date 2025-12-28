import os
import subprocess
from utils.tool_wrappers import get_bin_path

class PathwayManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        # Path to local KEGG database (Page 6 of blueprint)
        self.db_path = os.path.join(project_dir, "databases", "pathways", "kegg_db.dmnd")
        self.output_dir = os.path.join(project_dir, "pathway_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def map_to_kegg(self, protein_fasta):
        """
        Maps proteins to KEGG pathways using DIAMOND search.
        """
        if not os.path.exists(self.db_path):
            return {"success": False, "error": "KEGG database not found in databases/pathways/"}

        output_file = os.path.join(self.output_dir, "kegg_matches.tsv")
        diamond_exe = get_bin_path("diamond")

        # DIAMOND command for pathway mapping
        command = [
            diamond_exe, "blastp",
            "-d", self.db_path,
            "-q", protein_fasta,
            "-o", output_file,
            "--outfmt", "6", "qseqid", "sseqid", "pident", "evalue", "stitle",
            "--max-target-seqs", "1",
            "--evalue", "1e-5"
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            pathway_data = self.process_pathway_completeness(output_file)
            return {
                "success": True,
                "data": pathway_data,
                "message": "Metabolic pathway mapping complete."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def process_pathway_completeness(self, tsv_path):
        """
        Analyzes the hits to determine which KEGG pathways are present.
        """
        pathways = {}
        if not os.path.exists(tsv_path):
            return pathways

        with open(tsv_path, 'r') as f:
            for line in f:
                cols = line.strip().split('\t')
                if len(cols) >= 5:
                    # Extract KO number and Pathway info from the title
                    ko_id = cols[1]
                    description = cols[4]
                    pathways[ko_id] = description
        
        return pathways