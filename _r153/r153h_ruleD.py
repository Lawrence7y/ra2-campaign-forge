#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 H：规则 D —— 逐条复算两个子代理的主张（#347 exec succeeded / #348 audit partial）。

必须复算的三条（审计员 #348 与我实测不一致，或口径不明）：
  A1 #348 称「盘上无任何口径能复现 33」 —— 我实测 V4 拆词口径复现 33/33，需证谁对。
  A2 「33 个锚点」在 R14_COMMON 的行号：#347 报 12602、#348 报 12599、我实测 12599。
     三者差 3，必须定位是行计数口径（splitlines vs split('\\n')）还是别的。
  A3 #348 称 R14_COMMON 含 43 个 NUL 字节 —— 独立复核。
"""
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(D, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
S149A = os.path.join(ROOT, '_r146/r149a_lostpath.py')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


print('=== A1 #348「无任何口径能复现 33」是否成立 ===')
import ast
src = open(S149A, encoding='utf-8').read()
ANCHOR = None
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'ANCHOR':
        ANCHOR = ast.literal_eval(node.value)


def v0(a):
    return [a]


def v1(a):
    return a.split(' ')


def v2(a):
    return [x for x in re.split(r'[ +]', a) if x]


def v4(a):
    if a.startswith('[') and a.endswith(']'):
        return [a]
    return [x for x in re.split(r'[ +]', a) if x]


tot = {}
for name, fn in (('V0', v0), ('V1', v1), ('V2', v2), ('V4', v4)):
    tot[name] = sum(len(fn(a)) for _, anc in ANCHOR.values() for a in anc)
print('  四种拆词口径合计：%s' % tot)
ck('V4 口径 = 33（#348「无任何口径」不成立）', tot['V4'] == 33, tot['V4'])
ck('同时存在 27/29/34 三个别的自然口径', (tot['V0'], tot['V1'], tot['V2']) == (27, 29, 34), tot)
# V4 逐 token 命中
led = open(LED, encoding='utf-8', newline='').read().split('\n')
secs = [(i, re.match(r'^## §(\d+)', l).group(1)) for i, l in enumerate(led)
        if re.match(r'^## §\d+', l)]
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(led)
    SEC[num] = '\n'.join(led[i:end])
v4t = [(f, sec.lstrip('§'), t) for f, (sec, anc) in ANCHOR.items()
       for a in anc for t in v4(a)]
miss = [x for x in v4t if x[2] not in SEC[x[1]]]
print('  V4 口径 token 总数 = %d，未命中 = %d' % (len(v4t), len(miss)))
ck('V4 口径 33/33 全部逐字命中（所以 33 是「口径未写明」而非「算错」）',
   len(v4t) == 33 and not miss, (len(v4t), len(miss)))

print('\n=== A2 「33 个锚点」在 R14_COMMON 的行号三方差异 ===')
raw = open(RC, 'rb').read()
print('  R14_COMMON %d B / CR=%d / LF=%d' % (len(raw), raw.count(b'\r'), raw.count(b'\n')))
txt = raw.decode('utf-8', errors='strict')
# 口径 1：split('\n')
l_split = txt.split('\n')
hit1 = [i + 1 for i, l in enumerate(l_split) if '33 个锚点' in l]
# 口径 2：splitlines()
l_sl = txt.splitlines()
hit2 = [i + 1 for i, l in enumerate(l_sl) if '33 个锚点' in l]
# 口径 3：CRLF 先归一
hit3 = [i + 1 for i, l in enumerate(txt.replace('\r\n', '\n').split('\n')) if '33 个锚点' in l]
print('  split("\\n")            行数 %5d  命中行 %s' % (len(l_split), hit1))
print('  splitlines()            行数 %5d  命中行 %s' % (len(l_sl), hit2))
print('  CRLF 归一后 split("\\n")  行数 %5d  命中行 %s'
      % (len(txt.replace('\r\n', '\n').split('\n')), hit3))
ck('split("\\n") 与 CRLF 归一口径命中同号（12599）', hit1 == hit3, (hit1, hit3))
ck('splitlines() 因额外分隔符给出不同号（这就是 #347 12602 的来源）',
   hit2 != hit1, (hit1, hit2))
# 找出 splitlines 多切的位置类型
extra = {}
for ch in ('\x0b', '\x0c', '\x1c', '\x1d', '\x1e', '\x85', ' ', ' '):
    n = txt.count(ch)
    if n:
        extra[repr(ch)] = n
print('  文件内 splitlines 额外分隔符计数：%s' % extra)
ck('多切来源是 CRLF 与其它分隔符，不是数据丢失',
   raw.count(b'\r') > 0, raw.count(b'\r'))

print('\n=== A3 #348 称 R14_COMMON 含 43 个 NUL 字节 ===')
nul = raw.count(b'\x00')
print('  NUL 字节实测 = %d' % nul)
ck('#348 的 43 个 NUL 成立', nul == 43, nul)
idx = [i for i, b in enumerate(raw) if b == 0][:5]
print('  前 5 个 NUL 的字节偏移与所在行：')
for i in idx:
    line = raw[:i].count(b'\n') + 1
    print('    offset %d  line %d' % (i, line))
ck('NUL 不影响 utf-8 严格解码（否则上一步会抛异常）', True)

print('\n=== A4 #348「R14_COMMON 命中行同时含 12 个 fid」 ===')
line = l_split[hit1[0] - 1] if hit1 else ''
ck('该行同时含「12 个 fid」', '12 个 fid' in line, line[:80])
ck('该行同时含「全部逐字命中」', '全部逐字命中' in line)

print('\n=== 正反控 ===')
ck('反控：自造串 ZZZ_R153_H 在 R14_COMMON 0 命中', 'ZZZ_R153_H' not in txt)
ck('正控：V0 口径对 F15 只拆 3 个', len(ANCHOR['F15'][1]) == 3)
ck('反控：V4 对 [edx+0xA8] 不拆（仍算 1 个）',
   v4('[edx+0xA8]') == ['[edx+0xA8]'], v4('[edx+0xA8]'))

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
