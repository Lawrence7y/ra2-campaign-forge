# S17-K2 · PROGRESS（≤60 行）

> 卡号 S17-K2｜Ra2 逆向执行员｜静态定点卡（逼近 DoD 门槛）
> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，ImageBase `0x400000`，4,825,360 B（只读）。
> 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；复用 `S17-F1\work\pe_util.py`（只读 import）；未用 Ghidra。

## 核心数字（给审计：可独立复算）

| # | 数字 | 值 | 复算方法 |
|---|---|---|---|
| N1 | **atlas 分母（下界） DoD** | 分母 **102**；前 named **85/102=83.33%**、proved **49/102=48.04%**；后 named **92/102=90.20%**、proved **53/102=51.96%** → **双线跨 90%/50%** | `python work\t1_filter.py`（筛 `coverage.tsv` subsystem=S17 ∩ `function_atlas.tsv`）+ `python work\verify_dod.py`（模拟 M 卡合 delta 重算）→ `EVIDENCE\DOD_RECOMPUTE.txt` |
| N2 | **全 coverage 口径** | 分母 **104**（含 2 atlas 外行）；前 named 87/104=83.65%、proved 49/104=47.12%；后 named **94/104=90.38%**、proved **53/104=50.96%** → 同样跨线 | 同上脚本两口径并列输出 |
| N3 | 本卡 delta | **7 行**：4 行升至 `[已证]`（含 2 行由 RTTI/vtable slot13=Save + call 410410 双证）、2 行 `[未证]`→`[静态推断]`、1 行仅改名（BufferIOFileClass 析构）；**0 行无证据凑数** | `coverage_delta.tsv` + `EVIDENCE\T2_T3_EVIDENCE.txt` |

## 结论表

| 项 | 结论 | 等级 | 证据路径 |
|---|---|---|---|
| 分母核验 | 自算 S17 atlas_n=102 / named 85 / proved 49，与 PANEL.md 逐位一致 → **无 DISAGREE** | `[已证]` | `EVIDENCE\s17_rows_report.txt`；`work\t1_filter.py` |
| **0x41D6E0 → AirstrikeClass::Save** | RTTI vt `0x7E29A8`(=COL 0x7FB6F8→TD `.?AVAirstrikeClass@@`) slot13(+0x34)=本函数；slot13 在 3 张基类 vtable 均为 `AbstractClass::Save` 0x410410；函数体 `push [esp+4]; call 0x410410; ret 4` | `[已证]` | `EVIDENCE\T2_T3_EVIDENCE.txt` E1/E2/E3；`EVIDENCE\vtable_precise.txt` |
| **0x43A5D0 → NeuronClass::Save** | RTTI vt `0x7E3DF0` slot13=本函数；体 `call 0x410410` 后再以帧差 `0xA8ED84−[esi+0x30]` 调 `0x4A1D50` | `[已证]` | 同上 |
| **0x4B6BB0 → Swizzle_RegisterPointerArray** | `for i<[this+0x10]: push &[this+0x14+4i]; push 0xB0C110(SwizzleManager::Instance); call 0x6CF240(Here_I_Am)` | `[已证]` | `EVIDENCE\T2_T3_EVIDENCE.txt` E4 |
| **0x67C690 → Load_COM_ObjectVector** | IAT 实测 `ole32!OleLoadFromStream@0x7E15F8`；体先 `call [vptr+0xC]`(=IStream::Read) 读 u32 count，再循环 count 次 `OleLoadFromStream`(IID `0x7F7C90) | `[已证]` | `EVIDENCE\T2_T3_EVIDENCE.txt` E5；`EVIDENCE\naming_candidates_evidence.txt` §1 |
| 0x55AAC0 → Load_SwizzledObject | 体 `IStream::Read` + `call 0x6CF2C0`(Here_I_Am3) + 两次 `call 0x6CF240`(Here_I_Am) | `[静态推断]` | 同上 E6 |
| 0x539AE0 → Load_StreamFields | 体多次 `call [vptr+0xC]` 读入 `0xA9FAB4/0x827FC0/0x827FC4`，逐次判 HRESULT | `[静态推断]` | 同上 E7 |
| 0x431B80 → BufferIOFileClass::~BufferIOFileClass | RTTI `.?AVBufferIOFileClass@@`（vptr 0x7E3A2C）；体写自身 vptr、`[+0x24]!=0` 时 free `[+0x30]`、清标志、尾调 `0x65CA00` | `[静态推断]` | 同上 E8 |
| 反向控制（不凑数） | 0x4068E0 是单 `ret` 桩、0x773450 是 WebBrowser 构造器（串 `Instantiating embedded WebBrowser`）、0x49F740/8B0 是 COPYPROTECTION/MapView——**均不改名、不打 S17 语义** | `[已证]`（基线） | `EVIDENCE\T2_T3_EVIDENCE.txt` E9；`DISAGREE.md` |

## 分级 / 纪律合规

- **双通道**：通道 A = capstone `skipdata=True` + pefile（不依赖 atlas）；通道 B = 全镜像 `.rdata` dword 扫描 + RTTI COL→TD 链（不依赖 atlas）。类名一律 RTTI `COL+0xC→TD+8`，读不到即停（本卡 6 个 vtable 全部读出 `.?AV*@@`）。
- **先测基线**：slot13=Save 不是碰巧——3 张独立 vtable（AbstractClass/CellClass/Tactical）+ 全镜像 1219 个 vtable base 精确定界，非「随便挑 13 也中」；见 E9。
- **不由函数名反推语义**：7 行语义全部来自函数体字节（`call 0x410410`/`call 0x6CF240`/`OleLoadFromStream`/`IStream::Read`/free 路径），无一条来自猜测。
- **不跨类套偏移**：本卡唯一字段 `[this+0x10]/[this+0x14]` 只用于 0x4B6BB0 自己的循环；未把 `+0x94/+0x184/+0x80` 跨类套用。
- **不写台账 / 不改游戏文件 / 不 git commit**：全部写入限于 `S17-K2\`。
- **S17-F1 捷径已用**：0x41D6E0/0x43A5D0 类名正靠静态 vtable 初始化链思路（§946）；对「类名不可定」的 8 行先试链再下结论，未下的保持 `sub_`。

## 未闭环

见 `UNKNOWNS.md`（10 行未改名弱信号、S17 存档/读档非一一对应、3 行误归类候选）与 `DISAGREE.md`（分母一致，无 DISAGREE；内容层 3 处待 Lead 裁决）。
