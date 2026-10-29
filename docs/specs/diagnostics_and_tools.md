# 🛠️ SPEC: Diagnostics, Observability & Debug Tools

## 1. Automated Export Audit Report (`print/last_export_report.txt`)
Whenever a document or batch of volumes is exported, `core/diagnostics.py` automatically generates an audit report in the output `print/` folder.

### What it Contains:
- Exact margins requested by user vs. effective geometry applied to OpenXML.
- Safe binding gutter elevation status (whether inside margin was automatically elevated).
- Physical capacity calculations (Lines/page, characters/line, TOC entries/page).
- Volume breakdown and generated file paths.

### Why it Matters:
- Eliminates the black-box effect. Developers and users can check margins and formatting without writing inspection scripts or opening Microsoft Word.

---

## 2. CLI Tool: `tools/inspect_docx.py`
Instantly inspects OpenXML tags, margins, and headers/footers in any `.docx` file in < 0.2s:
```bash
python tools/inspect_docx.py "path/to/novel_Volume_01.docx"
```

Output:
```
============================================================
  DOCX DIAGNOSTIC INSPECTION: novel_Volume_01.docx
============================================================
OpenXML Mirror Margins     : FOUND (Enabled)
OpenXML Even/Odd Headers   : FOUND (Enabled)

Section Page Setup (w:pgMar):
  • Left Margin (Inside if Mirror) : 1.20 cm
  • Right Margin (Outside if Mirror): 0.60 cm
  • Top Margin                     : 1.20 cm
  • Bottom Margin                  : 1.20 cm
  • Footer Distance                : 0.70 cm

Header/Footer XML Parts: 3 found (word/footer1.xml, word/footer2.xml, word/footer3.xml)
============================================================
```

---

## 3. CLI Tool: `tools/simulate_splitting.py`
Simulates volume partitioning and TOC page capacity given any set of margins:
```bash
python tools/simulate_splitting.py "novel_folder" 1.2 0.6 0.6 0.6
```
