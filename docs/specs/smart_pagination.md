# 📄 SPEC: Smart Pagination & Orphan Header Prevention

## 1. Problem Statement
In traditional document exporting, either:
1. Every chapter starts on a new page (wastes 50-80% blank space on half-empty pages).
2. Chapters flow continuously (headings risk appearing at the very bottom of a page without text below them — "orphan headings").

---

## 2. The Rule of 8.0 Lines (`core/docx_builder.py`)
A physical page contains $N$ lines (e.g. 33.4 lines).
Starting a new chapter requires:
- Chapter Heading (`CHAPTER X`) + Ornament divider (`~ ✦ ~`) + spacing: $\approx 5.0\text{ lines}$
- Minimum body text to establish readable context: $\mathbf{3.0\text{ lines}}$
- **Minimum Required Space**: $\mathbf{8.0\text{ lines}}$

### Decision Logic:
```python
lines_remaining = lines_per_page - lines_on_current_page
if lines_remaining >= 8.0:
    # Sufficient space: insert decorative separator and start chapter on current page
    p_sep = doc.add_paragraph()
    ...
    lines_on_current_page += 2.0
else:
    # Insufficient space: insert page break to prevent orphan heading
    doc.add_page_break()
    lines_on_current_page = 0.0
```

---

## 3. Paragraph Keep-With-Next Locks
To ensure Word never breaks between a heading and its first sentence:
- `h.paragraph_format.keep_with_next = True` (attached to heading)
- `p_div.paragraph_format.keep_with_next = True` (attached to ornament)
- `first_para.paragraph_format.keep_with_next = True` (attached to paragraph 1)
