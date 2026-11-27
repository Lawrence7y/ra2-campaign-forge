#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 I：落盘 FACT_INDEX v5.41 -> v5.42（只追加，不动 grade / evidence_paths）。

本轮改两行：
  F08 limitations：补「R149 的 33 个锚点判据在 F08 这一项上结构上不可能失败」的
      可机械复核记录（原锚点 0x449440 + a′ 两个全在 §1064 内；a–e 三地址 §1064 内 0 次；
      ANCHOR 表 12 条里 10 条含 statement 里没有的词）。
  F23 limitations：补「R41_RECOMPUTE 三件曾在册（字节 + mtime 可机械反查）」，
      把「已失」的措辞从「可能从未存在」改成可区分两态。

纪律：wx 独占备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验；
      每条追加段先判是否已存在（S-378 幂等）。
"""
import hashlib
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
V541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')
V542DIR = os.path.join(D, 'R17_R114_FACTINDEX_V542')
V542 = os.path.join(V542DIR, 'FACT_INDEX.tsv')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')

EXPECT_BYTES = 90976
EXPECT_SHA = 'f31c8fdc7e962439f7323b784f447277df03dfb7daa33bd9d262fb3fb57a17ea'

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


raw = open(V541, 'rb').read()
ck('v5.41 字节 = 90,976', len(raw) == EXPECT_BYTES, len(raw))
ck('v5.41 sha = f31c8fdc…', hashlib.sha256(raw).hexdigest() == EXPECT_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
ck('v5.41 全 LF（CR=0）', raw.count(b'\r') == 0, raw.count(b'\r'))

rows = raw.decode('utf-8').split('\n')
ck('v5.41 段数 56（含末尾空串）', len(rows) == 56, len(rows))
data = [l for l in rows if l.strip()]
ck('v5.41 数据行 54 + 表头 1 = 55 非空', len(data) == 55, len(data))

F08_ADD = (
    '**【R153 补·本项判据的鉴别力边界】** R149 §1204 一 的「锚点逐字命中」判据在本项上'
    '**结构上不可能失败**，必须与命中结论一起引用：该判据对 F08 只取 `0x449440` 与 `a′` '
    '两个 token（`_r146/r149a_lostpath.py` 的 ANCHOR 表），两者都在台账 §1064 内 ⇒ 恒真；'
    '而 F08 真正要证明的 a–e 三个地址 `0x47C3D0` / `0x6F322F` / `0x6F2B40` 在 §1064 '
    '**全节（含事项 1–6）各 0 次**，只在 `R14_COMMON` §2.9 一 内有（各 1 次）'
    '（`_r153/r153c` / `r153e` / `r153g`，共 17 断言）。⇒ 把这三个地址并入锚点后立即出现 '
    '**3 个未命中**。另：该 ANCHOR 表 12 条里有 **10 条**含 statement 里根本不出现的词'
    '（如 F13 的 `modrm`、F11 的 `双口径`），故「锚点取自 statement 自身」这句只能理解为'
    '**取意**、不能理解为**机械导出**；且「33 个锚点」的 33 只在「空格与 + 都拆、'
    '方括号串不拆」这一拆词口径下成立（原样 27 / 只拆空格 29 / 空格+加号 34），'
    '**引用该数必须同写拆词口径**（`_r153/r153g` 第一部分 5 断言、`r153h` A1 3 断言）。'
)

F23_ADD = (
    '**【R153 补·「已失」要分两态】** 上句「三目录均不存在」只证**现在不在**，'
    '不证**从未存在**；两态已可机械区分：11-22 快照 `files_tier_A_snap2.tsv` '
    '（2,351,479 B / 数据行 24,723）在册 `R17_R41_RECOMPUTE` **三件**——'
    '`REPORT.md` **11,824 B** @2026-11-21T11:54:25Z、`crosscheck.json` **1,864 B** '
    '@11:54:38Z、`numbers.tsv` **2,289 B** @11:54:34Z（合计 **15,977 B**），'
    '三条 mtime 都落在 R41 之后、快照之前；同清单 `COVERAGE/coverage.tsv` 主份 '
    '**4,147,334 B** @2026-11-21T04:56:21Z 一并可反查（路径含 `/COVERAGE/coverage.tsv` '
    '的记录共 **4** 条 = 主份 1 + `_hygiene` 备份 3，与 statement ③ 的两口径一致）。'
    '反控：11,824 B 在快照内**唯一**（排除改名存活）；自造串 0 命中'
    '（`_r153/r153e` 8 断言）。⇒ **正确措辞是「曾在册、内容不可读」，不是「可能从未存在」**；'
    '本条的计数仍**不可重数**，结论不变、理由要照此写。'
    '另：快照行数存在两口径（`split("\\n")` 非空 24,724 含表头 / 数据行 24,723），'
    '**引用必须带口径**。'
)


def patch(rows, fid, add):
    out, hit = [], False
    for l in rows:
        if not l.strip():
            out.append(l)
            continue
        f = l.split('\t')
        if f[0] == fid:
            hit = True
            ck('%s 追加段幂等（尚未存在）' % fid, add[:40] not in f[4])
            f[4] = f[4] + add
            ck('%s 追加后 limitations 变长' % fid, len(f[4]) > 0)
            out.append('\t'.join(f))
        else:
            out.append(l)
    ck('%s 命中 1 行' % fid, hit)
    return out


new_rows = patch(rows, 'F08', F08_ADD)
new_rows = patch(new_rows, 'F23', F23_ADD)
new_txt = '\n'.join(new_rows)
new_raw = new_txt.encode('utf-8')

ck('新文件全 LF（CR=0）', new_raw.count(b'\r') == 0, new_raw.count(b'\r'))
ck('新文件段数与旧一致（只换行内内容）', len(new_rows) == len(rows), (len(new_rows), len(rows)))
new_data = [l for l in new_rows if l.strip()]
ck('数据行数仍 54 + 表头', len(new_data) == 55, len(new_data))

# 逐行比对：只有 F08 / F23 变化
old_map = {l.split('\t')[0]: l for l in rows if l.strip()}
new_map = {l.split('\t')[0]: l for l in new_rows if l.strip()}
ck('fact_id 集合不变', set(old_map) == set(new_map), len(new_map))
changed = [k for k in old_map if old_map[k] != new_map[k]]
ck('只有 F08 与 F23 两行变化', sorted(changed) == ['F08', 'F23'], changed)
for k in sorted(changed):
    o = old_map[k].split('\t')
    n = new_map[k].split('\t')
    diffs = [i for i in range(5) if o[i] != n[i]]
    ck('%s 只动第 5 列（limitations）' % k, diffs == [4], diffs)
    ck('%s grade / evidence_paths 未动' % k, o[2] == n[2] and o[3] == n[3])

# 其余 52 行逐字节相同
same = [k for k in old_map if k not in changed]
ck('其余 52 行逐字节相同',
   all(old_map[k].encode('utf-8') == new_map[k].encode('utf-8') for k in same), len(same))

sha_new = hashlib.sha256(new_raw).hexdigest()
print('\nv5.42 = %d B / sha256 %s' % (len(new_raw), sha_new))

# 落盘
os.makedirs(V542DIR, exist_ok=True)
ck('v5.42 目标文件尚不存在（不覆盖）', not os.path.exists(V542))
bak = os.path.join(BAKDIR, 'FACT_INDEX_V541.before_r153_%s.bak'
                   % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('备份 wx 独占创建', os.path.exists(bak), os.path.basename(bak))
ck('备份与 v5.41 逐字节相同', open(bak, 'rb').read() == raw)

with open(V542, 'wb') as f:
    f.write(new_raw)
ck('v5.42 回读一致', open(V542, 'rb').read() == new_raw)
back = open(V542, 'rb').read()
ck('v5.42 回读 sha 一致', hashlib.sha256(back).hexdigest() == sha_new)
ck('v5.42 回读 CR=0', back.count(b'\r') == 0)

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
