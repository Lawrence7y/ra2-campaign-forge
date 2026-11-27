#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 C7d 重钉：id 20 的 col5 锚点已随 GATE_VER R151->R152 变化，必须显式重钉
C7_TEXT_SHA256 与 C7_ROW_SHA['20']。先以「还原 id20 到 R151」复现旧钉 a46f9253… 作口径正控。
"""
import hashlib, os, re, subprocess, sys

D = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
DR = os.path.join(D, 'DISC_RECHECK.tsv')
G = os.path.join(D, 'check_disc.py')
fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


txt = open(DR, encoding='utf-8', newline='').read()
raw = [l for l in txt.split('\n') if l]
rows = [l.split('\t') for l in raw[1:]]
ck('门禁口径 rows = 31', len(rows) == 31, len(rows))
ck('首行 id 是数字（表头已丢弃）', rows[0][0].isdigit(), rows[0][0])


def digest(rs):
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rs if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


new_text = digest(rows)
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                               .encode('utf-8')).hexdigest() for r in rows if len(r) == 7}
print('现算 C7_TEXT_SHA256 = %s' % new_text)
print('id20 row sha        = %s' % rowsha['20'])

# 口径正控：把 id20 的 col5 还原成 R151 锚点，必须复现旧钉 a46f9253…
old_rows = []
for r in rows:
    r2 = list(r)
    if len(r2) == 7 and r2[0] == '20' and "GATE_VER = 'R152'" in r2[5]:
        r2[5] = r2[5].replace("GATE_VER = 'R152'", "GATE_VER = 'R151'")
    old_rows.append(r2)
old_text = digest(old_rows)
ck('口径正控：还原 id20 后复现旧钉 a46f9253…', old_text.startswith('a46f9253'), old_text[:12])

s = open(G, encoding='utf-8').read()
m = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", s)
ck('当前 C7_TEXT_SHA256 = a46f9253…', m.group(1).startswith('a46f9253'), m.group(1)[:12])
s = s.replace("C7_TEXT_SHA256 = '%s'" % m.group(1), "C7_TEXT_SHA256 = '%s'" % new_text)

m2 = re.search(r"C7_ROW_SHA = \{.*?'20': '([0-9a-f]{64})'", s, re.S)
ck('找到 C7_ROW_SHA[20]', m2 is not None)
print('当前 row[20] = %s' % m2.group(1)[:12])
s = s.replace("'20': '%s'" % m2.group(1), "'20': '%s'" % rowsha['20'])
open(G, 'wb').write(s.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == s.encode('utf-8'))

m3 = re.search(r"C7_ROW_SHA = \{(.*?)\}", open(G, encoding='utf-8').read(), re.S)
pairs = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", m3.group(1)))
ck('C7_ROW_SHA 条目 31', len(pairs) == 31, len(pairs))
bad = [k for k in rowsha if pairs.get(k) != rowsha[k]]
ck('C7_ROW_SHA 与现算逐键全等', bad == [], bad)

print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 frozen|C12|C15 |C16 |exit', ln):
        print('  ' + ln.strip())
print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
