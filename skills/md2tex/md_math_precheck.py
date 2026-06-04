import re,sys,argparse
from pathlib import Path

pat = re.compile(r'`([^`]+)`')
hint = re.compile(r'(\\sin|\\cos|\\tan|\\omega|\\delta|\\sum|\\int|\\infty|\\pi|\\tau|\\le|\\ge|_\{|\^\{|\(t\)|\(\\omega\)|[A-Za-z]_\d)')

def find(txt):
    out=[]
    for i,l in enumerate(txt.splitlines(),1):
        for m in pat.finditer(l):
            inner=m.group(1)
            if hint.search(inner):
                out.append((i,inner))
    return out

def fix(txt):
    def repl(m):
        s=m.group(1)
        return f'${s}$' if hint.search(s) else m.group(0)
    return pat.sub(repl,txt)

ap=argparse.ArgumentParser()
ap.add_argument('file')
ap.add_argument('--fix',action='store_true')
a=ap.parse_args()
p=Path(a.file)
text=p.read_text(encoding='utf-8')
issues=find(text)
if not issues:
    print('OK: no suspicious math backticks')
    sys.exit(0)
print(f'FOUND: {len(issues)} suspicious backtick math snippets')
for ln,s in issues[:20]:
    print(f'  line {ln}: `{s}`')
if len(issues)>20:
    print(f'  ... and {len(issues)-20} more')
if a.fix:
    p.write_text(fix(text),encoding='utf-8')
    print('AUTO-FIX APPLIED')
    sys.exit(0)
sys.exit(2)
