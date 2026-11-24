# S12-K2 DISAGREE（与台账/底座冲突与口径差异）

| # | 对象 | 本卡结论 | 差异性质 | 依据 |
|---|---|---|---|---|
| D1 | R14_COMMON §2.3：`0x7014A0` 中 `[+0x81]` 语义 `[未证]` | 本卡把 `[+0x81]` 闭合为 **Limbo 标志**（1=Limbo，0=在世界）：写点 `0x5F4E9E`、幂等读点 `0x5F4D45`、SetOwner 摘/挂门控 `0x701664`/`0x701681` | **补证，不是推翻**：§2.3 说“未证”，本卡给出字节级写+读双支撑，建议更新为 `[已证]` | `EVIDENCE/T3_SEMANTICS.md`、`EVIDENCE/t3_81_census.txt` |
| D2 | 台账 §959 / W177-C：`0x47C620` 仅 `[推断·可观测]`（真机未观测到调用） | 本卡全函数逐条反汇编闭合：`this=CellClass*`，3 栈参，AL=1/0，只扫 head A `+0xE4`，`ret 0xc` | **证据等级升级**：真机仍未见调用这一事实不变；本卡是静态 `[已证]`，不是运行时证据 | `EVIDENCE/t1_47C620_full.txt`、`EVIDENCE/T1_SEMANTICS.md` |
| D3 | R14_COMMON §2.2：`[格+0xE4]`/`[格+0xE8]` 两个链表头 | 本卡确认 `0x47E8A0` 按对象 `[+0x8C]` 选 A/B，但 `0x47C620` **从不读 B** | **新增限定**：不能把“格有两个链头”理解成“占用校验扫两个链头” | `EVIDENCE/t1_47C620_full.txt:24-52,67-84`、`EVIDENCE/t2_wrapper_and_8c_cellclass.txt` |
| D4 | 台账 §685-1（约 L12674 起）：`0x47E8A0` 全文关键分支“尾插/头插” | 本卡全文复核：对 WhatAmI==6 对象确有“走到链尾再 `tail->next=self; self->next=0`”；对其他对象在 `[+0x8C]` 选中的头上“`self->next=head; head=self`”，但多了“`head->next==self` 则跳过”的去重判断 | **细化**：去重只查第二节点，未做全链去重；不足以单独保证同格唯一 | `EVIDENCE/t1_callers_and_t2_attach.txt:505-662` |
| D5 | R14-R12 / 派卡提醒：`0x43F658 cmp ebp,3` 不是 mode 门控 | 本卡同意并限定：主循环路径 `0x43F241 xor ebp,ebp` ⇒ ebp 是计数器；只有短路路径 `0x43F188 mov ebp,[esp+0xBC]` 到达定义唯一时才是 mode 判定（mode 3 跳过 can-place#2） | **一致**，显式登记以防审计误判 | `EVIDENCE/t1_43F180_and_wrappers_and_whatami.txt`、`EVIDENCE/T1_SEMANTICS.md` |
| D6 | 台账 §958：CellClass GetSize `0x148` 双向闭合 | 本卡独立 RTTI 链 `TD 0x81CD70 → COL 0x7FD078 → vt 0x7E4EEC`，`v[12]=0x487E70=B8 48 01 00 00 C3`，12 处 `push 0x148` | **一致/独立复算**，无冲突 | `EVIDENCE/t4_factory_getsize.txt` |
| D7 | 台账 §675（已被 R14 §1 作废）：`0x43BCF0` = BuildingClass 构造函数 | 本卡未使用、未恢复该结论；BuildingClass 构造/分配只用 `push 0x720` 站点（15 处）作 GetSize 双支撑 | **登记作废索引遵守**，防止误引 | `R14_COMMON.md §1`、`EVIDENCE/t4_rtti_getsize.txt` |

无其它与台账直接冲突项。所有结论只用 `[已证]`/`[静态推断]`/`[未证]`；未改 `ra2youli\`，未改 `COVERAGE\coverage.tsv`，未 git commit/push。
