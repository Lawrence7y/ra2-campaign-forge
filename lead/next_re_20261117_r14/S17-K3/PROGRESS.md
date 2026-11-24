# S17-K3 · PROGRESS（≤60 行）

> 卡号 S17-K3｜RA2 逆向执行员｜静态定点卡（补 S17 差 1 个真名）
> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` / ImageBase `0x400000` / 4,825,360 B（只读，已复算一致）。
> 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；复用 `S17-F1\work\pe_util.py`（只读 import）；未用 Ghidra。

## 一句话结论
现盘 S17 **named(S)=91/102=89.22%**（差 1）；本卡以字节级证据补出 **00431B80 = `BufferIOFileClass::~BufferIOFileClass`**，合入后 **named(S)=92/102=90.20% 达标**，proved 53→54。

## 核心数字（给审计：可独立复算）
| # | 数字 | 值 | 复算方法 |
|---|---|---|---|
| N1 | 分母 / named / proved（现盘） | 分母 **102**；named_L=**91**、named_S=**91**（89.22%）；proved **53**（51.96%）；S17 内 `Class::sub_`=**0** | `python work\t1_named_count.py` → `EVIDENCE\t1_named_count.txt`；口径=coverage∩atlas、name 非空且非 `sub_` 且非 `::sub_XXXXXXXX` |
| N2 | NOT named(S) 行 | **11** 条（10 纯 `sub_` + 这 1 条待定），全部列出 | 同上文件 |
| N3 | 合 delta 后重算 | named(S) **92/102=90.20%**（+1，PASS）；proved **54/102=52.94%**（+1） | `python work\verify_dod.py` → `EVIDENCE\dod_recompute.txt`（**注意 delta 无表头，脚本显式给 fieldnames**） |
| N4 | T3 抽查 5 条 [已证] | **4 字节真实 / 1 偏软**（006CF240 Here_I_Am：YRpp 名复用，语义栏自带 [未证]）；即便它降级 proved 52/102=50.98% 仍过线 | `python work\t3_byte_audit.py` → `EVIDENCE\t3_byte_audit.txt` |

## 结论表
| 项 | 结论 | 等级 | 证据路径 |
|---|---|---|---|
| 分母/基线 | 102 / 91 / 91 / 53 与 PANEL.md:49 逐位一致 → **无 DISAGREE** | `[已证]` | `EVIDENCE\t1_named_count.txt` |
| **0x431B80 = BufferIOFileClass::~BufferIOFileClass** | vptr `0x7E3A2C`；RTTI `COL 0x7FBEF8→TD 0x815E18→.?AVBufferIOFileClass@@`；free `[+0x30]`（条件 `[+0x24]`）、清字段、尾调基类析构 `0x65CA00`；vt slot0 `0x432610` 指令同构 + `free(this)`；CDFileClass 删除析构 `0x401950` 以基类身份调它 | `[已证]` | `EVIDENCE\dtor_431B80_focus.txt`；`dtor_bytecmp.txt` |
| 其余 10 候选不可定名 | 单 ret 桩 / 通用 setter / 链表 splice / WebBrowser ctor 等，无 vtable/RTTI/调用者身份；保持 sub_、不编名 | `[已证]`（不可定） | `EVIDENCE\candidate_disasm.txt`；`TARGETS.tsv` |
| T3 前 4 条 | 0041D6E0/0043A5D0/004B6BB0/0067C690 字节逐条复现（call/RTTI/IAT 全对） | `[已证]` | `EVIDENCE\t3_byte_audit.txt` |
| T3 第 5 条偏软 | 006CF240 evidence 源=`self_known`(YRpp 名复用)+槽位、语义自带 [未证]；行为字节复核真实但 grade 依据不足 | `[静态推断]`（建议降级） | 同上；`DISAGREE.md` D3 |

## 关键说明：为何 delta 用 [已证]
K2 曾以 `[静态推断]` 报 00431B80 同名，但 `CONFLICTS.tsv` 已登记该名 vs prior `sub_00431B80`；按合并规则「同 grade 保留先出现者」被挡回，故 named 停在 91。本卡有字节级证据（RTTI 全值 + 析构指令 + vt slot0 + 调用链，可独立复算），满足升级硬规矩，以 `[已证]` 走「grade 高者优先」合入。合并员若因 conflict=1 仍拒合，需审计裁 CONFLICTS 该行；本卡只交 delta，不写台账。

## 纪律合规
- 类名只认 RTTI `COL+0xC→TD+8`，读全值、fail-closed（本卡两个类 BufferIOFileClass/CDFileClass 均实读 `.?AV*@@`）。
- 双通道：通道 A = capstone `skipdata=True`+pefile（不依赖 atlas）；通道 B = `.rdata` COL→TD 链 + 函数体字节/IAT（不依赖 atlas）。
- 先测基线：T1 口径由全局反解与 PANEL 22 行校验（非凑 91）；T3 全部自读字节，不复用他卡结论。
- 「分支逐条」/「字段偏移不定语义」/「槽号不假定」/「调用者名 [未证] 不支撑」均遵守；不用最近 E8、最大函数、无调用者=死代码等启发式。
- 不写台账 / 不改游戏文件 / 不 git commit / 未读 S17-K2 EVIDENCE（只读其 PROGRESS+VERDICT）。

## 未闭环
见 `UNKNOWNS.md`（10 条不可定名、K2 撞名/IID 标签沿用提示）与 `DISAGREE.md`（分母无分歧；delta 合入机制与 T3 水分需 Lead/审计注意）。
