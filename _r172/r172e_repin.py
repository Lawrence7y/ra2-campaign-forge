# -*- coding: utf-8 -*-
"""R172 E：把 facts_floors.py 与 gate_runner.py 重钉到 V552。

facts_floors 6 处：目录号+版本号、CUR_SHA256、TOTAL_BYTES、FLOORS['F23']、MASTER。
gate_runner 5 处：仅版本样 V551->V552（不改结构、不升 GATE_VER）。

硬闸：改前用 ast 复算 MASTER 必须命中旧常量 2da2851e…（S-582 纪律：机器复算的中间产物先自证）。
"""
import ast, datetime, hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')
STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
V551 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')
V552 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_R124_FACTINDEX_V552', 'FACT_INDEX.tsv')

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

# ===== 实测 V552 =====
raw = io.open(V552, 'rb').read()
SHA = hashlib.sha256(raw).hexdigest()
BYTES = len(raw)
rows = {}
for line in io.open(V552, encoding='utf-8'):
    c = line.rstrip('\n').split('\t'); rows[c[0]] = c
f23_st = len(rows['F23'][1].encode()); f23_lim = len(rows['F23'][4].encode())
print('  V552 = %d B / sha %s ; F23 st=%d lim=%d' % (BYTES, SHA[:16], f23_st, f23_lim))

# ===== 硬闸 =====
src = io.open(FF, 'rb').read(); text = src.decode('utf-8')
C0 = consts(text)
ck('N1 改前 ast 复算 MASTER 命中旧常量 2da2851e…（硬闸）',
   master_of(C0) == C0['MASTER_SHA256'] and C0['MASTER_SHA256'].startswith('2da2851e'),
   (master_of(C0)[:16], C0['MASTER_SHA256'][:16]))
ck('N1b 改前仍指 V551', "R17_R123_FACTINDEX_V551" in text)
if FAIL:
    print('\n!! 硬闸未过 —— fail-closed，不写盘'); sys.exit(1)

EDITS = [
    ("EXPECT_CUR = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')",
     "EXPECT_CUR = os.path.join(TIER, 'R17_R124_FACTINDEX_V552', 'FACT_INDEX.tsv')"),
    ("CUR_SHA256 = '5d4981c8b40ecfb1f0a4a3717da13b10a0b173eff600a763a20daac4da12a3fc'",
     "CUR_SHA256 = '%s'" % SHA),
    ("TOTAL_BYTES = 120540", "TOTAL_BYTES = %d" % BYTES),
    ("    'F23': (1785, 7778),", "    'F23': (%d, %d)," % (f23_st, f23_lim)),
]
for o, _ in EDITS:
    ck('P1 旧串恰 1 次: %s' % o[:56].replace('\n', ' '), text.count(o) == 1, text.count(o))
new = text
for o, n in EDITS: new = new.replace(o, n, 1)

C1 = consts(new); C1['MASTER_SHA256'] = C0['MASTER_SHA256']
m_new = master_of(C1)
print('  新 MASTER = %s' % m_new)
ck('P2 新 MASTER != 旧 MASTER', m_new != C0['MASTER_SHA256'])
ck('P2b 新 CUR_SHA256 / TOTAL_BYTES 与 V552 实测一致', C1['CUR_SHA256'] == SHA and C1['TOTAL_BYTES'] == BYTES)
ck('P2c 新 FLOORS[F23] == 实测 (%d, %d)' % (f23_st, f23_lim), C1['FLOORS']['F23'] == (f23_st, f23_lim))
ck('P2d GRADES/EVID/EVIDB/LOST/ITEMS/UNIQ/LOST_ITEMS/LOST_UNIQ 逐项未变，FLOORS 只差 F23',
   all(C1[k] == C0[k] for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ'))
   and [k for k in C0['FLOORS'] if C0['FLOORS'][k] != C1['FLOORS'][k]] == ['F23'],
   [k for k in C0['FLOORS'] if C0['FLOORS'][k] != C1['FLOORS'][k]])

new = new.replace("MASTER_SHA256 = '2da2851e24a7ae2a3679ac983297d82ab5cf262ece02c6531af6fb5af9f2f782'",
                  "MASTER_SHA256 = '%s'" % m_new, 1)
ck('P2e MASTER 串写入后与 ast 复算一致', consts(new)['MASTER_SHA256'] == master_of(consts(new)))

# 备份 + 写
bok = os.path.join(BAK, 'facts_floors.py.before_r172_V552_%s.bak' % STAMP)
with io.open(bok, 'xb') as f: f.write(src)
ck('P3 备份独占创建且字节相同', os.path.isfile(bok) and io.open(bok, 'rb').read() == src)
io.open(FF, 'wb').write(new.encode('utf-8'))
ck('P3b 回读逐字节 == 待写', io.open(FF, 'rb').read() == new.encode('utf-8'))

o_l, n_l = text.split('\n'), new.split('\n')
dl = [i for i in range(min(len(o_l), len(n_l))) if o_l[i] != n_l[i]]
ck('N2 facts_floors 行数不变', len(o_l) == len(n_l))
print('  变化 %d 行: %s' % (len(dl), [(i + 1, o_l[i].strip()[:38]) for i in dl]))
ck('N2b 变化行恰 5 行', len(dl) == 5, len(dl))
ck('N2c 每行都属于预期集',
   all(any(k in o_l[i] for k in ('EXPECT_CUR', 'CUR_SHA256 =', 'TOTAL_BYTES', "'F23':", 'MASTER_SHA256')) for i in dl))

# ===== gate_runner：5 处版本样 =====
gsrc = io.open(GR, 'rb').read(); gtxt = gsrc.decode('utf-8')
ck('Q1 改前 gate_runner 含 V551 恰 5 处',
   gtxt.count('V551') + gtxt.count('R17_R123') == 5, (gtxt.count('V551'), gtxt.count('R17_R123')))
ck('Q1b 改前不含 V552', 'V552' not in gtxt and 'R17_R124' not in gtxt)
gnew = gtxt.replace('R17_R123_FACTINDEX_V551', 'R17_R124_FACTINDEX_V552')
gnew = gnew.replace('V551/FACT_INDEX.tsv', 'V552/FACT_INDEX.tsv').replace('现盘 V551 sha256', '现盘 V552 sha256').replace('现盘 V551 字节数', '现盘 V552 字节数')
ck('Q2 改后 V552 恰 5 处、V551 残留 0', gnew.count('V552') + gnew.count('R17_R124') == 5 and 'V551' not in gnew and 'R17_R123' not in gnew,
   (gnew.count('V552'), gnew.count('R17_R124'), gnew.count('V551')))
ck('Q2b GATE_VER 未升（仍 R166）', re.search(r"^GATE_VER = '([^']+)'", gnew, re.M).group(1) == 'R166')
ck('Q2c gate_runner 仍无行首 GATE_VER 之外的结构改动（行数不变）',
   len(gtxt.split('\n')) == len(gnew.split('\n')))
gbok = os.path.join(BAK, 'gate_runner.py.before_r172_V552_%s.bak' % STAMP)
with io.open(gbok, 'xb') as f: f.write(gsrc)
ck('Q3 备份独占创建', os.path.isfile(gbok) and io.open(gbok, 'rb').read() == gsrc)
io.open(GR, 'wb').write(gnew.encode('utf-8'))
ck('Q3b 回读逐字节 == 待写', io.open(GR, 'rb').read() == gnew.encode('utf-8'))

# ===== 三段实跑 =====
def run(args, timeout=900):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr

CD = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'check_disc.py')
rc1, o1 = run([CD])
ck('M1 check_disc exit 0', rc1 == 0, o1[-600:])
ck('M1b 无行首 FAIL（NOTE 里的 FAIL 字样不算）',
   not any(l.strip().startswith('FAIL') for l in o1.split('\n')),
   [l for l in o1.split('\n') if l.strip().startswith('FAIL')])
rc2, o2 = run([FF])
ck('M2 facts_floors exit 0', rc2 == 0, o2[-600:])
ck('M2b facts_floors D0 = %s / D8 %d / D9 %s' % (SHA[:8], BYTES, m_new[:8]),
   SHA[:8] in o2 and str(BYTES) in o2 and m_new[:8] in o2,
   [l for l in o2.split('\n') if l.startswith(('D0', 'D8', 'D9'))])
rc3, o3 = run([GR])
ck('M3 gate_runner exit 0 且 G1=G2=G3=ok', rc3 == 0 and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3, o3[-600:])

# ===== 反控：把 facts_floors 指回 V551 必须 FAIL =====
tmp = os.path.join(HERE, '_ff_mut.py')
mut = new.replace("'R17_R124_FACTINDEX_V552'", "'R17_R123_FACTINDEX_V551'").replace("CUR_SHA256 = '%s'" % SHA, "CUR_SHA256 = '5d4981c8b40ecfb1f0a4a3717da13b10a0b173eff600a763a20daac4da12a3fc'")
io.open(tmp, 'w', encoding='utf-8').write(mut)
rc4, o4 = run([tmp])
ck('M4 反控：显式指向 V551 必须 FAIL', rc4 == 1, (rc4, o4[-200:]))
rc5, o5 = run([tmp, '--ignore-pin'])
ck('M4b 反控配套：--ignore-pin 下 exit 0（证明 FAIL 来自 pin 断言而非结构）', rc5 == 0, o5[-200:])
os.remove(tmp)

rec = {'v552_bytes': BYTES, 'v552_sha256': SHA, 'master_sha256': m_new,
       'f23_floors': [f23_st, f23_lim], 'ff_bak': os.path.relpath(bok, ROOT),
       'gr_bak': os.path.relpath(gbok, ROOT),
       'ff_sha_after': hashlib.sha256(io.open(FF, 'rb').read()).hexdigest(),
       'gr_sha_after': hashlib.sha256(io.open(GR, 'rb').read()).hexdigest()}
io.open(os.path.join(HERE, 'r172e_repin.json'), 'w', encoding='utf-8').write(json.dumps(rec, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
