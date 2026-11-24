# S13-DIRECT PROGRESS

## ① 开工核验（时间采样 2026-11-18T14:51:50+08:00）
- exe SHA-256 = 73201CC0…F67476 ✓（全 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476）
- 工具 Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；未建 venv / 未 pip install。
- 必读已读：R14_COMMON §1/§6/§8（含 ㉓-㉖ = 新错源 A/B/C/D：atexit 死vptr / 随机基线零鉴别力 / P=R=100% 自证 / 扫描规模自洽）+ S13_DIRECT/CARD.md。
- ⑨ 盘上复算（coverage SHA 502A56FE…，atlas W130 统一大小写）：n=240 ✓ / [静态推断]=129 ✓ / proved=**86**（卡面 89，差 3 = K12 审计白名单未落盘，见 DISAGREE D1）。

## ② 全 .text 扫描（100%）
- .text VA=0x1000 VSize=0x3df38d(4,060,045B) base=0x401000；capstone CS_MODE_32 skipdata=True。
- 解出 **1,392,592** 指令（含 65 skipdata；真实 1,392,527）；**E8@边界 68,253**；raw E8 = 81,715（13,462 非边界，§8.2.2 一致）。
- **覆盖率 100%**；逐字命中全扫基准 1,392,592 / 68,253。所有交付站点（0 个）落在自报范围内（空集平凡成立）。

## ③ ⑲ 自检
- 0x4386AB call dword ptr [eax+0x10]：hasattr(op,'index')=False；op.mem.index=0；is None=False。
- 本卡 direct 判据只读 ins.bytes（E8 + rel32），不依赖 operand.index，规避错源⑲。

## ④ direct 判据结果（仅 E8 / site+5+rel32==entry / 非自环）
- 129 行 [静态推断] 中，**>=1 合格 direct call site 的行数 = 0**。
- 全镜像 distinct direct-call 目标 6,728；44 个 S13 [已证] 行有 direct call（索引有效性 sanity ✓）⇒ 0 非扫描失效。

## ⑤ 基线 + 差分（新错源 B/D）
- 差分（同批 129 行 × 弱rawE8 / 强边界）：弱 0 / 强 0 / 差集 0 ⇒ 无「边界过滤误剔」同源错误。
- 随机基线：129 atlas entry 强判据命中 mean=64.40（10 seed）；129 coverage[静态推断]∩atlas mean=19.80（5 seed）。⇒ S13 静态行 0/129 为结构性真阴性。

## ⑥ ⑱ 按 entry 查全库冲突（只报不改名）
- 451 文件（docs/re + re_atlas/kb + 台账 + COVERAGE）；129 行均命中文本，但均为 coverage.tsv 自身/台账注释/range 端点，无外部异名冲突（详见 EVIDENCE/conflict_scan.json）。

## ⑦ 虚表可达（VIRTUAL_SKIPPED）
- 129 行全部有 .rdata dword 引用（虚表槽值），0 行零引用 ⇒ 全部 virtual-only；按纪律不升格。
- 不逐行判活/死 vptr（本卡禁虚派发；错源㉓/D-39 留后续）。

## ⑧ 交付
- coverage_delta.tsv：**仅表头，0 行**（无 direct 行可升）。
- VIRTUAL_SKIPPED.tsv：**129 行**（entry + 现有 ①②③ + 环④缺说明）。
- EVIDENCE/：direct_analysis.json、all_direct_call_sites.tsv、vref_analysis.json、conflict_scan.json、scan_stats.txt。
- work/：全部复算脚本（可审计复现）。

## ⑨ 核心数字（给审计员复算）
① direct 升 [已证] 行数 **0**；② 扫描 **1,392,592 指令 / 68,253 E8 / 100%**；③ 基线误命中 mean **19.80**(同类静态) / **64.40**(atlas)，差分差集 **0**；④ 逐行 grade 对照：**0 行改动**，129 行保留 [静态推断]；⑤ 并入后 S13 proved 实测 **86**（literal）/ **89**（审计口径），增量 **0**；⑥ VIRTUAL_SKIPPED **129 行**。
