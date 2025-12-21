from pygenomeviz import GenomeViz
import os

def generate_circular_map(gff_path, output_png):
    """
    Reads a GFF file and generates a circular visualization.
    """
    try:
        # 1. Initialize GenomeViz
        gv = GenomeViz(feature_track_ratio=0.3)
        
        # 2. Load the features from the GFF file
        # We find the length of the genome based on the last gene
        gv.from_gff(gff_path)
        
        # 3. Configure the Circular Plot
        fig = gv.plot_fig(plot_style="circular", 
                          fig_width=8, 
                          fig_track_height=0.5,
                          track_align=True)
        
        # 4. Save the figure
        fig.savefig(output_png, dpi=300)
        return True, output_png
    except Exception as e:
        return False, str(e)

def generate_linear_map(gff_path, output_png, start=0, end=10000):
    """
    Generates a linear map of a specific region (useful for gene clusters).
    """
    try:
        gv = GenomeViz()
        gv.from_gff(gff_path)
        fig = gv.plot_fig(plot_style="linear", range=(start, end))
        fig.savefig(output_png, dpi=300)
        return True, output_png
    except Exception as e:
        return False, str(e)