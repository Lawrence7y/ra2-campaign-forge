#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-b · FACT_INDEX V544 -> V545（三处纯追加 + F35 一处就地措辞校正）

写入纪律（与 R159/R164 同）：
  1) 备份：wx 独占创建 -> 断言旧 sha256 与字节 -> 一次性写入 -> 回读校验
  2) 除 F35/F29/F23 三行外，其余 51 行逐字节相同（用整文件差分断言，不靠行数）
  3) 每处改动都带反控：改前该串计数、改后该串计数都必须实测
幂等：若 V545 已是终态，只做终态校验并 exit 0。
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V544 = os.path.join(T, 'R17_R116_FACTINDEX_V544/FACT_INDEX.tsv')
D545 = os.path.join(T, 'R17_R117_FACTINDEX_V545')
V545 = os.path.join(D545, 'FACT_INDEX.tsv')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r165/r165b_write_v545.json')

OLD_SHA = '00c4f41fcba51c25828a3279542c0ab16727d994ddfcf3d2d8eda814fef764c2'
OLD_BYTES = 100616

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


# ---------------------------------------------------------------- 0 · 旧态
print('== 0 · 旧态 ==')
old = rb(V544)
ck('0.1 V544 sha256 == 钉住值', sha(old) == OLD_SHA, sha(old))
ck('0.2 V544 字节 == 100616', len(old) == OLD_BYTES, len(old))
oldtxt = old.decode('utf-8')
ck('0.3 V544 无 CR', oldtxt.count('\r') == 0, oldtxt.count('\r'))
oldlines = oldtxt.rstrip('\n').split('\n')
ck('0.4 V544 行数 55（rstrip 末尾换行后口径）', len(oldlines) == 55, len(oldlines))
ck('0.4b 反控：不 rstrip 时得 56（证明文件以单个换行结尾）', len(oldtxt.split('\n')) == 56, len(oldtxt.split('\n')))
rows = [l.split('\t') for l in oldlines if l]
ck('0.5 V544 每行 5 列', all(len(r) == 5 for r in rows), [len(r) for r in rows if len(r) != 5])

byid = {r[0]: r for r in rows}
f23, f29, f35 = byid['F23'], byid['F29'], byid['F35']

# ---------------------------------------------------------------- 1 · 改前计数（反控基线）
print()
print('== 1 · 改前计数（反控基线）==')
ck('1.1 F35 limitations 含「独立脚本」恰 1 次', f35[4].count('独立脚本') == 1, f35[4].count('独立脚本'))
ck('1.2 F35 limitations 含「不是独立实现」0 次', f35[4].count('不是独立实现') == 0, f35[4].count('不是独立实现'))
ck('1.3 F35 statement 含「不是独立实现」恰 1 次', f35[1].count('不是独立实现') == 1, f35[1].count('不是独立实现'))
ck('1.4 F35 limitations 含待替换原句', '另有 3 个独立脚本含同一逐字判据（' in f35[4])
ck('1.5 F29 statement 含「不在本条任何一列」恰 1 次', f29[1].count('不在本条任何一列') == 1, f29[1].count('不在本条任何一列'))
ck('1.6 F29 limitations 含「不在本条正文任何一列」恰 1 次', f29[4].count('不在本条正文任何一列') == 1, f29[4].count('不在本条正文任何一列'))
ck('1.7 F23 limitations 含 R159 段头恰 1 次', f23[4].count('【R159 补·12 行分解的缺口与作用域】') == 1)
ck('1.8 F23 limitations 内含「逐版扫 13 版（V530–V542）」', '逐版扫 13 版（V530–V542）' in f23[4])
# 反控：待替换句在**其它**行不得出现（否则全局替换会误伤）
allblob = oldtxt
ck('1.9 反控：待替换句全表恰 1 次（全局唯一，替换不会误伤别行）',
   allblob.count('另有 3 个独立脚本含同一逐字判据（') == 1,
   allblob.count('另有 3 个独立脚本含同一逐字判据（'))
ck('1.10 反控：自造串全表 0 次（尺子不被巧合命中）',
   allblob.count('另有 3 个独立脚本ZZQ') == 0)

# ---------------------------------------------------------------- 2 · 构造新三行
print()
print('== 2 · 构造新行 ==')

# --- F35 改动 1：就地校正（唯一一处替换，两侧都断言）
O1 = '另有 3 个独立脚本含同一逐字判据（'
N1 = '另 3 个脚本含同一逐字判据、但不是独立实现（'
new_f35_lim = f35[4].replace(O1, N1, 1)
ck('2.1 F35 替换后「独立脚本」= 0 次', new_f35_lim.count('独立脚本') == 0, new_f35_lim.count('独立脚本'))
ck('2.2 F35 替换后「不是独立实现」= 1 次（尚未加追加段）', new_f35_lim.count('不是独立实现') == 1,
   new_f35_lim.count('不是独立实现'))
ck('2.3 F35 替换只动了该处（长度差 = len(N1)-len(O1)）',
   len(f35[4]) - len(new_f35_lim) == len(O1) - len(N1),
   (len(f35[4]), len(new_f35_lim), len(O1) - len(N1)))

ADD35 = ('**【R165 补·两处措辞的回收】** 上文 R139 段写「另有 3 个独立脚本含同一逐字判据」，'
         '与本行 statement ② 的「不是独立实现……同血缘克隆」直接相反；本轮把前一处就地改为'
         '「另 3 个脚本含同一逐字判据、但不是独立实现」，使同一行两列口径一致。'
         '血缘判据是机械的：四个脚本（`RULING_R15_20261119/work/strict_panel.py` 第 78 行、'
         '`_cards/M59-MERGE/precheck.py` 第 60 行、`simulate.py` 第 72 行、`verify.py` 第 83 行）'
         '共用逐字相同的 `PROJ` 常量 `D:\\Project\\ra2-campaign-forge`，且都按同一对分段字面量打开同一对输入'
         '（`"COVERAGE", "coverage.tsv"` 与 `"W130_atlas", "function_atlas.tsv"`），'
         '故只能互证判据串、不能当交叉验证。反控两条例：写入器 `merge_panel.py` 有同一 `PROJ` 与同一 `ROOT` '
         '但**不含**该判据（`[未证]` 0 处）⇒ 共用 `PROJ` **不是**血缘充分条件，须同时具备同一对输入与同一判据串；'
         '把判据换回裸子串「未证」会多计（`LEAD_LOCK`「Lead 错误 #14」段：S22 16/1194 vs 26/1204，差 **10** 行）。'
         '该互斥表述在 **V540..V544 连续 5 版共存**，V545 起回收'
         '（`_r165/r165a_scope_measure.py` P2.1–P2.11、P2b.1–P2b.8，共 **24 断言 0 FAIL**）。')
new_f35_lim2 = new_f35_lim + ADD35
# 追加段自身**引用**了被撤回的旧措辞（这是必要的引文），故总量会回升 ——
# 正确的判据是分段的：正文前缀里不得再有把三者称为「独立脚本」的断言。
ck('2.4 追加后 F35 limitations 正文前缀段「独立脚本」0 次（改动 1 生效）',
   new_f35_lim.count('独立脚本') == 0, new_f35_lim.count('独立脚本'))
ck('2.4b 追加段自身含 1 次「独立脚本」= 对旧措辞的引文（如实记，不掩盖）',
   ADD35.count('独立脚本') == 1, ADD35.count('独立脚本'))
ck('2.4c 全文合计 1 次「独立脚本」且**只**在引文里',
   new_f35_lim2.count('独立脚本') == 1 and new_f35_lim2.count('独立脚本') == ADD35.count('独立脚本'),
   new_f35_lim2.count('独立脚本'))
ck('2.5 追加后 F35 limitations「不是独立实现」= 1（校正）+ 2（引文/结论）= 3 次',
   new_f35_lim2.count('不是独立实现') == 3, new_f35_lim2.count('不是独立实现'))
ck('2.6 追加段是纯后缀（前 len(new_f35_lim) 字节逐字不变）',
   new_f35_lim2[:len(new_f35_lim)] == new_f35_lim)

ADD29 = ('**【R165 补·一处自指句为假】** 上文（R138 段末）写 R135 审计的「6 个不同桩体」'
         '不在本条正文任何一列，实测在 **V544** 里该串在本行出现 **2 次**（**V545 起 3 次**，'
         '第 3 次就是本段的引文）：statement ④ 1 次'
         '（「是 R135 审计自报的中间数字，**不在本条任何一列**」）、limitations 1 次'
         '（「**不在本条正文任何一列**」），即该自指声明**本身就是那第二处出现** ⇒ '
         '正确措辞是「该数不参与本条任何计数」，而**不是**「不在任何一列」。'
         '判据：全表 54 条逐列扫「不在本条任何一列」型自指，命中**恰 1 行**（F29），'
         '且该行自身即反例（`_r165/r165c_selfref.py` 共 **9 断言 0 FAIL**）。'
         '本条四个比例与族统计一字未改。')
new_f29_lim = f29[4] + ADD29
ck('2.7 F29 statement 逐字节不变（追加只在 limitations）', byid['F29'][1] == f29[1])
ck('2.8 追加后 F29 limitations「不在本条正文任何一列」= 原 1 + 追加段引文 2 = 3 次（如实记）',
   new_f29_lim.count('不在本条正文任何一列') == 3
   and f29[4].count('不在本条正文任何一列') + ADD29.count('不在本条正文任何一列') == 3,
   (f29[4].count('不在本条正文任何一列'), ADD29.count('不在本条正文任何一列'),
    new_f29_lim.count('不在本条正文任何一列')))
# 口径纠正（S-511）：new_f29_lim 只是 limitations 列，行合计须再加 statement 列。
ck('2.8b 追加后 F29「6 个不同桩体」行合计 = statement 1 + limitations 2 = 3 次（V545 实况）',
   new_f29_lim.count('6 个不同桩体') == 2
   and f29[1].count('6 个不同桩体') + new_f29_lim.count('6 个不同桩体') == 3
   and f29[4].count('6 个不同桩体') + ADD29.count('6 个不同桩体') == new_f29_lim.count('6 个不同桩体'),
   (f29[1].count('6 个不同桩体'), f29[4].count('6 个不同桩体'),
    ADD29.count('6 个不同桩体'), new_f29_lim.count('6 个不同桩体')))
ck('2.9 追加段是纯后缀', new_f29_lim[:len(f29[4])] == f29[4])

ADD23 = ('**【R165 补·R159 作用域已过期】** 上文 R159 段自称「逐版扫 13 版（V530–V542）……'
         '首现于 V540、V541/V542 逐字延续」，该测量本身复算成立（13/13 与实测一致，不是虚构）；'
         '但它**只断言了「V539 及以前 0 版命中、首现 V540、V541/V542 延续」这三件事，'
         '没有给出逐版计数** —— 原文段内「每版」「1 次/版」「各 1 次」等逐版计数措辞实测 **0** 次，'
         '故**不得**把「该串每版 1 次」当成 R159 的原话引用（那是读者加的口径，不是原文的断言）。'
         '实测逐版真值：V530–V539 **0** 次、V540–V542 **各 1 次**（仅 statement）、'
         'V543–V544 **各 3 次**（新增两处都在 limitations：R159 段的段头与紧随的引文）、'
         'V545 起 **4 次**（第 4 次是本段引文）⇒ R159 的作用域上限停在 V542，'
         '**不能外推到 V543 及以后**，脱作用域引用会与现版实况相反。'
         '反控：statement 在 V540–V544 逐版恒 **1012** 字符、该串在 statement 恒 **1** 次 ⇒ '
         '增量全部来自 limitations，不是正文改写'
         '（`_r165/r165a_scope_measure.py` P1.1–P1.14 共 **14 断言 0 FAIL**；'
         '口径收窄由跨家族审计员 #385 的 D3 提出，我写 `_r165/r165e_recompute_385.py` 复算采纳，S-513）。')
new_f23_lim = f23[4] + ADD23
ck('2.10 F23 statement 逐字节不变', byid['F23'][1] == f23[1])
# S-517：重写后的追加段不再逐字引该串（改用「该串」指代）⇒ limitations 仍为原 2 次。
ck('2.11 追加后 F23 limitations「12 行分解」仍 = 2 次（追加段用「该串」指代，不重复引字面）',
   new_f23_lim.count('12 行分解') == 2
   and f23[4].count('12 行分解') == 2 and ADD23.count('12 行分解') == 0,
   (f23[4].count('12 行分解'), ADD23.count('12 行分解'), new_f23_lim.count('12 行分解')))
ck('2.11a 行合计 = statement 1 + limitations 2 = 3 次',
   f23[1].count('12 行分解') + new_f23_lim.count('12 行分解') == 3,
   (f23[1].count('12 行分解'), new_f23_lim.count('12 行分解')))
ck('2.11b 【作用域免疫】追加段的三处计数都带版本标（不把当前态写成无标结论）',
   ('V540–V542 **各 1 次**' in ADD23) and ('V543–V544 **各 3 次**' in ADD23)
   and ('V545 起 **4 次**' in ADD23)
   and ('在 **V544** 里该串在本行出现 **2 次**' in ADD29) and ('**V545 起 3 次**' in ADD29),
   'ok')
ck('2.11c 【审计员 #385 D3 收窄已吸收】明写「没给逐版计数」+「不得当成原话引用」，'
   '且「1 次/版」只作为被否定的措辞出现 1 次',
   '没有给出逐版计数' in ADD23 and '不得**把「该串每版 1 次」当成 R159 的原话引用' in ADD23
   and ADD23.count('1 次/版') == 1 and '逐版计数措辞实测 **0** 次' in ADD23,
   (ADD23.count('1 次/版'), '没有给出逐版计数' in ADD23))
ck('2.11d 反控：追加段仍保留「R159 段自称逐版扫 13 版」这半句（不抹掉原文自述）',
   '逐版扫 13 版（V530–V542）' in ADD23, 'ok')
ck('2.12 追加段是纯后缀', new_f23_lim[:len(f23[4])] == f23[4])
ck('2.13 反控：三条追加段互不含对方 fid 的专属串（防复制粘贴串台）',
   ('R159 作用域已过期' not in ADD29) and ('自指句为假' not in ADD23)
   and ('两处措辞的回收' not in ADD23) and ('两处措辞的回收' not in ADD29))

# ---------------------------------------------------------------- 3 · 组装新文件
print()
print('== 3 · 组装 ==')
newlines = list(oldlines)
idx = {r.split('\t')[0]: i for i, r in enumerate(newlines) if r and '\t' in r}
for fid, newval in (('F35', new_f35_lim2), ('F29', new_f29_lim), ('F23', new_f23_lim)):
    i = idx[fid]
    c = newlines[i].split('\t')
    c[4] = newval
    newlines[i] = '\t'.join(c)
newtxt = '\n'.join(newlines)
# 逐行差分：只有三行变化
old_rows = [l.split('\t') for l in oldlines if l]
new_rows = [l.split('\t') for l in newlines if l]
ck('3.0 新旧行数相同 55', len(new_rows) == 55, len(new_rows))
diff = [old_rows[i][0] for i in range(55) if old_rows[i] != new_rows[i]]
ck('3.1 差分行恰 [F23, F29, F35]', sorted(diff) == ['F23', 'F29', 'F35'], diff)
for fid in ('F23', 'F29', 'F35'):
    i = [k for k in range(55) if old_rows[k][0] == fid][0]
    ck('3.2 %s 前三列（1-3）逐字节不变' % fid, old_rows[i][:3] == new_rows[i][:3])
    ck('3.3 %s 第 4 列（evidence_paths）逐字节不变' % fid, old_rows[i][3] == new_rows[i][3])
ck('3.4 其余 51 行 x 5 列逐字节相同',
   all(old_rows[k] == new_rows[k] for k in range(55) if old_rows[k][0] not in ('F23', 'F29', 'F35')))
ck('3.5 新文本无 CR', newtxt.count('\r') == 0, newtxt.count('\r'))
ck('3.6 新文本每行 5 列', all(len(r) == 5 for r in new_rows))
ck('3.7 新总字节 > 旧总字节（纯追加 + 一处净增）', len(newtxt.encode()) > OLD_BYTES,
   (len(newtxt.encode()), OLD_BYTES))

# ---------------------------------------------------------------- 4 · 写盘
print()
print('== 4 · 写盘 ==')
if os.path.exists(V545) and sha(rb(V545)) == sha(newtxt.encode()):
    ck('4.0 幂等：V545 已是终态', True)
else:
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BD, 'FACT_INDEX.tsv.before_r165_v545_%s.bak' % stamp)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(old)
    ck('4.1 备份 wx 独占创建成功', os.path.isfile(bak), bak)
    ck('4.2 备份逐字节等于 V544', sha(rb(bak)) == OLD_SHA, sha(rb(bak)))
    if not os.path.isdir(D545):
        os.makedirs(D545)
    with open(V545, 'wb') as f:
        f.write(newtxt.encode())
    ck('4.3 V545 写盘成功', os.path.isfile(V545))

# ---------------------------------------------------------------- 5 · 回读校验
print()
print('== 5 · 回读校验 ==')
back = rb(V545)
ck('5.1 回读 sha256 与内存构造一致', sha(back) == sha(newtxt.encode()), sha(back))
ck('5.2 回读字节数', len(back) == len(newtxt.encode()), (len(back), len(newtxt.encode())))
ck('5.3 回读无 CR', back.decode('utf-8').count('\r') == 0)
bt = back.decode('utf-8').split('\n')
ck('5.4 回读 55 行', len(bt) == 55, len(bt))
brows = {l.split('\t')[0]: l.split('\t') for l in bt if l}
ck('5.5 回读 F35 limitations「独立脚本」= 1 次且与引文段相同（引文之外为 0）',
   brows['F35'][4].count('独立脚本') == 1
   and brows['F35'][4][:len(new_f35_lim)].count('独立脚本') == 0,
   brows['F35'][4].count('独立脚本'))
ck('5.6 回读 F35 limitations「不是独立实现」3 次', brows['F35'][4].count('不是独立实现') == 3,
   brows['F35'][4].count('不是独立实现'))
ck('5.7 回读 F23 limitations「12 行分解」2 次（行合计 3）',
   brows['F23'][4].count('12 行分解') == 2
   and brows['F23'][1].count('12 行分解') + brows['F23'][4].count('12 行分解') == 3,
   (brows['F23'][1].count('12 行分解'), brows['F23'][4].count('12 行分解')))
ck('5.8 回读 F29 limitations 含追加段', '一处自指句为假' in brows['F29'][4])
ck('5.9 V544 一字未改（sha 仍为钉住值）', sha(rb(V544)) == OLD_SHA, sha(rb(V544)))
ck('5.10 反控：V544 与 V545 不相同', sha(rb(V544)) != sha(back))

res = {'V545_SHA256': sha(back), 'V545_BYTES': len(back), 'FAILS': len(FAILS),
       'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('V545_SHA256=%s' % sha(back))
print('V545_BYTES=%d' % len(back))
print('FAILS=%d' % len(FAILS))
for f in FAILS:
    print('   -', f)
sys.exit(1 if FAILS else 0)
