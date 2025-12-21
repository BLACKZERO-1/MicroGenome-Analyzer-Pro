import os
import subprocess
from utils.tool_wrappers import get_bin_path

class VirulenceManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        # Path to VFDB database (Page 6 of blueprint)
        self.db_path = os.path.join(project_dir, "databases", "virulence", "vfdb_protein.dmnd")
        self.output_dir = os.path.join(project_dir, "virulence_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def detect_virulence_factors(self, protein_fasta):
        """
        Searches protein sequences against VFDB using DIAMOND[cite: 129, 165].
        """
        if not os.path.exists(self.db_path):
            return {"success": False, "error": "VFDB database not found in databases/virulence/"}

        output_file = os.path.join(self.output_dir, "virulence_hits.tsv")
        diamond_exe = get_bin_path("diamond")

        # Command to run DIAMOND search against VFDB [cite: 165]
        command = [
            diamond_exe, "blastp",
            "-d", self.db_path,
            "-q", protein_fasta,
            "-o", output_file,
            "--outfmt", "6", "qseqid", "sseqid", "pident", "length", "evalue", "stitle",
            "--max-target-seqs", "1",
            "--evalue", "1e-5"
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            hits = self.parse_vf_results(output_file)
            return {
                "success": True,
                "hits": hits,
                "message": f"Detected {len(hits)} virulence factors."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def parse_vf_results(self, tsv_path):
        """
        Parses the DIAMOND output into a clean list for the UI.
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
                        "vf_match": cols[1],
                        "identity": cols[2],
                        "evalue": cols[4],
                        "description": cols[5] # This usually contains the factor type (toxin, etc.)
                    })
        return results