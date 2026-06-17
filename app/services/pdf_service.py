from weasyprint import HTML
from io import BytesIO
from typing import List


def generate_checklist_pdf(documents: List[str], user_name: str = "User") -> BytesIO:
    """Generate PDF checklist for user"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            .document-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
            .header {{ margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Housing Stability Document Checklist</h1>
            <p>For: {user_name}</p>
        </div>
        <h2>Required Documents:</h2>
        <ul>
            {"".join([f'<li class="document-item">{doc}</li>' for doc in documents])}
        </ul>
        <div style="margin-top:40px; padding:20px; background:#f8f9fa;">
            <p><strong>Important:</strong> This is not legal advice. Contact legal aid for help.</p>
        </div>
    </body>
    </html>
    """
    pdf_bytes = BytesIO()
    HTML(string=html_content).write_pdf(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes
