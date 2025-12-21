import os
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio import AlignIO
from io import StringIO

class PhylogenyManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.output_dir = os.path.join(self.project_dir, "phylo_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def build_tree_from_alignment(self, alignment_path):
        """
        Takes a multiple sequence alignment (FASTA format) and 
        constructs a Neighbor-Joining (NJ) tree.
        """
        try:
            # 1. Load the alignment
            alignment = AlignIO.read(alignment_path, "fasta")

            # 2. Calculate the Distance Matrix (using 'identity' model)
            calculator = DistanceCalculator('identity')
            dm = calculator.get_distance(alignment)

            # 3. Construct the Tree (Neighbor Joining)
            constructor = DistanceTreeConstructor(calculator, 'nj')
            tree = constructor.build_tree(alignment)

            # 4. Save the tree in Newick format
            tree_path = os.path.join(self.output_dir, "phylogeny.nwk")
            Phylo.write(tree, tree_path, "newick")

            return {
                "success": True,
                "tree_path": tree_path,
                "tree_obj": tree,
                "message": "Phylogenetic tree constructed successfully."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}