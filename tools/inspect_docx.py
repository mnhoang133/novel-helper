"""
Tool: inspect_docx.py
Description: Fast command-line diagnostic tool to inspect a Word (.docx) file layout geometry,
             OpenXML tags (mirrorMargins, evenAndOddHeaders), and section margins without opening Word.
Usage: python tools/inspect_docx.py <path_to_docx>
"""

import sys
import os

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import zipfile
import xml.etree.ElementTree as ET

def inspect_docx(docx_path: str):
    if not os.path.isfile(docx_path):
        print(f"Error: File not found: {docx_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"  DOCX DIAGNOSTIC INSPECTION: {os.path.basename(docx_path)}")
    print("=" * 60)

    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            # 1. Inspect settings.xml
            settings_xml = ""
            if "word/settings.xml" in z.namelist():
                settings_xml = z.read("word/settings.xml").decode("utf-8", errors="ignore")

            has_mirror = "mirrorMargins" in settings_xml
            has_even_odd = "evenAndOddHeaders" in settings_xml

            print(f"OpenXML Mirror Margins     : {'FOUND (Enabled)' if has_mirror else 'NOT FOUND (Disabled)'}")
            print(f"OpenXML Even/Odd Headers   : {'FOUND (Enabled)' if has_even_odd else 'NOT FOUND (Disabled)'}")

            # 2. Inspect document.xml for sectPr
            doc_xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            root = ET.fromstring(doc_xml)

            # Find w:sectPr
            sectPr = None
            for elem in root.iter():
                if elem.tag.endswith("sectPr"):
                    sectPr = elem

            if sectPr is not None:
                print("\nSection Page Setup (w:pgMar):")
                for child in sectPr:
                    if child.tag.endswith("pgMar"):
                        # Values in dxa (1 cm = 567 dxa, 1 inch = 1440 dxa)
                        def to_cm(val):
                            return f"{float(val) / 567.0:.2f} cm" if val else "N/A"

                        top = child.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}top")
                        bottom = child.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bottom")
                        left = child.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}left")
                        right = child.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}right")
                        footer = child.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footer")

                        print(f"  • Left Margin (Inside if Mirror) : {to_cm(left)}")
                        print(f"  • Right Margin (Outside if Mirror): {to_cm(right)}")
                        print(f"  • Top Margin                     : {to_cm(top)}")
                        print(f"  • Bottom Margin                  : {to_cm(bottom)}")
                        print(f"  • Footer Distance                : {to_cm(footer)}")

            # 3. Check Footers
            footers = [n for n in z.namelist() if "footer" in n]
            print(f"\nHeader/Footer XML Parts: {len(footers)} found ({', '.join(footers)})")

    except Exception as e:
        print(f"Error inspecting docx: {e}")

    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/inspect_docx.py <path_to_docx>")
        sys.exit(1)
    inspect_docx(sys.argv[1])
