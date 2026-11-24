# S05-K1 · LAYOUT.md — `[未证]` 字段语义双重支撑取证（T3 增量）

> 筛法（脚本，不手抄）：`work/filter_s05.py` 从 `coverage.tsv` 筛 `subsystem=S05` 且 `grade='[未证]'` 或 `name` 以 `sub_` 开头 ⇒ **127 个**（[未证]102 + 无名127，并集 127，见 `work/s05_filter.txt`）。
> 全 `.text` 单遍扫描（capstone 5.0.7，`skipdata=True`，1,394,186 条指令，18,903 个不同 disp）见 `work/field_scan.py` / `EVIDENCE/field_access_scan.json`。
> 归属用「函数区间包含」（atlas 12,916 区间），**不用 `entry_at_or_before`**（纪律 17）。
> ⚠️ **字段偏移不能定语义**：下方每条都给该类自己的写点全集 + 读点采样（≥3），并显式区分「数据字段 `[reg+disp]`」与「虚表槽 `call [vptr+disp]`」——`+0x94`/`+0x1AC` 两种形态在同镜像并存，见 §3。

## 1. 双重支撑结论表（核心对象模型字段，8 条）

| 字段 | 宿主类 | 写点全集数 | 读点数 | 该类归属写/读 | 语义假设 | 分级 |
|---|---|---:|---:|---:|---|---|
| `+0x10` dword | AbstractClass | 6,847* | 14,329* | 1 / 2（抽象基类自身）；派生类 147(B)/96(U)/93(T)… | `UniqueID`（`AbstractClass::Save` @0x410418 序列化；ctor @0x410191 写 `0xFFFFFFFF` 哨兵） | **[已证]**（KB §22 双通道 + 本卡字节） |
| `+0x20` byte | AbstractClass | 3,099* | 6,671* | 1 / 2（自身）；`IsDirty` @0x410450 读 `!Dirty` | `Dirty` bool（setne 归一化；Save @0x410423 写出） | **[已证]** |
| `+0x74` byte | ObjectClass | 341 | 709 | 3 / 9 | 在世界中/在格中标志（构造 @0x5F394B=`bl`、@0x5F58F7=1；渲染消费端 0x48288C 读） | **[已证]** |
| `+0x80` byte | ObjectClass | 423 | 730 | 5 / 4 | 精灵级脏标记 NeedsRedraw（状态真变置 1、绘制消费清 0） | **[已证]** |
| `+0x81` byte | ObjectClass | 34 | 238 | 4 / 8 | Limbo 标志（1=离世界；Limbo 0x5F4D30 置 1、Unlimbo 0x5F4EC0 置 0/回滚置 1） | **[已证]** |
| `+0x94` dword | ObjectClass | 172 | 362 | 1 / 1（数据读在 0x4A9720/0x4A9770；上表"读"多为 `call [vptr+0x94]`） | 层索引（−1=无层），SetLayer 0x4A9720 写、RemoveFromLayer 0x4A9770 写 −1 | **[已证]**（KB §939/§928-3；本卡写点 172 与 §939 数字精确吻合） |
| `+0x21C` dword | TechnoClass | 12 | 1,288 | 4 / 196 | Owner `HouseClass*`（SetOwner 0x7014A0 @0x701735 写；读点 196 全部 Tech/Building/Infantry/Unit/Aircraft） | **[已证]** |
| `+0x1AC` — | TechnoClass | 20 | 111 | 0 / 3（均为 `call [reg+0x1AC]`） | **虚表槽 107（can-place 虚方法），非数据字段**；数据字段归属 `[未证]` | **[静态推断]**（形态证据），字段假设撤回 |

\* `+0x10`/`+0x20` 的全镜像计数被所有类共享前缀放大（每个 AbstractClass 后代都含该偏移），故以「抽象基类自身写/读 + `Save`/`IsDirty` 明确实例化」为支撑，而非全镜像计数。

## 2. 每条的写点/读点证据（引自 `EVIDENCE/field_access_scan.json`）

### +0x74（ObjectClass 在世界中）
- 写点全集 341；top 函数 `0x60CF00`(18), `0x530460`(11), `0x4B0F20`(9), `0x6A05F0`(9)。
- ObjectClass 归属写：`0x5F394B mov byte [esi+0x74],bl`（ctor 0x5F3900）、`0x5F58F7 mov byte [esi+0x74],1`、`0x5F5913 …bl`（0x5F5850 world predicate）。
- 读点采样（≥3）：`0x5F3F37`、`0x5F4F10`(Unlimbo)、`0x5F5879`、`0x5F58EC`、`0x5F590C`、`0x5F5FBB`。语义与 `kb/R14 §4.6`「渲染列表消费层 `[+0x74]!=0`」一致。

### +0x80（NeedsRedraw 脏标记）
- 写点全集 423；top `0x6E9140`(38, TRUCKB/TRUCKA)、`0x54BFF0`(8)、`0x5F8110`(8)、`0x6EFC70`(6)。
- 写 1 实例：`0x5F4D1A mov byte [ecx+0x80],1`（SetOwner 路径）；写 0 实例：`0x5F4EA5`/`0x5F4F55`/`0x6D98EF`。
- **陷阱已核**（`EVIDENCE/trap_verification.txt`）：`0x6D98EF` 字节 `c68680000000 00` = `mov byte [esi+0x80],0`，写值是 **0** 不是 1；不据此推"每帧无条件置位"（R14_COMMON §1 作废索引第 49 行、纪律 16）。
- 读点采样：`0x5F4B34`、`0x5F4D10`、`0x5F586B`、`0x5F62B4` + 绘制遍历器 `0x6D97D0/0x6D9920`（§925-1）。

### +0x81（Limbo）
- 写点 34；`0x44EBF0`(11)、`0x581140`(2)、`0x5F4EC0`(2)。ObjectClass 归属：`0x5F392A`(ctor=`al`)、`0x5F4E9E`(Limbo 置 1)、`0x5F4F4E`(Unlimbo 置 0)、`0x5F521C`(失败回滚置 1)。
- 读点 238；采样 `0x5F3E78`/`0x5F3FA4`/`0x5F452E`/`0x5F4B3E`/`0x5F4D45`/`0x5F4F02`/`0x5F5854`/`0x5F62D0`；SetOwner `0x7014A0` 6 处 +0x81 门控（已入账 §2.3）。

### +0x94（层索引，含形态陷阱）
- 数据写点全集 **172**，与 `R14_COMMON §4.7 / 台账 §939`「写点 172 → 对象字段 49 / 其它 112」的 **172** 精确吻合；本卡未重抄其细分，只独立复算总数。
- ObjectClass 数据写：`0x5F3987 mov dword [esi+0x94],ecx`（ctor）、`0x4A9720`(SetLayer)、`0x4A9770`(RemoveFromLayer，两处 −1 @0x4A97D2/0x4A982C)。
- **陷阱已核**（`EVIDENCE/trap_verification.txt`）：`0x636590` 内 `0x636595 mov ebp,ecx` ⇒ `ebp=this`，其 `mov [ebp+0x94],*` 是对象字段写，不是栈槽（曾被"base∈{esp,ebp}⇒栈槽"误判）；`0x695BC0` 同为成员函数序言。
- **形态陷阱**：扫描命中 `0x5F5C47 call dword [ebx+0x94]` —— 这是**虚表槽 37** 的调用，不是层索引读取。字段语义只由 `mov [obj+0x94],imm/reg` 与 `0x4A9770` 读取支撑；两类形态不得混算。

### +0x21C（TechnoClass owner）
- 写点 12，其中 TechnoClass 归属 4：`0x6F2D1B`(ctor 0x6F2B40)、`0x6F4610`(ctor 0x6F4500)、`0x701735`(SetOwner 0x7014A0)、`0x707A8E`。
- 读点 1,288；TechnoClass 归属 **196**（远超 ≥3 门槛）；采样 `0x6F3316`/`0x6F3589`/`0x6F3F43`/`0x6F49D2` 等。语义 `Owner HouseClass*` 与已入账 `0x7014A0` 一致（§2.3）。

### +0x1AC（撤回字段假设）
- 全镜像 `call [reg+0x1AC]` 20 处（如 `0x5F4471`、`0x700B75`、`0x700BFD`），这是虚表槽 107 的**虚方法调用**，不是对象数据字段。
- 数据字段读/写归属本类 0 ⇒ 按纪律 4 **不给字段语义**，`[静态推断]`（仅形态）。R14 §2.2 的"can-place `[+0x1AC]`"应理解为**虚槽 can-place 谓词**，非数据成员。

## 3. 本卡处理量
筛选得到 127 个 S05 `[未证]`/无名条目；其中 252 条带 `+0xNN` 的 `one_line` 里，**227 条是虚表槽偏移**（`ClassName::slotN (+0x4N)`），**25 条是对象字段相关**（+0x94 写点族 21 + +0x80 成员族 5，去重后 25）。本卡逐条双重支撑 8 个核心字段（§1），其余 119 个条目保留原级列 `UNKNOWNS.md`（不重抄已证、不臆造语义）。**处理字段/条目总数 8 ≤ 150**，符合上限。
