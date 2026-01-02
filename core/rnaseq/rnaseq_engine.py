import pandas as pd
import numpy as np

class RNASeqEngine:
    """
    Backend logic for Transcriptomics/RNA-Seq.
    Handles data loading, filtering, and statistical formatting.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.df = None

    def load_expression_data(self, file_path):
        """
        Loads a Count Matrix or Differential Expression CSV.
        Expected columns: 'Gene', 'log2FoldChange', 'padj' (or similar).
        """
        try:
            self.df = pd.read_csv(file_path)
            
            # Normalize column names to lowercase for consistency
            self.df.columns = [c.strip().lower() for c in self.df.columns]
            
            # Validate required columns
            # We look for partial matches (e.g., 'log2fc', 'logfc', 'log2foldchange')
            required_checks = {
                'gene': ['gene', 'id', 'symbol', 'locus'],
                'fc': ['foldchange', 'fc', 'log2foldchange', 'logfc', 'log2fc'],
                'pval': ['padj', 'pvalue', 'fdr', 'qvalue']
            }
            
            mapping = {}
            for key, options in required_checks.items():
                found = False
                for col in self.df.columns:
                    if col in options:
                        mapping[col] = key # Map 'log2foldchange' -> 'fc'
                        found = True
                        break
                if not found:
                    # If gene column is missing, use the index
                    if key == 'gene': 
                        self.df['gene'] = self.df.index
                    else:
                        return {"status": "error", "message": f"Missing column for {key} (e.g., log2FoldChange, padj)"}

            return {"status": "success", "rows": len(self.df), "cols": list(self.df.columns)}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_volcano_data(self):
        """Prepares X (FoldChange) and Y (-log10 P-value) for plotting."""
        if self.df is None: return None
        
        # Identify columns dynamically based on what exists
        cols = self.df.columns
        fc_col = next(c for c in cols if c in ['log2foldchange', 'logfc', 'fc', 'foldchange', 'log2fc'])
        p_col = next(c for c in cols if c in ['padj', 'pvalue', 'fdr', 'qvalue'])
        gene_col = 'gene' if 'gene' in cols else 'index'
        
        data = self.df.copy()
        
        # Calculate -log10(p-value)
        # Add tiny epsilon to avoid log(0)
        data['neg_log_p'] = -np.log10(data[p_col] + 1e-300)
        
        # Determine status
        conditions = [
            (data[fc_col] > 1) & (data[p_col] < 0.05),
            (data[fc_col] < -1) & (data[p_col] < 0.05)
        ]
        choices = ['UP', 'DOWN']
        data['status'] = np.select(conditions, choices, default='NEUTRAL')
        
        return {
            "x": data[fc_col].tolist(),
            "y": data['neg_log_p'].tolist(),
            "status": data['status'].tolist(),
            "genes": data.get('gene', data.index).tolist()
        }

    def get_top_genes(self, n=50):
        """Returns the top N most significant genes for the table."""
        if self.df is None: return []
        
        cols = self.df.columns
        p_col = next(c for c in cols if c in ['padj', 'pvalue', 'fdr', 'qvalue'])
        fc_col = next(c for c in cols if c in ['log2foldchange', 'logfc', 'fc', 'foldchange', 'log2fc'])
        gene_col = 'gene' if 'gene' in cols else 'index'
        
        # Sort by p-value
        sorted_df = self.df.sort_values(by=p_col).head(n)
        
        results = []
        for i, row in sorted_df.iterrows():
            gene_name = row[gene_col] if gene_col != 'index' else i
            results.append({
                "gene": str(gene_name),
                "fc": row[fc_col],
                "pval": row[p_col]
            })
        return results