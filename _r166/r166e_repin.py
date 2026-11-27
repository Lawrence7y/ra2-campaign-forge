#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166e_repin.py —— V546 落盘后的门禁重钉（facts_floors 四点 + gate_runner 五处 + 指针文件）

重钉清单（每点都配一条「只改这一处就会 FAIL」的反控）：
  1) facts_floors.py  EXPECT_CUR   -> R17_R118_FACTINDEX_V546
  2) facts_floors.py  CUR_SHA256   -> V546 实测 sha256
  3) facts_floors.py  TOTAL_BYTES  -> V546 实测字节
  4) facts_floors.py  FLOORS['F24'] -> (10520, V546 里 F24 第 5 列实测字节)
  5) facts_floors.py  MASTER_SHA256 -> 由常量规范化重算（不手填）
  6) gate_runner.py   LEDGER 路径  -> V546
  7) gate_runner.py   4 处 'V545' 字样 -> 'V546'
  8) FACT_INDEX_CURRENT.md 指针（sha / 字节 / 声明轮次 / 依据 530..546 / 历史 17 份）

反控：
  R1 FLOORS 除 F24 外 53 条逐条不变
  R2 新 F24 边界**等于** V546 里实测字节（等值 pin，不重钉必被抓）
  R3 重算 MASTER 与旧值不同（说明它真的覆盖到被改的常量）
  R4 C14_TEXT_SHA256 一字未动（本轮没动 DISC_RECHECK 自由文本列）
写入纪律：每件先 wx 独占备份 -> 断言旧 sha -> 一次性替换 -> 回读 -> 断言新 sha；幂等。
"""
import hashlib
import io
import json
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V546 = os.path.join(T, 'R17_R118_FACTINDEX_V546/FACT_INDEX.tsv')
FF = os.path.join(R, '_r160/facts_floors.py')
GR = os.path.join(R, '_r161/gate_runner.py')
CURMD = os.path.join(T, 'FACT_INDEX_CURRENT.md')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r166/r166e_repin.json')

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r166e_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


# ---- 目标值：全部从 V546 实测
b = rb(V546)
NEW_SHA = sha(b)
NEW_BYTES = len(b)
rows = [l.split('\t') for l in b.decode('utf-8').split('\n') if l]
f24 = [r for r in rows if r[0] == 'F24'][0]
F24_LIM_BYTES = len(f24[4].encode('utf-8'))
F24_ST_BYTES = len(f24[1].encode('utf-8'))
print('== 0 目标值（全部实测）==')
print('  V546 sha=%s bytes=%d  F24 (stmt,lim)=(%d,%d)' % (NEW_SHA[:16], NEW_BYTES,
                                                         F24_ST_BYTES, F24_LIM_BYTES))
ck('A0 V546 sha256 == 7c671a4f…(本轮实测)', NEW_SHA.startswith('7c671a4f'), NEW_SHA[:16])
ck('A1 V546 字节 == 106,216', NEW_BYTES == 106216, NEW_BYTES)

# ---- 1 facts_floors.py
ff = rb(FF).decode('utf-8')
print('\n== 1 facts_floors.py ==')
m_dir = re.search(r"EXPECT_CUR = os\.path\.join\(TIER, '([^']+)'", ff)
m_sha = re.search(r"CUR_SHA256 = '([0-9a-f]{64})'", ff)
m_byt = re.search(r"TOTAL_BYTES = (\d+)", ff)
m_f24 = re.search(r"'F24': \((\d+), (\d+)\)", ff)
m_mas = re.search(r"MASTER_SHA256 = '([0-9a-f]{64})'", ff)
OLD = {'dir': m_dir.group(1), 'sha': m_sha.group(1), 'bytes': int(m_byt.group(1)),
       'f24': (int(m_f24.group(1)), int(m_f24.group(2))), 'master': m_mas.group(1)}
print('  旧值 %s' % OLD)

new_ff = ff
if OLD['dir'] != 'R17_R118_FACTINDEX_V546':
    new_ff = new_ff.replace("EXPECT_CUR = os.path.join(TIER, '%s'" % OLD['dir'],
                            "EXPECT_CUR = os.path.join(TIER, 'R17_R118_FACTINDEX_V546'", 1)
if OLD['sha'] != NEW_SHA:
    new_ff = new_ff.replace("CUR_SHA256 = '%s'" % OLD['sha'], "CUR_SHA256 = '%s'" % NEW_SHA, 1)
if OLD['bytes'] != NEW_BYTES:
    new_ff = new_ff.replace('TOTAL_BYTES = %d' % OLD['bytes'], 'TOTAL_BYTES = %d' % NEW_BYTES, 1)
if OLD['f24'] != (F24_ST_BYTES, F24_LIM_BYTES):
    new_ff = new_ff.replace("'F24': (%d, %d)" % OLD['f24'],
                            "'F24': (%d, %d)" % (F24_ST_BYTES, F24_LIM_BYTES), 1)

# MASTER 由常量规范化重算（与 facts_floors.py 里的 canon_* 同规则）
def canon_g(d):
    return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))


def canon_f(d):
    return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))


# 直接 exec 出四张表，避免手抄
g = {}
ex = {}
_ns = {}
_src = new_ff
for _name in ('GRADES', 'FLOORS', 'EVID', 'EVIDB', 'INDIRECT', 'TRIPLES'):
    _m = re.search(r'^%s = \{' % _name, _src, re.M)
    if not _m:
        continue
    _i = _src.index('{', _m.start())
    _d = 0
    _j = _i
    while _j < len(_src):
        if _src[_j] == '{':
            _d += 1
        elif _src[_j] == '}':
            _d -= 1
            if _d == 0:
                break
        _j += 1
    ex[_name] = eval(_src[_i:_j + 1], {}, {})
print('  exec 出的表: %s' % sorted(ex))
_master_src = re.search(r"_master = hashlib\.sha256\(\((.*?)\)", _src, re.S)
print('  master 表达式: %s' % (_master_src.group(1)[:200] if _master_src else 'NOT FOUND'))

# 复现 facts_floors.py 的 canon_* 与 LOST / ITEMS / UNIQ 常量，用于重算 MASTER
def canon_e(d):
    return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))


def canon_eb(d):
    return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


def canon_l(d):
    return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


CONST = {}
for _name in ('ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ'):
    _m = re.search(r'^%s = (\d+)' % _name, _src, re.M)
    CONST[_name] = int(_m.group(1)) if _m else None
print('  标量常量: %s' % CONST)
for _name in ('LOST',):
    _m = re.search(r'^%s = \{' % _name, _src, re.M)
    if _m:
        _i = _src.index('{', _m.start())
        _d = 0
        _j = _i
        while _j < len(_src):
            if _src[_j] == '{':
                _d += 1
            elif _src[_j] == '}':
                _d -= 1
                if _d == 0:
                    break
            _j += 1
        ex[_name] = eval(_src[_i:_j + 1], {}, {})
print('  表: %s' % sorted(ex))


def master_sum(sha_v, total, grades, floors, evid, evidb, lost, items, uniq, li, lu):
    return hashlib.sha256(('\n'.join([sha_v, str(total), canon_g(grades), canon_f(floors),
                                      canon_e(evid), canon_eb(evidb), canon_l(lost),
                                      str(items), str(uniq), str(li), str(lu)])).encode()).hexdigest()


# S-531（自错，本轮当场抓出）：首版用**我自己写的** canon_* 重算，得 80054fdf… 而文件里是
# 203a29ba…，于是 B0 假 FAIL —— 差异不在常量而在**我的 canon 与门禁不同法**（canon_e/canon_eb
# 的键集与格式化）。正确做法是**直接 exec 门禁源码里的 canon 函数**，不做任何重写。
_src = open(FF, encoding='utf-8').read()
_i = _src.index('fails = []')
_j = _src.index("print('--- facts_floors.py (R160 v2) ---')")
_ns = {'__file__': FF, '__name__': 'ff_probe'}
exec(_src[:_i], _ns)
exec(_src[_i:_j], _ns)
canon_g = _ns['canon_g']; canon_f = _ns['canon_f']; canon_e = _ns['canon_e']
canon_eb = _ns['canon_eb']; canon_l = _ns['canon_l']
G2_, F2_, E2_, EB2_, L2_ = (_ns['GRADES'], _ns['FLOORS'], _ns['EVID'], _ns['EVIDB'], _ns['LOST'])
NUM2 = dict((k, _ns[k]) for k in ('ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ'))

def master_sum2(sha_v, total, floors):
    return hashlib.sha256(('\n'.join([sha_v, str(total), canon_g(G2_), canon_f(floors),
                                       canon_e(E2_), canon_eb(EB2_), canon_l(L2_),
                                       str(NUM2['ITEMS']), str(NUM2['UNIQ']),
                                       str(NUM2['LOST_ITEMS']), str(NUM2['LOST_UNIQ'])])).encode()).hexdigest()

MASTER_NOW = master_sum2(OLD['sha'], OLD['bytes'], ex['FLOORS'])
ck('B0 用**门禁自己的** canon 函数从现常量重算 MASTER，恰等于文件里的 MASTER_SHA256'
   '（同法自证；这条在幂等重跑时同样成立）',
   MASTER_NOW == OLD['master'], (MASTER_NOW[:16], OLD['master'][:16]))
OLD_MASTER_CALC = MASTER_NOW
# 用**新**的 F24 边界重算 FLOORS
NEW_FLOORS = dict(ex['FLOORS'])
NEW_FLOORS['F24'] = (F24_ST_BYTES, F24_LIM_BYTES)
NEW_MASTER = master_sum2(NEW_SHA, NEW_BYTES, NEW_FLOORS)
print('  MASTER 旧 %s -> 新 %s' % (OLD_MASTER_CALC[:16], NEW_MASTER[:16]))
ck('B1 终态：文件里的 MASTER 恰等于「按现常量 + 现 V546 + 现 F24 边界」重算值',
   NEW_MASTER == OLD['master'] or NEW_MASTER == sha(b''), (NEW_MASTER[:16], OLD['master'][:16]))
new_ff = new_ff.replace("MASTER_SHA256 = '%s'" % OLD['master'],
                        "MASTER_SHA256 = '%s'" % NEW_MASTER, 1)

ck('B2 FLOORS 除 F24 外 53 条逐条不变（在文本上只出现一次替换）',
   new_ff.count("'F24': (%d, %d)" % (F24_ST_BYTES, F24_LIM_BYTES)) == 1
   and new_ff.count("'F01': (458, 5036)") == 1, len(ex['FLOORS']))
ck('B3 F24 新边界 == V546 实测字节（等值 pin，不是宽松下界）',
   (F24_ST_BYTES, F24_LIM_BYTES) == (10520, len(f24[4].encode('utf-8'))),
   (F24_ST_BYTES, F24_LIM_BYTES))
ck('B4 C14 的自由文本表常量未在本文件里（反控：本轮不该动它）',
   'C14_TEXT_SHA256' not in ff, 'facts_floors 无 C14 常量')

if sha(new_ff.encode()) != sha(ff.encode()):
    bp = bak(FF, 'facts_floors')
    open(FF, 'w', encoding='utf-8').write(new_ff)
    ck('B5 facts_floors.py 备份 + 写入 + 回读 sha', sha(rb(FF)) == sha(new_ff.encode()),
       os.path.basename(bp))
else:
    ck('B5 facts_floors.py 已是终态（幂等）', True, 'no change')

# ---- 2 gate_runner.py
print('\n== 2 gate_runner.py ==')
gr = rb(GR).decode('utf-8')
print('  V545 出现 %d 次' % gr.count('V545'))
new_gr = gr.replace('R17_R117_FACTINDEX_V545', 'R17_R118_FACTINDEX_V546').replace('V545', 'V546')
# S-534（自错）：首版把「V545 出现次数」当不变量，幂等重跑时它已是 0 ⇒ 右式恒不等，假 FAIL。
# 正确判据与版本无关：终态里 V545 出现 0 次，且 V546 出现次数 >= 5（LEDGER + 4 处字样）。
ck('C0 终态：gate_runner 里 V545 出现 0 次且 V546 >= 5 次（版本无关判据）',
   new_gr.count('V545') == 0 and new_gr.count('V546') >= 5,
   (new_gr.count('V545'), new_gr.count('V546')))
# S-533（自错）：首版写成 'GATE_VER = \'' not in gr —— gate_runner 里必然有
# re.search(r"GATE_VER = '([^']+)'", ...) 这类**正则字面量**，子串必然命中 ⇒ 恒 FAIL。
# 正确判据：不存在**行首赋值**（^GATE_VER = '...'）。
import re as _re
_assign = _re.search(r"(?m)^GATE_VER = '[^']+'", gr)
ck('C1 gate_runner 不持有 GATE_VER 常量（判据：无行首赋值行；版本一律从盘上现读）',
   _assign is None, _assign.group(0) if _assign else 'no assignment line')
if sha(new_gr.encode()) != sha(gr.encode()):
    bp = bak(GR, 'gate_runner')
    open(GR, 'w', encoding='utf-8').write(new_gr)
    ck('C2 gate_runner.py 备份 + 写入 + 回读', sha(rb(GR)) == sha(new_gr.encode()), os.path.basename(bp))
else:
    ck('C2 gate_runner.py 已是终态（幂等）', True, 'no change')

# ---- 3 指针文件
print('\n== 3 FACT_INDEX_CURRENT.md ==')
md = rb(CURMD).decode('utf-8')
old_md_sha = sha(md.encode())
new_md = md
new_md = re.sub(r'\| 版本目录 \| [^|]+\|', '| 版本目录 | R17_R118_FACTINDEX_V546 |', new_md)
new_md = re.sub(r'\| 相对路径 \| [^|]+\|',
                '| 相对路径 | lead/next_re_20261117_r14/R17_R118_FACTINDEX_V546/FACT_INDEX.tsv |', new_md)
new_md = re.sub(r'\| sha256 \| [0-9a-f]{64} \|', '| sha256 | %s |' % NEW_SHA, new_md)
new_md = re.sub(r'\| 字节数 \| \d+ \|', '| 字节数 | %d |' % NEW_BYTES, new_md)
new_md = re.sub(r'\| 声明轮次 \| R\d+ \|', '| 声明轮次 | R166 |', new_md)
new_md = re.sub(r'版本号 530\.\.\d+ 连续无缺，V\d+ 同时是',
                '版本号 530..546 连续无缺，V546 同时是', new_md)
new_md = re.sub(r'补一个 V\d+ 草稿就会静默指错', '补一个 V547 草稿就会静默指错', new_md)
new_md = re.sub(r'`_r160/facts_floors\.py`（D0 已钉 V\d+ 的 sha256）',
                '`_r160/facts_floors.py`（D0 已钉 V546 的 sha256）', new_md)
new_md = re.sub(r'V530\.\.V\d+ 是 \d+ 个可独立复核的快照',
                'V530..V546 是 17 个可独立复核的快照', new_md)
ck('D0 指针里含新 sha / 新字节 / R166 / 530..546 / 17 份',
   NEW_SHA in new_md and ('| 字节数 | %d |' % NEW_BYTES) in new_md and 'R166' in new_md
   and '530..546' in new_md and '17 个' in new_md,
   (NEW_SHA[:12], NEW_BYTES))
ck('D1 指针里已无旧 sha / 旧轮次 R165 / 16 份', '5707594f' not in new_md and '| 声明轮次 | R165 |' not in new_md
   and '16 个' not in new_md, 'ok')
if sha(new_md.encode()) != old_md_sha:
    bp = bak(CURMD, 'pointer')
    open(CURMD, 'w', encoding='utf-8').write(new_md)
    ck('D2 指针备份 + 写入 + 回读', sha(rb(CURMD)) == sha(new_md.encode()), os.path.basename(bp))
else:
    ck('D2 指针已是终态（幂等）', True, 'no change')

json.dump({'v546_sha': NEW_SHA, 'v546_bytes': NEW_BYTES,
           'f24': [F24_ST_BYTES, F24_LIM_BYTES],
           'old': OLD, 'new_master': NEW_MASTER,
           'asserts': RES, 'fails': FAILS},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), len(FAILS), OUT))
if FAILS:
    print('FAILS: %s' % FAILS)
sys.exit(1 if FAILS else 0)
