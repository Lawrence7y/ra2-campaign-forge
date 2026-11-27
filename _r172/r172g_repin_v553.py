# -*- coding: utf-8 -*-
"""R172 G：把 facts_floors.py 与 gate_runner.py 从 V552 重钉到 V553（F24.statement +48 B）。

facts_floors 5 处：目录号+版本号、CUR_SHA256、TOTAL_BYTES、FLOORS['F24']、MASTER。
gate_runner 5 处：版本样 V552 -> V553。
硬闸：改前 ast 复算 MASTER 必须命中 V552 那一轮的 72cad997…，不命中不写盘。
"""
import ast, datetime, hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')
STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
V553 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_R125_FACTINDEX_V553', 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

def consts(code):
    out = {}
    for node in ast.parse(code).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try: out[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception: pass
    return out
def canon_g(d): return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d): return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d): return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def master_of(c):
    return hashlib.sha256(('\n'.join([
        c['CUR_SHA256'], str(c['TOTAL_BYTES']), canon_g(c['GRADES']), canon_f(c['FLOORS']),
        canon_e(c['EVID']), canon_eb(c['EVIDB']), canon_l(c['LOST']),
        str(c['ITEMS']), str(c['UNIQ']), str(c['LOST_ITEMS']), str(c['LOST_UNIQ'])])).encode()).hexdigest()

raw = io.open(V553, 'rb').read(); SHA = hashlib.sha256(raw).hexdigest(); BYTES = len(raw)
rows = {}
for line in io.open(V553, encoding='utf-8'):
    c = line.rstrip('\n').split('\t'); rows[c[0]] = c
f24_st = len(rows['F24'][1].encode()); f24_lim = len(rows['F24'][4].encode())
print('  V553 = %d B / sha %s ; F24 st=%d lim=%d' % (BYTES, SHA[:16], f24_st, f24_lim))

src = io.open(FF, 'rb').read(); text = src.decode('utf-8')
C0 = consts(text)
ck('N1 改前 ast 复算 MASTER 命中上一轮常量 72cad997…（硬闸，fail-closed）',
   master_of(C0) == C0['MASTER_SHA256'] and C0['MASTER_SHA256'].startswith('72cad997'),
   (master_of(C0)[:16], C0['MASTER_SHA256'][:16]))
ck('N1b 改前指向 V552 且 F24 floor 仍是 V551 时的 (10565, 31158)',
   'R17_R124_FACTINDEX_V552' in text and C0['FLOORS']['F24'] == (10565, 31158), C0['FLOORS']['F24'])
if FAIL:
    print('\n!! 硬闸未过 —— fail-closed，不写盘'); sys.exit(1)

EDITS = [
    ("EXPECT_CUR = os.path.join(TIER, 'R17_R124_FACTINDEX_V552', 'FACT_INDEX.tsv')",
     "EXPECT_CUR = os.path.join(TIER, 'R17_R125_FACTINDEX_V553', 'FACT_INDEX.tsv')"),
    ("CUR_SHA256 = '28155d363b75de4832d81ce7cf2e6a5bf432e7845aaf0815ccf32529c8361d42'",
     "CUR_SHA256 = '%s'" % SHA),
    ("TOTAL_BYTES = 120962", "TOTAL_BYTES = %d" % BYTES),
    ("    'F24': (10565, 31158),", "    'F24': (%d, %d)," % (f24_st, f24_lim)),
]
for o, _ in EDITS:
    ck('P1 旧串恰 1 次: %s' % o[:56].replace('\n', ' '), text.count(o) == 1, text.count(o))
new = text
for o, n in EDITS: new = new.replace(o, n, 1)
C1 = consts(new); C1['MASTER_SHA256'] = C0['MASTER_SHA256']
m_new = master_of(C1)
print('  新 MASTER = %s' % m_new)
ck('P2 新 MASTER != 旧 MASTER', m_new != C0['MASTER_SHA256'])
ck('P2b 新 CUR_SHA256 / TOTAL_BYTES 与 V553 实测一致', C1['CUR_SHA256'] == SHA and C1['TOTAL_BYTES'] == BYTES)
ck('P2c 新 FLOORS[F24] == 实测 (%d, %d)' % (f24_st, f24_lim), C1['FLOORS']['F24'] == (f24_st, f24_lim))
ck('P2d 其余常量逐项未变，FLOORS 只差 F24',
   all(C1[k] == C0[k] for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ'))
   and [k for k in C0['FLOORS'] if C0['FLOORS'][k] != C1['FLOORS'][k]] == ['F24'])
new = new.replace("MASTER_SHA256 = '72cad9977ff8676e8c9df5d1390abc1c0e641e16394f0eba7919429c12bedb0f'",
                  "MASTER_SHA256 = '%s'" % m_new, 1)
ck('P2e MASTER 写入后与 ast 复算一致', consts(new)['MASTER_SHA256'] == master_of(consts(new)))
bok = os.path.join(BAK, 'facts_floors.py.before_r172_V553_%s.bak' % STAMP)
with io.open(bok, 'xb') as f: f.write(src)
ck('P3 备份独占创建', os.path.isfile(bok) and io.open(bok, 'rb').read() == src)
io.open(FF, 'wb').write(new.encode('utf-8'))
ck('P3b 回读逐字节 == 待写', io.open(FF, 'rb').read() == new.encode('utf-8'))
dl = [i + 1 for i, (a, b) in enumerate(zip(text.split('\n'), new.split('\n'))) if a != b]
print('  facts_floors 变化 %d 行: %s' % (len(dl), dl))
ck('N2 变化恰 5 行且每行属预期集', len(dl) == 5 and all(
    any(k in text.split('\n')[i - 1] for k in ('EXPECT_CUR', 'CUR_SHA256 =', 'TOTAL_BYTES', "'F24':", 'MASTER_SHA256')) for i in dl), dl)

# gate_runner
gsrc = io.open(GR, 'rb').read(); gtxt = gsrc.decode('utf-8')
ck('Q1 改前 V552 恰 5 次 / V553 0 次', gtxt.count('V552') == 5 and gtxt.count('V553') == 0, (gtxt.count('V552'), gtxt.count('V553')))
g = gtxt.replace('R17_R124_FACTINDEX_V552', 'R17_R125_FACTINDEX_V553')
g = g.replace('V552/FACT_INDEX.tsv', 'V553/FACT_INDEX.tsv').replace('现盘 V552 sha256', '现盘 V553 sha256').replace('现盘 V552 字节数', '现盘 V553 字节数')
ck('Q2 改后 V553 恰 5 次 / V552 残留 0', g.count('V553') == 5 and g.count('V552') == 0, (g.count('V553'), g.count('V552')))
gdl = [i + 1 for i, (a, b) in enumerate(zip(gtxt.split('\n'), g.split('\n'))) if a != b]
ck('Q2b 变化恰 5 行', len(gdl) == 5, gdl)
ck('Q2c 仍无行首 GATE_VER 赋值（未偷偷升门）', re.search(r"^GATE_VER = '", g, re.M) is None)
gbok = os.path.join(BAK, 'gate_runner.py.before_r172_V553_%s.bak' % STAMP)
with io.open(gbok, 'xb') as f: f.write(gsrc)
ck('Q3 备份独占创建', os.path.isfile(gbok) and io.open(gbok, 'rb').read() == gsrc)
io.open(GR, 'wb').write(g.encode('utf-8'))
ck('Q3b 回读逐字节 == 待写', io.open(GR, 'rb').read() == g.encode('utf-8'))

def run(args, timeout=900):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr
CD = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'check_disc.py')
rc1, o1 = run([CD])
ck('M1 check_disc exit 0 且无行首 FAIL', rc1 == 0 and not any(l.strip().startswith('FAIL') for l in o1.split('\n')), o1[-500:])
rc2, o2 = run([FF])
ck('M2 facts_floors exit 0 / D0=%s / D8=%d / D9=%s' % (SHA[:8], BYTES, m_new[:8]),
   rc2 == 0 and SHA[:8] in o2 and str(BYTES) in o2 and m_new[:8] in o2,
   [l for l in o2.split('\n') if l.startswith(('D0', 'D8', 'D9'))])
rc3, o3 = run([GR])
ck('M3 gate_runner exit 0 / G1=G2=G3=ok / 输出指 V553',
   rc3 == 0 and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3 and 'V553' in o3, o3[-600:])
tmp = os.path.join(HERE, '_ff_mut553.py')
mut = new.replace("'R17_R125_FACTINDEX_V553'", "'R17_R124_FACTINDEX_V552'").replace("CUR_SHA256 = '%s'" % SHA,
                  "CUR_SHA256 = '28155d363b75de4832d81ce7cf2e6a5bf432e7845aaf0815ccf32529c8361d42'")
io.open(tmp, 'w', encoding='utf-8').write(mut)
rc4, o4 = run([tmp]); ck('M4 反控：指回 V552 必须 FAIL', rc4 == 1, (rc4, o4[-200:]))
io.open(tmp, 'w', encoding='utf-8').write(mut)
rc5, o5 = run([tmp, '--ignore-pin']); ck('M4b 反控配套：--ignore-pin 下 exit 0', rc5 == 0, o5[-200:])
os.remove(tmp)

io.open(os.path.join(HERE, 'r172g_repin_v553.json'), 'w', encoding='utf-8').write(json.dumps(
    {'v553_bytes': BYTES, 'v553_sha256': SHA, 'master': m_new, 'f24_floors': [f24_st, f24_lim],
     'ff_bak': os.path.relpath(bok, ROOT), 'gr_bak': os.path.relpath(gbok, ROOT)}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
