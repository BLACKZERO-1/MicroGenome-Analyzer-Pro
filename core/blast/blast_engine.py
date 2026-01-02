import os
import time
import random
import collections

class BlastEngine:
    """
    Backend logic for BLAST Alignment.
    Features: Batch, Auto-Detect, Simulation, Consensus Builder.
    """
    def __init__(self, db_manager):
        self.db = db_manager 

    def detect_type(self, sequence):
        """Auto-detects if input is DNA (blastn) or Protein (blastp)."""
        if not sequence: return "blastn"
        clean_seq = ""
        for line in sequence.split('\n'):
            if not line.startswith(">"):
                clean_seq += line.strip().upper()
        if not clean_seq: return "blastn"

        dna_chars = set("ATGCN")
        match_count = sum(1 for c in clean_seq if c in dna_chars)
        ratio = match_count / len(clean_seq)
        return "blastn" if ratio > 0.9 else "blastp"

    def parse_input(self, text_input, file_path):
        """Parses sequences from either text box OR uploaded file."""
        sequences = []
        raw_data = ""
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                raw_data = f.read()
        elif text_input.strip():
            raw_data = text_input
            
        if not raw_data: return []

        entries = raw_data.strip().split('>')
        for entry in entries:
            if not entry.strip(): continue
            lines = entry.split('\n')
            header = lines[0].strip()
            seq = "".join(l.strip() for l in lines[1:])
            if seq:
                sequences.append((header, seq))
        return sequences

    def generate_consensus(self, query_seq, hits):
        """
        Simulates building a consensus sequence from top hits.
        In a real engine, this would align all hits. 
        Here, we use the query and inject 'popular' mutations based on identity.
        """
        if not hits: return ""
        
        # Simulating a consensus: Take query, keep conserved regions, mask variable ones
        consensus = list(query_seq)
        avg_identity = sum(float(h['identity'][:-1]) for h in hits) / len(hits)
        
        # If identity is low, mask some bases with 'N' (ambiguous)
        if avg_identity < 95:
            for i in range(0, len(consensus), 10): # Every 10th base
                if random.random() > (avg_identity/100):
                    consensus[i] = 'N'
                    
        return "".join(consensus)

    def run_blast(self, sequences, program, db_target):
        yield "STATUS:Initializing BLAST Database..."
        time.sleep(0.5)
        
        total = len(sequences)
        results = []
        
        # Diverse taxonomy pool
        organisms = [
            ("Escherichia coli K-12", "Bacteria"), ("Salmonella enterica", "Bacteria"),
            ("Homo sapiens", "Eukaryota"), ("Mus musculus", "Eukaryota"),
            ("SARS-CoV-2", "Virus"), ("Staphylococcus aureus", "Bacteria"),
            ("Drosophila melanogaster", "Eukaryota"), ("Danio rerio", "Eukaryota"),
            ("Arabidopsis thaliana", "Plantae"), ("Unknown uncultured bacterium", "Bacteria")
        ]
        
        for i, (header, seq) in enumerate(sequences):
            yield f"STATUS:Processing {i+1}/{total}: {header[:15]}..."
            seq_len = len(seq)
            hits = []
            num_hits = random.randint(5, 20) # Generate enough hits to filter
            
            for _ in range(num_hits):
                org_name, org_type = random.choice(organisms)
                
                # Randomize Quality to test Filters
                # 20% chance of a "bad" hit
                if random.random() < 0.2:
                    identity = random.uniform(40.0, 75.0)
                    e_val = random.uniform(0.1, 5.0)
                else:
                    identity = random.uniform(85.0, 100.0)
                    e_val = 0.0 if identity > 98 else random.uniform(1e-100, 1e-10)
                
                start = random.randint(1, int(seq_len * 0.1) + 1)
                end = start + int(seq_len * (random.uniform(0.5, 1.0)))
                if end > seq_len: end = seq_len
                
                # Generate a semi-realistic Accession ID
                acc_prefix = "NM_" if org_type == "Eukaryota" else "CP"
                acc = f"{acc_prefix}{random.randint(100000,999999)}.{random.randint(1,4)}"

                hits.append({
                    "accession": acc,
                    "description": org_name,
                    "organism": org_name,
                    "type": org_type,
                    "e_value_raw": e_val, # Keep raw float for filtering
                    "e_value": f"{e_val:.2e}",
                    "identity_raw": identity, # Keep raw float for filtering
                    "identity": f"{identity:.1f}%",
                    "score": int(identity * 10),
                    "start": start,
                    "end": end,
                    "full_len": seq_len
                })
            
            hits.sort(key=lambda x: x['score'], reverse=True)
            
            # Generate Consensus for this result
            cons_seq = self.generate_consensus(seq, hits[:5])
            
            results.append({
                "query": header, 
                "query_seq": seq,
                "hits": hits,
                "consensus": cons_seq
            })

        yield "STATUS:Compiling Final Report..."
        
        # Taxonomy Summary
        taxa_counts = {}
        for res in results:
            for h in res['hits']:
                org = h['organism']
                taxa_counts[org] = taxa_counts.get(org, 0) + 1
                
        yield {
            "status": "success",
            "results": results,
            "taxonomy": taxa_counts
        }