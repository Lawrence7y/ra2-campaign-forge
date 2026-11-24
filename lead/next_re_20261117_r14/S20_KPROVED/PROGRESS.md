# S20-KPROVED PROGRESS

## 核验与口径
- 目标只读：`gamemd.exe` 4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与卡面一致。
- ⑨ 自算（atlas∩coverage）：S20 n=410、named=399、proved=40、`[静态推断]`=359、`[未证]`=11；与卡面一致。
- ⑲ 自检：直接 call `E8 00 00 00 00` → imm target `0x1005`；无 index 的 mem 操作数 `op.mem.index=0`。本环境 capstone 5.0.7 的 x86 operand 无 `op.index` 属性，故全程不按 index 过滤，只按 `op.type` / `op.mem.index` 判定。
- 自写 `work/scan_s20.py`：12,916 个 atlas 函数体 / 1,030,315 条指令；未 import 任何卡的 work 代码。

## 核心结果
- **C1 升 `[已证]`：40 行**（21 direct-call + 19 exact-dispatch）；`coverage_delta.tsv` 40 行、8 列、entry 唯一。
- 环④ direct：73 个 raw E8 命中 S20 静态行，全部经 atlas 函数体指令边界复核；交付取其中 21 行的外部 caller 站点。
- 环④ exact：绝对 global vptr 写（`C7 05`）+ 构造器链反推 global vptr 写，共解析 44 行；交付取 19 行，caller 均不在本批 40 行内。
- **C2 D-39 型：294 行**，只登记 `D39_CANDIDATES.tsv`，保持 `[静态推断]`；未把活 vptr 安装/vt imm32 当环④。
- 检出力基线：seed=20261118，随机同子系统 40 行，同一 C1 判据误命中 **8/40**；另有 25 行也过判据但因目标 40 行未交付，见 `EVIDENCE/unselected_c1_pass.tsv`。
- 逐行 grade：40 行均 `[静态推断]→[已证]`，见 `coverage_delta.tsv` 第 8 列；名字与 subsystem 未改。
- 并入后（仅内存复算，未写 COVERAGE）：S20 proved **80/410 = 19.51%**，门槛 205，仍差 125。

## 证据与自证
- 逐行四环：`EVIDENCE/PROOF_<entry>.txt`（40 份，含 ①atlas/vtable ②RTTI ③body ④direct/exact 及全量反汇编）。
- 机器证据：`EVIDENCE/s20_scan.json`、`direct_call_sites.tsv`、`exact_v3_resolved.tsv`、`vtable_rtti.tsv`、`raw_c7_s20vt.tsv`、`global_ctor_vptr_writes.tsv`。
- ⑱ 冲突扫描：451 文件 / 42 条 entry 命中，均仅为地址级命中；`0075F8B0` 的 subsystem/name OPEN 冲突已登记 `EVIDENCE/conflict_scan.tsv`，只报不改名。
- `work/validate.py` → `EVIDENCE/validation.txt`：**VALIDATION PASS**；目标 SHA 未变，delta/D39 无重叠，证据文件均存在。
