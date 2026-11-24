# S20-DIRECT PROGRESS（卡号 S20-DIRECT）

## 环境与⑨基线
- 目标 `ra2youli/gamemd.exe` SHA-256 `73201CC0…F67476` 全值一致，只读未碰；Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26，无 venv/pip。
- ⑨ 开工复算：S20 n=**410** / proved=**68** / static=**331** / unproved=11，与卡面逐字一致（门槛 205，差 137）。只动 grade。

## ② 扫描规模（EVIDENCE/scan_stats.json）
- `.text` VA `0x401000` RawSize `0x3E0000` = 4,063,232 B；`skipdata=True` 线性全扫覆盖 **100.0000%**。
- 解出 **1,394,186 条指令**（基准 1,392,592，+1,594/0.11%，口径差不影响 E8 集）；`E8` 原始字节 **81,715**；指令边界真 call **68,253**（与基准逐字一致）。
- ⑲ 自检：`op.index` 不存在（hasattr=False）、`op.mem.index=0`（无 index 返 0 非 None），脚本不依赖 `op.index`。
- 交付站点全部在自报范围内（`work/all_direct_call_sites.tsv` 68,253 行）。

## ①③⑥ 交付结果
- **direct 升格 11 行**：004C54E0 / 0062DF20 / 0062E070 / 0062F230 / 0070F1D0 / 0070FD70 / 00739AC0 / 00739CD0 / 0075E950 / 007610F0 / 007C978A（`coverage_delta.tsv`）。
- 逐行 348 站点逐字节复算：`site+5+rel32==entry` 全真、capstone call 全真、非自环全真、全部落 .text（`EVIDENCE/direct_call_sites_clean.tsv` / `verify_direct.json`）。
- ⑥ VIRTUAL_SKIPPED = **329 行**（仅虚表可达，不升格）；11 升级行与虚表集交集=0；2 行（005F3D90/007610A0）两者皆无，见 UNKNOWNS U2。
- ⑤ 并入后 S20 proved = 68+11 = **79**（门槛 205，仍差 126）。

## ④ 基线 / 差分 / 冲突
- **随机基线（N=11）**：未对齐 10 seed 全 **0/11**（mean 0.0）；4 对齐 10 seed **0/11·1/11** 交替（mean **0.2/11**）。
- 弱扫(raw E8 任意偏移) vs 强扫(边界 E8) 差集 **0**（`EVIDENCE/final_verification.json`）⇒ 无错源 B 同源系统误差。
- ⑱ 全库按地址查（docs/re + re_atlas/kb + 台账 + COVERAGE）：11 行均无竞争名；0062DF20/0062E070 的 `ParticleClass::Update`/`ParticleSystemClass::AI` 是同行他址 token（误报，见 U3）。只报不改名。

## 交付清单
`PROGRESS.md` / `UNKNOWNS.md` / `DISAGREE.md` / `coverage_delta.tsv` / `VIRTUAL_SKIPPED.tsv` /
`EVIDENCE/{scan_stats,verify_direct,baseline_and_conflicts,final_verification,summary}.json` /
`EVIDENCE/{direct_call_sites_clean.tsv,virtual_reachable_rows.json}` / `work/*`（脚本与全扫索引）。
