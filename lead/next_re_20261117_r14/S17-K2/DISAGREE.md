# S17-K2 · DISAGREE（与派卡/台账/权威口径的差异记录）

## D0 — 分母口径：**无 DISAGREE（实测一致）**

| 项 | 派卡/PANEL 口径 | 本卡脚本实测 | 一致? |
|---|---:|---:|---|
| S17 atlas_n | 102 | **102** | ✅ |
| S17 named_n（atlas 内） | 85 (83.33%) | **85 (83.33%)** | ✅ |
| S17 proved_n（atlas 内） | 49 (48.04%) | **49 (48.04%)** | ✅ |
| 缺口 | named +7（→92）、proved +2（→51） | 复算同 | ✅ |
| 全 coverage S17 | （派卡未给） | 104 行（named 87 / proved 49） | 本卡新增并列口径 |

- 结论：**停机核验通过**，无分母分歧；未因「目标要跨门槛」而调分母。
- 复算：`python work\t1_filter.py` → `EVIDENCE\s17_rows_report.txt` / `work\s17_rows.json`。

## D1 — 派卡「`[已证]` 缺口 ≈2」：实测需 +2（atlas）/ +3（全 coverage），本卡做 +4

- atlas 分母 102：`50% × 102 = 51`，49→51 需 **+2**（51/102=50.00%）。
- 全 coverage 分母 104：`50% × 104 = 52`，49→52 需 **+3**（52/104=50.00%）。
- 本卡提 4 条（atlas 53/102=51.96%；full 53/104=50.96%），**超过两口径最低需求**，均带字节双证，非凑数。
- 说明：多提 2 条（0x4B6BB0/0x67C690）是为留审计回退余量（即便各降 1 条仍跨线），且有独立证据，不是为「好看」。

## D2 — 派卡「S17 存档卡已入账 §946，类名 35/35 可定」：本卡引用一致，但发现归档 PROGRESS 自报与审计订正冲突（**引用审计订正版**）

- S17-F1 `PROGRESS.md` 自报「34/35 不可定」「内联向量块 28」「63 单元」；其 `_audit\VERDICT.md` 审计为 **0/35 不可定 / 29 块 / 64 单元**，且 §946 催办已按审计值入账。
- 本卡**只引用入账值**（35/35 可定、29 块），未复述已作废的 34/35 / 28 / 63；见 `DOD.md` 第 3 条。
- 本卡 delta 中 35 个 `Save_VectorBlock_*` 行一律未改（保持 `[已证]`，语义中 "class name unproven" 按 §946 已不代表真相，但本卡不擅自改 35 行语义——见 U3）。

## D3 — 内容层：3 行 S17 归属可疑 + 7 行弱信号（**本卡不改 subsystem，仅记录**）

- `0x49F740` / `0x49F8B0`：字面证据是 `COPYPROTECTION - Received message from launcher` / `Shutdown` + `MapViewOfFileEx`/`UnmapViewOfFile` + `RegOpenKeyExA(WChat\SysID)`，与存档/序列化无关。census 以「导入 MapViewOfFileEx → 存档」弱信号归 S17，属误归。
- `0x773450`：RTTI `WebBrowser` + `Instantiating embedded WebBrowser` + `CoCreateInstance`，属内嵌浏览器构造器，census 以「CoCreateInstance → 存档」弱信号归 S17，属误归。
- 7 行低地址 `sub_` `[静态推断]`（见 `UNKNOWNS.md` U1）：字节是通用链表/构造/setter，无 S17 专属原语；census 仅 callgraph 1 票。
- **处置**：保持原 subsystem=S17 与 grade（不强改，避免越权）；不打 S17 语义、不改名凑数；在 `TARGETS.tsv` 第 8 列与 U1/U2 记录，供下张 M/K 卡裁决是否移出 S17。

## D4 — 派卡「不许自造名」：本卡对 `0x431B80` 用 RTTI 类名 + 析构体，不按文件名推断

- `BufferIOFileClass::~BufferIOFileClass` 的依据是 **vtable `0x7E3A2C` 的 RTTI COL→TD `.?AVBufferIOFileClass@@`** + 函数体写自身 vptr / free `[+0x30]` / 尾调 base dtor `0x65CA00`（`EVIDENCE\T2_T3_EVIDENCE.txt` E8），**非**「按头文件名推断」（§8.1 ④ 错源）。
- 另 6 行名字依据分别是 RTTI vt slot13=Save（2 行）与调用已知 S17 原语（4 行），逐条列于 `PROGRESS.md` 结论表与 `EVIDENCE\T2_T3_EVIDENCE.txt`。**无一行凭「最近 E8 目标」「最大函数」「无调用者」等禁用启发式**（纪律 7/8）。

## D5 — 工具/方法差异

- 本卡复用 `S17-F1\work\pe_util.py`（只读 import）作 capstone/pefile 层；**未 import 任何 atlas 文件参与 class/name 判定**（atlas 仅用于 T1 分母求交）。双通道：capstone `skipdata=True` + 全镜像 `.rdata` dword/RTTI 扫描，二者互不依赖。
- 未用 Ghidra（定点命名不需要；避免 `_ghidra` 并发占用）。
- `Ghidra -noanalysis` 约束未触发；全局 Ghidra 并发仍为 0。
