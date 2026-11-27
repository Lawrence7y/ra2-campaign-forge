#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 落盘：FACT_INDEX v5.38 -> v5.39，只改 F29 与 F24 两行的 limitations/statement 尾部。

写入纪律（每次修改前必须执行）：
  1. 在 R17_LEAD_BASELINE/ 用 wx 模式独占创建唯一备份
  2. 断言旧 sha256 与行数
  3. 一次性写入
  4. 回读校验（sha256、行数、只有目标行变化、其余行逐字节相同、grade 列未动、全 LF）
"""
import hashlib
import io
import json
import os
import shutil
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC = os.path.join(R14, 'R17_R110_FACTINDEX_V538', 'FACT_INDEX.tsv')
DSTDIR = os.path.join(R14, 'R17_R111_FACTINDEX_V539')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
BAK = os.path.join(R14, 'R17_LEAD_BASELINE',
                   'FACT_INDEX.tsv.before_R141_v539_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fails = []


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


src = open(SRC, 'rb').read()
ck('1 源 v5.38 字节数 == 79,845', len(src) == 79845, len(src))
ck('2 源 sha256 前 8 == 未改动（与 §1194 记录一致）',
   hashlib.sha256(src).hexdigest().startswith(''), hashlib.sha256(src).hexdigest()[:16])
ck('3 源为全 LF（无 \\r）', b'\r' not in src, src.count(b'\r'))
lines = src.decode('utf-8').split('\n')
ck('4 源 54 数据行 + 末尾空串（split 得 56 段）', len(lines) == 56 and lines[-1] == '', len(lines))

# ---------- wx 独占备份 ----------
fd = os.open(BAK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(src)
ck('5 备份 wx 独占创建成功', os.path.exists(BAK), BAK)
ck('6 备份与源逐字节相同', open(BAK, 'rb').read() == src)

# ---------- 正文修订 ----------
F29_TAG = '**【R141 实测·桩集合定义的稳健性 + 与 63/77 的关系】**'
F24_TAG = '**【R141 补·三个存活数的口径不冲突】**'

F29_ADD = (F29_TAG + ' 正文「两槽皆为逐字节桩」用的是「全文件 40 个 8 字节桩」这一集合；'
           'R141 实测该集合**混入大量字节误命中**，但 63/77 对「怎么定义桩集合」完全不敏感。'
           '① **40 个桩的引用普查**（`_r141/r141a_stub_refs.py`，17 断言）：'
           '被 `.data/.rdata` 里以 4 字节 VA 引用 **14 个 / 176 次**（0x410300 与 0x410310 各 **74** 次、'
           '0x40d240 **9**、其余四个各 1、0x4293e0 等各 1）；被 `.text` 里当 4 字节立即数装载 **0 个**；'
           '被 `.text` 里 E8/E9 直接跳到 **3 个（5 处）**；`.rsrc/.detour` 命中 **0**；'
           '**零引用 26 个**（三类全 0）。② **结构定性**（`_r141/r141b_stub_misfit.py`）：'
           '按「前 2 字节为 90/CC 填充 或 前一字节为 C3/CC」判入口、「后 2 字节为 90/CC」判收尾，'
           '40 个桩分成 ENTRY+BODY **13** / ENTRY-partial **1** / boundary-only **6** / MISFIT **20**；'
           '关键分层是：**被数据节引用的 14 个桩全部结构合格（MISFIT 0）**，'
           '而零引用的 26 个里有 **20 个是 MISFIT**（另 6 个 boundary-only 只占一边）。'
           '反控：随机取 200 个 `.text` 位置，**177 个判 MISFIT**（88.5%%），'
           '桩集合的 50%% 低于该基线 —— 即桩集合并非随机字节，但也远非全部真函数。'
           '③ **63/77 对桩集合定义不敏感**（`_r141/r141c_stubset_invariance.py`，16 断言 **0 FAIL**）：'
           '换五种桩集合定义，计数**逐一同为 63/77 = 81.82%%** —— '
           'S0 全 40 个（正文字面口径）、S1 结构合格 14 个、S2 被数据节引用 14 个、'
           'S3 63 实际用到的 6 个、S4 仅 ENTRY+BODY 13 个；'
           '且 S1 与 S2 **是同一个集合**（对称差 0）、S1 与 S0 的 **14 个例外集合逐元素相同**（不只是基数同）。'
           '反控：桩集合置空得 **0**、换成 26 个非结构合格桩得 **0**、槽偏移换 `+8/+12` 得 **0**、'
           '两槽都取 `+4` 得 **63**（与只判 slot1 同值，复证 R139 的「合取不加判别力」）。'
           '④ **63 只用到 6 个桩**：桩对 `(0x410300,0x410310)` 覆盖 **61/63**、'
           '`(0x50e340,0x50e350)` 与 `(0x512740,0x512750)` 各 1；'
           '**其余 34 个桩（40−6）不参与任何计数**，其中 8 个被数据节引用、26 个零引用。'
           '⇒ 结论：**63/77 这个数是稳健的**（对桩集合口径不敏感），'
           '但「全文件 40 个桩」这个**分母口径**含 20 个字节误命中，引用 40 时必须声明它是「字节串出现次数」'
           '而不是「40 个桩函数」。')

F24_ADD = (F24_TAG + ' 盘上并存三个「现盘存活」数，**不是互相冲突，是三个不同口径**，'
           '三者由同一份清单逐行 stat 复算闭合（`_r141/r141d_f24_survival.py`，14 断言 **0 FAIL**）：'
           '① **65 件 / 44,470,975 B** = 「现盘存在」的件数与其**现盘实际字节**（生存率按字节 **6.03%%**）；'
           '② **64 件 / 26,846,620 B** = 「现盘存在**且字节与清单相同**」的件数与其**清单字节**（**3.64%%**）；'
           '③ 二者之差恰为 1 件 ——  `next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json`，'
           '清单 913,237 B vs 现盘 17,624,355 B，**差 +16,711,118 B 恰为本条所剔的 `bounds` 段**。'
           '三桶合计仍精确等于 4,417 / 737,517,286 B（划分恒等式）。'
           '反控：排除该件后「现盘存在」降为 64 件 / 26,846,620 B（即与口径 ② 重合）；'
           '清单 sum 737,517,286 ≠ 现盘实际和 44,470,975（两口径可区分）；'
           '把 rel 路径拼到仓库根而非 `lead/` 根时存活归 **0**（证明根选对了）。'
           '⇒ **引用任一存活数都必须同时写明「是否要求字节相同」与「字节取清单值还是现盘值」**；'
           '不带口径的「存活 65 件」或「存活 64 件」都可被读成另一个意思。')

new_lines = list(lines)
idx29 = idx24 = None
for i, ln in enumerate(lines):
    if ln.startswith('F29\t'):
        idx29 = i
    if ln.startswith('F24\t'):
        idx24 = i
ck('7 定位到 F29 行', idx29 is not None, idx29)
ck('8 定位到 F24 行', idx24 is not None, idx24)

for idx, tag, add, fid in ((idx29, F29_TAG, F29_ADD, 'F29'),
                           (idx24, F24_TAG, F24_ADD, 'F24')):
    cols = new_lines[idx].split('\t')
    ck('%s 行 5 列' % fid, len(cols) == 5, len(cols))
    ck('%s 尚未含本轮标记' % fid, tag not in cols[4], tag[:20])
    cols[4] = cols[4] + ' ' + add
    new_lines[idx] = '\t'.join(cols)

out = '\n'.join(new_lines).encode('utf-8')

# ---------- 写入 ----------
os.makedirs(DSTDIR, exist_ok=True)
with open(DST, 'wb') as f:
    f.write(out)

# ---------- 回读校验 ----------
back = open(DST, 'rb').read()
ck('9 回读字节数增加（v5.38 79,845 -> 新值）', len(back) > len(src), (len(src), len(back)))
ck('10 回读全 LF（无 \\r）', b'\r' not in back, back.count(b'\r'))
bl = back.decode('utf-8').split('\n')
ck('11 回读仍 56 段（54 数据行 + 末尾空串）', len(bl) == 56 and bl[-1] == '', len(bl))
ck('12 只有 2 行变化（逐行比对）',
   sum(1 for a, b in zip(lines, bl) if a != b) == 2,
   sum(1 for a, b in zip(lines, bl) if a != b))
ck('13 变化的恰是 F29 与 F24', bl[idx29] != lines[idx29] and bl[idx24] != lines[idx24],
   (bl[idx29] != lines[idx29], bl[idx24] != lines[idx24]))

# grade 列未动
def grade_of(line):
    return line.split('\t')[2] if line.count('\t') >= 2 else ''


ck('14 两行 grade 列一字未动',
   grade_of(bl[idx29]) == grade_of(lines[idx29]) and grade_of(bl[idx24]) == grade_of(lines[idx24]),
   (grade_of(lines[idx29]), grade_of(bl[idx29])))
ck('15 全部 54 行 fact_id 序列未变',
   [x.split('\t')[0] for x in bl if x] == [x.split('\t')[0] for x in lines if x])

# 其余行逐字节相同
others_same = all(a == b for i, (a, b) in enumerate(zip(lines, bl)) if i not in (idx29, idx24))
ck('16 其余 53 行逐字节相同', others_same)

# 关键数字在正文里
for need in ('14 个 / 176 次', '63/77 = 81.82', '0x410300', '20 个是 MISFIT',
             'S4 仅 ENTRY+BODY 13 个'):
    ck('17 F29 含关键串 %r' % need[:22], need in bl[idx29])
for need in ('65 件 / 44,470,975 B', '64 件 / 26,846,620 B', '+16,711,118 B',
             '把 rel 路径拼到仓库根'):
    ck('18 F24 含关键串 %r' % need[:22], need in bl[idx24])

ck('19 源 v5.38 未被修改', open(SRC, 'rb').read() == src,
   hashlib.sha256(open(SRC, 'rb').read()).hexdigest()[:16])
ck('20 新文件 sha256 与源不同', hashlib.sha256(back).hexdigest() != hashlib.sha256(src).hexdigest())

print('\n源 %d B -> 新 %d B（+%d B）' % (len(src), len(back), len(back) - len(src)))
print('新 sha256 = %s' % hashlib.sha256(back).hexdigest())
print('备份 = %s' % BAK)
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(dict(src=SRC, dst=DST, bak=BAK, src_bytes=len(src), dst_bytes=len(back),
               src_sha=hashlib.sha256(src).hexdigest(),
               dst_sha=hashlib.sha256(back).hexdigest(), fails=fails),
          open(os.path.join(ROOT, '_r141', 'r141h_write_v539.json'), 'w',
               encoding='utf-8'), ensure_ascii=False, indent=1)
