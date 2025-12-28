import os
import subprocess
import sys

def test_blast_tools():
    base_path = os.getcwd()
    blast_bin = os.path.join(base_path, "tools", "blast")
    makeblastdb = os.path.join(blast_bin, "makeblastdb.exe")
    blastn = os.path.join(blast_bin, "blastn.exe")
    output_dir = os.path.join(base_path, "results", "comparative_debug")
    os.makedirs(output_dir, exist_ok=True)

    print(f"🔍 Checking Tools in: {blast_bin}")
    if not os.path.exists(makeblastdb): print("❌ makeblastdb.exe MISSING"); return
    if not os.path.exists(blastn): print("❌ blastn.exe MISSING"); return
    print("✅ Tools found.")

    # 1. Create Dummy Input
    dummy_fasta = os.path.join(output_dir, "test.fasta")
    with open(dummy_fasta, "w") as f:
        f.write(">seq1\nATGCATGCATGC\n>seq2\nATGCATGCATGC")
    print(f"📄 Created dummy input: {dummy_fasta}")

    # 2. Test makeblastdb
    print("\n⚙️  TEST 1: Running makeblastdb...")
    db_out = os.path.join(output_dir, "test_db")
    cmd_db = [
        makeblastdb,
        "-in", dummy_fasta,
        "-dbtype", "nucl",
        "-out", db_out,
        "-title", "TestDB"
    ]
    
    try:
        # Running without shell=True to see raw output
        result = subprocess.run(
            cmd_db, 
            capture_output=True, 
            text=True, 
            stdin=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print("✅ makeblastdb SUCCESS!")
        else:
            print("❌ makeblastdb FAILED!")
            print("STDERR:", result.stderr)
            return
    except Exception as e:
        print(f"❌ Python Exception: {e}")
        return

    # 3. Test blastn
    print("\n⚔️  TEST 2: Running blastn...")
    cmd_blast = [
        blastn,
        "-query", dummy_fasta,
        "-db", db_out,
        "-outfmt", "6",
        "-out", os.path.join(output_dir, "results.txt")
    ]
    
    try:
        result = subprocess.run(
            cmd_blast, 
            capture_output=True, 
            text=True, 
            stdin=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print("✅ blastn SUCCESS!")
            print("🎉 ALL SYSTEMS GO. The tools work correctly.")
        else:
            print("❌ blastn FAILED!")
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"❌ Python Exception: {e}")

if __name__ == "__main__":
    test_blast_tools()