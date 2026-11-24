# S10-K1 · UNKNOWNS

| # | 未知项 | 状态 | 已尝试 / 下一步 |
|---:|---|---|---|
| U1 | `+0xB8` byte 标志的**读点** | `[未证]` | MissionClass 区 0x5B2E00..0x5B3B40 只有 6 处写（均写 0，`field_trace.txt`）。全 .text 的 `[reg+0xB8]` 命中绝大多数是其它类的 dword 字段（AITrigger+0xB8 Weight、VTable 等），无法可靠归属为 MissionClass 的 byte 读。需真机读该字节变化时机，或按类 layout 反查偏移量相同的字段是否复用。 |
| U2 | `+0xCC` handler 参数槽的**读点** | `[未证]` | 32 个 stub 均写 `mov [esi+0xCC], arg`（`dump_ai_dispatch.txt`），但 0x5B3B00 前的序列化块只读 +AC/+B0/+B4/+BC/+C8/+D0/+C0，不读 +CC。可能由各 Mission handler 内部读取，未逐一追。 |
| U3 | `0x709290 / 0x7091d0` 的敌对判据逐位语义 | `[未证]` | 已见 `[+0x2B4]`(目标)、`[+0x21C]`、`[+0x5D4]`、`[esi+0x14]>>2&1`、v[0x2AC]/v[0x330] 等判据（`ga_final.txt`），但各 v 槽名与关系位未解。Guard→Attack 的"Mission 号切换"链已证，判据语义待 S13/S14 交叉。 |
| U4 | `UnitClass` 真实 vtable 地址 | `[未证]` | 猜测的 `0x7EF31C` 经 COL[-4] 校验为代码桩（`0x4104B0`），非 RTTI COL，已弃用；未定位到 UnitClass 的 TD。本卡 Mission 矩阵用 Foot/Infantry/Aircraft/Building 四类（RTTI 已验），Harvester 的 Harvest 实现 `0x522E70` 归 Infantry 表（来源 `dump_mission_vslots.txt`，ClassName 待二次确认）。 |
| U5 | 43 个非桩实现中"哪些 Mission_* 由哪个 YRpp 源名对应" | 部分 | 已按 Mission 号（==索引）与字符串表命名，非按源码符号名；未引用任何源码字符串作命名依据（纪律 17）。 |
| U6 | Ghidra 反编译交叉验证 | 未做 | 副本 `_ghidra\S10-K1` 已复制（W150，147MB）并已按任务要求"用完删副本"删除。capstone 全量反汇编 + 数据表双通道已满足两项独立证据要求，未启动 headless。 |

## 停机核验

- 核心数字 32 / 11 / 32 / 43 / `0x5B30C1` 均由 `work/` 脚本现算，与 LAYOUT/PROGRESS 一致；无凑数、无"N/N 通过当证据"。
- 未发现与 `R14_COMMON §1` 作废索引、`R14_COMMON §8` 六类错源冲突之处；写"新发现"前已 grep 主台账（仅见 S10 归属说明与 Census 统计，无 Mission 枚举/字段/派发结论）。
