# SPEC: Margins, Mirror Margins & Book Binding

## 1. Physical Book Binding Requirements
In physical two-sided book printing, sheets are bound together at the central spine.
- **Inside Margin (Gáy dán)**: Must be wider than the outer margin so text is not pinched into the binding glue/thread.
- **Outside Margin (Mép ngoài)**: The outer cut edge where the reader holds and turns pages.

---

## 2. OpenXML Elements
To achieve native Microsoft Word two-sided page mirroring:
1. `<w:mirrorMargins/>`: Injected into `word/settings.xml`. Tells Word to alternate the `left_margin` and `right_margin` definitions between facing pages:
   - **Odd Pages (Trang lẻ - right side of spread)**: Left edge is Inside (Gáy dán); Right edge is Outside (Mép ngoài).
   - **Even Pages (Trang chẵn - left side of spread)**: Left edge is Outside (Mép ngoài); Right edge is Inside (Gáy dán).
2. `<w:evenAndOddHeaders/>`: Injected into `word/settings.xml`. Enables distinct footers for even and odd pages:
   - **Odd Page Footer (`sec.footer`)**: Numbering aligned **RIGHT** (outer edge).
   - **Even Page Footer (`sec.even_page_footer`)**: Numbering aligned **LEFT** (outer edge).
   - **Cover Page Footer (`sec.first_page_footer`)**: Cleared (suppressed).

---

## 3. Smart Safe Binding Rule
If the user sets inside margin $\le$ outside margin (e.g. setting all margins to 0.6cm to save paper), the system automatically enforces a safe binding width:
$$\text{Inside Margin} = \max\left(1.2\text{ cm}, \text{Outside Margin} \times 2.0\right)$$
- If Outside = 0.6 cm $\rightarrow$ Inside becomes 1.2 cm.
  - Page 6 (even): Left = 0.6 cm, Right = 1.2 cm.
  - Page 7 (odd): Left = 1.2 cm, Right = 0.6 cm.

---

## 4. Verification Tool
Verify any generated DOCX in 0.2s without opening Word:
```bash
python tools/inspect_docx.py "path/to/document.docx"
```
