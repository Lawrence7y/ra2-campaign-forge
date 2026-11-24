# S05-K1 · PROGRESS.md — 对象模型深化（增量）

> 卡号 S05-K1｜2026-11-17｜目标只读 `gamemd.exe` SHA `73201CC0…F67476`｜写域仅本目录
> 一句话结论：10 个核心类 RTTI 名/槽数/父类全恢复；GetSize 双向核对 4/4 具体类闭合；8 字段双支撑；4 处构造器误归交 delta。

## 结论表（分级 + 证据路径）

| 项 | 结论 | 分级 | 证据 |
|---|---|---|---|
| RTTI 类名恢复 | 10/10（链 `COL+0xC→TD+8`） | [已证] | `EVIDENCE/class_chain_core.json` |
| 槽数（`.rdata` 定界） | 10/10 与 classes_meta 吻合 | [已证] | 同上；`work/recover_class_chain.py` |
| 父类（CHD base[1]） | 10/10；发现漏层 Mission/Radio | [已证] | `EVIDENCE/class_chain_core.json` |
| GetSize 双向核对 | 4/4 具体类闭合（0x720/0x8E8/0x6F0/0x6D8） | [已证] | `EVIDENCE/ctor_association.txt`、`getsize_alloc_sites.json` |
| 抽象基类 GetSize 桩 | 6/6 = 0x4C9150（不可比，非失败） | [已证] | `EVIDENCE/alloc_disasm.txt` |
| 字段双支撑 | 8 字段（+0x10/20/74/80/81/94/21C/1AC） | 7 已证 +1 静态推断 | `EVIDENCE/field_access_scan.json`、`trap_verification.txt` |
| T4 布局边界 | 4/4 构造器越界写 0；max disp ≤ GetSize | [已证] | `EVIDENCE/layout_boundary_check.txt` |
| 批量类名通道 | 243/245（99.2%），基线 0.5% | [已证] | `EVIDENCE/vtable_write_scan.txt` |
| coverage 误归 | 4 主 + 变体（Unit/Infantry/Techno/Foot ctor） | [已证] | `DISAGREE.md` D2–D5、`coverage_delta.tsv`(36 行) |

## 给审计员的 3 个核心数字（可独立复算）

1. **GetSize 双向闭合 = 4/4 具体类（总 10 类中 6 抽象桩不可比）**。复算：
   `python work/recover_class_chain.py` 取每类 `v[12]` 的 `B8 imm C3`；
   `python work/find_alloc_sites.py` 找 `68 <imm> → call 0x7C8E17`；
   `python work/verify_ctor_assoc.py` 验 `mov ecx,eax; call <写该类 vptr 的函数>`。三处独立吻合即闭合。

2. **静态 vtable 初始化链恢复 = 243/245 (99.2%)，随机基线 = 1/200 (0.5%)**。复算：
   `python work/scan_sites.py`：全 `.text` 扫 `C7 05 <dest><val>` 且 `val∈.rdata` ⇒ 245 个不同 val；对每个取 `val[-1]=COL → COL+0xC=TD → TD+8` 得名；243 名有效（2 失败值 0x807A68/0x80808080 为数据非 vtable）。基线同脚本 200 随机 4 对齐 `.rdata` 地址仅 1 命中。该基线排除"随便挑也过"。

3. **字段双支撑 = 7/8 达 [已证]（+0x21C 写4/读196；+0x81 写34/读238 等）**。复算：
   `python work/field_scan.py` 全 `.text` skipdata 扫描（1,394,186 条），按 disp 索引写/读 + 函数区间归属；每字段写点全集 + ≥3 读点采样见 `EVIDENCE/field_access_scan.json`；第 8 项 +0x1AC 因 `call [reg+0x1AC]` 为虚槽调用、数据字段归属 0，按纪律 4 降 `[静态推断]`。

## 交付与纪律自检
- 交付：CLASS_CHAIN.md / LAYOUT.md / UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv(36) / EVIDENCE/(9 文件) / work/(12 脚本)。
- 双通道非同源：类名通道(RTTI 字节)与 GetSize 通道(vtable imm + 分配点 push imm)互不依赖 `function_atlas.tsv` 的 entry+size（atlas 仅用于函数区间归属，不参与取数）。
- 先测基线：243/245 与 4/4 均先经随机对照（0.5%）排除空判据；未写"N/N"前无基线不得下结论（纪律 1）。
- 槽数从 `.rdata` 定界，未用 atlas 边界反推（避 §8.1⑦ TClassFactory 坑）。
- 类名只认 TD；读 COL[+8] 得 CD 的坑已规避（本卡一律 COL+0xC）。
- 字段偏移未定语义：+0x94/+0x1AC 的 `call [vptr+disp]` 已显式剔除，不混入数据字段读点。
- 陷阱核验：0x6D98EF 写 0（非 1）、0x636595 ebp=ecx（+0x94 是字段非栈槽）——见 EVIDENCE/trap_verification.txt。
- 未改 gamemd.exe / coverage.tsv；未 git commit/push；未写主台账。
