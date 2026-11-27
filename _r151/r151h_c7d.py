#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R151 C7d 重钉（修正版）：按门禁自己的口径构造 rows —— 丢掉空行、丢掉第一行表头。
上一版误把表头当成数据行（32 行），导致算出的 sha 与门禁不同。本版先复现门禁的旧 sha
（de4e943b…）作为口径正控，再算新 sha。
"""
import hashlib, os, re, subprocess, sys

D = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
DR = os.path.join(D, 'DISC_RECHECK.tsv')
G = os.path.join(D, 'check_disc.py')

fail = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
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

# 口径正控：把 id 20 的 col5 临时还原成旧锚点，必须复现旧全表 sha de4e943b…
old_rows = []
for r in rows:
    r2 = list(r)
    if len(r2) == 7 and r2[0] == '20' and "GATE_VER = 'R151'" in r2[5]:
        r2[5] = r2[5].replace("GATE_VER = 'R151'", "GATE_VER = 'R150'")
    old_rows.append(r2)
old_text = digest(old_rows)
ck('口径正控：还原 id20 后复现旧钉 de4e943b…', old_text.startswith('de4e943b'), old_text[:12])
print('还原后 = %s' % old_text)

s = open(G, encoding='utf-8').read()
# ---------- 1. C7_TEXT_SHA256 ----------
m = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", s)
ck('找到 C7_TEXT_SHA256，当前应为上一版误钉 0efeb3e1…', m.group(1).startswith('0efeb3e1'), m.group(1)[:12])
s = s.replace("C7_TEXT_SHA256 = '%s'" % m.group(1), "C7_TEXT_SHA256 = '%s'" % new_text)

# ---------- 2. C7_ROW_SHA['20'] ----------
m2 = re.search(r"C7_ROW_SHA = \{.*?'20': '([0-9a-f]{64})'", s, re.S)
ck('找到 C7_ROW_SHA[20]', m2 is not None)
print('当前 row[20] = %s' % m2.group(1)[:12])
s = s.replace("'20': '%s'" % m2.group(1), "'20': '%s'" % rowsha['20'])

open(G, 'wb').write(s.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == s.encode('utf-8'))

# ---------- 3. 逐键核对 ----------
m3 = re.search(r"C7_ROW_SHA = \{(.*?)\}", open(G, encoding='utf-8').read(), re.S)
pairs = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", m3.group(1)))
ck('C7_ROW_SHA 条目 31', len(pairs) == 31, len(pairs))
bad = [k for k in rowsha if pairs.get(k) != rowsha[k]]
ck('C7_ROW_SHA 与现算逐键全等', bad == [], bad)

# ---------- 4. 跑门禁 ----------
print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=300)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 frozen|C12|C15 |C16 |PASS|FAIL|BOUNDARY|exit', ln):
        print('  ' + ln.strip())

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
