# -*- coding: utf-8 -*-
"""R171 G v2：把 facts_floors.py 重钉到 V551（5 处：目录号/版本号、CUR_SHA256、TOTAL_BYTES、FLOORS[F24]、MASTER）。

R171 自错 S-582：v1 用 `^NAME = \\{.*?^\\}` 正则抽字典，`canon_e` 里 `]`/`}` 嵌套导致截断，
复算出的 MASTER 是**假值**，而 v1 仍把它写进了文件。已从 .bak 还原（sha 38e09380 复原成功）。
v2 改法：**用 ast 从源码里取常量**，不靠正则；且 N1 反控必须先在**改前**文件上命中旧 MASTER，
不命中就不写盘（fail-closed）。
"""
import ast, hashlib, io, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE',
                   'facts_floors.py.before_r171v2_V551_%s.bak' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
pins = json.load(io.open(os.path.join(HERE, 'r171f_pins.json'), encoding='utf-8'))

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src = io.open(FF, 'rb').read()
CK_OLD = hashlib.sha256(src).hexdigest()
text = src.decode('utf-8')
print('  改前 facts_floors.py = %d B / sha %s' % (len(src), CK_OLD[:16]))
ck('P-1 起点确实是未改版本（MASTER 仍是 90ff6911…）',
   "MASTER_SHA256 = '90ff6911" in text and "R17_R122_FACTINDEX_V550" in text)

# ---- 用 ast 取常量（不用正则）----
def consts(code):
    tree = ast.parse(code)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name):
                try:
                    out[t.id] = ast.literal_eval(node.value)
                except Exception:
                    pass
    return out

C0 = consts(text)
need = ['GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS',
        'LOST_UNIQ', 'CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256']
ck('P0 ast 取到全部 12 个常量', all(k in C0 for k in need), [k for k in need if k not in C0])

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

# ---- N1 硬闸：改前文件复算必须命中旧 MASTER，否则不写盘 ----
m_old = master_of(C0)
ck('N1 改前文件 ast 复算 MASTER == 90ff6911…（算法同法，硬闸）',
   m_old == C0['MASTER_SHA256'], (m_old[:16], C0['MASTER_SHA256'][:16]))
if FAIL:
    print('\n!! N1 未过 —— fail-closed，不写盘。')
    print('=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
    sys.exit(1)

# ---- 4 个文本替换 ----
EDITS = [
    ("EXPECT_CUR = os.path.join(TIER, 'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv')",
     "EXPECT_CUR = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')"),
    ("CUR_SHA256 = 'd85034b0b2e42fd34e8140e37e1d27be22cefbc2198d455b0295ef662c58a386'",
     "CUR_SHA256 = '%s'" % pins['sha']),
    ("TOTAL_BYTES = 120495", "TOTAL_BYTES = %d" % pins['bytes']),
    ("    'F24': (10520, 31158),", "    'F24': (%d, %d)," % tuple(pins['f24_floors'])),
]
for o, n in EDITS:
    ck('P1 旧串恰 1 次: %s' % o[:50].replace('\n', ' '), text.count(o) == 1, text.count(o))
new = text
for o, n in EDITS:
    new = new.replace(o, n, 1)

# ---- 改后用 ast 复算新 MASTER ----
C1 = consts(new)
C1['MASTER_SHA256'] = C0['MASTER_SHA256']  # 尚未改，先只算数据
m_new = master_of(C1)
print('  新 MASTER = %s' % m_new)
ck('P2 新 MASTER != 旧 MASTER', m_new != C0['MASTER_SHA256'])
ck('P2b 新 CUR_SHA256/TOTAL_BYTES 与 V551 实测一致',
   C1['CUR_SHA256'] == pins['sha'] and C1['TOTAL_BYTES'] == pins['bytes'])
ck('P2c 新 FLOORS[F24] == (10565, 31158)', C1['FLOORS']['F24'] == (10565, 31158), C1['FLOORS']['F24'])
ck('P2d GRADES/EVID/EVIDB/LOST/ITEMS 等**逐项未变**（只动 1 个 floor）',
   all(C1[k] == C0[k] for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ',
                                'LOST_ITEMS', 'LOST_UNIQ')) and
   [k for k in C0['FLOORS'] if C0['FLOORS'][k] != C1['FLOORS'][k]] == ['F24'])

new = new.replace("MASTER_SHA256 = '90ff6911e98087ca422264ef72c3bd5dc65d68f60a372f49f3d5a6800dd12aa2'",
                  "MASTER_SHA256 = '%s'" % m_new, 1)
ck('P2e MASTER 串改写后与 ast 复算一致', consts(new)['MASTER_SHA256'] == master_of(consts(new)))

# ---- 备份 + 写 ----
with io.open(BAK, 'xb') as f:
    f.write(src)
ck('P3 备份独占创建（未覆盖既有）', os.path.isfile(BAK))
ck('P3b 备份字节 == 改前字节', io.open(BAK, 'rb').read() == src)
io.open(FF, 'wb').write(new.encode('utf-8'))
back = io.open(FF, 'rb').read()
ck('P3c 回读逐字节 == 待写', back == new.encode('utf-8'))

# ---- 反控：diff ----
o_l, n_l = text.split('\n'), new.split('\n')
ck('N2 行数不变', len(o_l) == len(n_l))
dl = [i for i in range(min(len(o_l), len(n_l))) if o_l[i] != n_l[i]]
print('  变化 %d 行: %s' % (len(dl), [(i, o_l[i].strip()[:40]) for i in dl]))
ck('N2b 变化行恰 5 行', len(dl) == 5, len(dl))
ck('N2c 每行都属于预期集',
   all(any(k in o_l[i] for k in ('EXPECT_CUR', 'CUR_SHA256 =', 'TOTAL_BYTES =', "'F24':", 'MASTER_SHA256'))
       for i in dl), [(i, o_l[i][:50]) for i in dl])

# ---- 实跑 ----
def run(args):
    p = subprocess.run([sys.executable, FF] + args, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout + p.stderr
rc, out = run([])
ck('N3 默认（V551）exit 0', rc == 0, out[-400:])
print('   ' + '\n   '.join([l for l in out.strip().split('\n') if l.startswith('  D')][:9]))
V550 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv')
rc2, out2 = run([V550])
ck('N4 指向 V550 必须 FAIL', rc2 == 1, out2[-300:])
rc3, out3 = run(['--ignore-pin'])
ck('N4b --ignore-pin exit 0', rc3 == 0, out3[-300:])
ck('N4c N3 输出里 D9 打印的是新 MASTER', m_new[:16] in out, out[-200:])

io.open(os.path.join(HERE, 'r171g_repin.json'), 'w', encoding='utf-8').write(json.dumps(
    {'ff_sha_before': CK_OLD, 'ff_sha_after': hashlib.sha256(back).hexdigest(),
     'bak': os.path.relpath(BAK, ROOT), 'master_new': m_new, 'changed_lines': dl}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
