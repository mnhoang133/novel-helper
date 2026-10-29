# SPEC: Dynamic Page Math & TOC Capacity

## 1. Printable Page Dimensions (A4)
Standard A4 dimensions: **21.0 cm $\times$ 29.7 cm**.

$$\text{Printable Height} = 29.7 - (\text{Top Margin} + \text{Bottom Margin})$$
$$\text{Printable Width} = 21.0 - (\text{Inside Margin} + \text{Outside Margin})$$

---

## 2. Dynamic Capacity Formulas (`core/page_metrics.py`)

### A. Body Lines Per Page
Base reference: 27.3cm height (1.2cm margins) with 14pt Georgia font = 32.0 lines.
$$\text{Lines Per Page} = 32.0 \times \left(\frac{\text{Printable Height}}{27.3}\right) \times \left(\frac{14.0}{\text{Body Font Size}}\right)$$
- Narrow margins (0.6cm top/bottom, 28.5cm height): **~33.4 lines** (or **~39.0 lines** with 12pt font).

### B. Characters Per Line
Base reference: 17.8cm width with 14pt Georgia font = 68 characters.
$$\text{Chars Per Line} = \text{round}\left(68.0 \times \left(\frac{\text{Printable Width}}{17.8}\right) \times \left(\frac{14.0}{\text{Body Font Size}}\right)\right)$$
- Narrow margins (1.2cm inside, 0.6cm outside, 19.2cm width): **~73 chars/line**.

### C. Table of Contents Capacity (TOC Entries Per Page)
TOC header occupies ~3.2cm. Each TOC row consumes ~0.65cm.
$$\text{TOC Capacity} = \text{int}\left(\frac{\text{Printable Height} - 3.2}{0.65}\right)$$
- Standard 1.2cm margins: **32 chapters/page**.
- Narrow 0.6cm margins: **38 to 40 chapters/page**!
- Wide 2.0cm margins: **26 to 28 chapters/page**.

---

## 3. Balanced Volume Partitioning (`core/volume_splitter.py`)
To prevent the final volume from having an awkward 2-chapter stub and maximize Table of Contents efficiency:
1. Supported Tiers:
   - **Tier Tối ưu 1 (Full 1 trang TOC)**: Finds the exact $K$ that maximizes TOC fullness on 1 single page (~95% full), dividing chapters evenly so no volume differs from another by more than 1 chapter.
   - **Tier Tối ưu 2 (Full 2 trang TOC - Cuốn dày / Chap ngắn)**: Finds the exact $K$ that fills 2 full TOC pages (~60-80 chapters/vol), tailored for thick volumes or novels with short chapters.
   - **Tier 1: Mỏng (50 - 100 trang)**
   - **Tier 2: Chuẩn (100 - 200 trang)**
   - **Tier 3: Vừa (200 - 300 trang)**
   - **Tier 4: Dày (300 - 400 trang)**
2. Equalize chapter counts across $K$ volumes:
   $$\text{Base Chapters} = \lfloor N / K \rfloor, \quad \text{Remainder} = N \pmod K$$
   - The first $\text{Remainder}$ volumes receive $\text{Base} + 1$ chapters, and the remaining receive $\text{Base}$ chapters.
   - Guaranteed equalized chapter distribution and zero orphan stubs.

---

## 4. Verification Tool
Simulate volume partitions and TOC fit instantly:
```bash
python tools/simulate_splitting.py "novel_folder" 1.2 0.6 0.6 0.6
```
