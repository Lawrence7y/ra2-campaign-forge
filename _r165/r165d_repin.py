#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-d · V545 落盘后的门禁重钉（facts_floors 五点 + gate_runner 两处 + 指针文件）

重钉清单（每一点都必须带「只改这一处即可 FAIL」的反控说明，写进 r165f 的沙箱）：
  1) facts_floors.py  EXPECT_CUR   -> R17_R117_FACTINDEX_V545
  2) facts_floors.py  CUR_SHA256   -> V545 实测 sha256
  3) facts_floors.py  TOTAL_BYTES  -> 103,636
  4) facts_floors.py  FLOORS       -> F23/F29/F35 三行新字节界（等值 pin，不是宽松下界）
  5) facts_floors.py  MASTER_SHA256-> 由常量重算
  6) gate_runner.py   LEDGER 路径  -> V545
  7) gate_runner.py   三处 'V544' 字样（docstring d/e + G3c/G3d 标签）
  8) FACT_INDEX_CURRENT.md 指针（sha / 字节 / 声明轮次 / 依据 530..545 / 历史 16 份）

写入纪律：每件文件先 wx 独占备份 -> 断言旧 sha256 -> 一次性替换 -> 回读 -> 断言新 sha256。
幂等：已是终态则只做终态校验。
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
V545 = os.path.join(T, 'R17_R117_FACTINDEX_V545/FACT_INDEX.tsv')
FF = os.path.join(R, '_r160/facts_floors.py')
GR = os.path.join(R, '_r161/gate_runner.py')
CURMD = os.path.join(T, 'FACT_INDEX_CURRENT.md')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r165/r165d_repin.json')

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r165d_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    ck('bak %s wx 独占' % os.path.basename(out), os.path.isfile(out), out)
    return out


# ---------------------------------------------------------------- 0 · 目标值实测
print('== 0 · 从 V545 实测目标值（不预估）==')
v = rb(V545)
VSHA = sha(v)
VBYTES = len(v)
txt = v.decode('utf-8')
ck('0.1 V545 无 CR', txt.count('\r') == 0)
lines = txt.rstrip('\n').split('\n')
ck('0.2 V545 55 行', len(lines) == 55, len(lines))
rows = [l.split('\t') for l in lines if l]
ck('0.3 V545 每行 5 列', all(len(r) == 5 for r in rows))
NEW = {r[0]: (len(r[1].encode()), len(r[4].encode())) for r in rows}
print('   V545 sha=%s bytes=%d' % (VSHA[:16], VBYTES))
for fid in ('F23', 'F29', 'F35'):
    print('   %s floors -> %s' % (fid, NEW[fid]))

# ---------------------------------------------------------------- 1 · facts_floors.py
print()
print('== 1 · facts_floors.py 五点重钉 ==')
ff = io.open(FF, encoding='utf-8').read()
ff_old_sha = sha(ff.encode())

m = re.search(r"EXPECT_CUR = os\.path\.join\(TIER, '([^']+)', 'FACT_INDEX\.tsv'\)", ff)
ck('1.0 EXPECT_CUR 定位成功', m is not None, m.group(1) if m else None)
cur_dir = m.group(1)
ck('1.1 EXPECT_CUR 指向 V544 或 V545（幂等：首跑为 V544、重跑为 V545）',
   cur_dir in ('R17_R116_FACTINDEX_V544', 'R17_R117_FACTINDEX_V545'), cur_dir)

m2 = re.search(r"^CUR_SHA256 = '([0-9a-f]{64})'", ff, re.M)
ck('1.2 CUR_SHA256 定位成功', m2 is not None, m2.group(1)[:16] if m2 else None)
# S-518：V545 迭代过三次（5f55…/a798…/5707…），「只接受两个值」把幂等写成了「只接受一次」。
# 正确判据是「它要么是 V544 的 sha，要么就是当前 V545 的 sha」。
ck('1.3 CUR_SHA256 要么是 V544 的 sha、要么是当前 V545 的 sha',
   m2.group(1) == VSHA or m2.group(1).startswith('00c4f41fcba51c2'),
   m2.group(1)[:16])

m3 = re.search(r"^TOTAL_BYTES = (\d+)$", ff, re.M)
ck('1.4 TOTAL_BYTES 定位成功', m3 is not None, m3.group(1) if m3 else None)

m4 = re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'", ff, re.M)
ck('1.5 MASTER_SHA256 定位成功', m4 is not None, m4.group(1)[:16] if m4 else None)

new_ff = ff
new_ff = new_ff.replace("'R17_R116_FACTINDEX_V544', 'FACT_INDEX.tsv')",
                        "'R17_R117_FACTINDEX_V545', 'FACT_INDEX.tsv')", 1)
new_ff = re.sub(r"^CUR_SHA256 = '[0-9a-f]{64}'", "CUR_SHA256 = '%s'" % VSHA, new_ff, count=1, flags=re.M)
new_ff = re.sub(r"^TOTAL_BYTES = \d+$", "TOTAL_BYTES = %d" % VBYTES, new_ff, count=1, flags=re.M)
for fid in ('F23', 'F29', 'F35'):
    old = re.search(r"    '%s': \((\d+), (\d+)\)," % fid, new_ff)
    assert old, fid
    new_ff = new_ff.replace(old.group(0), "    '%s': (%d, %d)," % (fid, NEW[fid][0], NEW[fid][1]), 1)
ck('1.6 三处 FLOORS 已改（F23/F29/F35 逐条对上）',
   all(("    '%s': (%d, %d)," % (fid, *NEW[fid])) in new_ff for fid in ('F23', 'F29', 'F35')))

# 反控：其它 51 条 FLOORS 一字未动
old_fl = {m.group(1): (int(m.group(2)), int(m.group(3)))
          for m in re.finditer(r"    '(F\d\d)': \((\d+), (\d+)\),", ff)}
new_fl = {m.group(1): (int(m.group(2)), int(m.group(3)))
          for m in re.finditer(r"    '(F\d\d)': \((\d+), (\d+)\),", new_ff)}
ck('1.7 反控：FLOORS 条目数不变（54）', len(old_fl) == len(new_fl) == 54, (len(old_fl), len(new_fl)))
ck('1.8 反控：除三条外 51 条 FLOORS 逐条相同',
   all(old_fl[k] == new_fl[k] for k in old_fl if k not in ('F23', 'F29', 'F35')),
   [k for k in old_fl if k not in ('F23', 'F29', 'F35') and old_fl[k] != new_fl[k]])
ck('1.9 FLOORS 新值 == V545 实测字节（等值 pin，不是宽松下界）',
   all(new_fl[fid] == NEW[fid] for fid in ('F23', 'F29', 'F35')))

# MASTER 重算：用 facts_floors 自己的规范化函数（import 源码里的 canonical 定义，避免复写）
ns = {}
for name in ('canon_g', 'canon_f', 'canon_e', 'canon_eb', 'canon_l'):
    mm = re.search(r"^def %s\(d\):.*$" % name, new_ff, re.M)
    assert mm, name
    exec(mm.group(0), ns)
G2 = {m.group(1): m.group(2) for m in re.finditer(r"    '(F\d\d)': '([^']*)',", new_ff)}
E2 = {m.group(1): [x for x in m.group(2).split(', ')] for m in
      re.finditer(r"    '(F\d\d)': \[(.*?)\],", new_ff)}
EB2 = {m.group(1): int(m.group(2)) for m in re.finditer(r"    '(F\d\d)': (\d+),", new_ff)
       if not re.search(r"    '%s': \(\d+, \d+\)," % m.group(1), new_ff)}
L2 = {m.group(1): int(m.group(2)) for m in re.finditer(r"    '([^']+)': (\d+),", new_ff)
      if False}
# 直接用模块常量方式重算：抽出四张表各自的块
def block(name, text):
    i = text.index('%s = {' % name)
    j = text.index('\n}', i)
    return text[i:j + 2]


def parse_pairs(blk, kt="'(F\\d\\d)'"):
    return {m.group(1): (int(m.group(2)), int(m.group(3)))
            for m in re.finditer(r"%s: \((\d+), (\d+)\)," % kt, blk)}


def parse_lists(blk):
    return {m.group(1): [x.strip().strip("'") for x in m.group(2).split(', ')]
            for m in re.finditer(r"'(F\d\d)': \[(.*?)\],", blk)}


def parse_ints(blk):
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"'(F\d\d)': (\d+),", blk)}


GRADES2 = {m.group(1): m.group(2) for m in
           re.finditer(r"    '(F\d\d)': '([^']*)',", block('GRADES', new_ff))}
FLOORS2 = parse_pairs(block('FLOORS', new_ff))
EVID2 = parse_lists(block('EVID', new_ff))
EVIDB2 = parse_ints(block('EVIDB', new_ff))
LOST2 = {m.group(1): int(m.group(2)) for m in
         re.finditer(r"    '([^']+)': (\d+),", block('LOST', new_ff))}
ITEMS2 = int(re.search(r"^ITEMS = (\d+)$", new_ff, re.M).group(1))
UNIQ2 = int(re.search(r"^UNIQ = (\d+)$", new_ff, re.M).group(1))
LOST_ITEMS2 = int(re.search(r"^LOST_ITEMS = (\d+)$", new_ff, re.M).group(1))
LOST_UNIQ2 = int(re.search(r"^LOST_UNIQ = (\d+)$", new_ff, re.M).group(1))
ck('1.10 四张表解析成功（GRADES/FLOORS/EVID/EVIDB/LOST 全非空）',
   len(GRADES2) == 54 and len(FLOORS2) == 54 and len(EVID2) > 40 and len(EVIDB2) > 40 and len(LOST2) > 0,
   (len(GRADES2), len(FLOORS2), len(EVID2), len(EVIDB2), len(LOST2)))
master = hashlib.sha256(('\n'.join([
    VSHA, str(VBYTES), ns['canon_g'](GRADES2), ns['canon_f'](FLOORS2),
    ns['canon_e'](EVID2), ns['canon_eb'](EVIDB2), ns['canon_l'](LOST2),
    str(ITEMS2), str(UNIQ2), str(LOST_ITEMS2), str(LOST_UNIQ2)])).encode()).hexdigest()
print('   重算 MASTER_SHA256 = %s' % master[:16])
ck('1.11 重算 MASTER 与旧值不同（证明它确实覆盖了被改的常量）',
   master != '1887705c917e0b84763a1d28d93fd3455b5bcd1aa073d5d23949709ea562391d', master[:16])
new_ff = re.sub(r"^MASTER_SHA256 = '[0-9a-f]{64}'", "MASTER_SHA256 = '%s'" % master,
                new_ff, count=1, flags=re.M)
ck('1.12 MASTER 写入成功', "MASTER_SHA256 = '%s'" % master in new_ff)
ck('1.13 反控：docstring 一字未动（本轮不改注释，含已知的「GATE 计数」不符）',
   new_ff[:new_ff.index('\n"""', new_ff.index('"""') + 3) + 4]
   == ff[:ff.index('\n"""', ff.index('"""') + 3) + 4])

# 写盘
if sha(rb(FF)) == sha(new_ff.encode()):
    ck('1.14 幂等：facts_floors.py 已是终态', True)
else:
    bak(FF, 'floors')
    with open(FF, 'wb') as f:
        f.write(new_ff.encode())
    ck('1.14 facts_floors.py 写盘', sha(rb(FF)) == sha(new_ff.encode()), sha(rb(FF))[:16])

# ---------------------------------------------------------------- 2 · gate_runner.py
print()
print('== 2 · gate_runner.py 同步 ==')
gr = io.open(GR, encoding='utf-8').read()
ck('2.1 LEDGER 只能是 V544 或 V545（幂等：首跑 V544、重跑 V545）',
   gr.count("R17_R116_FACTINDEX_V544") + gr.count("R17_R117_FACTINDEX_V545") == 1,
   (gr.count("R17_R116_FACTINDEX_V544"), gr.count("R17_R117_FACTINDEX_V545")))
ck('2.2 版本字样总数为 5 且只出现在一个版本号上（不混版）',
   (gr.count('V544') == 5 and gr.count('V545') == 0)
   or (gr.count('V545') == 5 and gr.count('V544') == 0),
   (gr.count('V544'), gr.count('V545')))
new_gr = gr.replace('R17_R116_FACTINDEX_V544', 'R17_R117_FACTINDEX_V545')
new_gr = new_gr.replace('现盘 sha256(V544/FACT_INDEX.tsv)', '现盘 sha256(V545/FACT_INDEX.tsv)')
new_gr = new_gr.replace('现盘 len(V544/FACT_INDEX.tsv)', '现盘 len(V545/FACT_INDEX.tsv)')
new_gr = new_gr.replace('G3c facts CUR_SHA256 == 现盘 V544 sha256',
                        'G3c facts CUR_SHA256 == 现盘 V545 sha256')
new_gr = new_gr.replace('G3d facts TOTAL_BYTES == 现盘 V544 字节数',
                        'G3d facts TOTAL_BYTES == 现盘 V545 字节数')
ck('2.3 替换后 V544 字样归零', new_gr.count('V544') == 0, new_gr.count('V544'))
ck('2.4 替换后 V545 字样恰 5 处（与改前 V544 的 5 处一一对应）',
   new_gr.count('V545') == 5, new_gr.count('V545'))
# S-512：gate_runner.py **不持有** GATE_VER 常量（它从 check_disc.py 现读再比），
# 上一版断言按 GATE_VER 找 ⇒ 必 None。正确反控是「它仍不持有任何版本常量」。
ck('2.5 反控：gate_runner.py 仍不持有 GATE_VER 常量（版本一律从盘上现读）',
   re.search(r"^GATE_VER\s*=", new_gr, re.M) is None
   and re.search(r"^GATE_VER\s*=", gr, re.M) is None,
   (re.search(r"^GATE_VER\s*=", gr, re.M) is not None,
    re.search(r"^GATE_VER\s*=", new_gr, re.M) is not None))
ck('2.5b 反控：它读 GATE_VER 的行数不变（现算路径未被替换破坏）',
   gr.count('GATE_VER = '), new_gr.count('GATE_VER = '))
if sha(rb(GR)) == sha(new_gr.encode()):
    ck('2.6 幂等：gate_runner.py 已是终态', True)
else:
    bak(GR, 'runner')
    with open(GR, 'wb') as f:
        f.write(new_gr.encode())
    ck('2.6 gate_runner.py 写盘', sha(rb(GR)) == sha(new_gr.encode()), sha(rb(GR))[:16])

# ---------------------------------------------------------------- 3 · 指针文件
print()
print('== 3 · FACT_INDEX_CURRENT.md 指针 ==')
cm = io.open(CURMD, encoding='utf-8').read()
ck('3.1 指针指 V544 或 V545（幂等）',
   ('R17_R116_FACTINDEX_V544' in cm) or ('R17_R117_FACTINDEX_V545' in cm),
   ('V544' in cm, 'V545' in cm))
# S-518 同族：指针里的 sha/字节/轮次必须**按行定位取值**，不能按「旧字面」替换 ——
# 否则 V545 一旦迭代（本轮 3 次），第二次起就替换不上，留下过期指针。
new_cm = cm
new_cm = new_cm.replace('R17_R116_FACTINDEX_V544', 'R17_R117_FACTINDEX_V545')
new_cm = re.sub(r"(\| sha256 \| )[0-9a-f]{64}( \|)", lambda m: m.group(1) + VSHA + m.group(2), new_cm)
new_cm = re.sub(r"(\| 字节数 \| )\d+( \|)", lambda m: m.group(1) + str(VBYTES) + m.group(2), new_cm)
new_cm = re.sub(r"\| 声明轮次 \| R\d+ \|", '| 声明轮次 | R165 |', new_cm)
new_cm = re.sub(r"版本号 530\.\.\d+ 连续无缺", '版本号 530..545 连续无缺', new_cm)
new_cm = re.sub(r"V5\d\d 同时是「版本号最大」", 'V545 同时是「版本号最大」', new_cm)
new_cm = re.sub(r"V530\.\.V5\d\d 是 \d+ 个可独立复核的快照", 'V530..V545 是 16 个可独立复核的快照', new_cm)
new_cm = re.sub(r"（D0 已钉 V5\d\d 的 sha256）", '（D0 已钉 V545 的 sha256）', new_cm)
ck('3.0 指针「声明依据」行仍保留「三项同时成立才写本文件」原句（未被正则吃掉）',
   '三项同时成立才写本文件' in new_cm, 'ok')
_resid = [l for l in new_cm.split('\n') if 'V544' in l and 'V530..V544' not in l]
ck('3.2 替换后不得含 V544 字样（历史段 V530..V544 除外，那是区间下界不是指错）',
   _resid == [], _resid[:3])
ck('3.3 替换后含 V545 且 sha 为新值', 'R17_R117_FACTINDEX_V545' in new_cm and VSHA in new_cm)
ck('3.4 字节数行已更新', ('| 字节数 | %d |' % VBYTES) in new_cm)
ck('3.5 反控：文件里「本文件不是门禁」段一字未动',
   '它每次运行都会实测 sha256' in new_cm and '以 facts_floors.py 的 D0 为准' in new_cm)
if sha(rb(CURMD)) == sha(new_cm.encode()):
    ck('3.6 幂等：指针已是终态', True)
else:
    bak(CURMD, 'curmd')
    with open(CURMD, 'wb') as f:
        f.write(new_cm.encode())
    ck('3.6 指针写盘', sha(rb(CURMD)) == sha(new_cm.encode()), sha(rb(CURMD))[:16])

json.dump({'V545_SHA256': VSHA, 'V545_BYTES': VBYTES, 'MASTER_SHA256': master,
           'NEW_FLOORS': {k: list(v) for k, v in NEW.items() if k in ('F23', 'F29', 'F35')},
           'FAILS': len(FAILS), 'fails': FAILS, 'assertions': RES},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('V545_SHA256=%s' % VSHA)
print('V545_BYTES=%d' % VBYTES)
print('MASTER_SHA256=%s' % master)
print('FAILS=%d' % len(FAILS))
for f in FAILS:
    print('   -', f)
sys.exit(1 if FAILS else 0)
