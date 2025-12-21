import os
from fpdf import FPDF
from datetime import datetime

class ReportManager:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.output_dir = os.path.join(self.project_dir, "reports")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf_report(self, sample_name, annotation_data, amr_hits, vf_hits):
        """
        Compiles analysis results into a structured PDF report.
        """
        pdf = FPDF()
        pdf.add_page()
        
        # 1. Header
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 10, "MicroGenome Analyzer - Analysis Report", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)

        # 2. Genome Summary Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Sample: {sample_name}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Total Genes Predicted: {len(annotation_data)}", ln=True)
        pdf.ln(5)

        # 3. AMR Findings (Section 4.4)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 10, "Antimicrobial Resistance Profile", ln=True, fill=True)
        pdf.set_font("Arial", size=10)
        if amr_hits:
            for hit in amr_hits[:10]: # Top 10 hits
                pdf.multi_cell(0, 8, f"- {hit['card_match']}: {hit['description']} ({hit['identity']}% id)")
        else:
            pdf.cell(0, 10, "No significant AMR genes detected.", ln=True)
        pdf.ln(5)

        # 4. Virulence Findings (Section 4.5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Virulence Factor Assessment", ln=True, fill=True)
        pdf.set_font("Arial", size=10)
        if vf_hits:
            for hit in vf_hits[:10]:
                pdf.multi_cell(0, 8, f"- {hit['vf_match']}: {hit['description']}")
        else:
            pdf.cell(0, 10, "No major virulence factors detected.", ln=True)

        # 5. Save the report
        report_path = os.path.join(self.output_dir, f"{sample_name}_Summary.pdf")
        pdf.output(report_path)
        return report_path