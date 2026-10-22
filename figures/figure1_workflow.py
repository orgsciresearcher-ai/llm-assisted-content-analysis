"""Figure 1: researcher-centered workflow and the two planned validity tests.

Draws an SVG and renders it with Chromium via Playwright (pip install playwright; playwright install chromium).
Usage: python figures/figure1_workflow.py [output.png]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('figure1_workflow.png')
W_, H_ = 1344, 960
BLUE, BLUE_F = '#C96D4B', '#F6E8E2'   # human (researcher) = terracotta
ORG, ORG_F = '#3979A8', '#E2EBF3'     # AI (LLM) = blue
GRY = '#CFCBC3'                       # data outline
SHARED = '#E9E7E2'                    # shared sphere (tests: human + LLM)
DASH = '#A8A49A'
ARR = '#A8A49A'
T1, T2 = '#1B1B1B', '#555555'

LX, LW = 42, 598          # left column
RX, RW = 760, 540         # right column
BH, GAP, TOP = 92, 46, 70

left = [
    ('Corpus', 'Documents (here: job ads)', 'data'),
    ('Codebook', 'Theory-based codes with rules sharpened by hand coding', 'res'),
    ('Prompt', 'Nine modular blocks, codebook included', 'res'),
    ('LLM coding, one document per call', 'Each segment: codes, confidence, rationale', 'llm'),
    ('Human review', 'Low-confidence segments and inductive suggestions', 'res'),
    ('Coded dataset', 'Document-level profiles for the analysis', 'data'),
]
ys = [TOP + i * (BH + GAP) for i in range(len(left))]
cy = [y + BH / 2 for y in ys]

svg = []
add = svg.append


def box(x, y, w, h, kind):
    if kind == 'res':
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{BLUE_F}" stroke="{BLUE}" stroke-width="3"/>')
    elif kind == 'llm':
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{ORG_F}" stroke="{ORG}" stroke-width="3"/>')
    elif kind == 'data':
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#FFFFFF" stroke="{GRY}" stroke-width="2.5"/>')
    else:  # planned test / output
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{SHARED}" stroke="{DASH}" '
            f'stroke-width="2.5" stroke-dasharray="9 7"/>')


def text(x, y, s, size=19, color=T2, weight=400):
    s = s.replace('&', '&amp;')
    add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{s}</text>')


def arrow(points, label=None, lx=None, ly=None):
    d = 'M ' + ' L '.join(f'{x} {y}' for x, y in points)
    add(f'<path d="{d}" fill="none" stroke="{ARR}" stroke-width="2.2" marker-end="url(#ah)"/>')
    if label:
        text(lx, ly, label, 18, T2)


# note on top
text(LX, 36, 'Workflow steps on the left. Planned validity tests and their output on the right, attached where they act.',
     18, '#6B6B6B')

# left column
for (t, s, k), y in zip(left, ys):
    box(LX, y, LW, BH, k)
    text(LX + 28, y + 38, t, 23, T1, 600)
    text(LX + 28, y + 70, s, 19)
for i in range(len(left) - 1):
    arrow([(LX + LW / 2, ys[i] + BH), (LX + LW / 2, ys[i + 1] - 3)])

# theory-label test (aligned with Prompt)
th_y, th_h = cy[2] - 70, 140
box(RX, th_y, RW, th_h, 'test')
text(RX + 26, th_y + 38, 'Theory-label test', 23, T1, 600)
text(RX + 26, th_y + 70, "A, A′: original prompt · B: de-labeled copy", 19)
text(RX + 26, th_y + 98, 'Does coding follow the text or the theory?', 19)
text(RX + 26, th_y + 126, 'A vs. A′: noise floor and run stability', 19)
arrow([(RX, cy[2]), (LX + LW + 3, cy[2])])

# confidence-calibration test (aligned with LLM coding)
ca_h = 112
ca_y = max(cy[3] - ca_h / 2, th_y + th_h + 22)
box(RX, ca_y, RW, ca_h, 'test')
text(RX + 26, ca_y + 38, 'Confidence-calibration test', 23, T1, 600)
text(RX + 26, ca_y + 70, 'Blind coding of 227 segments across confidence levels', 19)
text(RX + 26, ca_y + 98, 'Yields the review-effort curve (Figure 2)', 19)
arrow([(LX + LW, cy[3]), (RX - 3, cy[3])])

# typology (aligned with coded dataset row)
ty_h = 100
ty_y = ys[5]
box(RX, ty_y, RW, ty_h, 'test')
text(RX + 26, ty_y + 38, 'Typology of error modes', 23, T1, 600)
text(RX + 26, ty_y + 70, 'Fed by both tests and turned into a review checklist', 19)

# calibration -> human review (sets the review share)
rs_y = cy[4] - 18
arrow([(RX + 250, ca_y + ca_h), (RX + 250, rs_y), (LX + LW + 3, rs_y)])
add(f'<text x="{(LX + LW + RX + 250) / 2}" y="{rs_y - 10}" font-size="18" fill="{T2}" text-anchor="middle">sets the review share</text>')
# typology -> human review (checklist)
ck_y = cy[4] + 22
arrow([(RX, ty_y + ty_h / 2), (700, ty_y + ty_h / 2), (700, ck_y), (LX + LW + 3, ck_y)])
# tests -> typology
arrow([(RX + 440, ca_y + ca_h), (RX + 440, ty_y - 3)])
arrow([(RX + RW, th_y + th_h / 2), (RX + RW + 24, th_y + th_h / 2), (RX + RW + 24, ty_y + ty_h / 2),
       (RX + RW + 3, ty_y + ty_h / 2)])

# legend
ly = ys[5] + BH + 58
items = [('res', 'Researcher step'), ('llm', 'LLM step'), ('data', 'Data'), ('test', 'Planned validity test or its output')]
x = LX
for k, lab in items:
    if k == 'res':
        add(f'<rect x="{x}" y="{ly-20}" width="26" height="26" rx="6" fill="{BLUE_F}" stroke="{BLUE}" stroke-width="2.5"/>')
    elif k == 'llm':
        add(f'<rect x="{x}" y="{ly-20}" width="26" height="26" rx="6" fill="{ORG_F}" stroke="{ORG}" stroke-width="2.5"/>')
    elif k == 'data':
        add(f'<rect x="{x}" y="{ly-20}" width="26" height="26" rx="6" fill="#fff" stroke="{GRY}" stroke-width="2"/>')
    else:
        add(f'<rect x="{x}" y="{ly-20}" width="26" height="26" rx="6" fill="{SHARED}" stroke="{DASH}" stroke-width="2" '
            f'stroke-dasharray="5 4"/>')
    text(x + 40, ly, lab, 19, T1)
    x += 40 + len(lab) * 10.2 + 46

H = ly + 30
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#fff}} svg{{display:block;font-family:Inter,"DejaVu Sans",sans-serif}}
</style></head><body>
<svg id="fig" xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H}" viewBox="0 0 {W_} {H}">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0 0 L10 5 L0 10 z" fill="{ARR}"/></marker></defs>
<rect width="100%" height="100%" fill="#fff"/>
{''.join(svg)}
</svg></body></html>'''
OUT.with_suffix('.html').write_text(html, encoding='utf-8')
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(device_scale_factor=2, viewport={'width': W_, 'height': int(H)})
    pg.set_content(html)
    pg.locator('#fig').screenshot(path=str(OUT))
    b.close()
print(OUT, W_, H)
