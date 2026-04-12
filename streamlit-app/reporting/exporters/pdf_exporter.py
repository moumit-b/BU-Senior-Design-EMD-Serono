"""PDF Exporter — converts markdown report to PDF bytes via WeasyPrint."""

import markdown as _md


_CSS = """
body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a2e;
    margin: 2cm 2.5cm;
}
h1 { font-size: 18pt; color: #0d3b66; border-bottom: 2px solid #0d3b66; padding-bottom: 4px; }
h2 { font-size: 14pt; color: #1b4f72; margin-top: 1.4em; }
h3 { font-size: 12pt; color: #2c3e50; margin-top: 1em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
th { background: #0d3b66; color: white; padding: 6px 10px; text-align: left; }
td { padding: 5px 10px; border-bottom: 1px solid #dce3ea; }
tr:nth-child(even) td { background: #f4f7fb; }
code { background: #f0f4f8; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }
pre { background: #f0f4f8; padding: 10px; border-radius: 4px; overflow-x: auto; }
blockquote { border-left: 4px solid #0d3b66; margin: 0; padding-left: 1em; color: #555; }
a { color: #0d3b66; }
"""


class PDFExporter:
    def export(self, report_data: dict) -> bytes:
        """Convert markdown report to PDF bytes.

        Returns PDF bytes if WeasyPrint is available, otherwise raises RuntimeError.
        """
        md_content = report_data.get("markdown", str(report_data))
        html_body = _md.markdown(
            md_content,
            extensions=["tables", "fenced_code", "nl2br"],
        )
        full_html = (
            f"<!DOCTYPE html><html><head>"
            f"<meta charset='utf-8'>"
            f"<style>{_CSS}</style>"
            f"</head><body>{html_body}</body></html>"
        )

        try:
            import weasyprint
            pdf_bytes = weasyprint.HTML(string=full_html).write_pdf()
            return pdf_bytes
        except ImportError:
            raise RuntimeError(
                "WeasyPrint is not installed. "
                "Install it with: pip install weasyprint"
            )
