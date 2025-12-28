import subprocess
import os
import sys

def get_bin_path(tool_name):
    """
    Helper to find the correct binary path within the 'tools' folder.
    Adds .exe extension if running on Windows.
    """
    base_path = os.path.join(os.getcwd(), "tools", tool_name)
    if sys.platform == "win32":
        return f"{base_path}.exe"
    return base_path

def run_prodigal(input_fasta, output_gff):
    """
    Wrapper for Prodigal (Gene Prediction)[cite: 97, 164].
    Takes a FASTA file and produces a GFF3 annotation file.
    """
    exe = get_bin_path("prodigal")
    
    # Check if the binary exists before running
    if not os.path.exists(exe):
        return False, f"Error: {exe} not found. Please bundle tools correctly."

    # Construct the command line arguments for Prodigal
    # -i: input, -o: output, -f: format gff
    command = [exe, "-i", input_fasta, "-o", output_gff, "-f", "gff"]

    try:
        # Run the tool as a background process
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        return True, "Success"
    except subprocess.CalledProcessError as e:
        return False, f"Prodigal failed: {e.stderr}"
    except Exception as e:
        return False, str(e)