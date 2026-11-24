direct 升了 31 行 / 最多 108 行

# S03-DIRECT · PROGRESS

## 环境 / 必读
- 目标 `ra2youli/gamemd.exe` 只读；SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，4,825,360 B（与 S11_DIRECT 实测一致，本卡未改）。
- Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26（系统 python，无 venv / 无 pip install / 未 import 他卡 work）。
- 已读 R14_COMMON.md（§8 错源 ⑲⑳㉑㉒、§8.4 容器族映射、§8.5 判据口径）+ 本卡 CARD.md。
- 写域：仅 `S03_DIRECT/` 与 `_ghidra/S03-DIRECT/`（本卡未用 Ghidra，未建副本）。

## ⑨ 停机核验（atlas∩coverage，与卡面逐字一致 → 继续）
- coverage 18,431 数据行；atlas 12,916 行；atlas∩S03：**n=194 / named(L)=125 / proved=18 / [静态推断]=108 / [未证]=68** ✅。
- 纯 coverage S03=196（多 `004A2780`/`0065C590`，不在 atlas），按卡面口径排除；门槛 proved 97（差 79）。
- 工作面 = 108 条 [静态推断]，全部已有名字。

## 扫描规模自证（错源 ㉖）
- `.text` VA 0x401000..0x7E038D；capstone `skipdata=True` 线性反汇编覆盖 `.text` **100%**。
- 实测 **1,392,592 条指令 / 68,253 个 E8@边界 / raw E8 81,715** —— 与卡面全扫基准逐字一致。
- ⑲ 自检：capstone 5.0.7 对 `call [eax]` 的 `op.mem.index=0`（int，非 None），`op.index` 属性不存在；已知阳性 `E8 10 00 00 00` target check PASS。
- 276 个交付站点全部落在自报 `.text` 范围内（0 越界），bytes5/rel32/target 逐字节核 OK（276/276）。

## direct 命中与判据
- 三条件：E8 在 capstone 边界 / `site+5+rel32==entry`（逐字节核）/ caller 区间不含 entry（自环）。
- 自环 A（site 在本行体内）与 B（caller 区间含 entry）双解均 **0 命中**；区间外 caller 0。
- 命中 **31 行**（全 symbolic 槽名），交付 **31 行**；只动 grade，名字/subsystem 不动。EVIDENCE 276 站点。
- caller 加分项：39 站点 caller 为 `[已证]`（13 个不同 caller），73 `[静态推断]`，164 `[未证]`。

## 基线 / 差分（错源 B / ㉔）
- 随机 .text 地址 1,000 个：强判据命中 3/1000=0.30%，弱判据 3/1000=0.30%（判据对随机字节非特异）。
- 随机 atlas 入口 11 个（seed 20261118）：命中 7/11（direct 对「真实函数入口」非特异，与 S11_DIRECT 同量级）。
- 差分（同批 108 行 × 弱/强判据）：`weak=31, strong=31, weak_only=0` —— 无弱判据伪命中，31 行全部由强判据命中。

## ⑱ 冲突（只报不改名）
- 31 候选按 entry 地址查 `docs/re/` + `re_atlas/kb/` + 台账 + `COVERAGE/`：无跨子系统语义冲突，**0 排除**。
- `00431F10` docs 命中实为同一 E8 调用的正证据；`004325A0` 台账为边界口径告诫；`006C9890` 台账 File_Stream_Crypto 与 S03 一致。详见 DISAGREE.md。

## 落盘 / 并入后复算
- `coverage_delta.tsv`（31 行×8 列）、`VIRTUAL_SKIPPED.tsv`（76 行）、`EVIDENCE/direct_call_sites{,_clean}.tsv`（276 站点）、`work/`（脚本+json）、`UNKNOWNS.md`、`DISAGREE.md`。
- 模拟 M 合并：S03 n=194、**proved 18→49（+31）**、[静态推断] 108→77、[未证] 68；proved 门槛 97（仍差 48），named 门槛 175 本卡不处理。
