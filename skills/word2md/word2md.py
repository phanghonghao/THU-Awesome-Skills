# -*- coding: utf-8 -*-
"""Convert DOCX with Office Math (OMML) to Markdown with LaTeX.
Supports: images, tables, bold/italic, math formulas, heading styles.
"""
import sys, io, re, os, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
from docx.oxml.ns import qn

# ─── Math helpers (unchanged) ───────────────────────────────────────

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
                # avoid overwrite: if different file with same name, add counter
                base, ext = os.path.splitext(basename)
                counter = 1
                while os.path.exists(out_path):
                    with open(out_path, 'rb') as f:
                        if f.read() == data:
                            break  # same file already exists
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


# ─── Run text with formatting ───────────────────────────────────────

def get_run_text_formatted(run_elem):
    """Get text from a run, preserving bold/italic/strike/underline."""
    texts = [t.text for t in run_elem.findall(qn('w:t')) if t.text]
    text = ''.join(texts)
    if not text:
        return ''

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

    if bold and italic:
        text = f'***{text}***'
    elif bold:
        text = f'**{text}**'
    elif italic:
        text = f'*{text}*'
    if strike:
        text = f'~~{text}~~'
    if underline:
        text = f'<u>{text}</u>'
    return text


# ─── Paragraph processing (with images + formatting) ────────────────

def get_heading_prefix(para_elem):
    """Determine markdown heading prefix from paragraph style."""
    pPr = para_elem.find(qn('w:pPr'))
    if pPr is None:
        return ''
    pStyle = pPr.find(qn('w:pStyle'))
    if pStyle is None:
        return ''
    val = pStyle.get(qn('w:val'), '')
    if 'Heading1' in val or val == '1':  return '# '
    if 'Heading2' in val or val == '2':  return '## '
    if 'Heading3' in val or val == '3':  return '### '
    if 'Heading4' in val or val == '4':  return '#### '
    if 'Heading5' in val or val == '5':  return '##### '
    return ''


def process_paragraph_elem(para_elem, doc, img_map, img_dir_name):
    """Process a <w:p> element -> markdown string (with images, formatting, math)."""
    line_parts = []  # (kind, content)
    img_count = 0

    for child in para_elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'pPr':
            continue

        elif tag == 'r':
            # image?
            img_file = get_image_from_run(child, doc, img_map)
            if img_file:
                img_count += 1
                rel_path = img_dir_name + '/' + img_file
                line_parts.append(('image', f'![image{img_count}]({rel_path})'))
            # formatted text
            text = get_run_text_formatted(child)
            if text:
                line_parts.append(('text', text))

        elif tag == 'hyperlink':
            for r_elem in child.findall(qn('w:r')):
                img_file = get_image_from_run(r_elem, doc, img_map)
                if img_file:
                    img_count += 1
                    rel_path = img_dir_name + '/' + img_file
                    line_parts.append(('image', f'![image{img_count}]({rel_path})'))
                text = get_run_text_formatted(r_elem)
                if text:
                    line_parts.append(('text', text))

        elif tag == 'oMathPara':
            for om in child.findall(qn('m:oMath')):
                ltx = omml_to_latex(om)
                if ltx:
                    line_parts.append(('display', ltx))

        elif tag == 'oMath':
            ltx = omml_to_latex(child)
            if ltx:
                line_parts.append(('inline', ltx))

    if not line_parts:
        return ''

    # Pure display math paragraph
    text_parts = [c for t, c in line_parts if t == 'text']
    display_parts = [c for t, c in line_parts if t == 'display']
    all_text = ''.join(text_parts).strip()

    if not all_text and not any(t == 'inline' for t, _ in line_parts) and display_parts:
        return '\n'.join(f'$$\n{dp}\n$$' for dp in display_parts)

    # Build mixed paragraph
    result = []
    for kind, content in line_parts:
        if kind == 'image':
            result.append(content)
        elif kind == 'text':
            result.append(content)
        elif kind == 'inline':
            result.append(f'${content}$')
        elif kind == 'display':
            result.append(f'\n$$\n{content}\n$$\n')

    line = ''.join(result)
    prefix = get_heading_prefix(para_elem)
    return f'{prefix}{line}'.strip()


# ─── Table processing ────────────────────────────────────────────────

def process_table(tbl_elem, doc, img_map, img_dir_name):
    """Convert <w:tbl> -> markdown table string (with images in cells)."""
    rows = tbl_elem.findall(qn('w:tr'))
    if not rows:
        return ''

    img_counter = [0]  # mutable counter for image numbering in tables

    md_rows = []
    for row in rows:
        cells = row.findall(qn('w:tc'))
        cell_texts = []
        for cell in cells:
            paras = cell.findall(qn('w:p'))
            para_strs = []
            for p in paras:
                p_parts = []
                for child in p:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag == 'r':
                        # check for image
                        img_file = get_image_from_run(child, doc, img_map)
                        if img_file:
                            img_counter[0] += 1
                            rel_path = img_dir_name + '/' + img_file
                            p_parts.append(f'![img{img_counter[0]}]({rel_path})')
                        # text
                        text = get_run_text_formatted(child)
                        if text:
                            p_parts.append(text)
                    elif tag == 'oMath':
                        ltx = omml_to_latex(child)
                        if ltx:
                            p_parts.append(f'${ltx}$')
                para_strs.append(''.join(p_parts).strip())
            cell_texts.append('<br>'.join(s for s in para_strs if s) if para_strs else '')
        md_rows.append(cell_texts)

    if not md_rows:
        return ''

    n_cols = max(len(r) for r in md_rows)
    for r in md_rows:
        while len(r) < n_cols:
            r.append('')

    lines = []
    lines.append('| ' + ' | '.join(md_rows[0]) + ' |')
    lines.append('| ' + ' | '.join(['---'] * n_cols) + ' |')
    for r in md_rows[1:]:
        lines.append('| ' + ' | '.join(r) + ' |')
    return '\n'.join(lines)


# ─── Post-processing (unchanged) ─────────────────────────────────────

def postprocess(text):
    # 1. Remove stray $ inside display math
    text = re.sub(r'\$\$\n\$(.*?)\n\$\$',
                  lambda m: '$$\n' + m.group(1).strip() + '\n$$',
                  text, flags=re.DOTALL)
    # 2. Double-dollar inline -> single dollar
    def fix_dd(m):
        c = m.group(1)
        return '$$' + c + '$$' if '\n' in c else '$' + c + '$'
    text = re.sub(r'\$\$(.*?)\$\$', fix_dd, text, flags=re.DOTALL)
    # 3. \pid -> \pi d
    for cmd in ['pi', 'mu', 'sigma', 'tau', 'lambda', 'gamma', 'rho', 'alpha', 'omega', 'Delta']:
        text = re.sub(r'\\' + cmd + r'([a-zA-Z])', r'\\' + cmd + r' \1', text)
    # 4. ^{^\circ} -> ^\circ
    text = text.replace('^{^\\circ}', '^\\circ')
    # 5-6. Fix punctuation next to $
    text = re.sub(r'\$([^$]+?)\$。$', r'$\1$。', text)
    text = re.sub(r'\$([^$]+?)，\$', r'$\1$，', text)
    # 7. $$ inline -> $
    text = re.sub(r'\$\$([^$\n]+?)\$\$', r'$\1$', text)
    # 8. Space before inline math after CJK
    text = re.sub(r'([\u4e00-\u9fff])(\$)', r'\1 \2', text)
    # 9. Clean blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 10. Trailing whitespace
    text = '\n'.join(l.rstrip() for l in text.split('\n'))
    return text


# ─── Main conversion ─────────────────────────────────────────────────

def convert(input_path, output_path=None):
    doc = Document(input_path)

    # image output dir = same folder as output md (or input docx)
    if output_path:
        base_dir = os.path.dirname(os.path.abspath(output_path))
    else:
        base_dir = os.path.dirname(os.path.abspath(input_path))
    img_dir = os.path.join(base_dir, 'images')
    img_dir_name = 'images'

    img_map = extract_images(input_path, img_dir)
    if img_map:
        print(f'Extracted {len(img_map)} image(s) to {img_dir}')

    output = []
    body = doc.element.body

    for elem in body:
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'p':
            result = process_paragraph_elem(elem, doc, img_map, img_dir_name)
            if result:
                output.append(result)
        elif tag == 'tbl':
            result = process_table(elem, doc, img_map, img_dir_name)
            if result:
                output.append(result)
        # skip sdt, etc.

    text = '\n\n'.join(output)
    text = postprocess(text)

    if output_path:
        with io.open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Written to {output_path}')
    else:
        print(text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python word2md.py input.docx [output.md]')
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
