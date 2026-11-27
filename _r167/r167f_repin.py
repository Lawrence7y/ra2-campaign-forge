#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167f_repin.py —— V547 落盘后的门禁重钉（幂等版）

重钉点：
  1) facts_floors.py EXPECT_CUR -> R17_R119_FACTINDEX_V547
  2) facts_floors.py CUR_SHA256 -> V547 实测 sha256
  3) facts_floors.py TOTAL_BYTES -> V547 实测字节
  4) facts_floors.py FLOORS['F24'] -> (F24 stmt 字节, F24 limitations 字节) 实测
  5) facts_floors.py MASTER_SHA256 -> 用门禁自己的五个 canon 函数 + 11 项拼接顺序重算
  6) gate_runner.py LEDGER 路径 + 5 处 V546 -> V547（该文件不持有 GATE_VER 赋值，反控）
  7) FACT_INDEX_CURRENT.md 指针（sha / 字节 / 声明轮次 / 依据 530..547 / 历史 18 份）

每点配反控；幂等：若目标文件**已是**终态则跳过写入但仍做全部终态断言。
反控清单：
  R1 旧值同法自证：用 AST 取到的真实常量重算 MASTER 必须命中**落盘时**的 MASTER（同法自证）
  R2 FLOORS 除 F24 外 53 条逐条不变
  R3 新 F24 下界 == V547 实测（等值 pin）
  R4 改写后三件都必须能 compile，且编译出的常量读回 == 目标值
  R5 gate_runner 仍无行首 GATE_VER 赋值
  R6 V547 剥掉 R167 补段后与 V546 逐字节相同
自错记录（本轮，全由断言当场抓出）：
  S-538 MASTER canon 首版漏 ITEMS/UNIQ/LOST_ITEMS/LOST_UNIQ 四个整数
  S-539 GATE_VER 反控首版写成「全文不含该名」（该文件有 9 处引用，本就没赋值）
  S-540 指针文件首版漏第 30 行那处 V546
  S-541 首版用正则 grab() 抓 dict，抓出的 5 个 dict 与真实值不等 ⇒ 改 ast.literal_eval
  S-542 FLOORS 替换串自带尾逗号导致双逗号，门禁 SyntaxError ⇒ 加 compile 断言
  S-543 首版无幂等：脚本二次运行后 B1/B3/B6 全 FAIL ⇒ 改成「已是终态则跳过」
"""
import ast, hashlib, io, json, os, re, sys, time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V546 = os.path.join(T, 'R17_R118_FACTINDEX_V546/FACT_INDEX.tsv')
V547 = os.path.join(T, 'R17_R119_FACTINDEX_V547/FACT_INDEX.tsv')
FF = os.path.join(R, '_r160/facts_floors.py')
GR = os.path.join(R, '_r161/gate_runner.py')
CURMD = os.path.join(T, 'FACT_INDEX_CURRENT.md')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r167/r167f_repin.json')

FAILS, RES = [], []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok: FAILS.append(n)

def rb(p):
    with open(p, 'rb') as f: return f.read()
def sha(b): return hashlib.sha256(b).hexdigest()
def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r167f_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(path))
    return out
def consts(text):
    out = {}
    for n in ast.parse(text).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try: out[n.targets[0].id] = ast.literal_eval(n.value)
            except Exception: pass
    return out

# ---------------------------------------------------------------- 0 目标值（全部实测）
b547 = rb(V547)
NEW_SHA, NEW_BYTES = sha(b547), len(b547)
rows = [l.split('\t') for l in b547.decode('utf-8').split('\n') if l]
f24 = [r for r in rows if r[0] == 'F24'][0]
F24_ST, F24_LIM = len(f24[1].encode('utf-8')), len(f24[4].encode('utf-8'))
print('== 0 目标值（实测）==')
print('  V547 sha=%s bytes=%d  F24 (stmt,lim)=(%d,%d)' % (NEW_SHA[:16], NEW_BYTES, F24_ST, F24_LIM))
ck('A0 V547 sha256 前 8 位 == 919263cf', NEW_SHA.startswith('919263cf'), NEW_SHA[:16])
ck('A1 V547 字节 == 109,220', NEW_BYTES == 109220, NEW_BYTES)

# R6：V547 剥掉 R167 补段后与 V546 逐字节相同
b546 = rb(V546)
ck('A2 V546 一字未改（sha 7c671a4f… / 106,216 B）',
   sha(b546).startswith('7c671a4f') and len(b546) == 106216, (sha(b546)[:16], len(b546)))
t546, t547 = b546.decode('utf-8'), b547.decode('utf-8')
i0 = t547.index('**【R167 补·那 65 条的语义已定')
i1 = t547.index('不进入本条任何既有计数。', i0) + len('不进入本条任何既有计数。')
APPX = t547[i0:i1]
ck('A3 R6：剥掉 R167 补段后 V547 == V546 逐字节', t547.replace(APPX, '') == t546,
   (len(t547.replace(APPX, '')), len(t546)))

# ---------------------------------------------------------------- 1 facts_floors.py
ff = rb(FF).decode('utf-8')
CF = consts(ff)
print('\n== 1 facts_floors.py ==')
def canon_g(d):  return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d):  return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d):  return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d):  return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def master(cur_sha, total, C):
    return sha(('\n'.join([cur_sha, str(total), canon_g(C['GRADES']), canon_f(C['FLOORS']),
                           canon_e(C['EVID']), canon_eb(C['EVIDB']), canon_l(C['LOST']),
                           str(C['ITEMS']), str(C['UNIQ']), str(C['LOST_ITEMS']),
                           str(C['LOST_UNIQ'])])).encode())

# R1 同法自证：用当前文件的真实常量重算，必须命中当前文件的 MASTER（不管它是 V546 还是 V547 态）
self_master = master(CF['CUR_SHA256'], CF['TOTAL_BYTES'], CF)
ck('B1 R1 同法自证：当前常量重算 MASTER 命中当前 pin', self_master == CF['MASTER_SHA256'],
   (self_master[:16], CF['MASTER_SHA256'][:16]))
CF2 = {k: (dict(v) if isinstance(v, dict) else v) for k, v in CF.items()}
CF2['FLOORS'] = dict(CF['FLOORS']); CF2['FLOORS']['F24'] = (F24_ST, F24_LIM)
new_master = master(NEW_SHA, NEW_BYTES, CF2)
print('  当前态: dir=%s sha=%s bytes=%d F24=%s master=%s'
      % (re.search(r"TIER, '([^']+)'", ff).group(1), CF['CUR_SHA256'][:8], CF['TOTAL_BYTES'],
         CF['FLOORS']['F24'], CF['MASTER_SHA256'][:16]))
print('  目标新 MASTER %s' % new_master[:16])

ALREADY = (CF['CUR_SHA256'] == NEW_SHA and CF['TOTAL_BYTES'] == NEW_BYTES
           and CF['FLOORS']['F24'] == (F24_ST, F24_LIM) and CF['MASTER_SHA256'] == new_master
           and 'R17_R119_FACTINDEX_V547' in ff)
if ALREADY:
    print('  [幂等] facts_floors.py 已是 V547 终态，跳过替换断言')
    ck('B2 已是终态时 5 个常量读回全等于目标（不靠替换）',
       (CF['CUR_SHA256'], CF['TOTAL_BYTES'], CF['FLOORS']['F24'], CF['MASTER_SHA256'])
       == (NEW_SHA, NEW_BYTES, (F24_ST, F24_LIM), new_master))
else:
    m_dir = re.search(r"(EXPECT_CUR = os\.path\.join\(TIER, ')([^']+)(')", ff)
    m_sha = re.search(r"CUR_SHA256 = '([0-9a-f]{64})'", ff)
    m_byt = re.search(r"TOTAL_BYTES = (\d+)", ff)
    m_f24 = re.search(r"'F24': \((\d+), (\d+)\)", ff)
    m_mas = re.search(r"MASTER_SHA256 = '([0-9a-f]{64})'", ff)
    ck('B0 五个锚点都在盘上', all([m_dir, m_sha, m_byt, m_f24, m_mas]))
    subs = [(m_dir.group(0), m_dir.group(1) + 'R17_R119_FACTINDEX_V547' + m_dir.group(3)),
            (m_sha.group(0), "CUR_SHA256 = '%s'" % NEW_SHA),
            (m_byt.group(0), "TOTAL_BYTES = %d" % NEW_BYTES),
            (m_f24.group(0), "'F24': (%d, %d)" % (F24_ST, F24_LIM)),
            (m_mas.group(0), "MASTER_SHA256 = '%s'" % new_master)]
    new_ff = ff
    for o, n in subs:
        if o not in new_ff:
            ck('B0 替换锚点存在: ' + o[:44], False); continue
        new_ff = new_ff.replace(o, n, 1)
    ck('B2 五处替换全部生效（新 sha 恰 1 次 / 无 V546 残留）',
       new_ff.count(NEW_SHA) == 1 and 'R17_R118_FACTINDEX_V546' not in new_ff,
       (new_ff.count(NEW_SHA), new_ff.count('V546')))
    ff = new_ff

# R2 / R3
ck('B3 R2 FLOORS 除 F24 外 53 条逐条不变',
   all(CF2['FLOORS'][k] == CF['FLOORS'][k] for k in CF['FLOORS'] if k != 'F24'),
   len([k for k in CF['FLOORS'] if k != 'F24']))
ck('B4 R3 新 F24 下界 == V547 实测（等值 pin）', CF2['FLOORS']['F24'] == (F24_ST, F24_LIM),
   CF2['FLOORS']['F24'])

# R4 编译 + 读回
try:
    compile(ff, FF, 'exec')
    ck('B5 R4 改写后 facts_floors.py 能编译', True)
    CX = consts(ff)
    ck('B6 R4 编译读回 CUR_SHA256/TOTAL_BYTES/FLOORS[F24]/MASTER 全等目标',
       (CX['CUR_SHA256'], CX['TOTAL_BYTES'], CX['FLOORS']['F24'], CX['MASTER_SHA256'])
       == (NEW_SHA, NEW_BYTES, (F24_ST, F24_LIM), new_master),
       (CX['CUR_SHA256'][:8], CX['TOTAL_BYTES'], CX['FLOORS']['F24'], CX['MASTER_SHA256'][:16]))
    ck('B7 改写后 EXPECT_CUR 指向 V547', 'R17_R119_FACTINDEX_V547' in ff)
    ck('B8 改写后 GRADES 54 条逐条不变（本轮不动 grade）',
       CX['GRADES'] == CF['GRADES'], len(CX['GRADES']))
except SyntaxError as e:
    ck('B5 R4 改写后 facts_floors.py 能编译', False, str(e))

# ---------------------------------------------------------------- 2 gate_runner.py
gr = rb(GR).decode('utf-8')
print('\n== 2 gate_runner.py ==')
n546 = gr.count('V546')
if 'R17_R119_FACTINDEX_V547' in gr and n546 == 0:
    print('  [幂等] 已是 V547 终态')
    ck('C0 已是终态时 V547 恰 5 处', gr.count('V547') == 5, gr.count('V547'))
else:
    ck('C0 改前 V546 共 5 处', n546 == 5, n546)
    gr = gr.replace('R17_R118_FACTINDEX_V546', 'R17_R119_FACTINDEX_V547').replace('V546', 'V547')
    ck('C1 改后 V547 共 5 处', gr.count('V547') == 5, gr.count('V547'))
ck('C2 R5 gate_runner 仍无行首 GATE_VER 赋值（反控）', re.search(r"^GATE_VER = '", gr, re.M) is None,
   len(re.findall('GATE_VER', gr)))
try:
    compile(gr, GR, 'exec'); ck('C3 R4 改写后 gate_runner.py 能编译', True)
except SyntaxError as e:
    ck('C3 R4 改写后 gate_runner.py 能编译', False, str(e))

# ---------------------------------------------------------------- 3 指针文件
md = rb(CURMD).decode('utf-8')
print('\n== 3 FACT_INDEX_CURRENT.md ==')
old_sha = '7c671a4f10a1f131eddc3652d5e6baba153a593d217dddb24841fe9f5393bf6a'
if NEW_SHA in md and NEW_BYTES and str(NEW_BYTES) in md and 'R17_R119_FACTINDEX_V547' in md:
    print('  [幂等] 已是 V547 终态')
else:
    ck('D0 改前指针指 V546 且 sha 是旧值', 'R17_R118_FACTINDEX_V546' in md and old_sha in md)
    md = md.replace('R17_R118_FACTINDEX_V546', 'R17_R119_FACTINDEX_V547')
    md = md.replace(old_sha, NEW_SHA).replace('106216', str(NEW_BYTES))
    md = md.replace('| 声明轮次 | R166 |', '| 声明轮次 | R167 |')
    md = md.replace('版本号 530..546 连续无缺，V546 同时是「版本号最大」且「其目录序号 R116 为最大」，且 R116 下只有这一个 FACT_INDEX 目录',
                    '版本号 530..547 连续无缺，V547 同时是「版本号最大」且「其目录序号 R119 为最大」，且 R119 下只有这一个 FACT_INDEX 目录')
    md = md.replace('V530..V546 是 17 个可独立复核的快照', 'V530..V547 是 18 个可独立复核的快照')
    md = md.replace('D0 已钉 V546 的 sha256', 'D0 已钉 V547 的 sha256')
ck('D1 指针五要素全对（dir/sha/bytes/R167/530..547）',
   all(['R17_R119_FACTINDEX_V547' in md, NEW_SHA in md, str(NEW_BYTES) in md,
        '| 声明轮次 | R167 |' in md, '530..547' in md, '18 个可独立复核' in md]))
ck('D2 指针里 V546 字样清零', 'V546' not in md, md.count('V546'))

# ---------------------------------------------------------------- 4 落盘
print('\n== 4 落盘（wx 备份 -> 写 -> 回读）==')
def apply(path, new_text, tag):
    old = rb(path); new_b = new_text.encode('utf-8')
    if old == new_b:
        ck('%s 幂等：已是终态' % tag, True); return
    b = bak(path, tag)
    ck('%s 备份 wx 创建且逐字节等于旧件' % tag, rb(b) == old, os.path.basename(b))
    with open(path, 'wb') as f: f.write(new_b)
    ck('%s 回读 sha 与内存一致' % tag, sha(rb(path)) == sha(new_b), sha(new_b)[:16])

apply(FF, ff, 'FF')
apply(GR, gr, 'GR')
apply(CURMD, md, 'CURMD')

obj = {'v547_sha': NEW_SHA, 'v547_bytes': NEW_BYTES, 'f24': [F24_ST, F24_LIM],
       'new_master': new_master, 'self_master_when_started': self_master,
       'started_already_terminal': ALREADY, 'asserts': RES, 'fails': FAILS}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1))
print('\n断言 %d 条，FAIL %d' % (len(RES), len(FAILS)))
if FAILS: print('FAILS', FAILS)
sys.exit(1 if FAILS else 0)
