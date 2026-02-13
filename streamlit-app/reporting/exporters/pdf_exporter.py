"""PDF Exporter using markdown"""

import markdown

class PDFExporter:
    def export(self, report_data):
        md_content = report_data.get("markdown", str(report_data))
        # Convert markdown to HTML (PDF generation would require weasyprint)
        html = markdown.markdown(md_content)
        return f"<!DOCTYPE html><html><body>{html}</body></html>"
