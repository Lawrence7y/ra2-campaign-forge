"""Diff REPORT.md's per-row anchor table against my measurements."""
import re, io, json

rep = io.open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B2\REPORT.md", encoding='utf-8').read()
rows = json.load(open('rows_all.json'))
r4 = json.load(open('ring4b.json'))

tbl = {}
for line in rep.splitlines():
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cells) == 5 and re.fullmatch(r'\d+', cells[0]) and re.fullmatch(r'[0-9A-F]{8}', cells[1]):
        tbl[cells[1]] = cells[2:5]

print('report table rows parsed:', len(tbl))
for e, parts in tbl.items():
    ring2, ring3, ring4 = parts[0], parts[1], parts[2]
    a = re.findall(r'[0-9A-F]{8}', ring2)
    b = re.findall(r'[0-9A-F]{8}', ring3)
    c = re.findall(r'[0-9A-F]{8}', ring4)
    mine2 = [rows[e]['slots'][0]['slot'], rows[e]['slots'][0]['vt'], rows[e]['slots'][0]['col'], rows[e]['slots'][0]['td']]
    mine3 = [d for d in [rows[e]['disp'][0][0], rows[e]['obj_ctor'], rows[e]['obj_main']['vt'], rows[e]['disp'][1][0]]]
    mine4 = [r4[e]['new'], r4[e]['ctor_site'], r4[e]['reg_site'], r4[e]['clsid']]
    ok = (a == mine2 and b == mine3 and c == mine4)
    print('%s %s' % (e, 'MATCH' if ok else 'DIFF'))
    if not ok:
        print('   report 2:', a, '\n   mine   2:', mine2)
        print('   report 3:', b, '\n   mine   3:', mine3)
        print('   report 4:', c, '\n   mine   4:', mine4)
