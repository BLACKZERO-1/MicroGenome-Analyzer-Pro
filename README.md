# 🧬 MicroGenome Analyzer Pro

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production_Ready-success.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-GUI-green.svg?style=for-the-badge&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg?style=for-the-badge)

**MicroGenome Analyzer Pro** is a comprehensive desktop bioinformatics suite designed for the offline analysis of microbial genomes. Built for researchers and students, it integrates industry-standard tools into a modern "Mission Control" interface, allowing for seamless annotation, phylogenetic inference, and pathogen screening without requiring command-line expertise.

---

## 🚀 Key Features

### 1. 🧬 Automated Annotation
* **Engine:** **Prodigal (v2.6.3)** integration for high-accuracy gene prediction.
* **Logic:** Smart mode switching (Single vs. Metagenomic) based on genome size.
* **Output:** Generates standard GFF3 feature tables and protein FASTA files.

### 2. 🛡️ Pathogen Screening (Bio-Defense)
* **Engine:** **NCBI BLAST+ (v2.16.0)** local alignment search.
* **Databases:** Integrated support for **CARD** (Antimicrobial Resistance) and **VFDB** (Virulence Factors).
* **Alerts:** Real-time "Red Alert" system for detecting critical resistance genes (e.g., *blaTEM*, *mecA*).

### 3. 🌳 Phylogenetics & Alignment
* **Pipeline:** Automated workflow using **MAFFT** (Alignment) → **FastTree** (ML Tree Construction).
* **Visualization:** Generates Newick tree strings for immediate analysis.

### 4. 📊 Comparative Genomics
* **Metric:** **ANI (Average Nucleotide Identity)** calculation.
* **Function:** Pairwise BLAST alignment to determine species similarity (0-100%) and coverage.

### 5. 📝 Publication-Ready Reports
* **Engine:** Custom HTML Report Generator.
* **Output:** Produces interactive Executive Summaries with findings, badges, and threat assessments.

---

## 🛠️ Installation & Usage

### Option A: Run as Standalone App (No Python Required)
1. Download the latest **Release** from the right sidebar.
2. Extract the ZIP file.
3. Open the folder and run **`MicroGenome Analyzer.exe`**.
4. *Note: Ensure the `tools` and `databases` folders are in the same directory as the executable.*

### Option B: Run from Source
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/BLACKZERO-1/MicroGenome-Analyzer-Pro.git](https://github.com/BLACKZERO-1/MicroGenome-Analyzer-Pro.git)
   cd MicroGenome-Analyzer-Pro
