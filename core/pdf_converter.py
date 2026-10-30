"""
Module: core.pdf_converter
Description: High-fidelity DOCX to PDF conversion via Microsoft Word COM automation,
             refreshing Table of Contents and Page numbering prior to saving.
Author: Google Deepmind Agent
"""

import os
import subprocess


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Converts a DOCX file to PDF using Microsoft Word COM automation.
    Refreshes Table of Contents and Page Numbers before rendering.
    """
    docx_abs = os.path.abspath(docx_path).replace("'", "''")
    pdf_abs = os.path.abspath(pdf_path).replace("'", "''")

    if os.path.isfile(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass

    ps_cmd = f"""
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    try {{
        $doc = $word.Documents.Open('{docx_abs}')
        foreach ($toc in $doc.TablesOfContents) {{ $toc.Update() }}
        foreach ($f in $doc.Fields) {{ $f.Update() }}
        $doc.SaveAs([ref]'{pdf_abs}', [ref]17)
        $doc.Close([ref]0)
        Write-Output "SUCCESS_CONVERT"
    }} catch {{
        Write-Error $_
    }} finally {{
        $word.Quit()
    }}
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=180
        )
        if "SUCCESS_CONVERT" in res.stdout:
            return True
        print(f"Word COM conversion error: {res.stderr}")
        return False
    except Exception as e:
        print(f"Exception converting DOCX to PDF: {e}")
        return False
