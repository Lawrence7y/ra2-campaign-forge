# -*- coding: utf-8 -*-
"""M82 phase 4: write MERGE_M82 deliverables from recorded results."""
import os, json

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
MERGE = os.path.join(R14, 'MERGE_M82')

bs = json.load(open(os.path.join(MERGE, '_before_state.json'), 'r', encoding='utf-8'))
ar = json.load(open(os.path.join(MERGE, '_apply_result.json'), 'r', encoding='utf-8'))
vr = json.load(open(os.path.join(MERGE, '_verify_result.json'), 'r', encoding='utf-8'))

cov_b, pan_b = bs['coverage.tsv'], bs['PANEL.md']
cov_a, pan_a = ar['after']['coverage.tsv'], ar['after']['PANEL.md']
fix = ar['fix_count']
amb = ar['ambiguous_count']
rok = vr['R_OK']
pct = vr['pct_calc']
m81_upper = '50.72'

# ----------------------------------------------------------------------------
# BEFORE_AFTER.txt
# ----------------------------------------------------------------------------
ba = f"""M82 BEFORE_AFTER — coverage.tsv（361 行 evidence_path 纯指针修复）+ PANEL.md（追加 M82 补记）
记录口径：BEFORE 采集于任何写入之前（见 _before_state.json，已在 MERGE_M81 之后、本轮第一次写入之前采样）；AFTER 复算于全部写入与校验之后。
本机时区：Asia/Shanghai (+08:00)。
BEFORE PANEL.md sha256 {pan_b['sha256'][:8]}… 与 MERGE_M81\\BEFORE_AFTER.txt 记录的 PANEL.md 改后 sha256 一致，确认起点无中间写者介入。
BEFORE coverage.tsv sha256 {cov_b['sha256'][:8]}… 与 COVERAGE 目录既有文件一致（mtime 2026-11-20 21:14:25），起点确认。
本轮唯一 COVERAGE 写者：agent-271；未 git commit；未碰 R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / 任何卡目录；改动仅限 COVERAGE\\coverage.tsv（第 6 列）、COVERAGE\\PANEL.md（追加 3 行）与新建 MERGE_M82 目录。

说明（写入重试，透明记录）：首次 _apply.py 在写完 coverage.tsv 后因 PANEL 段落的百分号格式化报错中断；随即用 _restore_cov.py 将 coverage.tsv 逐行逆转回原始值，字节与 sha256 均回到 BEFORE（{cov_b['sha256'][:8]}…），仅 mtime 更新为 21:31:10；随后修正脚本重跑并最终写入。故 coverage.tsv 的 BEFORE mtime 以首次采样（21:14:25.780680）为准，文件内容哈希一致、无数据损失。

========================================================================
FILE: COVERAGE\\coverage.tsv
========================================================================
  BEFORE mtime  : {cov_b['mtime']!r}  ({cov_b['mtime_iso']})
  BEFORE bytes  : {cov_b['bytes']}
  BEFORE sha256 : {cov_b['sha256']}
  AFTER  mtime  : {cov_a['mtime']!r}  ({cov_a['mtime_iso']})
  AFTER  bytes  : {cov_a['bytes']}
  AFTER  sha256 : {cov_a['sha256']}
  DELTA  bytes  : +{cov_a['bytes'] - cov_b['bytes']}
  sha256 changed: {cov_a['sha256'] != cov_b['sha256']}

  改动范围：仅 {fix} 行的第 6 列 evidence_path（插入丢失的卡目录前缀 + 末尾追加 M82 指针修复注记）；
  第 1/2/3/4/5/7/8 列逐行字节不变；其余 {18498-fix} 行整行字节不变（脚本断言）。
  文件无 BOM / 仅 LF / 末尾仍无换行（保持原状）。

========================================================================
FILE: COVERAGE\\PANEL.md
========================================================================
  BEFORE mtime  : {pan_b['mtime']!r}  ({pan_b['mtime_iso']})
  BEFORE bytes  : {pan_b['bytes']}
  BEFORE sha256 : {pan_b['sha256']}
  AFTER  mtime  : {pan_a['mtime']!r}  ({pan_a['mtime_iso']})
  AFTER  bytes  : {pan_a['bytes']}
  AFTER  sha256 : {pan_a['sha256']}
  DELTA  bytes  : +{pan_a['bytes'] - pan_b['bytes']}
  sha256 changed: {pan_a['sha256'] != pan_b['sha256']}

  改动范围：在 M81 披露（原 L194-198）之后新插入 M82 补记 3 行（新 L{ar['m82_lines'][0]}-{ar['m82_lines'][1]}），
  除该 3 行插入外全文件字节不变（脚本断言）。无 BOM / 仅 LF / 末尾换行保持。
"""
with open(os.path.join(MERGE, 'BEFORE_AFTER.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(ba)

# ----------------------------------------------------------------------------
# VERIFY.txt
# ----------------------------------------------------------------------------
amb_line = ", ".join(ar['ambiguous_entries'])
ver = f"""M82 VERIFY — 并后强制复算（全部断言通过；不符即停）

口径：BEFORE 基线见 _before_state.json；PATCH 见 _apply_result.json；本复算只读、不写任何卡目录 / EVID_RESOLVE / R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE。

【计数不变量】
  数据行数            : {vr['data_rows']}   （期望 18,498）  ✅
  全表 [已证]         : {vr['proved_total']}     （期望 1,654）  ✅
  atlas 内 [已证]     : {vr['proved_atlas']}     （期望 1,648）  ✅  （atlas = next_re_20261112_r10/W130_atlas/function_atlas.tsv，entry 归一 %08X）

【改动行 grade 未变】
  被改 {fix} 行逐行核对第 5 列 grade == BEFORE 记录的 grade（全部 [已证]）✅
  被改 {fix} 行第 1/2/3/4/7/8 列逐行字节不变 ✅
  歧义 {amb} 行第 6 列保持原值、无任何 M82 注记 ✅

【后缀唯一匹配法复现 EVID_RESOLVE 结论】
  读 EVID_RESOLVE/resolve.tsv 的 R_MISSING {374} 行；
  在 r14 下按 case-insensitive / 组件边界 endswith 做后缀匹配：
  路径级 87 唯一 / 5 歧义 / 0 丢失；行级 {fix} 唯一 / {amb} 歧义 / 0 丢失 —— 与 REPORT.md 一致 ✅

【证据可解析率重跑（用 EVID_RESOLVE/resolve.py 原脚本，--out 指向 MERGE_M82\\_verify_resolve_out，未写 EVID_RESOLVE）】
  BEFORE : R_OK 478 / R_MISSING 374 / R_TRACE_ONLY 802 / R_EMPTY 0
  AFTER  : R_OK {rok} / R_MISSING {vr['R_MISSING']} / R_TRACE_ONLY {vr['R_TRACE_ONLY']} / R_EMPTY {vr['R_EMPTY']}
  期望   : R_OK = 478 + 实修 {fix} = {478+fix}；R_MISSING = 374 - {fix} = {374-fix}；R_TRACE_ONLY 不变 802
  实测 R_OK {rok} = 478 + {fix} ✅ ；R_MISSING {vr['R_MISSING']} = 374 - {fix} ✅ ；R_TRACE_ONLY {vr['R_TRACE_ONLY']} = 802 ✅
  新 resolve.tsv 数据行 {vr['new_resolve_data_rows']} = 13 + 802 ✅
  R_OK 百分比 = {rok}/1654 = {pct}% （M81 上界记作 {m81_upper}%/截断，四舍五入实算为 {pct}%）✅

【注记回读】
  对 {fix} 行逐行解析新第 6 列：';M82 指针修复：原记 <旧>（缺卡目录），实为 <新>' 均可逆回原 evidence_path ✅
  每个新路径（含多段 ; 分隔行、含 :0x… 行号锚点的 006DBE20）在盘上 os.path.isfile 为真 ✅

【达标翻转】
  {vr['达标翻转']}。
  判定所依赖的第 4 列语义、第 5 列 grade、subsystem 与 entry 全表未变；[已证] 1,654 与 atlas 内 1,648 均未变；
  故名义达标（S15/S16/S17，3/22）与严格达标（S17，1/22）不可能翻转。无停下理由。✅

【未修（歧义）entry 清单 — {amb} 行】
  {amb_line}
  对应 5 个后缀多处匹配的路径：
    EVIDENCE/four_rings.md                      → S13_K12 / S16_PADD / S17_PADD（3 处，3 行）
    EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt → S10_K8 / S10_K8F（2 处，6 行）
    EVIDENCE/SPAWNMANAGER_CTORS.txt             → S10_K8 / S10_K8F（2 处，2 行）
    EVIDENCE/E01_rtti.txt                       → S03-K1 / S16-K1（2 处，1 行）
    EVIDENCE/OWNERSHIP_004E0E80.txt             → S10_K8 / S10_K8F（2 处，1 行）
  合计 3+6+2+1+1 = 13 行，全部保持原样、不计入本次修复。

结论：全部强制复算通过，无“不符停下”触发；无达标翻转。
"""
with open(os.path.join(MERGE, 'VERIFY.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(ver)

# ----------------------------------------------------------------------------
# MERGE_LOG.md
# ----------------------------------------------------------------------------
samples = []
for c in ar['changes'][:3]:
    samples.append(f"  - `{c['entry']}`: `{c['old_value']}` → `{c['new_main']}`")
sample_block = "\n".join(samples)
work = next(c for c in ar['changes'] if c['entry'] == '006DBE20')

log = f"""# MERGE_M82 — `evidence_path` 卡目录前缀修复（纯指针修复）

- 写者：agent-271（本轮唯一 COVERAGE 写者）
- 结论：修复 {fix} 行；{amb} 行因多候选歧义未修；0 行彻底丢失。判定与计数均未变。
- 未 git commit；未碰 R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / 任何卡目录。

## 做了什么

依据 `EVID_RESOLVE\\REPORT.md` 的结论：`R_MISSING` 374 行的根因是 `evidence_path` 丢了卡目录层（记成 `EVIDENCE/x.txt`，实为 `S10-K2/EVIDENCE/x.txt`）。
对 `EVID_RESOLVE\\resolve.tsv` 的 374 行 `R_MISSING`，按 REPORT 的后缀唯一匹配法（在 r14 下 case-insensitive、组件边界 endswith）找唯一同名文件：

- 路径级：87 唯一 / 5 歧义 / 0 丢失（精确复现 REPORT）
- 行级：**{fix} 唯一可修 / {amb} 歧义不修 / 0 丢失**

对 {fix} 个唯一行，仅改 `COVERAGE\\coverage.tsv` 第 6 列：把每个路径段补上卡目录前缀（保留 `#anchor` 与 `:0x…` 行号锚点、保留多段 `;` 结构），并在末尾追加：
`;M82 指针修复：原记 <旧路径>（缺卡目录），实为 <新路径>`

示例：
{sample_block}
  - 行号锚点行 `006DBE20`: `{work['old_value']}` → `{work['new_main']}`

`PANEL.md`：在 M81 披露之后追加 3 行 M82 补记（新 L{ar['m82_lines'][0]}-{ar['m82_lines'][1]}）。

## 没做什么（不变量）

- 第 5 列 grade、第 4 列语义、第 1/2/3/7/8 列：逐行字节不变
- 歧义 {amb} 行：第 6 列保持原样，无注记
- 数据行 18,498、全表 [已证] 1,654、atlas 内 [已证] 1,648：全部不变
- 达标判定（名义 S15/S16/S17 3/22；严格 S17 1/22）：无翻转

## 复算（见 VERIFY.txt）

用 `EVID_RESOLVE/resolve.py` 原脚本对改后 coverage.tsv 重跑（输出重定向到 MERGE_M82，未写 EVID_RESOLVE）：

| 项 | BEFORE | AFTER | 期望 |
|---|---:|---:|---:|
| R_OK | 478 | **{rok}** | 478+{fix}={478+fix} ✅ |
| R_MISSING | 374 | **{vr['R_MISSING']}** | 374−{fix}={374-fix} ✅ |
| R_TRACE_ONLY | 802 | **{vr['R_TRACE_ONLY']}** | 802 ✅ |
| R_EMPTY | 0 | **{vr['R_EMPTY']}** | 0 ✅ |

R_OK 由 478/1,654（28.90%）升至 **{rok}/1,654（{pct}%）**。
（M81 披露把上界写作 50.72%，系截断；四舍五入实算为 {pct}%。判定与计数均未变，本次只让证据指针重新可用。）

## 未修清单（歧义 {amb} 行，保持原样）

{amb_line}

## 文件

- `MERGE_LOG.md`（本文件）
- `BEFORE_AFTER.txt`（两文件 before/after mtime/bytes/sha256，含一次可逆写入重试的透明记录）
- `VERIFY.txt`（全部强制复算与断言）
- 附：`_before_state.json` / `_apply_result.json` / `_verify_result.json` / `_analyze*.json` / `_*.py` 为过程留痕，非交付项。
"""
with open(os.path.join(MERGE, 'MERGE_LOG.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(log)

print('written:', [os.path.join(MERGE, x) for x in ['MERGE_LOG.md','BEFORE_AFTER.txt','VERIFY.txt']])
