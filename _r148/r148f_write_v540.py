#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 F：FACT_INDEX v5.39 -> v5.40，只改 F23/F24/F29/F35 四行的 statement 列。

写入纪律：wx 独占备份 -> 断言旧 sha/行数/CR -> 一次性写入 -> 回读校验。
不许改 grade / evidence_paths / fact_id；其余 50 行必须逐字节相同。
"""
import hashlib, io, json, os, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC = os.path.join(R14, 'R17_R111_FACTINDEX_V539', 'FACT_INDEX.tsv')
DSTDIR = os.path.join(R14, 'R17_R112_FACTINDEX_V540')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
BAK = os.path.join(R14, 'R17_LEAD_BASELINE',
                   'FACT_INDEX.tsv.before_R148_v540_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


src = open(SRC, 'rb').read()
ck('1 源 83,637 B', len(src) == 83637, len(src))
ck('2 源 sha256 == ec0a63a4…（v5.39）',
   hashlib.sha256(src).hexdigest() == 'ec0a63a4c7ef9bafde04dad6a52fa58cc3206d080b72689c6f5af3bd4b62f94c',
   hashlib.sha256(src).hexdigest()[:16])
ck('3 源全 LF', b'\r' not in src, src.count(b'\r'))
lines = src.decode('utf-8').split('\n')
ck('4 源 54 数据行 + 末尾空串 = 56 段', len(lines) == 56 and lines[-1] == '', len(lines))

fd = os.open(BAK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(src)
ck('5 备份 wx 独占创建', os.path.exists(BAK))
ck('6 备份逐字节相同', open(BAK, 'rb').read() == src)

TAG = '**【R148 补·'

ADD = {}
ADD['F23'] = (TAG + '两处正文口径】** ① 本条 limitations 的「12 行分解」三个分项 '
              '6 + 2 + 3 之和为 **11**，与 total=12 差 **1 行无归属**；换读法 6+2+3+3 = **14** > 12 '
              '⇒ **两读法都不闭合**，缺口对读法不敏感（`_r148/r148a_verify_facts.py` A1a–A1c，'
              '一个必须为真的反例与一个必须为假的反例各跑一次，3/3 PASS）。'
              '② 本条**全部计数**（458 / 291 / 293 / 1,196 / 12 / 2 / 9 与分母 1,654）依赖 '
              '`coverage.tsv`（4,147,334 B / 18,498 行 / 8 列），该文件**已失**：全库按文件名精确命中 '
              '**0**、按 4,147,334 B 精确字节反查 **0**，`COVERAGE/`、`R17_DELIVERY/`、'
              '`R17_R41_RECOMPUTE/` 三目录均不存在（`_r148/r148a` A2a–A2c + `_r148/r148c` X8c）'
              '⇒ 本机只能证**算术闭合**，**不能重数**底层计数。'
              '③ 现盘清单里该文件的记录数**有两个口径、须带口径引用**：按 basename 精确口径 '
              '**18 条**（主份 1 + 备份 17，17 份字节两两不同）＝ `_r148/r148d_cov_records.py` 13 断言；'
              '按「路径含 /COVERAGE/」口径 **4 条**（主份 1 + `_hygiene` 下 COVERAGE 子目录 3 份）'
              '＝ `_r148/r148e_cov_scope.py` 9 断言；两口径分别闭合、**互不推导**（S2 − S1 = 14）。'
              '故 limitations 里「4 条记录」**只在后一口径成立**，单写「4 条」会被读成总数。')

ADD['F24'] = (TAG + '正文撤下与失效期标注】** ① 「86.19%%」**已从本条正文撤下**（正文现存的一切提及'
              '都是撤回说明本身）：R136 三实现实测 **99.992%%（1,392,481/1,392,592）有字节对应**、'
              '未命中 111 条全部落在前一指令起始 +1..8 内；`bounds` 段**仍剔**，依据改为**结构判据'
              '「单列地址、没有可回原址复核的第二列」** —— 数字错、方向对，两者分开处理，'
              '**不得再把 86.19%% 当作剔除理由**。'
              '② 本条语料值 **4,417 件 / 737,517,286 B 是 2026-11-22 快照值，不是现盘可 stat 到的体量**：'
              '清单 `tier_final_4417.tsv` 的 4,417 行与 sum(bytes) = 737,517,286 可机械复核'
              '（`_r148/r148a` A5a–A5e 五断言、`_r148/r148b_f24_survival.py` 13 断言 0 FAIL），'
              '但按清单 rel 相对 `lead/` 解析，现盘**存在 65 件 / 44,470,975 B**'
              '（其中**字节与清单相同 64 件 / 26,846,620 B**，差 1 件 = `a2_sites.json`：'
              '清单 913,237 vs 现盘 17,624,355，差 **+16,711,118 B 恰为被剔的 `bounds` 段**）、'
              '**不存在 4,352 件 / 709,757,429 B**。'
              '⇒ **引用本值必须同写三项**：「11-22 快照」「相对 `lead/` 根解析」「是否要求字节相同」；'
              '缺「相对 `lead/` 解析」时任何人复算都得 **0 件 / 0 B**（反控实测，`r148b` 断言 10）。')

ADD['F29'] = (TAG + '四处作用域落位正文】** ① 「两份拷贝」= 17 字节序列 '
              '8B44240483C00450FF15C8117E00C20400 在 `.text` **全镜像 80 次**里的两份'
              '（`_r148/r148a` A6a–A6f：逐节切片实测 `.text` **80** 次、其它节 **0** 次、'
              '负控改 1 字节得 **0**），**不可读成「全镜像只有两份」**。'
              '② `FirstThunk idx=62` 是 **DLL 内 0-based** 口径，同址另有**全局 0-based 63**、'
              '**全局 1-based 64**，三口径互不相同，**缺口径即不可引**。'
              '③ 「40」是**字节串出现次数**（8 字节桩序列 B8 01 00 00 00 C2 04 00 全镜像 40 次），'
              '**不是「40 个桩函数」** —— 其中 34 个不参与任何计数、20 个是字节误命中（R141 §2.145）。'
              '④ 「40 次桩体」与「63/77 双槽皆桩」**非因果**：77 mod 40 = 37、77 − 40 = 37，'
              '两者无可推关系、**不得互相印证**；「6 个不同桩体」是 R135 审计自报的中间数字，'
              '**不在本条任何一列**，不采用、不需补作用域。')

ADD['F35'] = (TAG + '定义与输入的分离】** ① `proved_strict` 的**定义在盘、有一手代码权威**：'
              '`RULING_R15_20261119/work/strict_panel.py` 第 78 行 '
              'if "[未证]" not in sem: （**带方括号字面**，嵌套在第 76 行 if grade == "[已证]": 内），'
              '文件头第 14 行给出同一条件的散文措辞；全文 `[未证]` 恰 **2 次**（14 行散文 + 78 行代码）、'
              '代码形态恰 **1 次**（`_r148/r148a` A3a–A3e + `_r148/r148c` X2a–X2f，11 断言）'
              '⇒ R138 那句「**缺一手权威**」**已撤回，不得再写**。'
              '② 另 3 个脚本含同一判据但**不是独立实现**：`_cards/M59-MERGE/precheck.py:60`'
              '（not in sem）、`simulate.py:72` 与 `verify.py:83`（均 not in r[3]，r[3] 即 '
              'one_line_semantics，`verify.py:50` 表头自证）；四者共用同一 `PROJ` 常量与同一对输入，'
              '属**同血缘克隆**，**只能互证判据串、不能当交叉验证**；写入器 `merge_panel.py` '
              '**不含**该判据（反控，`_r148/r148c` X4 实测 0 命中）。'
              '③ 真正失联的是该脚本的**两个输入**：`COVERAGE/coverage.tsv` 与 '
              '`lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv` 均不存在、两父目录亦不存在'
              '（`_r148/r148a` A3f–A3h）。'
              '④ 本条 evidence_paths **5 项里只有 `COVERAGE/PANEL.md` 失联**、其余 4 项在盘'
              '（`_r148/r148c` X6/X6b）⇒ 本条**不再是整行证据链失联项**，与 F23（2/2 全失联，'
              '`_r148/r148c` X5）必须分开表述。')

new_lines = list(lines)
idx = {}
for i, ln in enumerate(lines):
    for fid in ADD:
        if ln.startswith(fid + '\t'):
            idx[fid] = i
ck('7 定位到 4 行', len(idx) == 4, sorted(idx))

for fid, add in ADD.items():
    cols = new_lines[idx[fid]].split('\t')
    ck('%s 行 5 列' % fid, len(cols) == 5, len(cols))
    ck('%s 尚未含本轮标记' % fid, '【R148 补·' not in cols[1])
    cols[1] = cols[1] + ' ' + (add % () if '%%' in add else add)
    new_lines[idx[fid]] = '\t'.join(cols)

out = '\n'.join(new_lines).encode('utf-8')
os.makedirs(DSTDIR, exist_ok=True)
with open(DST, 'wb') as f:
    f.write(out)

back = open(DST, 'rb').read()
ck('8 回读字节增加', len(back) > len(src), (len(src), len(back)))
ck('9 回读全 LF', b'\r' not in back, back.count(b'\r'))
bl = back.decode('utf-8').split('\n')
ck('10 回读仍 56 段', len(bl) == 56 and bl[-1] == '', len(bl))
chg = [i for i, (a, b) in enumerate(zip(lines, bl)) if a != b]
ck('11 恰 4 行变化', len(chg) == 4, len(chg))
ck('12 变化行 == F23/F24/F29/F35', sorted(chg) == sorted(idx[f] for f in ADD),
   sorted(chg))
for fid in ADD:
    o = lines[idx[fid]].split('\t')
    n = bl[idx[fid]].split('\t')
    ck('%s fact_id/grade/evidence 三列逐字节未动' % fid,
       o[0] == n[0] and o[2] == n[2] and o[3] == n[3], (o[2], n[2]))
    ck('%s limitations 列逐字节未动' % fid, o[4] == n[4])
ck('13 其余 50 行逐字节相同',
   all(a == b for i, (a, b) in enumerate(zip(lines, bl)) if i not in chg))
ck('14 fact_id 序列未变', [x.split('\t')[0] for x in bl if x] == [x.split('\t')[0] for x in lines if x])
ck('15 源 v5.39 未被修改', open(SRC, 'rb').read() == src)

# 关键串回读
NEED = {'F23': ['6 + 2 + 3 之和为 **11**', '1 行无归属', 'coverage.tsv', '4,147,334 B', '18 条', '4 条'],
        'F24': ['86.19', '99.992', '4,417 件 / 737,517,286 B', '65 件 / 44,470,975 B',
                '4,352 件 / 709,757,429 B', '相对 `lead/`'],
        'F29': ['80 次', 'DLL 内 0-based', '40 次', '非因果', '37'],
        'F35': ['定义在盘', '第 78 行', '已撤回，不得再写', '同血缘克隆', '只有 `COVERAGE/PANEL.md` 失联']}
for fid, ns in NEED.items():
    for s in ns:
        ck('%s 正文含 %r' % (fid, s[:26]), s in bl[idx[fid]])

print('\n源 %d B -> 新 %d B（+%d B）' % (len(src), len(back), len(back) - len(src)))
print('新 sha256 = %s' % hashlib.sha256(back).hexdigest())
print('备份 = %s' % BAK)
print('=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(dict(fails=fails, src_bytes=len(src), dst_bytes=len(back),
               src_sha=hashlib.sha256(src).hexdigest(),
               dst_sha=hashlib.sha256(back).hexdigest(), bak=BAK),
          open(os.path.join(ROOT, '_r148', 'r148f_write_v540.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
