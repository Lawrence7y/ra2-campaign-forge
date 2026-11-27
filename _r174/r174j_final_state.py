#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-J · 门禁写入后的最终态复核（只读，幂等；r174i 首跑已写盘，本脚本不重跑写逻辑）

为什么单独一个脚本：r174i 首跑时 S-619 让写盘发生在最后一道断言之前，且 N8b 断言值写错。
写盘内容本身是对的（由 Q1..Q5 / N2 与三段实跑当场证过），但「写盘位置」违反纪律。
本脚本以磁盘为准重新判一遍，并把 r174i 的「应有值」与磁盘实测值逐项对齐。

判据：
  Z1  facts_floors 六个常量与实测值一致（ast 取，不用正则）
  Z2  MASTER 用磁盘常量复算命中磁盘 pin
  Z3  facts_floors 里不再出现任何 V554 字样与旧 sha/旧字节字面量
  Z4  gate_runner 目录号为 V555、且不持有任何 sha 字面量
  Z5  备份两件存在且 sha 等于改前 sha
  Z6  三段实跑（默认 facts_floors / gate_runner / check_disc）全 exit 0
  Z7  V554 与 V555 母本/新版两者磁盘态未被后续改动（sha 与 r174g/h 记的一致）
"""
import ast
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
BAKD = os.path.join(TIER, 'R17_LEAD_BASELINE')
V554 = os.path.join(TIER, 'R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
V555 = os.path.join(TIER, 'R17_R127_FACTINDEX_V555/FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r174/r174j_final_state.json')

V554_SHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
V555_SHA = '5396d2df9f032e1cc6febdd340dd51591c4a52a961591a2babde52ef25f3496c'
V555_BYTES = 124834

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


print('== Z0 · 磁盘基线 ==')
ff_raw = io.open(FF, 'rb').read()
gr_raw = io.open(GR, 'rb').read()
print('facts_floors sha=%s bytes=%d' % (hashlib.sha256(ff_raw).hexdigest()[:16], len(ff_raw)))
print('gate_runner  sha=%s bytes=%d' % (hashlib.sha256(gr_raw).hexdigest()[:16], len(gr_raw)))
c = consts(FF)

print('== Z1 · facts_floors 六常量 ==')
ck('Z1a CUR_SHA256 == V555 sha', c['CUR_SHA256'] == V555_SHA, c['CUR_SHA256'][:16])
ck('Z1b TOTAL_BYTES == 124,834', c['TOTAL_BYTES'] == V555_BYTES, c['TOTAL_BYTES'])
ck('Z1c EXPECT_CUR 指向 V555 目录', 'R17_R127_FACTINDEX_V555' in ff_raw.decode('utf-8'),
   'R17_R127_FACTINDEX_V555' in ff_raw.decode('utf-8'))
v555_lines = io.open(V555, encoding='utf-8').read().rstrip('\n').split('\n')
cur = {l.split('\t')[0]: l.split('\t') for l in v555_lines[1:]}
f24 = (len(cur['F24'][1].encode()), len(cur['F24'][4].encode()))
f35 = (len(cur['F35'][1].encode()), len(cur['F35'][4].encode()))
ck('Z1d FLOORS[F24] == 磁盘实测字节对', c['FLOORS']['F24'] == f24, (c['FLOORS']['F24'], f24))
ck('Z1e FLOORS[F35] == 磁盘实测字节对', c['FLOORS']['F35'] == f35, (c['FLOORS']['F35'], f35))

print('== Z2 · MASTER 自洽 ==')
m = master(c)
print('复算 MASTER = %s ; 磁盘 pin = %s' % (m[:16], c['MASTER_SHA256'][:16]))
ck('Z2 复算命中磁盘 pin', m == c['MASTER_SHA256'], (m[:16], c['MASTER_SHA256'][:16]))

print('== Z3 · 无 V554 残留 ==')
txt = ff_raw.decode('utf-8')
ck('Z3a 无 V554 目录名', 'R17_R126_FACTINDEX_V554' not in txt)
ck('Z3b 无旧 sha 字面量 5de4084b', '5de4084b' not in txt, txt.count('5de4084b'))
ck('Z3c 无旧字节字面量 123851', '123851' not in txt, txt.count('123851'))
ck('Z3d 无旧 MASTER 字面量 5f3ba93c', '5f3ba93c' not in txt, txt.count('5f3ba93c'))

print('== Z4 · gate_runner ==')
gt = gr_raw.decode('utf-8')
ck('Z4a 目录号已是 V555', "R17_R127_FACTINDEX_V555" in gt)
ck('Z4b 无 V554 残留', 'R17_R126_FACTINDEX_V554' not in gt)
ck('Z4c 不持有新 sha 字面量', gt.count('5396d2df') == 0, gt.count('5396d2df'))
ck('Z4d 不持有旧 sha 字面量', gt.count('5de4084b') == 0, gt.count('5de4084b'))
ck('Z4e 仍用正则从 facts_floors 读 CUR_SHA256', 'CUR_SHA256' in gt, gt.count('CUR_SHA256'))

print('== Z5 · 备份 ==')
baks = sorted([f for f in os.listdir(BAKD) if 'before_r174_V555' in f])
print('r174 备份: %s' % baks)
ck('Z5a 两件备份都存在', len(baks) == 2, baks)
ff_bak = [os.path.join(BAKD, b) for b in baks if b.startswith('facts_floors')]
gr_bak = [os.path.join(BAKD, b) for b in baks if b.startswith('gate_runner')]
ck('Z5b facts_floors 备份一份', len(ff_bak) == 1, ff_bak)
ck('Z5c gate_runner 备份一份', len(gr_bak) == 1, gr_bak)
if ff_bak and gr_bak:
    bff = consts(ff_bak[0])
    ck('Z5d 备份里 CUR_SHA256 仍是 V554 sha', bff['CUR_SHA256'] == V554_SHA, bff['CUR_SHA256'][:16])
    ck('Z5e 备份里 TOTAL_BYTES 仍是 123,851', bff['TOTAL_BYTES'] == 123851, bff['TOTAL_BYTES'])
    ck('Z5f 备份里 MASTER 是旧 pin', bff['MASTER_SHA256'].startswith('5f3ba93c'), bff['MASTER_SHA256'][:16])
    ck('Z5g 备份的 gate_runner 仍是 V554 目录号',
       'R17_R126_FACTINDEX_V554' in io.open(gr_bak[0], encoding='utf-8').read())

print('== Z7 · FACT_INDEX 两版磁盘态 ==')
ck('Z7a V554 sha 未变', hashlib.sha256(io.open(V554, 'rb').read()).hexdigest() == V554_SHA)
ck('Z7b V555 sha 未变', hashlib.sha256(io.open(V555, 'rb').read()).hexdigest() == V555_SHA)
ck('Z7c V555 字节 == 124,834', os.path.getsize(V555) == V555_BYTES, os.path.getsize(V555))

print('== Z6 · 三段实跑 ==')
def run(args):
    p = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True, timeout=400)
    return p.returncode, p.stdout + p.stderr

rc, out = run([os.path.join(ROOT, '_r160/facts_floors.py')])
ck('Z6a facts_floors exit 0', rc == 0, rc)
ck('Z6b D0 打印 5396d2df', '5396d2df' in out)
ck('Z6c D8 打印 124834', '124834' in out)
ck('Z6d D9 打印新 pin 前缀', c['MASTER_SHA256'][:16] in out, c['MASTER_SHA256'][:16])

rc2, out2 = run([os.path.join(ROOT, '_r161/gate_runner.py')])
ck('Z6e gate_runner exit 0', rc2 == 0, rc2)
ck('Z6f G1=G2=G3=ok', all(x in out2 for x in ('G1=ok', 'G2=ok', 'G3=ok')))
ck('Z6g GATE_VER 仍 R166', 'GATE_VER=R166' in out2)

rc3, out3 = run([os.path.join(TIER, 'check_disc.py')])
lf = [l for l in out3.split('\n') if l.strip().startswith('FAIL')]
ck('Z6h check_disc exit 0', rc3 == 0, rc3)
ck('Z6i 行首 FAIL 数 == 0', len(lf) == 0, lf[:3])

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {
    'script': 'r174j_final_state.py',
    'ff_sha256': hashlib.sha256(ff_raw).hexdigest(),
    'gr_sha256': hashlib.sha256(gr_raw).hexdigest(),
    'cur_sha256': c['CUR_SHA256'], 'total_bytes': c['TOTAL_BYTES'],
    'master_sha256': c['MASTER_SHA256'],
    'floors_f24': list(c['FLOORS']['F24']), 'floors_f35': list(c['FLOORS']['F35']),
    'backups': baks,
    'gates': {'facts_floors': rc, 'gate_runner': rc2, 'check_disc': rc3},
    'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
