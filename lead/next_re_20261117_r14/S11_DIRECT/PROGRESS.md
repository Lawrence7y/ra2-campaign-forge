# S11-DIRECT PROGRESS

## 环境核验（2026-11-18）
- 目标 `ra2youli/gamemd.exe`：SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（全值实测一致），4,825,360 B — **只读，未触碰**。
- Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26（系统 python，无 venv / 无 pip install）。
- 已读 R14_COMMON.md（§1/§6/§8 含错源 A/B/C/D=⑲⑳㉓㉔㉕㉖）+ 本卡 CARD.md。
- 写域：仅 `S11_DIRECT/` 与 `_ghidra/S11-DIRECT/`（本卡未用 Ghidra，未建副本）。

## ⑨ 盘上基线复算（与卡面完全一致 → 继续）
- coverage.tsv 数据行 18,431；atlas 12,916 行。
- `S11 ∩ atlas`：n=**368**、proved([已证])=**29**、[静态推断]=**331**、[未证]=**8**；门槛 ceil(368/2)=**184**，差 **155**。
- 只动 grade，不动名字 / subsystem。

## 扫描规模自证（错源 D）
- `.text` VA+size = 0x401000..0x7E038D（ImageBase 0x400000 + VirtualAddress 0x1000，Size = VirtualSize 0x3DF38D）。
- capstone `skipdata=True` 线性反汇编覆盖 `.text` **100%**：解出 **1,392,592** 条指令（含 skipdata .byte），真指令 1,392,527；`E8` 落在指令边界 **68,253** 个（全部解为 `call rel32`，size=5）。与卡面全扫基准逐字一致。
- ⑲ 自检：capstone 5.0.7 对 `call [eax]` 的 `op.mem.index` 返回 **0（int），非 None** — 已实测确认陷阱存在。
- 所有 16 个交付站点已逐字节复核：bytes5 / rel32 / target / 指令边界 / 覆盖区间 全部 OK（16/16），落在 0x401000..0x7E038D 内。

## direct 命中与判据
- 339 个 S11 非 `[已证]` 行（331 静态 + 8 未证）中，有 direct call site 的共 **11** 行（8 静态 + 3 未证）。
- 3 个 `[未证]` 行（`005AE860`/`005AF1A0`/`007559B0`）因 ⑱ 冲突不升格：
  `005AE860`=`Matrix3D::Identity`（docs/re/bullet_particle_fog_deep_dive.md:148、vxl_cache_layout.md:206）；
  `007559B0`=阴影投影矩阵查表（ARCHITECTURE_ATLAS.md:3858/3946 等 5 处）；`005AF1A0` 同域弱信号。详见 DISAGREE.md D1。
- **交付 direct 升 `[已证]` 行数 = 8**（全部来自 `[静态推断]`）：0040B270 / 00415C60 / 00442D90 / 0055A910 / 0055A930 / 0055ABA0 / 0055ABB0 / 0055AD00。
- caller 加分项：`00415C60` 两 caller 均 `[已证]`；`0040B270`/`0055A930` 各 1 个 `[已证]` caller。

## 基线 / 差分（错源 B）
- 随机抽 11 个 atlas 入口，direct 判据误命中（seed 0..9）：5,4,1,4,4,5,7,3,6,8 / 11（均值 ≈4.7）。判据对「是否真实函数」非特异，见 DISAGREE.md D2。
- 差分检验（同一批 339 行 × 弱/强判据）：`weak_hits=11`、`strong_hits=11`、`weak_only=0` — 无弱判据伪命中，11 行全部由强判据命中。

## 落盘交付
- `coverage_delta.tsv`：8 行（8 列），只含 direct 升格行；未动名字/subsystem。
- `VIRTUAL_SKIPPED.tsv`：323 行（只靠虚表可达、本卡不升格）。
- `EVIDENCE/direct_call_sites.tsv`：107 站点（11 候选全量）；`EVIDENCE/direct_call_sites_clean.tsv`：16 站点（8 交付行）。
- `DISAGREE.md`（D1 冲突行 / D2 基线）、`UNKNOWNS.md`、`work/`（扫描脚本 + json）。

## 并入后复算（模拟 M 卡合并 delta）
- S11 n=**368**、proved=**37**（29→37，+8）、[静态推断]=323、[未证]=8、门槛 184（仍差 147）。
- 全部检查通过。

## 进度
- [x] 必读 COMMON / CARD、环境核验、⑨ 基线复算
- [x] 全 .text 100% 扫描 + 覆盖率自证（1,392,592 / 68,253）+ ⑲ 自检
- [x] direct 命中穷举 + 冲突检查（⑱）+ 基线 / 差分
- [x] VIRTUAL_SKIPPED 判定 + 逐行核验 + 落盘 delta / EVIDENCE
- [x] 并入后 proved 复算 + 自检报告