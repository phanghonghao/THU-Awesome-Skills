# html-slides

Generate 16:9 HTML presentations (slides) from content, with light-color backgrounds and configurable accent color. Output a single self-contained `.html` file + optional PDF export via Playwright.

## When to Use

User mentions: `html-slides`, `html ppt`, `HTML 演示文稿`, `HTML 幻灯片`, `生成 PPT`, `生成幻灯片`, `slide`, `slides`, `演示文稿`, `presentation`, or wants to create a visual slide deck from notes/reports/content.

## Core Principles

1. **Light background is MANDATORY** — all slides use pale/white backgrounds (`#FEFEFF`, `#FDF8FF`, `#F9F5FC` range). Never use dark/black slide backgrounds.
2. **Accent color** — default Tsinghua purple `#660874`. User can override (e.g., "清华紫", "蓝色", "#3366CC").
3. **16:9 aspect ratio** — slide container is `1280px × 720px`.
4. **Self-contained HTML** — all CSS/JS inline, no external dependencies except Google Fonts CDN (Noto Sans SC).
5. **Font size ≥ 20px** — all readable content text must be at least 20px. Slide titles 28-36px, body text 20-24px.
6. **Max 10 slides** — keep presentations concise; if content is dense, use multiple cards per slide.

## Slide Layout Types

### 1. Cover Slide
- Centered title + subtitle + tags/team
- Light gradient background (pale accent → white)
- Optional background image at very low opacity (≤ 10%)

### 2. Split Slide (image + text)
- Left: full-height image (480px wide)
- Right: header + content cards
- Use for visual storytelling slides

### 3. Standard Slide (text-only)
- Header bar (number badge + title)
- Two-column or single-column card layout
- Cards with left border accent

### 4. Step/Grid Slide
- 4-column grid for timelines, roadmaps
- Cards with top border accent

### 5. Team/Conclusion Slide
- Avatar cards for team members
- Gradient conclusion banner

## Workflow

### Step 1: Collect Content

Ask user for content source:
- A `.md` / `.docx` / `.pdf` file path → read and extract
- Or direct text description of what slides should contain

### Step 2: Plan Slides

Analyze content and plan slide structure:

```
Slide 1: Cover (title + subtitle + team)
Slide 2: [Topic A] — split layout with image
Slide 3: [Topic B] — two-column cards
...
Slide N: Team + Conclusion
```

Present plan to user for confirmation.

### Step 3: Generate Images (Optional)

If user wants AI-generated images, call `/ai-gen` to produce:
- Cover image
- Section/topic illustrations (1536×1024 landscape)

Save images alongside the HTML file in an `ai_gen_output/` subfolder.

### Step 4: Generate HTML

Create a single `.html` file with all slides. Follow these CSS conventions:

**Color palette (light theme):**
```css
--purple: #660874;          /* accent */
--purple-light: #8B2FA0;
--purple-pale: #F3E5F8;     /* card backgrounds */
--purple-accent: #9B30FF;
--bg: #FEFEFF;              /* slide background — near white */
--card-bg: #F9F5FC;         /* card fill — very pale purple */
--text: #2D2D3A;
--text-light: #5A5A6E;
```

**Font sizes (minimums):**
- Slide title: 32-36px, font-weight 700
- Card heading (h3): 22-24px, font-weight 700
- Card body (p, li): 20-22px, line-height 1.5-1.7
- Quote text: 20-22px
- Year numbers: 32-36px, font-weight 900
- Cover title: 56-68px
- Cover subtitle: 24-28px
- Cover tags: 20-22px

**HTML structure:**
```html
<div class="presentation" style="width:1280px;height:720px;">
  <div class="slide slide-cover active">...</div>
  <div class="slide slide-standard">...</div>
  <div class="slide slide-split">...</div>
  ...
</div>
```

**Navigation JS:**
- Keyboard: Arrow keys, Space to advance
- Bottom nav bar with prev/next buttons and page counter
- Touch swipe support

### Step 5: Export PDF (if requested)

Use Playwright to export each slide as a PDF page, then merge with PyMuPDF:

```python
from playwright.async_api import async_playwright
import fitz

async def export_pdf(html_path, pdf_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 720})
        await page.goto(f'file:///{html_path}')
        total = await page.evaluate('document.querySelectorAll(".slide").length')

        temp_pdfs = []
        for i in range(total):
            await page.evaluate(f'show({i})')
            await page.wait_for_timeout(500)
            temp = f'_slide_{i}.pdf'
            await page.pdf(path=temp, width='1280px', height='720px',
                          margin={'top':'0','bottom':'0','left':'0','right':'0'},
                          print_background=True)
            temp_pdfs.append(temp)
        await browser.close()

    # Merge
    merged = fitz.open()
    for tp in temp_pdfs:
        d = fitz.open(tp); merged.insert_pdf(d); d.close(); os.remove(tp)
    merged.save(pdf_path); merged.close()
```

### Step 6: Deliver

Report to user:
- HTML file path (open in browser to view)
- PDF file path (if exported)
- Brief slide summary table

## Tips

- Keep bullet points short — ≤ 2 lines each at 20px
- Use `strong` tags for key terms, not bold colors
- Cards should have max 4-5 bullets to avoid overflow
- For dense content, split across more slides rather than cramming
- Always test that text doesn't overflow the 720px slide height
- Images in `slide-split` layout: 480px wide, object-fit: cover
