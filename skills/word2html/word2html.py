# -*- coding: utf-8 -*-
"""Convert DOCX to standalone HTML with tables, images, math formulas.

Features:
  - Tables with merged cells (colspan / rowspan via gridSpan / vMerge)
  - Images: extracted to `images/` folder, referenced via <img> tags
  - Bold / italic / underline / strikethrough
  - OMML math formulas rendered as LaTeX via MathJax
  - Self-contained HTML (inline CSS, only external dep is MathJax CDN)
"""
import sys, io, os, zipfile, base64, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
from docx.oxml.ns import qn

# ─── Math helpers (shared with word2md) ──────────────────────────────

GREEK = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\varepsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta',
    'ι': r'\iota', 'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
    'ν': r'\nu', 'ξ': r'\xi', 'π': r'\pi', 'ρ': r'\rho',
    'σ': r'\sigma', 'τ': r'\tau', 'υ': r'\upsilon', 'φ': r'\varphi',
    'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Φ': r'\Phi',
    'Ψ': r'\Psi', 'Ω': r'\Omega',
}
SYMBOLS = {
    '≥': r'\geq ', '≤': r'\leq ', '≈': r'\approx ', '≠': r'\neq ',
    '⋅': r'\cdot ', '×': r'\times ', '∼': r'\sim ',
    '→': r'\to ', '∈': r'\in ', '∘': r'^\circ',
    '∓': r'\mp ', '±': r'\pm ',
}


def texify(s):
    for ch, cmd in GREEK.items():
        s = s.replace(ch, cmd)
    for ch, cmd in SYMBOLS.items():
        s = s.replace(ch, cmd)
    return s


def omml_to_latex(elem):
    parts = []
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'r':
            txt = ''.join(t.text or '' for t in child.findall(qn('m:t')))
            if txt:
                parts.append(texify(txt))
        elif tag == 'sSub':
            b = omml_to_latex(child.find(qn('m:e')))
            s = omml_to_latex(child.find(qn('m:sub')))
            parts.append(f'{b}_{{{s}}}' if b and s else (b or ''))
        elif tag == 'sSup':
            b = omml_to_latex(child.find(qn('m:e')))
            s = omml_to_latex(child.find(qn('m:sup')))
            parts.append(f'{b}^{{{s}}}' if b and s else (b or ''))
        elif tag == 'sSubSup':
            b = omml_to_latex(child.find(qn('m:e')))
            s = omml_to_latex(child.find(qn('m:sub')))
            sp = omml_to_latex(child.find(qn('m:sup')))
            r = b or ''
            if s: r += f'_{{{s}}}'
            if sp: r += f'^{{{sp}}}'
            parts.append(r)
        elif tag == 'f':
            n = omml_to_latex(child.find(qn('m:num')))
            d = omml_to_latex(child.find(qn('m:den')))
            parts.append(f'\\frac{{{n}}}{{{d}}}' if n and d else (n or ''))
        elif tag == 'rad':
            deg = omml_to_latex(child.find(qn('m:deg')))
            e = omml_to_latex(child.find(qn('m:e')))
            parts.append(f'\\sqrt[{deg}]{{{e}}}' if deg else f'\\sqrt{{{e}}}')
        elif tag == 'd':
            dpr = child.find(qn('m:dPr'))
            bc, ec = '(', ')'
            if dpr is not None:
                be = dpr.find(qn('m:begChr'))
                ee = dpr.find(qn('m:endChr'))
                if be is not None: bc = be.get(qn('m:val'), '(')
                if ee is not None: ec = ee.get(qn('m:val'), ')')
            inner = [omml_to_latex(e) for e in child.findall(qn('m:e'))]
            parts.append(f'\\left{bc}{",".join(inner)}\\right{ec}')
        elif tag == 'nary':
            npr = child.find(qn('m:naryPr'))
            ce = npr.find(qn('m:chr')) if npr is not None else None
            cv = ce.get(qn('m:val')) if ce is not None else None
            opm = {'∑': '\\sum', '∫': '\\int', '∏': '\\prod'}
            op = opm.get(cv, cv or '\\sum')
            se = omml_to_latex(child.find(qn('m:sub')))
            spe = omml_to_latex(child.find(qn('m:sup')))
            ee = omml_to_latex(child.find(qn('m:e')))
            r = op
            if se: r += f'_{{{se}}}'
            if spe: r += f'^{{{spe}}}'
            if ee: r += f' {ee}'
            parts.append(r)
        elif tag == 'func':
            fn = omml_to_latex(child.find(qn('m:fName')))
            e = omml_to_latex(child.find(qn('m:e')))
            if fn: parts.append(fn)
            if e: parts.append(e)
        elif tag == 'limLow':
            e = omml_to_latex(child.find(qn('m:e')))
            l = omml_to_latex(child.find(qn('m:lim')))
            parts.append(f'{{{e}}}_{{{l}}}' if e and l else (e or ''))
        elif tag == 'limUpp':
            e = omml_to_latex(child.find(qn('m:e')))
            l = omml_to_latex(child.find(qn('m:lim')))
            parts.append(f'{{{e}}}^{{{l}}}' if e and l else (e or ''))
        elif tag == 'acc':
            apr = child.find(qn('m:accPr'))
            cv = '\u0302'
            if apr is not None:
                ce = apr.find(qn('m:chr'))
                if ce is not None: cv = ce.get(qn('m:val'), '\u0302')
            am = {'\u0302': '\\hat', '\u0304': '\\bar', '\u0303': '\\tilde',
                  '\u0307': '\\dot', '\u20d7': '\\vec'}
            e = omml_to_latex(child.find(qn('m:e')))
            if e: parts.append(f'{am.get(cv, "\\hat")}{{{e}}}')
        elif tag in ('e', 'oMath', 'oMathPara'):
            inner = omml_to_latex(child)
            if inner: parts.append(inner)
        elif not tag.endswith('Pr') and tag != 'ctrlPr':
            txt = ''.join(t.text or '' for t in child.findall(qn('m:t')))
            if txt: parts.append(texify(txt))
            inner = omml_to_latex(child)
            if inner: parts.append(inner)
    return ''.join(parts)


# ─── Image extraction ────────────────────────────────────────────────

def extract_images(input_path, img_dir):
    """Extract all images from docx zip -> img_dir. Return {internal_path: filename}."""
    img_map = {}
    os.makedirs(img_dir, exist_ok=True)
    with zipfile.ZipFile(input_path) as zf:
        for name in zf.namelist():
            if name.startswith('word/media/'):
                data = zf.read(name)
                basename = os.path.basename(name)
                out_path = os.path.join(img_dir, basename)
                base, ext = os.path.splitext(basename)
                counter = 1
                while os.path.exists(out_path):
                    with open(out_path, 'rb') as f:
                        if f.read() == data:
                            break
                    basename = f'{base}_{counter}{ext}'
                    out_path = os.path.join(img_dir, basename)
                    counter += 1
                if not os.path.exists(out_path):
                    with open(out_path, 'wb') as f:
                        f.write(data)
                img_map[name] = basename
    return img_map


def get_image_from_run(run_elem, doc, img_map):
    """Get extracted image filename from a run's drawing/blip element."""
    blips = run_elem.findall('.//' + qn('a:blip'))
    for blip in blips:
        rId = blip.get(qn('r:embed'))
        if not rId:
            continue
        try:
            rel = doc.part.rels[rId]
            target = rel.target_ref
            internal = target if target.startswith('word/') else 'word/' + target
            if internal in img_map:
                return img_map[internal]
            basename = os.path.basename(target)
            for path, name in img_map.items():
                if os.path.basename(path) == basename:
                    return name
        except KeyError:
            pass
    return None


# ─── HTML escape ─────────────────────────────────────────────────────

def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# ─── Run -> HTML ─────────────────────────────────────────────────────

def run_to_html(run_elem, doc, img_map, img_dir_name):
    """Convert a <w:r> element -> HTML string (text with formatting + images)."""
    parts = []

    # Image
    img_file = get_image_from_run(run_elem, doc, img_map)
    if img_file:
        rel_path = img_dir_name + '/' + img_file
        parts.append(f'<img src="{html_escape(rel_path)}" style="max-width:100%;">')

    # Text
    texts = [t.text for t in run_elem.findall(qn('w:t')) if t.text]
    text = ''.join(texts)
    if not text:
        return ''.join(parts)

    rPr = run_elem.find(qn('w:rPr'))
    bold = italic = strike = underline = False
    if rPr is not None:
        b_elem = rPr.find(qn('w:b'))
        if b_elem is not None:
            val = b_elem.get(qn('w:val'))
            bold = val is None or val not in ('0', 'false')
        i_elem = rPr.find(qn('w:i'))
        if i_elem is not None:
            val = i_elem.get(qn('w:val'))
            italic = val is None or val not in ('0', 'false')
        if rPr.find(qn('w:strike')) is not None:
            strike = True
        if rPr.find(qn('w:u')) is not None:
            underline = True

    text = html_escape(text)
    if bold and italic:     text = f'<b><i>{text}</i></b>'
    elif bold:              text = f'<b>{text}</b>'
    elif italic:            text = f'<i>{text}</i>'
    if strike:              text = f'<s>{text}</s>'
    if underline:           text = f'<u>{text}</u>'

    parts.append(text)
    return ''.join(parts)


# ─── Paragraph -> HTML ───────────────────────────────────────────────

def get_heading_level(para_elem):
    pPr = para_elem.find(qn('w:pPr'))
    if pPr is None: return 0
    pStyle = pPr.find(qn('w:pStyle'))
    if pStyle is None: return 0
    val = pStyle.get(qn('w:val'), '')
    if 'Heading1' in val or val == '1':  return 1
    if 'Heading2' in val or val == '2':  return 2
    if 'Heading3' in val or val == '3':  return 3
    if 'Heading4' in val or val == '4':  return 4
    if 'Heading5' in val or val == '5':  return 5
    return 0


def paragraph_to_html(para_elem, doc, img_map, img_dir_name):
    """Convert <w:p> -> HTML string."""
    parts = []

    for child in para_elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'pPr':
            continue
        elif tag == 'r':
            parts.append(run_to_html(child, doc, img_map, img_dir_name))
        elif tag == 'hyperlink':
            for r_elem in child.findall(qn('w:r')):
                parts.append(run_to_html(r_elem, doc, img_map, img_dir_name))
        elif tag == 'oMathPara':
            for om in child.findall(qn('m:oMath')):
                ltx = omml_to_latex(om)
                if ltx:
                    parts.append(f'<div class="math-display">$${ltx}$$</div>')
        elif tag == 'oMath':
            ltx = omml_to_latex(child)
            if ltx:
                parts.append(f'\\({ltx}\\)')

    content = ''.join(parts).strip()
    if not content:
        return ''

    heading = get_heading_level(para_elem)
    if heading > 0:
        return f'<h{heading}>{content}</h{heading}>\n'
    return f'<p>{content}</p>\n'


# ─── Table -> HTML (with merged cells) ───────────────────────────────

def table_to_html(tbl_elem, doc, img_map, img_dir_name):
    """Convert <w:tbl> -> HTML table with colspan/rowspan."""
    rows = tbl_elem.findall(qn('w:tr'))
    if not rows:
        return ''

    # Parse grid to compute rowspan
    # First pass: collect grid data
    grid_data = []  # [row_idx][col_idx] = (cell_elem, colspan, vMerge_type)
    for row in rows:
        cells = row.findall(qn('w:tc'))
        row_data = []
        for cell in cells:
            tcPr = cell.find(qn('w:tcPr'))
            colspan = 1
            vmerge_type = None  # None = not merged, 'restart' = starts merge, 'continue' = continues merge

            if tcPr is not None:
                gs = tcPr.find(qn('w:gridSpan'))
                if gs is not None:
                    colspan = int(gs.get(qn('w:val'), '1'))

                vm = tcPr.find(qn('w:vMerge'))
                if vm is not None:
                    val = vm.get(qn('w:val'))
                    vmerge_type = 'restart' if val == 'restart' else 'continue'

            row_data.append((cell, colspan, vmerge_type))
        grid_data.append(row_data)

    # Second pass: compute rowspan by tracking merge starts
    # merge_track[col] = (start_row, remaining_span)
    max_cols = max(sum(c[1] for c in row) for row in grid_data) if grid_data else 0
    merge_track = {}  # col -> (start_row_idx, span_count)

    html_rows = []
    for ri, row_data in enumerate(grid_data):
        html_cells = []
        col_offset = 0

        for ci, (cell, colspan, vmerge_type) in enumerate(row_data):
            # Skip cells that are covered by a rowspan from above
            while col_offset in merge_track:
                start_ri, span = merge_track[col_offset]
                if span <= 0:
                    del merge_track[col_offset]
                else:
                    col_offset += span
            if col_offset >= max_cols:
                break

            # Build cell content
            paras = cell.findall(qn('w:p'))
            cell_parts = []
            for p in paras:
                p_html = ''
                for child in p:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag == 'r':
                        p_html += run_to_html(child, doc, img_map, img_dir_name)
                    elif tag == 'oMath':
                        ltx = omml_to_latex(child)
                        if ltx:
                            p_html += f'\\({ltx}\\)'
                p_html = p_html.strip()
                if p_html:
                    cell_parts.append(p_html)

            cell_content = '<br>'.join(cell_parts) if cell_parts else '&nbsp;'
            attrs = []
            if colspan > 1:
                attrs.append(f'colspan="{colspan}"')

            if vmerge_type == 'restart':
                # Count how many 'continue' rows follow
                rowspan = 1
                for future_ri in range(ri + 1, len(grid_data)):
                    found_continue = False
                    future_col = 0
                    for fc in grid_data[future_ri]:
                        if future_col == col_offset:
                            if fc[2] == 'continue':
                                rowspan += 1
                                found_continue = True
                            break
                        future_col += fc[1]
                    if not found_continue:
                        break
                attrs.append(f'rowspan="{rowspan}"')
                merge_track[col_offset] = (ri, colspan)
                html_cells.append(f'<td {" ".join(attrs)}>{cell_content}</td>')
            elif vmerge_type == 'continue':
                # This cell is merged into one above — skip rendering
                pass
            else:
                html_cells.append(f'<td {" ".join(attrs)}>{cell_content}</td>')

            col_offset += colspan

        # Clean up expired merges
        expired = [c for c, (_, s) in merge_track.items() if ri >= _ + s]
        # Actually we handle this differently — merges persist until their rowspan ends

        if html_cells:
            html_rows.append('<tr>' + ''.join(html_cells) + '</tr>')

    return '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">\n' + \
           '\n'.join(html_rows) + '\n</table>\n'


# ─── Main ────────────────────────────────────────────────────────────

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
    font-family: "Microsoft YaHei", "SimSun", Arial, sans-serif;
    max-width: 900px;
    margin: 20px auto;
    padding: 0 20px;
    line-height: 1.6;
    color: #333;
}}
h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 6px; }}
h3 {{ color: #7f8c8d; }}
table {{
    border-collapse: collapse;
    margin: 12px 0;
    width: 100%;
    font-size: 14px;
}}
th, td {{
    border: 1px solid #999;
    padding: 6px 10px;
    text-align: center;
    vertical-align: middle;
}}
th {{
    background-color: #f0f0f0;
    font-weight: bold;
}}
img {{
    max-width: 100%;
    height: auto;
}}
td img {{
    max-width: 200px;
}}
.math-display {{
    text-align: center;
    margin: 10px 0;
}}
</style>
<script>
MathJax = {{
    tex: {{ inlineMath: ['\\\\(', '\\\\)'], displayMath: ['$$', '$$'] }},
    svg: {{ fontCache: 'global' }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
</head>
<body>
{body}
</body>
</html>'''


def convert(input_path, output_path=None):
    doc = Document(input_path)

    # Determine output dir
    if output_path:
        base_dir = os.path.dirname(os.path.abspath(output_path))
    else:
        base_dir = os.path.dirname(os.path.abspath(input_path))
        output_path = os.path.splitext(os.path.abspath(input_path))[0] + '.html'

    img_dir = os.path.join(base_dir, 'images')
    img_dir_name = 'images'

    img_map = extract_images(input_path, img_dir)
    if img_map:
        print(f'Extracted {len(img_map)} image(s) to {img_dir}')

    body_parts = []
    body = doc.element.body

    for elem in body:
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'p':
            result = paragraph_to_html(elem, doc, img_map, img_dir_name)
            if result:
                body_parts.append(result)
        elif tag == 'tbl':
            result = table_to_html(elem, doc, img_map, img_dir_name)
            if result:
                body_parts.append(result)

    title = os.path.splitext(os.path.basename(input_path))[0]
    html = HTML_TEMPLATE.format(title=html_escape(title), body='\n'.join(body_parts))

    with io.open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Written to {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python word2html.py input.docx [output.html]')
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
