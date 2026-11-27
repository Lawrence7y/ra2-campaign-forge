# -*- coding: utf-8 -*-
"""R172 E2：gate_runner.py V551 -> V552（5 处版本样），单独一段（E1 因断言口径错在写盘前中止，gate_runner 未改）。

R172 自错 S-588：E1 的 Q1 写「含 V551 恰 5 处」却把 V551 与 R17_R123 两串相加得 6；
R172 自错 S-589：E1 的 Q2b 用 ^GATE_VER 正则，而 gate_runner **本来就没有行首 GATE_VER 赋值**
（R170 PA7 已记「仍不持有 GATE_VER」）⇒ .group(1) 抛 AttributeError。两处都是「断言里写了本该被测量的量」。
"""
import datetime, hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE',
                   'gate_runner.py.before_r172v2_V552_%s.bak' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src = io.open(GR, 'rb').read(); text = src.decode('utf-8')
print('  改前 gate_runner.py = %d B / sha %s' % (len(src), hashlib.sha256(src).hexdigest()[:16]))

# ---- 改前基线（先测再断言；两条串分开计数，不相加）----
n_v = text.count('V551'); n_d = text.count('R17_R123')
n_v552 = text.count('V552'); n_d124 = text.count('R17_R124')
print('  基线：V551=%d  R17_R123=%d  V552=%d  R17_R124=%d' % (n_v, n_d, n_v552, n_d124))
ck('Q1 改前 V551 出现 5 次（与 R170 PA7 记的 5 处一致）', n_v == 5, n_v)
ck('Q1b 改前 R17_R123 出现 1 次（与 V551 同在一行，不可相加）', n_d == 1, n_d)
ck('Q1c 改前无 V552 / R17_R124', n_v552 == 0 and n_d124 == 0, (n_v552, n_d124))
ck('Q1d gate_runner 本来就没有行首 GATE_VER 赋值（反控：不得用 ^GATE_VER 做断言，S-589）',
   re.search(r"^GATE_VER = '", text, re.M) is None)

# ---- 只换版本样 ----
g = text.replace('R17_R123_FACTINDEX_V551', 'R17_R124_FACTINDEX_V552')
g = g.replace('V551/FACT_INDEX.tsv', 'V552/FACT_INDEX.tsv') \
        .replace('现盘 V551 sha256', '现盘 V552 sha256') \
        .replace('现盘 V551 字节数', '现盘 V552 字节数')
ck('Q2 改后 V552 恰 5 次、V551 残留 0', g.count('V552') == 5 and g.count('V551') == 0, (g.count('V552'), g.count('V551')))
ck('Q2b 改后 R17_R124 恰 1 次、R17_R123 残留 0', g.count('R17_R124') == 1 and g.count('R17_R123') == 0)
ck('Q2c 行数不变（只改字符不改结构）', len(text.split('\n')) == len(g.split('\n')))
ck('Q2d 仍无行首 GATE_VER 赋值（未偷偷升门）', re.search(r"^GATE_VER = '", g, re.M) is None)
dl = [i + 1 for i, (a, b) in enumerate(zip(text.split('\n'), g.split('\n'))) if a != b]
print('  变化 %d 行: %s' % (len(dl), dl))
ck('Q2e 变化恰 5 行', len(dl) == 5, len(dl))

with io.open(BAK, 'xb') as f: f.write(src)
ck('Q3 备份独占创建且字节相同', os.path.isfile(BAK) and io.open(BAK, 'rb').read() == src)
io.open(GR, 'wb').write(g.encode('utf-8'))
ck('Q3b 回读逐字节 == 待写', io.open(GR, 'rb').read() == g.encode('utf-8'))

# ---- 三段实跑（当场）----
def run(args, timeout=900):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr

CD = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'check_disc.py')
rc1, o1 = run([CD])
ck('M1 check_disc exit 0', rc1 == 0, o1[-600:])
ck('M1b 无行首 FAIL（NOTE 里含 FAIL 字样不算）',
   not any(l.strip().startswith('FAIL') for l in o1.split('\n')),
   [l for l in o1.split('\n') if l.strip().startswith('FAIL')])
rc2, o2 = run([FF])
ck('M2 facts_floors exit 0', rc2 == 0, o2[-600:])
ck('M2b D0=28155d36 / D8=120962 / D9=72cad997',
   '28155d36' in o2 and '120962' in o2 and '72cad997' in o2,
   [l for l in o2.split('\n') if l.startswith(('D0', 'D8', 'D9'))])
rc3, o3 = run([GR])
ck('M3 gate_runner exit 0 且 G1=G2=G3=ok', rc3 == 0 and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3, o3[-800:])
ck('M3b gate_runner 输出的 G3c/G3d 指 V552', 'V552' in o3, o3[-800:])

io.open(os.path.join(HERE, 'r172e2_gr.json'), 'w', encoding='utf-8').write(json.dumps(
    {'gr_sha_before': hashlib.sha256(src).hexdigest(),
     'gr_sha_after': hashlib.sha256(io.open(GR, 'rb').read()).hexdigest(),
     'bak': os.path.relpath(BAK, ROOT), 'changed_lines': dl}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
