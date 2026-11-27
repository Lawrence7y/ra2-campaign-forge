#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-M · 门禁重钉 V555 -> V556 + 指针同步（全部断言在写盘之前，S-619 教训）

必改：facts_floors 五点（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / FLOORS[F35] / MASTER_SHA256）
      gate_runner 一处（LEDGER 目录号）
      FACT_INDEX_CURRENT.md 指针（V555 -> V556）

结构纪律（这是本轮最重要的整改）：本脚本只做「读 → 全部断言 → 最后统一写盘 → 写后回读」，
任何一条断言不过就直接 sys.exit(1)，**一处都不写**。

判据：
  P1  旧常量 ast 复算旧 MASTER 命中旧 pin（硬闸）
  P2  新 F35 两列字节不小于旧 floor；F24 两列字节也不小于旧 floor
  P3  新 MASTER 由新常量算出、且 != 旧 MASTER
  P4  GRADES/EVID/EVIDB/LOST/ITEMS/UNIQ 六容器逐项未变；FLOORS 只有 F35 一键变化
  P5  六个替换串各恰 1 次；facts_floors 变化行恰 6 行且全落在预期常量
  P6  gate_runner 一个替换串恰 1 次、变化行恰 1 行、不持有任何 sha 字面量
  P7  指针 8 个替换串各恰 1 次、新文本无 V555 字样
写后：
  Q1  三段实跑全 ok；Q2 指定 V555 路径必须 FAIL；Q3 母本 V555/V556 磁盘态未变
"""
import ast
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
BAKD = os.path.join(TIER, 'R17_LEAD_BASELINE')
V555 = os.path.join(TIER, 'R17_R127_FACTINDEX_V555/FACT_INDEX.tsv')
V556 = os.path.join(TIER, 'R17_R128_FACTINDEX_V556/FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r174/r174m_repin_v556.json')

OLD_SHA = '5396d2df9f032e1cc6febdd340dd51591c4a52a961591a2babde52ef25f3496c'
OLD_BYTES = 124834
NEW_SHA = 'eac22c67683179436d47db864600dd2e9fa69a59105644ec05f1976fb595886f'
NEW_BYTES = 125538
NEW_DIR = 'R17_R128_FACTINDEX_V556'

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def consts(path):
    tree = ast.parse(io.open(path, encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                out[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    return out


def canon_g(d):   return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d):   return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d):   return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d):  return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d):   return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


def master(c):
    return hashlib.sha256(('\n'.join([
        c['CUR_SHA256'], str(c['TOTAL_BYTES']), canon_g(c['GRADES']), canon_f(c['FLOORS']),
        canon_e(c['EVID']), canon_eb(c['EVIDB']), canon_l(c['LOST']),
        str(c['ITEMS']), str(c['UNIQ']), str(c['LOST_ITEMS']), str(c['LOST_UNIQ'])])).encode()).hexdigest()


print('== 0 · 基线 ==')
ff_raw = io.open(FF, 'rb').read()
gr_raw = io.open(GR, 'rb').read()
pt_raw = io.open(PTR, 'rb').read()
for pth, nm in ((V555, 'V555'), (V556, 'V556')):
    b = io.open(pth, 'rb').read()
    print('%s bytes=%d sha=%s' % (nm, len(b), hashlib.sha256(b).hexdigest()[:16]))
ck('0a V555 sha == 当前 pin', hashlib.sha256(io.open(V555, 'rb').read()).hexdigest() == OLD_SHA)
ck('0b V556 sha == 新实测', hashlib.sha256(io.open(V556, 'rb').read()).hexdigest() == NEW_SHA)
ck('0c V556 字节 == 125,538', os.path.getsize(V556) == NEW_BYTES, os.path.getsize(V556))

print('== P1 · 硬闸 ==')
c0 = consts(FF)
m0 = master(c0)
ck('P1a 复算旧 MASTER 命中旧 pin', m0 == c0['MASTER_SHA256'], (m0[:16], c0['MASTER_SHA256'][:16]))
ck('P1b 旧 CUR_SHA256 == V555 sha', c0['CUR_SHA256'] == OLD_SHA, c0['CUR_SHA256'][:16])
if fails:
    print('★ fail-closed（硬闸未过）')
    sys.exit(1)

print('== P2 · 新字节与 floor ==')
v556_raw = io.open(V556, 'rb').read()
cur = {l.split('\t')[0]: l.split('\t') for l in v556_raw.decode('utf-8').rstrip('\n').split('\n')[1:]}
f35 = (len(cur['F35'][1].encode()), len(cur['F35'][4].encode()))
f24 = (len(cur['F24'][1].encode()), len(cur['F24'][4].encode()))
print('F35 新字节对 %s（旧 floor %s）; F24 %s（旧 floor %s）' %
      (f35, c0['FLOORS']['F35'], f24, c0['FLOORS']['F24']))
ck('P2a F35 两列不小于旧 floor', f35[0] >= c0['FLOORS']['F35'][0] and f35[1] >= c0['FLOORS']['F35'][1], f35)
ck('P2b F24 两列不小于旧 floor', f24[0] >= c0['FLOORS']['F24'][0] and f24[1] >= c0['FLOORS']['F24'][1], f24)
ck('P2c F35.limitations 变长了（应为纯追加 +1,128 B 量级）',
   f35[1] > c0['FLOORS']['F35'][1], (c0['FLOORS']['F35'][1], f35[1]))

print('== P3/P4 · 新常量 ==')
c1 = dict(c0)
c1['CUR_SHA256'] = NEW_SHA
c1['TOTAL_BYTES'] = NEW_BYTES
c1['FLOORS'] = dict(c0['FLOORS'])
c1['FLOORS']['F35'] = f35
m1 = master(c1)
print('新 MASTER = %s' % m1)
ck('P3a 新 MASTER != 旧 MASTER', m1 != c0['MASTER_SHA256'])
for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ'):
    ck('P4.%s 未变' % k, c0[k] == c1[k], k)
chg = [k for k in c0['FLOORS'] if c0['FLOORS'][k] != c1['FLOORS'][k]]
ck('P4.FLOORS 只有 F35 一键变化', chg == ['F35'], chg)

print('== P5 · facts_floors 替换 ==')
txt = ff_raw.decode('utf-8')
reps = [
    ("os.path.join(TIER, 'R17_R127_FACTINDEX_V555', 'FACT_INDEX.tsv')",
     "os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEW_DIR),
    ("CUR_SHA256 = '%s'" % OLD_SHA, "CUR_SHA256 = '%s'" % NEW_SHA),
    ('TOTAL_BYTES = %d' % OLD_BYTES, 'TOTAL_BYTES = %d' % NEW_BYTES),
    ("    'F35': (%d, %d)," % c0['FLOORS']['F35'], "    'F35': (%d, %d)," % f35),
    ("MASTER_SHA256 = '%s'" % c0['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % m1),
]
newff = txt
for a, b in reps:
    ck('P5 替换串恰 1 次: %s' % a[:40].replace('\n', ' '), newff.count(a) == 1, newff.count(a))
    newff = newff.replace(a, b, 1)
ck('P5f facts_floors CR == 0', '\r' not in newff)
ol, nl = txt.split('\n'), newff.split('\n')
ck('P5g 行数不变', len(ol) == len(nl), (len(ol), len(nl)))
ndiff = [i for i, (a, b) in enumerate(zip(ol, nl)) if a != b]
print('变化行(1-based): %s' % [i + 1 for i in ndiff])
ck('P5h 变化行恰 5 行（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / F35 / MASTER）', len(ndiff) == 5, len(ndiff))
exp = ['EXPECT_CUR', 'CUR_SHA256', 'TOTAL_BYTES', "'F35'", 'MASTER_SHA256']
hit = sorted({k for i in ndiff for k in exp if k in ol[i] or k in nl[i]})
ck('P5i 命中常量集合 == 预期集合', hit == sorted(exp), hit)

print('== P6 · gate_runner ==')
gt = gr_raw.decode('utf-8')
ga = "os.path.join(TIER, 'R17_R127_FACTINDEX_V555', 'FACT_INDEX.tsv')"
gb = "os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEW_DIR
ck('P6a gate_runner 不持有旧 sha', gt.count(OLD_SHA[:8]) == 0, gt.count(OLD_SHA[:8]))
ck('P6b gate_runner 不持有新 sha', gt.count(NEW_SHA[:8]) == 0, gt.count(NEW_SHA[:8]))
ck('P6c 目录号替换串恰 1 次', gt.count(ga) == 1, gt.count(ga))
newgr = gt.replace(ga, gb, 1)
ck('P6d gate_runner CR == 0', '\r' not in newgr)
gol, gnl = gt.split('\n'), newgr.split('\n')
gdiff = [i for i, (a, b) in enumerate(zip(gol, gnl)) if a != b]
ck('P6e 变化行恰 1 行', len(gdiff) == 1, len(gdiff))

print('== P7 · 指针 ==')
pt = pt_raw.decode('utf-8')
preps = [
    ('| 版本目录 | R17_R127_FACTINDEX_V555 |', '| 版本目录 | %s |' % NEW_DIR),
    ('lead/next_re_20261117_r14/R17_R127_FACTINDEX_V555/FACT_INDEX.tsv',
     'lead/next_re_20261117_r14/%s/FACT_INDEX.tsv' % NEW_DIR),
    ('| sha256 | %s |' % OLD_SHA, '| sha256 | %s |' % NEW_SHA),
    ('| 字节数 | %d |' % OLD_BYTES, '| 字节数 | %d |' % NEW_BYTES),
    ('| 声明轮次 | R174 |', '| 声明轮次 | R174 |'),
    ('版本号 530..555 连续无缺', '版本号 530..556 连续无缺'),
    ('V530..V555 是 26 个', 'V530..V556 是 27 个'),
    ('（D0 已钉 V555 的 sha256）', '（D0 已钉 V556 的 sha256）'),
    ('V555 同时是「版本号最大」且「其目录序号 R127 为最大」，且 R127 下只有这一个 FACT_INDEX 目录',
     'V556 同时是「版本号最大」且「其目录序号 R128 为最大」，且 R128 下只有这一个 FACT_INDEX 目录'),
]
newpt = pt
for a, b in preps:
    ck('P7 替换串恰 1 次: %s' % a[:40], newpt.count(a) == 1, newpt.count(a))
    newpt = newpt.replace(a, b, 1)
ck('P7j 新指针无 V555 字样', 'V555' not in newpt, newpt.count('V555'))
ck('P7k 新指针含 V556 至少 4 处', newpt.count('V556') >= 4, newpt.count('V556'))
ck('P7l 新指针 CR == 0', '\r' not in newpt)
vers = sorted(int(re.search(r'V(\d+)$', d).group(1))
              for d in glob.glob(os.path.join(TIER, 'R17_R1*_FACTINDEX_V*')) if re.search(r'V(\d+)$', d))
print('版本目录 %d..%d 共 %d' % (vers[0], vers[-1], len(vers)))
ck('P7m 磁盘版本目录 530..556 连续、共 27 个', vers == list(range(530, 557)) and len(vers) == 27,
   (vers[0], vers[-1], len(vers)))

print('== 写盘前总闸 ==')
if fails:
    print('★ fail-closed：%d 条未过，一处都不写' % len(fails))
    print('FAILS: %s' % fails)
    sys.exit(1)

ts = time.strftime('%Y%m%d_%H%M%S')
baks = []
for src, nm in ((FF, 'facts_floors.py'), (GR, 'gate_runner.py'), (PTR, 'FACT_INDEX_CURRENT.md')):
    bp = os.path.join(BAKD, '%s.before_r174m_V556_%s.bak' % (nm, ts))
    fd = os.open(bp, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, io.open(src, 'rb').read())
    os.close(fd)
    baks.append(bp)
print('备份三件: %s' % [os.path.basename(b) for b in baks])

io.open(FF, 'w', encoding='utf-8', newline='\n').write(newff)
io.open(GR, 'w', encoding='utf-8', newline='\n').write(newgr)
io.open(PTR, 'w', encoding='utf-8', newline='\n').write(newpt)
print('三处已写')

print('== 写后回读 ==')
c2 = consts(FF)
ck('Q0a 回读 CUR_SHA256 == 新值', c2['CUR_SHA256'] == NEW_SHA)
ck('Q0b 回读 FLOORS[F35] == 新值', c2['FLOORS']['F35'] == f35, c2['FLOORS']['F35'])
ck('Q0c 回读 MASTER 命中新 pin', master(c2) == m1, master(c2)[:16])
ck('Q0d 回读指针含新 sha 与 V556', NEW_SHA in io.open(PTR, encoding='utf-8').read() and NEW_DIR in io.open(PTR, encoding='utf-8').read())


def run(args):
    p = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True, timeout=400)
    return p.returncode, p.stdout + p.stderr


rc, out = run([os.path.join(ROOT, '_r160/facts_floors.py')])
ck('Q1a facts_floors 默认 exit 0', rc == 0, rc)
ck('Q1b D0 打印新 sha 前缀', NEW_SHA[:8] in out)
ck('Q1c D8 打印 125538', '125538' in out)
ck('Q1d D9 打印新 MASTER 前缀', m1[:16] in out)

rc, out = run([os.path.join(ROOT, '_r160/facts_floors.py'), V555])
print('指定 V555（不加 --ignore-pin）exit=%d' % rc)
ck('Q2 指定 V555 必须 FAIL', rc != 0, rc)
ck('Q2b 失败理由为 D6/D8/D0 之一', any(k in out for k in ('D6', 'D8', 'D9', 'D0')),
   [l for l in out.split('\n') if 'FAIL' in l][:3])

rc, out = run([os.path.join(ROOT, '_r161/gate_runner.py')])
ck('Q1e gate_runner exit 0', rc == 0, rc)
ck('Q1f G1=G2=G3=ok', all(x in out for x in ('G1=ok', 'G2=ok', 'G3=ok')))
ck('Q1g GATE_VER 仍 R166', 'GATE_VER=R166' in out)

rc, out = run([os.path.join(TIER, 'check_disc.py')])
lf = [l for l in out.split('\n') if l.strip().startswith('FAIL')]
ck('Q1h check_disc exit 0', rc == 0, rc)
ck('Q1i 行首 FAIL 0', len(lf) == 0, lf[:3])

print('== Q3 · 两版磁盘态 ==')
ck('Q3a V555 未改', hashlib.sha256(io.open(V555, 'rb').read()).hexdigest() == OLD_SHA)
ck('Q3b V556 未改', hashlib.sha256(io.open(V556, 'rb').read()).hexdigest() == NEW_SHA)

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {
    'script': 'r174m_repin_v556.py',
    'ff_sha256_before': hashlib.sha256(ff_raw).hexdigest(),
    'ff_sha256_after': hashlib.sha256(io.open(FF, 'rb').read()).hexdigest(),
    'gr_sha256_before': hashlib.sha256(gr_raw).hexdigest(),
    'gr_sha256_after': hashlib.sha256(io.open(GR, 'rb').read()).hexdigest(),
    'old_master': c0['MASTER_SHA256'], 'new_master': m1,
    'new_cur_sha': NEW_SHA, 'new_total': NEW_BYTES, 'f35_floor': list(f35),
    'ff_changed_lines': [i + 1 for i in ndiff], 'gr_changed_lines': [i + 1 for i in gdiff],
    'backups': baks, 'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
