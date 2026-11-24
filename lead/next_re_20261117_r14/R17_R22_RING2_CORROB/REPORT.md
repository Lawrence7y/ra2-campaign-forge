D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R22-RING2-CORROB · in-binary RTTI 对「②（类身份）」的独立佐证测量

- 镜像校验：第一行实际路径与 sha256；前缀 73201CC0 匹配，结果有效。
- 镜像大小 4,825,360 B；只读 PE 节 .rdata/.data，声明读取 643,072 B；未建目标进程、未调试、未启动 gamemd。
- coverage.tsv 只读：4,147,334 B，sha256 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A；写后复核 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A，未修改。
- 筛选口径与全部判据均在 work.py 中显式实现；中间结果见 _stage0_sections.json / _stage1_index.json / _stage2_rows.json / _stage3_measure.json。

## Q1 · in-binary 索引

- 复现 TD 装饰名 988 个，唯一裸名 988 个；COL 记录 1,201 条，COL 数据引用 1,205 处。
- 候选 vtable 基址（引用+4）1,205 个；连续 .text 槽值 13,955 个；空槽表 4 个。
- 精确裸类索引键 954 个，其中多 vtable 类 91 个。
- 主口径另展开模板基名别名（如 ?$DynamicVectorClass@H → DynamicVectorClass）：索引键 1062 个，其中多 vtable 类 111 个。

## Q2 · 候选行

- coverage 数据行 18,498；列宽异常 0。
- grade 精确筛选 [已证]：**1,654** 行。
- 第 4 列类名正则：(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])；逐行去重。
- MSVC 前缀链 PAV/AV/PA/P/A：代码生成最长优先候选串，取第一个能命中 in-binary 索引的候选；裸 AbstractClass 不会被误剥成 bstractClass。
- 主口径可定位行：**1,094**；精确裸名变体 1,085 行（仅敏感性对照，不作主结果）。

## Q3 · 交叉测量（只给数）

| 项目 | 行数 |
|---|---:|
| [已证] 行总数 | 1,654 |
| 提到的类名可在 in-binary 索引定位 | 1,094 |
| entry 与该行某定位类同一 vtable 槽值闭合 | **433** |
| entry 出现在非该类 vtable（矛盾信号，按行计；可与闭合重叠） | 141 |
| 其中：仅非该类命中、未闭合 | 64 |

- 闭合判据：entry 数值等于该类某 vtable 连续 .text 槽值之一。
- 矛盾判据：entry 数值等于任一 vtable 槽值，但该 vtable 的类键不在本行定位类键集合中。
- 精确裸名变体敏感性：可定位 1,085、闭合 397、矛盾 168。

## Q4 · 闭合行的既有 ② 证据分布

- 判据（只查第 4 列语义）：命中 VERDICT|verdict.tsv|_audit|AUDIT|审计|独立|④|活表槽位见证|RTTI|rtti-vftable|vt=|vtable|虚表槽|slotN|槽N|PROOF|VERIFY|CHAIN|链（不区分大小写）即记「有独立审计链」；否则（含 YRpp named / YRpp/kb 地址名 / 名字已证，语义据名，以及未命中独立链标记的保守兜底）记「仅 YRpp 代理」。

| 既有 ② 证据类型 | 闭合行数 |
|---|---:|
| 有独立审计链 | 393 |
| 仅 YRpp 代理 | 40 |

- 逐行闭合命中见 corroborated.tsv；不据此改 grade。

## Q5 · 诚实限制

1. in-binary 只覆盖**有 RTTI 的类**；无 RTTI 的类不会出现在本索引中。
2. 「entry 出现在该类 vtable 里」只说明**地址相等**，不等于「该 entry 就是该类的成员」（可能与别处同址复用）。
3. 本卡**不建议任何 grade 变更**，也不得被引用为「② 已升级」。

未取得项：0。
