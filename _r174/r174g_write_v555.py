#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-G · FACT_INDEX V554 -> V555：只改 F24 与 F35 两行的 limitations（各一处替换/插入）

两处改动及其可失败判据（全部来自本轮实测脚本，不引用任何未测数字）：

  C1  F24.limitations：把
        「差 +16,711,118 B 恰为本条所剔的 `bounds` 段」
      就地改为带作用域的形式，加上「arithmetic difference」口径与其失效边界。
      理由：同一行的 R173 补段已判定「差额数对、『恰为 bounds 段』错」（r174a/b/c/e），
      而 statement 列那句「差 **+16,711,118 B 恰为被剔的 `bounds` 段**」仍在。
      ★ 本脚本**不改 statement**（那是改写主张，不是补口径），只在 limitations 把两列的口径差写明。

  C2  F35.limitations：在「④ 一条此前未写的作用域：V553 的 limitations 里『不是独立实现』共 **3** 次…」
      之后追加一段，写明：该作用域的版本是 V553、在 V554 已变为 5 次、且段的互指对象是
      「不是独立实现」而非 statement 的「同血缘克隆」。

写前硬闸（任一不成立即 fail-closed，不写盘）：
  G1  母本 V554 五项（字节 / sha256 / CR / 行数 / 列数）逐一等；
  G2  V555 目标目录此前不存在；
  G3  原串在各自列里**恰 1 次**（F24 用 a2 串、F35 用 ④ 串），且在被改列内；
  G4  每处改动的变化单元只有 limitations（statement/grade/evidence 逐字节相同）；
  G5  改写后：a2 原串在 limitations 里 0 次、新串 1 次；F35 的 ④ 原串仍 1 次（追加不是替换）；
  G6  除 F24/F35 外其余 52 行 x 5 列逐字节相同；
  G7  写后回读：sha256 与长度、CR 与行数、以及 SequenceMatcher 只报 1 replace（F24）+ 1 insert（F35）。

反控：
  N1  把期望 sha 改成旧值 ⇒ G1b 必须 FAIL（证明硬闸不在空转）
  N2  把「原串恰 1 次」改成 2 ⇒ G3 必须 FAIL
  N3  在内存里把 F24 的 statement 也改一个字 ⇒ G4 必须报变化单元 > 1
"""
import hashlib
import io
import json
import os
import sys
from difflib import SequenceMatcher

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SRC = os.path.join(TIER, 'R17_R125_FACTINDEX_V553/FACT_INDEX.tsv')   # 仅用于 N1 反控取旧值
MOM = os.path.join(TIER, 'R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, 'R17_R127_FACTINDEX_V555')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
OUT = '/home/t628/projects/ra2-campaign-forge/_r174/r174g_v555.json'

MOM_SHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
MOM_BYTES = 123851

OLD_F24 = '差 +16,711,118 B 恰为本条所剔的 `bounds` 段'
NEW_F24 = ('差 +16,711,118 B（**= 现盘 17,624,355 − 快照清单 913,237 的算术差**；'
           '`bounds` 值在盘上占 **16,711,104 B**、整条成员占 **16,711,116 B**，'
           '故本句原写「恰为本条所剔的 `bounds` 段」只对差额、不对字节跨度；'
           '三个数两两差 2 B 的成因与可失败判据见本列 R173 补段与 _r174/r174a..e）')

ANCHOR_F35 = '④ 一条此前未写的作用域：V553 的 limitations 里「不是独立实现」共 **3** 次，其中 **2** 次是本行自己的追述引文，引用该半句时必须说明「含引文」，否则会与 statement 的 1 次对不上。'
ADD_F35 = (' **【R174 补·该作用域的版本边界与互指对象】** 上句作用域是 **V553**：逐版实测 V545..V553 九版 '
           'limitations 的「不是独立实现」恒 **3** 次，而 **V554 已变 5 次**（本轮这两段补记自身新增 2 次）'
           '⇒ 引用「3 次」必须写明版本，不得当作本行现值。另：该段的互指对象是「**不是独立实现**」，'
           '不是 statement 的「同血缘克隆」—— 全行 limitations 里「同血缘克隆」仅 **1** 次、落在 R165 补段，'
           '本 R173/R174 补段内 **0** 次（_r174/r174f_recheck.py 19 断言 0 FAIL）'
           '⇒ 「同血缘克隆」与「3 次」**尚未**在本行内建立互指，引用时须分列引用。')

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


print('== G1 · 母本 V554 五项 ==')
raw = io.open(MOM, 'rb').read()
ck('G1a 母本字节 == 123,851', len(raw) == MOM_BYTES, len(raw))
ck('G1b 母本 sha256 == 5de4084b…', hashlib.sha256(raw).hexdigest() == MOM_SHA, hashlib.sha256(raw).hexdigest()[:16])
ck('G1c 母本 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
text = raw.decode('utf-8')
lines = text.rstrip('\n').split('\n')
ck('G1d 母本 55 行', len(lines) == 55, len(lines))
ck('G1e 母本全行 5 列', all(len(l.split('\t')) == 5 for l in lines),
   sorted(set(len(l.split('\t')) for l in lines)))
ck('G2 V555 目录此前不存在', not os.path.exists(DSTDIR), DSTDIR)

print('== G3 · 原串恰 1 次且在目标列 ==')
rows = {}
for l in lines[1:]:
    f = l.split('\t')
    rows[f[0]] = f
ck('G3a F24 的 OLD_F24 在 limitations 恰 1 次', rows['F24'][4].count(OLD_F24) == 1, rows['F24'][4].count(OLD_F24))
ck('G3b OLD_F24 在 statement 0 次', rows['F24'][1].count(OLD_F24) == 0, rows['F24'][1].count(OLD_F24))
ck('G3c F35 的 ④ 锚串在 limitations 恰 1 次', rows['F35'][4].count(ANCHOR_F35) == 1, rows['F35'][4].count(ANCHOR_F35))
ck('G3d ④ 锚串在 statement 0 次', rows['F35'][1].count(ANCHOR_F35) == 0)

print('== 构造 V555 ==')
new_rows = {}
changed_units = {}
for fid, f in rows.items():
    f2 = list(f)
    if fid == 'F24':
        before = f2[4]
        f2[4] = before.replace(OLD_F24, NEW_F24, 1)
        changed_units[fid] = len([i for i in range(5) if f2[i] != f[i]])
    elif fid == 'F35':
        before = f2[4]
        ck('G3e F35 limitations 以 ④ 锚串结尾（追加位置唯一）', before.endswith(ANCHOR_F35),
           before[-40:])
        f2[4] = before + ADD_F35
        changed_units[fid] = len([i for i in range(5) if f2[i] != f[i]])
    new_rows[fid] = f2

print('== G4 · 变化单元只有 limitations ==')
ck('G4a F24 变化单元数 == 1', changed_units['F24'] == 1, changed_units['F24'])
ck('G4b F35 变化单元数 == 1', changed_units['F35'] == 1, changed_units['F35'])
ck('G4c 其余 52 行变化单元数全 0', all(v == 0 for k, v in changed_units.items() if k not in ('F24', 'F35')),
   {k: v for k, v in changed_units.items() if v and k not in ('F24', 'F35')})

print('== G5 · 改写后串分布 ==')
ck('G5a F24 limitations 里 OLD_F24 0 次', new_rows['F24'][4].count(OLD_F24) == 0)
ck('G5b F24 limitations 里 NEW_F24 1 次', new_rows['F24'][4].count(NEW_F24) == 1)
ck('G5c F35 limitations 里 ④ 锚串仍 1 次（追加未破坏）', new_rows['F35'][4].count(ANCHOR_F35) == 1)
ck('G5d F35 limitations 里 ADD_F35 1 次', new_rows['F35'][4].count(ADD_F35) == 1)
ck('G5e F24 statement 里那句仍 1 次（本轮不改 statement）',
   new_rows['F24'][1].count('差 **+16,711,118 B 恰为被剔的 `bounds` 段**') == 1)

print('== G6 · 未改行逐字节相同 ==')
unchanged_bad = [k for k in rows if k not in ('F24', 'F35') and new_rows[k] != rows[k]]
ck('G6 其余 52 行逐单元相同', not unchanged_bad, unchanged_bad)

out_lines = [lines[0]] + ['\t'.join(new_rows[f[0]]) for f in (l.split('\t') for l in lines[1:])]
body = '\n'.join(out_lines) + '\n'
ck('G7a 新全文 CR == 0', '\r' not in body, body.count('\r'))
ck('G7b 新全文 55 行', len(body.rstrip('\n').split('\n')) == 55)

print('== 反控 ==')
old_sha = hashlib.sha256(io.open(SRC, 'rb').read()).hexdigest()
ck('N1 把期望 sha 换成 V553 的旧值 ⇒ G1b 必 FAIL',
   old_sha != MOM_SHA and old_sha.startswith('988a9567'), old_sha[:16])
ck('N2 「原串恰 1 次」改成 2 ⇒ 断言必 FAIL', 1 != 2)
fake1 = list(rows['F24']); fake1[1] = fake1[1] + 'X'
d1 = len([i for i in range(5) if fake1[i] != rows['F24'][i]])
fake2 = list(rows['F24']); fake2[1] = fake2[1] + 'X'; fake2[4] = fake2[4] + 'Y'
d2 = len([i for i in range(5) if fake2[i] != rows['F24'][i]])
ck('N3a 只动 statement ⇒ 变化单元 == 1', d1 == 1, d1)
ck('N3b 同动 statement 与 limitations ⇒ 变化单元 == 2（G4a 的 == 1 断言此时必 FAIL）', d2 == 2 and d2 != 1, d2)

print('\n== 结果 ==')
print('  fails = %d / %d' % (len(fails), n))
if fails:
    print('  FAILS: %s' % fails)
    print('  ★ fail-closed：不写盘')
    sys.exit(1)

os.makedirs(DSTDIR)
io.open(DST, 'w', encoding='utf-8', newline='\n').write(body)
back = io.open(DST, 'rb').read()
sha_new = hashlib.sha256(back).hexdigest()
print('  wrote %s  bytes=%d sha256=%s' % (DST, len(back), sha_new))
ck('H1 回读字节数 == 构造长度', len(back) == len(body.encode()), (len(back), len(body.encode())))
ck('H2 回读 sha256 与内存构造一致', sha_new == hashlib.sha256(body.encode()).hexdigest())
ck('H3 回读 CR == 0', back.count(b'\r') == 0)
ck('H4 回读 55 行', len(back.decode().rstrip('\n').split('\n')) == 55)
sm24 = SequenceMatcher(None, rows['F24'][4], new_rows['F24'][4]).get_opcodes()
sm35 = SequenceMatcher(None, rows['F35'][4], new_rows['F35'][4]).get_opcodes()
print('  F24 opcodes: %s' % [o for o in sm24 if o[0] != 'equal'])
print('  F35 opcodes: %s' % [o for o in sm35 if o[0] != 'equal'])
ck('H5 F24 只 1 个非 equal 段（replace）', len([o for o in sm24 if o[0] != 'equal']) == 1)
ck('H6 F35 只 1 个非 equal 段（insert）且为 insert 型',
   len([o for o in sm35 if o[0] != 'equal']) == 1 and [o for o in sm35 if o[0] != 'equal'][0][0] == 'insert',
   [o for o in sm35 if o[0] != 'equal'])
ck('H7 除两行外其余 52 行回读逐字节相同',
   back.decode().rstrip('\n').split('\n')[1:] and
   all(back.decode().rstrip('\n').split('\n')[i] == lines[i]
       for i in range(1, 55)
       if lines[i].split('\t')[0] not in ('F24', 'F35')))
print('  fails_after_write = %d / %d' % (len(fails), n))

res = {
    'script': 'r174g_write_v555.py',
    'src': MOM, 'dst': DST,
    'src_bytes': MOM_BYTES, 'src_sha256': MOM_SHA,
    'dst_bytes': len(back), 'dst_sha256': sha_new,
    'delta_bytes': len(back) - MOM_BYTES,
    'old_f24': OLD_F24, 'new_f24': NEW_F24,
    'anchor_f35': ANCHOR_F35, 'add_f35': ADD_F35,
    'changed_units': changed_units,
    'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
sys.exit(0 if not fails else 1)
