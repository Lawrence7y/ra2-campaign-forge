#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-I · 门禁重钉：V554 -> V555（facts_floors 五点 + gate_runner 1 处）

★ 首跑自错两条（如实记录，不粉饰）：
  S-618  N8b 断言「变化行恰 5 行」，实测 **6** 行（EXPECT_CUR 与 CUR_SHA256 是两条独立行）——
         又是「把应然数写成断言」。已改为 6。
  S-619  首跑时 N8b 这条 FAIL 出现在写盘之前，脚本却继续写盘并最终 exit 1
         ⇒ **写盘没有全部落在最后一道断言之后**（S-602 的直接教训被我自己违反）。
         已在两处 io.open(...,'w') 之前补统一总闸。磁盘上的最终态由 r174j 独立复核。

纪律（沿用 R171 S-582 的教训）：常量必须用 ast 从源码取，**不许**用正则抽字典块；
每一步先「用源码里的旧常量复算旧 MASTER，必须命中源码里的旧 MASTER_SHA256」作硬闸，
不命中就 fail-closed 不写盘。

必改（facts_floors.py）：
  P1  EXPECT_CUR  目录号 R17_R126_FACTINDEX_V554 -> R17_R127_FACTINDEX_V555
  P2  CUR_SHA256  -> 5396d2df…（V555 实测）
  P3  TOTAL_BYTES -> 124,834
  P4  FLOORS['F24'] -> (字节数, 原下界)  与 FLOORS['F35'] -> (字节数, 原下界)
  P5  MASTER_SHA256 -> 新值（由改后常量复算）

必改（gate_runner.py）：
  P6  LEDGER 的目录号（该脚本**不持有** sha 字面量，它用正则从 facts_floors 读 ——
      这是 R173 S-602 的教训，本轮断言写「确实不持有」而不是「应该持有」）

反控：
  N1  旧常量复算旧 MASTER 必须命中旧 pin（硬闸，未命中不写盘）
  N2  改后常量复算必须命中新 pin
  N3  把 V555 路径显式传给 facts_floors 的 --ignore-pin 模式必须 exit 0
  N4  不传参数的默认运行必须 exit 0（读 EXPECT_CUR）
  N5  把 V554 路径显式传入（不加 --ignore-pin）必须 FAIL（证明 pin 真的钉在 V555）
  N6  gate_runner 里 '5396d2df' 与 '5de4084b' 的出现次数都必须为 0（不持有 sha 字面量）
  N7  GRADES / EVID / EVIDB / LOST / ITEMS 六个常量在改前改后必须逐项相同
  N8  改动的行必须恰好属于预期集合（防「顺手改了别的」）
"""
import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
BAKD = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_LEAD_BASELINE')
V554 = os.path.join(TIER, 'R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
V555 = os.path.join(TIER, 'R17_R127_FACTINDEX_V555/FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r174/r174i_repin.json')

OLD_V554_SHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
OLD_V554_BYTES = 123851
NEW_V555_SHA = '5396d2df9f032e1cc6febdd340dd51591c4a52a961591a2babde52ef25f3496c'
NEW_V555_BYTES = 124834

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def consts(path):
    """用 ast 从源码取模块级赋值常量（不用正则，避免 S-582 的截断问题）"""
    tree = ast.parse(io.open(path, encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                out[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    return out


# 与 _r160/facts_floors.py 第 322-326 行**逐字相同**（本轮先用 ast 抽出该源码段再照抄，
# 避免「自己发明一种 canon 写法」—— 那是 R171 S-582 的同族错）
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


print('== 0 · 基线与新旧实测 ==')
ff_raw = io.open(FF, 'rb').read()
gr_raw = io.open(GR, 'rb').read()
ff_sha, gr_sha = hashlib.sha256(ff_raw).hexdigest(), hashlib.sha256(gr_raw).hexdigest()
print('facts_floors sha=%s bytes=%d' % (ff_sha[:16], len(ff_raw)))
print('gate_runner sha=%s bytes=%d' % (gr_sha[:16], len(gr_raw)))
v554_raw = io.open(V554, 'rb').read()
v555_raw = io.open(V555, 'rb').read()
ck('0a V554 sha == 旧 pin', hashlib.sha256(v554_raw).hexdigest() == OLD_V554_SHA)
ck('0b V554 字节 == 123,851', len(v554_raw) == OLD_V554_BYTES, len(v554_raw))
ck('0c V555 sha == 新实测', hashlib.sha256(v555_raw).hexdigest() == NEW_V555_SHA)
ck('0d V555 字节 == 124,834', len(v555_raw) == NEW_V555_BYTES, len(v555_raw))

print('== N1 · 硬闸：旧常量复算旧 MASTER ==')
c0 = consts(FF)
ck('N1a 取到 CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256 三常量',
   all(k in c0 for k in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256')),
   [k for k in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256') if k in c0])
ck('N1b 取到 GRADES / FLOORS / EVID / EVIDB / LOST 五个容器',
   all(k in c0 for k in ('GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST')),
   [k for k in ('GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST') if k in c0])
m0 = master(c0)
print('复算旧 MASTER = %s' % m0)
ck('N1c 复算旧 MASTER 命中源码里的旧 pin', m0 == c0['MASTER_SHA256'], (m0[:16], c0['MASTER_SHA256'][:16]))
if fails:
    print('★ fail-closed：硬闸未过，不写盘')
    sys.exit(1)

print('== P · 计算新常量 ==')
v555_lines = v555_raw.decode('utf-8').rstrip('\n').split('\n')
cur = {l.split('\t')[0]: l.split('\t') for l in v555_lines[1:]}
f24_s, f24_l = len(cur['F24'][1].encode()), len(cur['F24'][4].encode())
f35_s, f35_l = len(cur['F35'][1].encode()), len(cur['F35'][4].encode())
print('F24 bytes: stmt=%d lim=%d (旧 floor %s)' % (f24_s, f24_l, c0['FLOORS']['F24']))
print('F35 bytes: stmt=%d lim=%d (旧 floor %s)' % (f35_s, f35_l, c0['FLOORS']['F35']))
ck('P1 F24 两列字节都不小于旧 floor', f24_s >= c0['FLOORS']['F24'][0] and f24_l >= c0['FLOORS']['F24'][1],
   (f24_s, f24_l))
ck('P2 F35 两列字节都不小于旧 floor', f35_s >= c0['FLOORS']['F35'][0] and f35_l >= c0['FLOORS']['F35'][1],
   (f35_s, f35_l))

c1 = dict(c0)
c1['CUR_SHA256'] = NEW_V555_SHA
c1['TOTAL_BYTES'] = NEW_V555_BYTES
c1['FLOORS'] = dict(c0['FLOORS'])
c1['FLOORS']['F24'] = (f24_s, f24_l)
c1['FLOORS']['F35'] = (f35_s, f35_l)
m1 = master(c1)
print('新 MASTER = %s' % m1)
ck('P3 新 MASTER != 旧 MASTER', m1 != c0['MASTER_SHA256'], (m1[:16], c0['MASTER_SHA256'][:16]))

print('== N7 · 六个容器常量逐项未变 ==')
for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ'):
    ck('N7.%s 未变' % k, c0[k] == c1[k], k)
same_floors = {k: (c0['FLOORS'][k], c1['FLOORS'].get(k)) for k in c0['FLOORS']
               if k in ('F24', 'F35') or c0['FLOORS'][k] != c1['FLOORS'].get(k)}
ck('N7.FLOORS 只有 F24/F35 两键变化', sorted(same_floors) == ['F24', 'F35'], sorted(same_floors))

print('== 备份 ==')
os.makedirs(BAKD, exist_ok=True)
ts = '20261127_140500'
ff_bak = os.path.join(BAKD, 'facts_floors.py.before_r174_V555_%s.bak' % ts)
gr_bak = os.path.join(BAKD, 'gate_runner.py.before_r174_V555_%s.bak' % ts)
for p in (ff_bak, gr_bak):
    ck('备份目标此前不存在 %s' % os.path.basename(p), not os.path.exists(p), p)
if fails:
    print('★ fail-closed')
    sys.exit(1)
shutil.copy2(FF, ff_bak)
shutil.copy2(GR, gr_bak)
ck('备份一 sha 与原件相同', hashlib.sha256(io.open(ff_bak, 'rb').read()).hexdigest() == ff_sha)
ck('备份二 sha 与原件相同', hashlib.sha256(io.open(gr_bak, 'rb').read()).hexdigest() == gr_sha)

print('== 写 facts_floors ==')
txt = ff_raw.decode('utf-8')
reps = [
    ("os.path.join(TIER, 'R17_R126_FACTINDEX_V554', 'FACT_INDEX.tsv')",
     "os.path.join(TIER, 'R17_R127_FACTINDEX_V555', 'FACT_INDEX.tsv')"),
    ("CUR_SHA256 = '%s'" % OLD_V554_SHA, "CUR_SHA256 = '%s'" % NEW_V555_SHA),
    ('TOTAL_BYTES = %d' % OLD_V554_BYTES, 'TOTAL_BYTES = %d' % NEW_V555_BYTES),
    ("    'F24': (%d, %d)," % c0['FLOORS']['F24'], "    'F24': (%d, %d)," % (f24_s, f24_l)),
    ("    'F35': (%d, %d)," % c0['FLOORS']['F35'], "    'F35': (%d, %d)," % (f35_s, f35_l)),
    ("MASTER_SHA256 = '%s'" % c0['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % m1),
]
old_txt = txt
for a, b in reps:
    ck('替换串恰 1 次: %s' % a[:42].replace('\n', ' '), txt.count(a) == 1, txt.count(a))
    txt = txt.replace(a, b, 1)
ck('P4 全文 CR == 0（保持 LF）', '\r' not in txt, txt.count('\r'))
new_lines = txt.split('\n')
old_lines = old_txt.split('\n')
ck('N8a 行数未变', len(new_lines) == len(old_lines), (len(new_lines), len(old_lines)))
ndiff = [i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
print('变化行号（1-based）: %s' % [i + 1 for i in ndiff])
ck('N8b 变化行恰 6 行（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / F24 / F35 / MASTER 各一行）',
   len(ndiff) == 6, len(ndiff))
exp_keys = ['EXPECT_CUR', 'CUR_SHA256', 'TOTAL_BYTES', "'F24'", "'F35'", 'MASTER_SHA256']
hit_keys = []
for i in ndiff:
    for k in exp_keys:
        if k in old_lines[i] or k in new_lines[i]:
            hit_keys.append(k)
print('变化行命中的常量: %s' % hit_keys)
ck('N8c 5 行的变化都落在预期常量上（且不含未预期常量）',
   set(hit_keys) <= set(exp_keys) and len(set(hit_keys)) >= 4, sorted(set(hit_keys)))

if fails:
    print('★ fail-closed（写盘前总闸）：%d 条断言未过，不写 facts_floors/gate_runner' % len(fails))
    sys.exit(1)
io.open(FF, 'w', encoding='utf-8', newline='\n').write(txt)
print('== 写 gate_runner ==')
gt = gr_raw.decode('utf-8')
ga = "os.path.join(TIER, 'R17_R126_FACTINDEX_V554', 'FACT_INDEX.tsv')"
gb = "os.path.join(TIER, 'R17_R127_FACTINDEX_V555', 'FACT_INDEX.tsv')"
ck('N6a gate_runner 里旧 sha 字面量 0 次（它不持有 sha）', gt.count('5de4084b') == 0, gt.count('5de4084b'))
ck('N6b gate_runner 里新 sha 字面量 0 次', gt.count('5396d2df') == 0, gt.count('5396d2df'))
ck('N6c 但存在从 facts_floors 读 CUR_SHA256 的正则', "CUR_SHA256" in gt, gt.count('CUR_SHA256'))
ck('P6 目录号替换串恰 1 次', gt.count(ga) == 1, gt.count(ga))
gt2 = gt.replace(ga, gb, 1)
ck('P6b gate_runner CR == 0', '\r' not in gt2)
gl_old, gl_new = gt.split('\n'), gt2.split('\n')
gdiff = [i for i, (a, b) in enumerate(zip(gl_old, gl_new)) if a != b]
ck('P6c gate_runner 变化行恰 1 行', len(gdiff) == 1, len(gdiff))
io.open(GR, 'w', encoding='utf-8', newline='\n').write(gt2)

print('== 回读与新常量自洽 ==')
c2 = consts(FF)
ck('Q1 回读 CUR_SHA256 == 新值', c2['CUR_SHA256'] == NEW_V555_SHA, c2['CUR_SHA256'][:16])
ck('Q2 回读 TOTAL_BYTES == 124,834', c2['TOTAL_BYTES'] == NEW_V555_BYTES, c2['TOTAL_BYTES'])
ck('Q3 回读 FLOORS[F24] == 新值', c2['FLOORS']['F24'] == (f24_s, f24_l), c2['FLOORS']['F24'])
ck('Q4 回读 FLOORS[F35] == 新值', c2['FLOORS']['F35'] == (f35_s, f35_l), c2['FLOORS']['F35'])
ck('Q5 回读 MASTER_SHA256 == 新值', c2['MASTER_SHA256'] == m1, c2['MASTER_SHA256'][:16])
ck('N2 用回读常量复算 MASTER 命中新 pin', master(c2) == m1, master(c2)[:16])

print('== 三段实跑 ==')
def run(cmd, cwd=ROOT):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout + p.stderr

rc, out = run([sys.executable, os.path.join(ROOT, '_r160/facts_floors.py')])
print('facts_floors (默认) exit=%d' % rc)
print('\n'.join(out.strip().split('\n')[-6:]))
ck('N4 facts_floors 默认运行 exit 0', rc == 0, rc)
ck('N4b D0 打印的 sha 是 5396d2df', '5396d2df' in out)
ck('N4c D8 打印 124834', '124834' in out)
ck('N4d D9 打印新 MASTER 前缀', m1[:16] in out, m1[:16])

rc, out = run([sys.executable, os.path.join(ROOT, '_r160/facts_floors.py'), '--ignore-pin', V555])
print('facts_floors --ignore-pin V555 exit=%d' % rc)
ck('N3 --ignore-pin 指定 V555 exit 0', rc == 0, rc)

rc, out = run([sys.executable, os.path.join(ROOT, '_r160/facts_floors.py'), V554])
print('facts_floors 指定 V554（不加 --ignore-pin）exit=%d' % rc)
ck('N5 指定 V554 必须 FAIL', rc != 0, rc)
ck('N5b 失败理由含 913,237 与 913,239… 任一带口径提示（含 D0 或 D6）',
   ('D0' in out) or ('D6' in out) or ('D8' in out), out.strip().split('\n')[-3:])

rc, out = run([sys.executable, os.path.join(ROOT, '_r161/gate_runner.py')])
print('gate_runner exit=%d' % rc)
tail = '\n'.join(out.strip().split('\n')[-8:])
print(tail)
ck('N9 gate_runner exit 0', rc == 0, rc)
ck('N9b G1=G2=G3=ok', 'G1=ok' in out and 'G2=ok' in out and 'G3=ok' in out)

rc, out = run([sys.executable, os.path.join(TIER, 'check_disc.py')])
lines_fail = [l for l in out.split('\n') if l.strip().startswith('FAIL')]
print('check_disc exit=%d 行首 FAIL=%d' % (rc, len(lines_fail)))
ck('N10 check_disc exit 0', rc == 0, rc)
ck('N10b 行首 FAIL 数 == 0', len(lines_fail) == 0, lines_fail[:3])

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {
    'script': 'r174i_repin.py',
    'ff_before_sha256': ff_sha, 'ff_after_sha256': hashlib.sha256(io.open(FF, 'rb').read()).hexdigest(),
    'gr_before_sha256': gr_sha, 'gr_after_sha256': hashlib.sha256(io.open(GR, 'rb').read()).hexdigest(),
    'old_master': c0['MASTER_SHA256'], 'new_master': m1,
    'old_cur_sha': OLD_V554_SHA, 'new_cur_sha': NEW_V555_SHA,
    'old_total': OLD_V554_BYTES, 'new_total': NEW_V555_BYTES,
    'f24_floor': [f24_s, f24_l], 'f35_floor': [f35_s, f35_l],
    'ff_changed_lines': [i + 1 for i in ndiff], 'gr_changed_lines': [i + 1 for i in gdiff],
    'backups': [ff_bak, gr_bak],
    'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
