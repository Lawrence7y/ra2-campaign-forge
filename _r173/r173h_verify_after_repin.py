#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 H：**写后复验**（r173g 那一步因 S-602 方向反了的断言报了 1 FAIL，但写盘已发生）。

本脚本不写盘，只把 r173g 声称的每一项结果在现盘上重新验一遍，并给出「当时 fail-closed 是否被绕过」
的如实判定：S-602 是一条**假 FAIL**（断言写反方向），不是真缺陷；但它确实说明 r173g 的
硬闸顺序有缺陷 —— 写 gate_runner 之前没有 fail-closed。这条要如实登记。
"""
import ast, hashlib, io, json, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FL = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
NEWSHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
NEWBYTES = 123851
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

src = io.open(FL, encoding='utf-8').read()
tree = ast.parse(src)
c = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) \
       and node.targets[0].id in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES',
                                  'FLOORS', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ',
                                  'LOST_ITEMS', 'LOST_UNIQ'):
        c[node.targets[0].id] = ast.literal_eval(node.value)

ck('H1 facts_floors 的 CUR_SHA256 已是 V554 的 sha256', c['CUR_SHA256'] == NEWSHA, c['CUR_SHA256'][:16])
ck('H2 facts_floors 的 TOTAL_BYTES 已是 123,851', c['TOTAL_BYTES'] == NEWBYTES, c['TOTAL_BYTES'])
ck('H3 facts_floors 的 EXPECT_CUR 指向 V554',
   "R17_R126_FACTINDEX_V554" in src and "R17_R125_FACTINDEX_V553" not in src, True)

canon_g = lambda d: '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
canon_f = lambda d: '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
canon_e = lambda d: '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
canon_eb = lambda d: '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
canon_l = lambda d: '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
m = hashlib.sha256(('\n'.join([c['CUR_SHA256'], str(c['TOTAL_BYTES']), canon_g(c['GRADES']),
                              canon_f(c['FLOORS']), canon_e(c['EVID']), canon_eb(c['EVIDB']),
                              canon_l(c['LOST']), str(c['ITEMS']), str(c['UNIQ']),
                              str(c['LOST_ITEMS']), str(c['LOST_UNIQ'])])).encode()).hexdigest()
ck('H4 MASTER 自洽（用现盘常量复算 == 现盘常量）', m == c['MASTER_SHA256'], (m[:16], c['MASTER_SHA256'][:16]))
ck('H5 MASTER 前 16 位 == 5f3ba93cb0f091e3（r173g 报的值）', m[:16] == '5f3ba93cb0f091e3', m[:16])

gr = io.open(GR, encoding='utf-8').read()
ck('H6 gate_runner 的 LEDGER 指向 V554',
   "R17_R126_FACTINDEX_V554" in gr and "R17_R125_FACTINDEX_V553" not in gr, True)
ck('H7 gate_runner 自己仍不持有 CUR_SHA256 字面量（S-602 订正口径）',
   gr.count(NEWSHA) == 0 and gr.count('988a9567155d8dc385ccf542909eb5b7007a1c966168a9b750429d679396876c') == 0, True)
ck('H8 gate_runner 仍用正则从 facts_floors 读 CUR_SHA256/TOTAL_BYTES',
   gr.count(r"^CUR_SHA256 = '([0-9a-f]{64})'") >= 1 and gr.count(r'^TOTAL_BYTES = (\d+)$') >= 1, True)

r1 = subprocess.run([sys.executable, FL], capture_output=True, text=True, timeout=300)
ck('H9 facts_floors 实跑 exit 0', r1.returncode == 0, r1.returncode)
ck('H10 facts_floors 输出 D0 5de4084b / D8 123851 / D9 5f3ba93c',
   'D0 sha=5de4084b' in r1.stdout and 'total bytes: 123851' in r1.stdout
   and 'D9 master pin: 5f3ba93c' in r1.stdout, None)
ck('H11 facts_floors 无行首 FAIL', not any(l.strip().startswith('FAIL') for l in r1.stdout.split('\n')), None)

r2 = subprocess.run([sys.executable, GR], capture_output=True, text=True, timeout=400)
ck('H12 gate_runner 实跑 exit 0', r2.returncode == 0, r2.returncode)
ck('H13 gate_runner G1=G2=G3=ok', 'G1=ok' in r2.stdout and 'G2=ok' in r2.stdout and 'G3=ok' in r2.stdout, None)
ck('H14 gate_runner 报告里 G3c/G3d 都是 PASS（不是 None 假通过）',
   'PASS  G3c' in r2.stdout and 'PASS  G3d' in r2.stdout,
   [l for l in r2.stdout.split('\n') if 'G3c' in l or 'G3d' in l])

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n, master=m), open('/home/t628/projects/ra2-campaign-forge/_r173/r173h_verify_after_repin.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
