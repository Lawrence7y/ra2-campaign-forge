#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-L · 修正我自己 V555 里的自指失效：F35 的「同血缘克隆 仅 1 次」已不再成立

机理（与 R173 待办里记的「3 次 → 5 次」完全同族，且这次是**我本轮亲手引入**）：
  V554 的 F35.limitations 里「同血缘克隆」= 1 次；
  V555 我追加的 R174 补段**自己引用了 3 次**（"不是 statement 的「同血缘克隆」"、
  "全行 limitations 里「同血缘克隆」仅 1 次"、"「同血缘克隆」与「3 次」尚未…"）
  ⇒ 全行实测变为 **4 次**，而正文仍写「仅 1 次」。
  同段还写「V554 已变 5 次（本轮这两段补记自身新增 2 次）」—— 对「不是独立实现」这一项，
  V555 实测 7 次（V554 5 + 本段 2），该句已自带「新增 2 次」的说法，**数字本身没写错**
  （它说的是 V554 的值），但读者会把它当现值 ⇒ 同样要补版本边界。

处置（只改 F35.limitations 一处，纯插入，不删任何既有字符）：
  在「引用时须分列引用。」之后插入一段，写明两个**引文自指**版本的实测计数：
  不得把「同血缘克隆 1 次」与「不是独立实现 3 次」当成当前值引用；给出现值并说明差值来自补段自身。

判据：
  M1  母本 V555 五项（字节 124,834 / sha 5396d2df / CR 0 / 55 行 / 5 列）
  M2  F35.limitations 里「同血缘克隆」实测 4 次、「不是独立实现」7 次（V554 分别是 1 / 5）
  M3  插入位置唯一（锚串「引用时须分列引用。」在该列恰 1 次且位于 R174 补段末尾）
  M4  写入后：插入串 1 次、原文 4 个片段全保留、变化单元只有 limitations
  M5  写后回读：sha / 字节 / CR / 行数 / 其余 52 行逐字节相同 / 母本未改

反控：
  N1  把锚串改成「引用时须分列引用」（去句号）⇒ 命中最少 1 次但位置仍是 1，证明锚串选择要靠句号定位
  N2  把新插入串里的 4 改成 3 ⇒ 与磁盘实测不符（断言必须 FAIL）
  N3  调换 old/new 做 SequenceMatcher ⇒ 必须出现 delete 型（证明是纯插入）
"""
import hashlib
import io
import json
import os
import sys
import time
from difflib import SequenceMatcher

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
MOM = os.path.join(TIER, 'R17_R127_FACTINDEX_V555/FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, 'R17_R128_FACTINDEX_V556')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
PREV554 = os.path.join(TIER, 'R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
BAKD = os.path.join(TIER, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r174/r174l_write_v556.json')

MOM_SHA = '5396d2df9f032e1cc6febdd340dd51591c4a52a961591a2babde52ef25f3496c'
MOM_BYTES = 124834
ANCHOR = '引用时须分列引用。'
ADD = (' **【R174-R2 补·两个引文自指版本的实测计数】** 上两段（R173 / R174）的计数一律是**引文自指**：'
       '它们写作时自身就增加了被计数的串。以磁盘实测为准：V554 的 F35.limitations 里「同血缘克隆」**1** 次、'
       '「不是独立实现」**5** 次；V555（加入 R173 补段后）分别变 **4** 次与 **7** 次；'
       '本 V556 再加本段后两者各再加 **1**、**1** 次而变为 **5** 与 **8**（本段自身即各含 1 次）。'
       '⇒ 引用这两个词的出现次数**必须带版本号**，且**不得**把任何一版的数字当现值；'
       '凡写「仅 N 次」都必须同时写「该段写作时」与版本号（_r174/r174m_selfref.py 复算）。')

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def rows_of(path):
    raw = io.open(path, 'rb').read()
    lines = raw.decode('utf-8').rstrip('\n').split('\n')
    d = {}
    for l in lines[1:]:
        f = l.split('\t')
        d[f[0]] = f
    return raw, lines, d


print('== M1 · 母本 V555 五项 ==')
raw, lines, R = rows_of(MOM)
ck('M1a 字节 == 124,834', len(raw) == MOM_BYTES, len(raw))
ck('M1b sha == 5396d2df…', hashlib.sha256(raw).hexdigest() == MOM_SHA, hashlib.sha256(raw).hexdigest()[:16])
ck('M1c CR == 0', raw.count(b'\r') == 0)
ck('M1d 55 行', len(lines) == 55, len(lines))
ck('M1e 全行 5 列', all(len(l.split('\t')) == 5 for l in lines))
ck('M2a V556 目录此前不存在', not os.path.exists(DSTDIR), DSTDIR)

print('== M2 · 两个词的实测计数（V554 vs V555） ==')
_, _, R5 = rows_of(PREV554)
CLONE, NEEDLE = '同血缘克隆', '不是独立实现'
c554, n554 = R5['F35'][4].count(CLONE), R5['F35'][4].count(NEEDLE)
c555, n555 = R['F35'][4].count(CLONE), R['F35'][4].count(NEEDLE)
print('V554: clone=%d needle=%d ; V555: clone=%d needle=%d' % (c554, n554, c555, n555))
ck('M2b V554 的 clone == 1', c554 == 1, c554)
ck('M2c V554 的 needle == 5', n554 == 5, n554)
ck('M2d V555 的 clone == 4', c555 == 4, c555)
ck('M2e V555 的 needle == 7', n555 == 7, n555)
ck('M2f V555 正文里的「仅 **1** 次」已与实测 4 冲突（这就是要修的自指失效）',
   '「同血缘克隆」仅 **1** 次' in R['F35'][4] and c555 == 4, c555)

print('== M3 · 锚串唯一 ==')
lim = R['F35'][4]
ck('M3a 锚串在 limitations 恰 1 次', lim.count(ANCHOR) == 1, lim.count(ANCHOR))
ck('M3b 锚串在 statement 0 次', R['F35'][1].count(ANCHOR) == 0)
ck('M3c 锚串位于 R174 补段末尾（其后无别的补段）', lim.endswith(ANCHOR), lim[-30:])

print('== 构造 V556 ==')
new_lim = lim + ADD
new_rows = {}
units = {}
for fid, f in R.items():
    f2 = list(f)
    if fid == 'F35':
        f2[4] = new_lim
    units[fid] = len([i for i in range(5) if f2[i] != f[i]])
    new_rows[fid] = f2
ck('M4a F35 变化单元 == 1', units['F35'] == 1, units['F35'])
ck('M4b 其余 53 行变化单元全 0', all(v == 0 for k, v in units.items() if k != 'F35'),
   {k: v for k, v in units.items() if v})
ck('M4c 新串在 limitations 里 1 次', new_lim.count(ADD) == 1)
ck('M4d 原 limitations 是 new 的前缀（纯追加）', new_lim.startswith(lim))
ck('M4e F35 statement 未变', new_rows['F35'][1] == R['F35'][1])

print('== 反控 ==')
no_dot = ANCHOR.rstrip('。')
ck('N1 去句号后命中次数 >= 1（锚串要靠句号定位唯一）', lim.count(no_dot) >= 1, lim.count(no_dot))
bad_add = ADD.replace('**4** 次与 **7** 次', '**3** 次与 **6** 次')
ck('N2 把 4/7 改成 3/6 ⇒ 与磁盘实测不符（该断言必 FAIL）',
   bad_add != ADD and c555 == 4 and n555 == 7)
rev = [o for o in SequenceMatcher(None, new_lim, lim, autojunk=False).get_opcodes() if o[0] != 'equal']
ck('N3 反向比较必须出现 delete 型', any(o[0] == 'delete' for o in rev), [o[0] for o in rev])

print('== 写盘前总闸（S-619 教训：全部断言必须在写盘之前） ==')
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    sys.exit(1)

body = '\n'.join([lines[0]] + ['\t'.join(new_rows[l.split('\t')[0]]) for l in lines[1:]]) + '\n'
ck('M4f 新全文 CR == 0', '\r' not in body)
os.makedirs(DSTDIR)
io.open(DST, 'w', encoding='utf-8', newline='\n').write(body)
back = io.open(DST, 'rb').read()
sha_new = hashlib.sha256(back).hexdigest()
print('wrote %s bytes=%d sha=%s' % (DST, len(back), sha_new))

print('== M5 · 写后回读 ==')
_, lines2, R2 = rows_of(DST)
ck('M5a 回读 55 行 5 列', len(lines2) == 55 and all(len(l.split('\t')) == 5 for l in lines2))
ck('M5b 回读 CR == 0', back.count(b'\r') == 0)
ck('M5c 回读 sha 与构造一致', sha_new == hashlib.sha256(body.encode()).hexdigest())
ck('M5d 其余 53 行逐字节相同',
   all(R2[k] == R[k] for k in R if k != 'F35'),
   [k for k in R if k != 'F35' and R2[k] != R[k]][:5])
ck('M5e 母本 V555 一字未改', hashlib.sha256(io.open(MOM, 'rb').read()).hexdigest() == MOM_SHA)
ops = [o for o in SequenceMatcher(None, lim, new_lim, autojunk=False).get_opcodes() if o[0] != 'equal']
print('F35 opcodes: %s' % ops)
ck('M5f F35 只有 1 个非 equal 段且为 insert', len(ops) == 1 and ops[0][0] == 'insert', ops)
ck('M5g 插在末尾（old_end == len(old)）', ops[0][1] == len(lim), (ops[0][1], len(lim)))
new_c, new_n = R2['F35'][4].count(CLONE), R2['F35'][4].count(NEEDLE)
print('V556: clone=%d needle=%d' % (new_c, new_n))
ck('M5h V556 的 clone == 5（本段自含 1）', new_c == 5, new_c)
ck('M5i V556 的 needle == 8（本段自含 1）', new_n == 8, new_n)
ck('M5j 本段正文预告的 5 与 8 与实测一致',
   '**5** 与 **8**' in R2['F35'][4] and new_c == 5 and new_n == 8, (new_c, new_n))

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {
    'script': 'r174l_write_v556.py', 'src': MOM, 'dst': DST,
    'src_bytes': MOM_BYTES, 'src_sha256': MOM_SHA,
    'dst_bytes': len(back), 'dst_sha256': sha_new, 'delta_bytes': len(back) - MOM_BYTES,
    'counts': {'v554': {'clone': c554, 'needle': n554}, 'v555': {'clone': c555, 'needle': n555},
               'v556': {'clone': new_c, 'needle': new_n}},
    'anchor': ANCHOR, 'add': ADD,
    'f35_ops': ops, 'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
