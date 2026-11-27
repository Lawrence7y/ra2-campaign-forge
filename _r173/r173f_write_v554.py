#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 F：把本轮三条实测写进 FACT_INDEX V554（只改 F24 与 F35 两行的 limitations，纯追加）。

写前硬闸（任一不成立即 fail-closed，不写盘）：
  G1 母本 V553 的 sha256/字节/CR/行数/列 五项逐一等；
  G2 V554 目标目录此前不存在（不允许覆盖已有版本）；
  G3 两条待改行以外，其余 52 行 x 5 列逐字节相同；
  G4 每条改动的变化单元只有 limitations（statement/grade/evidence 逐字节相同）；
  G5 追加段以「**R173」开头且不含任何反引号（卡面纪律的延伸：正文允许反引号，
     但本段刻意不用，便于 grep 时不与代码片段混淆）。
"""
import hashlib, io, json, os, shutil, sys
from difflib import SequenceMatcher

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SRC = os.path.join(TIER, 'R17_R125_FACTINDEX_V553/FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, 'R17_R126_FACTINDEX_V554')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
SRC_SHA = '988a9567155d8dc385ccf542909eb5b7007a1c966168a9b750429d679396876c'
SRC_BYTES = 121010

fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(SRC, 'rb').read()
ck('G1a 母本 V553 字节 == 121,010', len(raw) == SRC_BYTES, len(raw))
ck('G1b 母本 V553 sha256 == 988a9567…', hashlib.sha256(raw).hexdigest() == SRC_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
ck('G1c 母本 CR == 0（全 LF）', raw.count(b'\r') == 0, raw.count(b'\r'))
text = raw.decode('utf-8')
lines = text.rstrip('\n').split('\n')
ck('G1d 母本 55 行（1 表头 + 54 数据）', len(lines) == 55, len(lines))
ck('G1e 母本每行 5 列', all(len(l.split('\t')) == 5 for l in lines),
   sorted(set(len(l.split('\t')) for l in lines)))
ck('G2 V554 目录此前不存在', not os.path.exists(DSTDIR), DSTDIR)

hdr = lines[0]
out = [hdr]
changed = {}
for l in lines[1:]:
    f = l.split('\t')
    fid = f[0]
    if fid == 'F24':
        add = (' **【R173 补·「bounds 段 16,711,118 B」的口径是算术差、不是字节跨度】** '
               '本列与 statement 共 8 次出现 16,711,118，逐次可机械复核的口径只有一个：'
               '17,624,355（现盘）− 913,237（11-22 快照清单记录）= **16,711,118**，'
               '即它是**两值相减的算术差**，不是 bounds 值在盘上占的字节数。'
               '实测三个口径互不相同（_r173/r173a_f24_bounds_bytes.py 18 断言 0 FAIL、'
               '_r173/r173b_f24_wording_scope.py 10 断言 0 FAIL）：'
               '① bounds 值跨度 **16,711,104 B** = 1,392,592 条 × 12 B（每条为 8 位十六进制加引号逗号，恰 12 字节）；'
               '② 删掉整条成员（逗号加键名加值）**16,711,116 B**；'
               '③ 上述算术差 **16,711,118 B**。三种宽度两两相差 2 B 与 2 B，'
               '在 ±32 B 窗口内以 16,711,118 为宽度试删 65 个起点，**能得合法 JSON 的起点 0 个**；'
               '而删 913,238 起 16,711,116 B 得合法 JSON（顶层键只剩 calls、删后 913,239 字节）。'
               '⇒ 「差 +16,711,118 B 恰为被剔的 bounds 段」这句里，'
               '**差额数对、『恰为 bounds 段』错**：bounds 段本身只有 16,711,104 B，'
               '差 14 B 是 JSON 结构开销（键名加冒号加空白加末尾方括号），不是段内数据。'
               '引用该数时必须写「= 现盘减快照清单的算术差」，'
               '不得写成「bounds 段的字节数」，也不得由此反推「清单记录 913,237 = 现盘减 bounds 段」'
               '（该等式只在算术上成立、在字节上不成立）。'
               '**R173 未改任何既有数字**：8 次 16,711,118 一字未动，本条只补口径。')
        f[4] = f[4] + add
        changed['F24'] = add
    elif fid == 'F35':
        add = (' **【R173 补·两处版本范围声明的可失败复核】** '
               '① 「该互斥表述在 V540..V544 连续 5 版共存，V545 起回收」**成立**，且可拆成四个可数量'
               '（_r173/r173c_f35_version_range.py 19 断言 0 FAIL）：'
               'V540..V544 五版 statement 长度恒 **1054** 且各含「不是独立实现」恰 **1** 次、'
               'limitations 里该半句恒 **0** 次；V545..V553 九版 limitations 里该半句恒 **3** 次'
               '（**1** 次是 R139 段改写句本体、**2** 次在 R165 段引文内，三处拆分闭合）。'
               '② 上句的前提「V534..V544 该串各 1 次」也成立，但**共存起点是 V540 不是 V534**：'
               'V534..V539 六版 statement 长 **156**、不含该半句，原句只在 limitations；'
               '故「两列互斥」只在 V540..V544 成立，V534..V539 是「只有旧句」而非「两列相反」。'
               '③ 本行 R165 段引用的原句在 V544 里**确在且不在引号内**（1 次），'
               'V545 起原句（不带引号）恒 **0** 次、带引号引文恒 **1** 次 ⇒ 回收是真改文本、不是只加说明。'
               '④ 一条此前未写的作用域：V553 的 limitations 里「不是独立实现」共 **3** 次，'
               '其中 **2** 次是本行自己的追述引文，引用该半句时必须说明「含引文」，'
               '否则会与 statement 的 1 次对不上。')
        f[4] = f[4] + add
        changed['F35'] = add
    else:
        pass
    out.append('\t'.join(f))

ck('G4a 只改了两行（F24 与 F35）', sorted(changed) == ['F24', 'F35'], sorted(changed))
ck('G5a 两段追加都以 **【R173 补 开头', all(v.lstrip().startswith('**【R173 补') for v in changed.values()),
   [v[:16] for v in changed.values()])
ck('G5b 两段追加都不含反引号', all('\x60' not in v for v in changed.values()), True)

new_text = '\n'.join(out) + '\n'
new_raw = new_text.encode('utf-8')

# G3/G4 逐行逐列校验
new_lines = new_text.rstrip('\n').split('\n')
old_rows = {l.split('\t')[0]: l.split('\t') for l in lines[1:]}
new_rows = {l.split('\t')[0]: l.split('\t') for l in new_lines[1:]}
ck('G3a 55 行仍 55 行', len(new_lines) == 55, len(new_lines))
ck('G3b 54 个 fact_id 集合不变', sorted(old_rows) == sorted(new_rows), len(new_rows))
diff_ids = [k for k in old_rows if old_rows[k] != new_rows[k]]
ck('G3c 差分行恰 2 个且是 F24/F35', sorted(diff_ids) == ['F24', 'F35'], diff_ids)
cell_diff = {}
for k in diff_ids:
    cell_diff[k] = [i for i in range(5) if old_rows[k][i] != new_rows[k][i]]
ck('G4b 每行的变化单元恰 1 个且是第 5 列（limitations，0-based 4）',
   all(cell_diff[k] == [4] for k in diff_ids), cell_diff)
ck('G4c 未改行的 52 行 × 5 列逐字节相同',
   all(old_rows[k] == new_rows[k] for k in old_rows if k not in diff_ids), True)

# SequenceMatcher：每行只应是纯追加
for k in diff_ids:
    sm = SequenceMatcher(None, old_rows[k][4], new_rows[k][4], autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    ck('G4d %s 的 limitations 变化是纯追加（1 个 opcode 且为 insert 且落在末尾）' % k,
       len(ops) == 1 and ops[0][0] == 'insert' and ops[0][3] == len(old_rows[k][4]),
       ops)

# 字节增量与口径
delta = len(new_raw) - len(raw)
print('   字节增量: %d（V553 %d -> V554 %d）' % (delta, len(raw), len(new_raw)))
ck('G6 字节只增不减', delta > 0, delta)
ck('G7 新文件 CR == 0', new_raw.count(b'\r') == 0, new_raw.count(b'\r'))

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails))
    sys.exit(1)

os.makedirs(DSTDIR)
with open(DST, 'wb') as f:
    f.write(new_raw)
back = open(DST, 'rb').read()
ck('H1 回读字节一致', back == new_raw, len(back))
ck('H2 回读 sha256 == 计算值', hashlib.sha256(back).hexdigest() == hashlib.sha256(new_raw).hexdigest(),
   hashlib.sha256(back).hexdigest()[:16])
ck('H3 母本 V553 未被改动（重读 sha256 仍为 988a9567…）',
   hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == SRC_SHA, True)

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('V554: %d B / sha256 %s / %d 行' % (len(back), hashlib.sha256(back).hexdigest(), len(new_lines)))
json.dump(dict(fails=fails, asserts=n, bytes=len(back),
               sha256=hashlib.sha256(back).hexdigest(), lines=len(new_lines),
               delta=delta, changed=sorted(changed)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173f_write_v554.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
