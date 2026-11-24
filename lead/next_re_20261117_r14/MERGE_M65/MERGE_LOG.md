# M65 MERGE_LOG — 并表 15 行（S22 十四行 + S05 一行）

- 时间：2026-11-20T11:52+08:00
- 依据卡片：`_cards/M65-MERGE.md`
- 独占写权：本卡为唯一 COVERAGE 写者，仅改 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`。

## 前置核对（改前，不符即停 —— 全部符合，继续执行）

| 项 | 卡片期望 | 盘上实测 | 结论 |
|---|---:|---:|---|
| 数据行 | 18,498 | 18,498 | ✓ |
| 全表 [已证] | 1,512 | 1,512 | ✓ |
| atlas 内 [已证] | 1,506 | 1,506 | ✓ |
| atlas 外 [已证] | 6 | 6 | ✓ |
| S22（atlas 内）proved | 55 | 55 | ✓ |
| S05（atlas 内）proved | 170 | 170 | ✓ |

- 14 行 S22 改前 grade 全部 `[未证]`：实测 14/14 ✓
- `00748190` 改前 `[静态推断]`：实测 ✓
- 15 行全部在 atlas 内（entry 归一为大写比对）：实测 15/15 ✓
- 另记录 FAIL 两行 `006BFF90`/`006C0A10` 改前 grade 均为 `[未证]`（用于改后“未变”复核）。

## 并入内容（合计 15 行）

### A. S22 十四行（源 `NAMED_PUSH_S22_B1/delta.tsv`，审计 `NAMED_PUSH_AUDIT4/verdict.tsv` PASS）
`006BF810` `006BF990` `006BFB10` `006BFC90` `006BFE10` `006C0110` `006C0290` `006C0410`
`006C0590` `006C0710` `006C0890` `006C0B90` `006C0D10` `006C0E90`
- 16 行审计中 PASS 14；FAIL 2 行整行拒绝，一个字未改：
  - `006BFF90`（AUDIT4 verdict.tsv 行 7，FAIL）
  - `006C0A10`（AUDIT4 verdict.tsv 行 14，FAIL）
  - 拒因：`007EB6D4`/`007F36B4` 是构造函数内嵌成员表（分别为 `[esi+0xC4]` TypeList、`[esi+0x38]` DynamicVectorClass），
    所谓 QueryInterface 实为 `VectorClass<T>` 析构式函数，不比较 IID、不写 `*ppvOut`、不返回 HRESULT 三态；
    真主虚表 `007F5728`/`007F3650`，槽 0 均 `00410260`。

### B. S05 一行（源 `NAMED_PUSH_S05_B3/delta.tsv`，审计 `NAMED_PUSH_AUDIT3/verdict.tsv` PASS）
`00748190`

## 改动范围

`coverage.tsv` 上述 15 行各改 3 列：
- 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列原文照抄（逐字节一致，15/15 复核通过）
- 第 5 列 `grade` → `[已证]`
- 第 6 列 `evidence_path` → 14 行 `NAMED_PUSH_AUDIT4/VERDICT.md`；`00748190` `NAMED_PUSH_AUDIT3/VERDICT.md`

第 1/2/3/7/8 列不动；数据行仍 18,498、8 列、TAB 分隔。
FAIL 两行 `006BFF90`/`006C0A10` 整行未改（grade 保持 `[未证]`）。

## PANEL.md 同步

- 主面板：S22 proved 55→69（1.42%）、S05 170→171（26.59%）、TOTAL 1506→1521（11.78%）。
- 全表/atlas 内 [已证] 1,512/1,506 → 1,527/1,521，atlas 外仍 6；变更日志标题行追加 M65 摘要。
- 备注列追加 M65 并表说明 + 额外限定段（模板级低信息量 ③b②，异族审计 16 行 14 真 2 假）
  + FAIL 两行整行拒绝说明。
- 严格双列表按盘上实算写为 S05 171/139、S22 69/26、TOTAL 1521/1204。
  - 说明：改前 coverage 盘上实算 S22 strict=12、TOTAL strict=1189，PANEL 旧记 2/1179
    （系 M60 旧截面差 10 行未同步）；本卡按卡片“按你实算”以盘上改后实算值更正，
    并在严格双列表下新增一条 M65 实算说明注记，透明记录差异构成（本次 +14/+1/+15，无额外并表）。
- 达标判定未改变：名义仍 S15/S16/S17（3/22），严格仍仅 S17（1/22）。无达标翻转。

## 核盘自检

- (a) 数据行 18,498→18,498，entry 增删 0；表头 1 行 + 数据 18,498 行 ✓
- (b) 全表 [已证] +15（1,512→1,527）；atlas 内 +15（1,506→1,521）；atlas 外 +0（6）✓
- (c) 15 行新 grade/语义/evidence 逐项对 delta 与卡片一致（15/15）✓
- (d) FAIL 两行 grade 未变（均 `[未证]`）✓
- (e) 达标判定 21 个子系统实算：名义 {S15,S16,S17}、严格 {S17}，与改前一致，无翻转 ✓
- (f) 两文件改前/改后 mtime/字节/sha256 见 `BEFORE_AFTER.txt`；详细核验见 `VERIFY.txt`。

## 交付文件

- `MERGE_M65/MERGE_LOG.md`（本文件）
- `MERGE_M65/BEFORE_AFTER.txt`
- `MERGE_M65/VERIFY.txt`
