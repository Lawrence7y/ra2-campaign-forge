# S12-K2 LAYOUT（T4：RTTI 实测 + GetSize 双向核对；字段布局只做增量）

类名一律走 `COL + 0xC → TD + 8` 链，读不到即 fail-closed。证据：`EVIDENCE/t4_rtti_getsize.txt`,
`EVIDENCE/t4_factory_getsize.txt`, `EVIDENCE/t4_factory_names.txt`；脚本 `work/t4_rtti_getsize.py`,
`work/t4_factory_getsize.py`, `work/t4_factory_names.py`。

## 1. RTTI 实测类名（不预设、按槽值反查）

| slot73 值 | vtable | COL | TD | TD+8 名称 | 等级 |
|---|---|---|---|---|---|
| `0x43F180` | `0x7E3EBC` | `0x7FC360` | `0x818D60` | `.?AVBuildingClass@@` | `[已证]` |
| `0x4D3780` | `0x7E22A4`/`0x7E8C94`/`0x7EB058`/`0x7F5C70` | 各自 COL | 各自 TD | `.?AVAircraftClass@@` / `.?AVFootClass@@` / `.?AVInfantryClass@@` / `.?AVUnitClass@@` | `[已证]` |
| `0x6F4A70` | `0x7F4960` | `0x80C058` | `0x817B58` | `.?AVTechnoClass@@` | `[已证]` |
| `0x71BFB0` | `0x7F522C` | `0x80C3E0` | `0x842D48` | `.?AVTerrainClass@@` | `[已证]` |
| `0x4151E0` | 候选 `0x7E23BC` | `0x4144B0` | `0x8B5655C0`（越界） | **读不到 ⇒ fail-closed，不命名** | `[未证]` |

## 2. GetSize 双向核对（v[12] 的 `B8 imm32 C3` + 构造器 `push size`）

| 类 | vtable | GetSize VA | v[12] imm | `68 <size>` 分配点 | 闭合 |
|---|---|---|---|---|---|
| BuildingClass | `0x7E3EBC` | `0x459E70` | `0x720` (1824)，bytes `b8 20 07 00 00 c3` | 15 处：`0x44FAF8`,`0x44FD6E`,`0x45E806`,`0x45E883`,`0x473841`,`0x590554`,`0x595420`,`0x5A66B0`,`0x5A848F`,`0x5A94BF`,`0x5A967D`,`0x5CAB4B`,… | `[已证]` |
| CellClass | `0x7E4EEC` | `0x487E70` | `0x148` (328) | 12 处：`0x4063F5`,`0x469D99`,`0x48A3AC`,`0x4C3EAC`,`0x5663C3`,`0x566B96`,`0x6BBB03`,`0x6BF9BC`,`0x6C17BC`,`0x6E25BE`,`0x702351`,`0x74A2D5` | `[已证]`（与台账 §958 一致） |
| TerrainClass | `0x7F522C` | `0x71D2F0` | `0xE0` (224) | 9 处：`0x40A264`,`0x5A2BD6`,`0x5A4874`,`0x6BBC46`,`0x6BF3BC`,`0x71CB55`,`0x71DDD3`,`0x71DE13`,`0x7795D7` | `[已证]` |
| FactoryClass | `0x7E88D0` | `0x4CA760` | `0x74` (116) | **0 处** `push 0x74` ⇒ 只有单边 | `[未证]`（不得称闭合） |

`Aircraft/Foot/Infantry/Unit` 四类的 slot73 同为 `0x4D3780`（R14 §2.1 的“三者共用”由 RTTI 进一步扩为四类共用）。

## 3. 字段布局增量（只登记与 `re_atlas/kb/11_class_layouts.md` / 台账的差异）

`11_class_layouts.md` 覆盖的是触发器族，不含 S12 核心类；台账已入账的关键偏移列出对照。
**本卡没有发现可安全登记为“新偏移”的字段**：`+0x81`/`+0xE4`/`+0xE8`/`+0x30`/`+0x8C`/`+0x520`
均已在 R14 COMMON §2.2 / 台账 §959、§685-1、§951 入账。只登记以下证据/语义增量：

| 已入账偏移 | 本卡增量 | 写点 | 读点 | 等级 |
|---|---|---|---|---|
| ObjectClass `+0x81`（W177-C §959 LimboFlag，原为观测级） | 补“写+读双重支撑”闭环：Limbo 成功尾写 1；同函数入口读它做幂等门控；SetOwner 用它门控摘/挂 | `0x5F4E9E mov byte [esi+0x81],1`（`0x5F4D30` 内） | `0x5F4D45`（Limbo 入口）；`0x70158A`,`0x701664`,`0x701681`,`0x701757`,`0x7017C0`（`0x7014A0` SetOwner） | `[已证]` |
| ObjectClass `+0x8C`（台账 §685-1 链选择） | 本卡重新取证确认 `0x5684B1 mov dl,[edi+0x8C]` 送到 `0x47E8A0` 的 byte 参，选 head B(非零)/head A(零)；全镜像 byte 写 59 处 | `0x75C179`(=1), `0x75C193`(=0), `0x738041`, `0x7382B7`, … | `0x5684B1` | `[已证]` |
| CellClass `+0xE4`/`+0xE8`/`+0x30`（R14 §2.2 / §959） | `0x47C620` 只扫 `+0xE4`，**从不读 `+0xE8`**；worker `0x47E8A0` 按 `[obj+0x8C]` 选头 | `0x47E90B`,`0x47E91F`,`0x47EAC4`,`0x47EACF`,`0x47E8EB` | `0x47C657`,`0x47C683`,`0x47C712`,`0x47C79E`,`0x47C7D9` | `[已证]` |

### 明确不登记
- `cell+0x124` byte `test ...,0x3F` @`0x47C85F`：本卡只读到，未定位该类自己的写点 ⇒ 语义 `[未证]`，不新增为字段。
- `arg2+0x16BF/0x16BE/0x16B7/0xE58/0xE54/0xCCE`：在 `0x47C620` 读到，但 `arg2` 的类归属静态未闭合（调用点传入的是技术/建筑对象，未逐点 RTTI）⇒ 不登记为新字段，列 `UNKNOWNS.md`。
- `FactoryClass 0x74` 只有 v[12] 单边 ⇒ 不满足“构造点分配”双支撑，不称布局闭合。
