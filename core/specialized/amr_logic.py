import os
import subprocess
from utils.tool_wrappers import get_bin_path

class AMRManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        # Path to CARD database (Page 6 of blueprint)
        self.db_path = os.path.join(project_dir, "databases", "amr", "card_protein.dmnd")
        self.output_dir = os.path.join(project_dir, "amr_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def detect_amr_genes(self, protein_fasta):
        """
        Searches protein sequences against CARD using DIAMOND[cite: 123, 165].
        """
        if not os.path.exists(self.db_path):
            return {"success": False, "error": "CARD database not found in databases/amr/"}

        output_file = os.path.join(self.output_dir, "amr_hits.tsv")
        diamond_exe = get_bin_path("diamond")

        # DIAMOND command for high-sensitivity protein search [cite: 165]
        command = [
            diamond_exe, "blastp",
            "-d", self.db_path,
            "-q", protein_fasta,
            "-o", output_file,
            "--outfmt", "6", "qseqid", "sseqid", "pident", "length", "evalue", "stitle",
            "--max-target-seqs", "1",
            "--evalue", "1e-10",
            "--id", "80" # High identity threshold for AMR 
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            hits = self.parse_amr_results(output_file)
            return {
                "success": True,
                "hits": hits,
                "message": f"Detected {len(hits)} potential AMR genes."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def parse_amr_results(self, tsv_path):
        """
        Parses the TSV output into a clean list of dictionaries for the UI[cite: 126].
        """
        results = []
        if not os.path.exists(tsv_path):
            return results

        with open(tsv_path, 'r') as f:
            for line in f:
                cols = line.strip().split('\t')
                if len(cols) >= 6:
                    results.append({
                        "gene_id": cols[0],
                        "card_match": cols[1],
                        "identity": cols[2],
                        "evalue": cols[4],
                        "description": cols[5]
                    })
        return results