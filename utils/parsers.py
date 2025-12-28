import os

def parse_gff3(file_path):
    """
    Parses a GFF3 file to extract gene features.
    Returns a list of dictionaries for each gene found.
    """
    genes = []
    
    if not os.path.exists(file_path):
        return genes

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Skip header lines
                if line.startswith("#") or not line.strip():
                    continue
                
                parts = line.strip().split('\t')
                
                # We only care about 'CDS' (Coding Sequences) or 'gene' features
                if len(parts) >= 9 and parts[2] in ['CDS', 'gene']:
                    attributes = parts[8]
                    # Extract ID from the attributes column
                    gene_id = "unknown"
                    for attr in attributes.split(';'):
                        if attr.startswith("ID="):
                            gene_id = attr.replace("ID=", "")
                    
                    genes.append({
                        "id": gene_id,
                        "start": parts[3],
                        "end": parts[4],
                        "strand": parts[6]
                    })
        return genes
    except Exception as e:
        print(f"Error parsing GFF3: {e}")
        return []