# -*- coding: utf-8 -*-
"""R183 D：指针文件自身两处自述过期（声明轮次 R180 -> R183；版本范围 530..563/34 份 -> 530..564/35 份）。
fail-closed：全部断言在写盘之前。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(PTR, 'rb').read()
s = raw.decode('utf-8')
print('== A · 旧态 ==')
ck('A1 指针 %d B' % len(raw), len(raw) == 2944, len(raw))
ck('A2 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('A3 声明轮次行 = R180（1 次）', s.count('| 声明轮次 | R180 |') == 1, s.count('| 声明轮次 | R180 |'))
ck('A4 声明依据里 530..563 出现 1 次', s.count('版本号 530..563 连续无缺') == 1, s.count('版本号 530..563 连续无缺'))
ck('A5 历史版本行 530..563 / 34 份 出现 1 次', s.count('V530..V563 是 34 个') == 1, s.count('V530..V563 是 34 个'))

print('== B · 现盘实数（不许预估）==')
import glob, re
# S-183d1（与 R180 S-665 同族第二次复发）：初版正则把早期命名 V53/V58/V511 当成 53/58/511
# => 「38 份，不连续」假 FAIL。修法：显式加 >=530 下界，并把被排除的目录名如实打印出来。
_all = [d for d in os.listdir(TIER) if re.match(r'^R17_R\d+_FACTINDEX_V\d+$', d)]
vs_all = sorted((int(re.search(r'V(\d+)$', d).group(1)), d) for d in _all)
_excl = [(v, d) for v, d in vs_all if v < 530]
vs = [v for v, d in vs_all if v >= 530]
print('   被排除的早期命名目录 %d 个：%r' % (len(_excl), [d for v, d in _excl]))
ck('B1 现盘版本 530..564 连续 35 份', vs == list(range(530, 565)), (len(vs), vs[:3], vs[-3:]))

print('== C · 构造新文 ==')
t = s
t = t.replace('| 声明轮次 | R180 |', '| 声明轮次 | R183 |', 1)
ck('C1 声明轮次已换', '| 声明轮次 | R183 |' in t and '| 声明轮次 | R180 |' not in t)
t = t.replace('版本号 530..563 连续无缺', '版本号 530..564 连续无缺', 1)
t = t.replace('现依据固定为「版本号最大（现盘 530..563 连续 34 份）',
              '现依据固定为「版本号最大（现盘 530..564 连续 35 份）', 1)
ck('C2 声明依据两处范围已换', '530..563 连续 34 份' not in t and '530..564 连续 35 份' in t)
t = t.replace('V530..V563 是 34 个可独立复核的快照', 'V530..V564 是 35 个可独立复核的快照', 1)
ck('C3 历史版本行已换', 'V530..V564 是 35 个可独立复核的快照' in t)
ck('C4 旧串全清（530..563 / 34 份 / R180 声明轮次）',
   'V530..V563 是 34 个' not in t and '| 声明轮次 | R180 |' not in t)
# 关键字段一字不动（D10 只认 sha256 / 字节数两行，但也不该被本题改到）
for frag in ('| 版本目录 | R17_R131_FACTINDEX_V564 |',
             '| sha256 | 081553aafe5b9f68188c72f65d2cb21ec5bd4a363122e68399109c47ad938039 |',
             '| 字节数 | 134245 |'):
    ck('C5 关键字段未动：%s' % frag[:22], frag in t)
ck('C6 CR 仍 0', t.count('\r') == 0, t.count('\r'))
import difflib
dl = [x for x in difflib.unified_diff(s.split('\n'), t.split('\n'), lineterm='', n=0) if x.startswith(('+', '-')) and not x.startswith(('+++', '---'))]
print('   差异行 %d：' % len(dl))
for x in dl: print('     ', x[:120])
ck('C7 差异行恰 6（3 处替换 × 一删一增）', len(dl) == 6, len(dl))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)

print('== D · 写盘 ==')
o = hashlib.sha256(raw).hexdigest()
bak = os.path.join(BASE, 'FACT_INDEX_CURRENT.md.before_r183_selfdesc_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f: f.write(raw)
ck('D1 备份独占且 sha 一致', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
nb = t.encode('utf-8')
io.open(PTR, 'w', encoding='utf-8', newline='').write(t)
back = open(PTR, 'rb').read()
ck('D2 回读一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(nb).hexdigest())
print('   指针 %d -> %d B（%+d）; sha %s -> %s' % (len(raw), len(back), len(back) - len(raw), o[:16], hashlib.sha256(back).hexdigest()[:16]))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
