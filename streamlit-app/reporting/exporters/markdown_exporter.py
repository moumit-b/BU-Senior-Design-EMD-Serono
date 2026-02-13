"""Markdown Exporter"""

class MarkdownExporter:
    def export(self, report_data):
        return report_data.get("markdown", str(report_data))
