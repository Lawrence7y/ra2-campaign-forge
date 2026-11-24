# S10-K1 · Mission 系统布局（RA2 · gamemd.exe · SHA256 73201CC0…F67476 · IB 0x400000）

> 卡号 S10-K1｜2026-11-17｜所有地址为 VA。证据见 `EVIDENCE/`，脚本见 `work/`。
> 分级：`[已证]`＝静态双重支撑／`[静态推断]`｜`[未证]`。discipline 10：EIP 权重≠调用频率；本报告不据 EIP 判频率。

## 1 · MissionType 字符串表（枚举表）

- **指针表基址 `0x816CAC`，末址（exclusive）`0x816D2C`，共 32 项**（4B/项，0x80 B）。字符串实体在 `0x816D2C..0x816E77`（`.data`）。
- 双通道（互不依赖 function_atlas）：
  - 通道 A（数据结构）：`dump_ptr_table.txt` 逐项解引用 32 个指针，前一项 `0x816CA8 = 0`（非指针），后一个 dword `0x816D2C` 是 ASCII `Spyp`（字符串起点）⇒ 边界闭合。
  - 通道 B（代码）：`find_mission_xrefs.txt` 中 `0x5B3910` 函数 `mov esi,0x816cac` 循环到 `cmp esi,0x816d2c; jl`，步长 `add esi,4` ⇒ (0x816D2C−0x816CAC)/4 = 32。另有 10 处 `mov eax,[eax*4+0x816cac]`（`0x5B374D..0x5B3955`），证明该表按整数下标索引。

| idx | 名字 | idx | 名字 | idx | 名字 | idx | 名字 |
|---:|---|---:|---|---:|---|---:|---|
| 0 | Sleep | 8 | Capture | 16 | Unload | 24 | Open |
| 1 | Attack | 9 | Eaten | 17 | Sabotage | 25 | Patrol |
| 2 | Move | 10 | Harvest | 18 | Construction | 26 | Paradrop Approach |
| 3 | QMove | 11 | Area Guard | 19 | Selling | 27 | Paradrop Overfly |
| 4 | Retreat | 12 | Return | 20 | Repair | 28 | Wait |
| 5 | Guard | 13 | Stop | 21 | Rescue | 29 | Attack Move |
| 6 | Sticky | 14 | Ambush | 22 | Missile | 30 | Spyplane Approach |
| 7 | Enter | 15 | Hunt | 23 | Harmless | 31 | Spyplane Overfly |

核心映射（任务点名）：`Move=2, Attack=1, Guard=5, Harvest=10, Return=12, Stop=13, Capture=8, Enter=7`。全部 `[已证]`。

## 2 · MissionClass 字段表（Mission 调度结构）

MissionClass RTTI：vtable `0x7EDCC0` → COL `0x805D28` → TD `0x817B18`（name@TD+0xC = `0x817B24` = `.?AVMissionClass@@`）。`[已证]`（TD 名逐字符核对，`rtti_verify.txt`）。

| 偏移 | 宽 | 类型 | 写者 | 读者 | 语义 | 级 |
|---|---:|---|---|---|---|---|
| +0xAC | 4 | MissionType | `5B2FEF`,`5B357F`,`5B3675`,`5B36BB` | `5B3040`(GetCurrentMission),`5B30B2`(派发下标),`5B3A00`,`6FA697` | **当前 Mission** | 已证 |
| +0xB0 | 4 | MissionType | `5B367B`,`5B368C`,`5B36C1`(=−1) | `5B36B0`,`5B3A10` | 前一/备用 Mission（栈式回退；−1=空） | 已证 |
| +0xB4 | 4 | MissionType | `5B2FEF`(=−1),`5B3585`(=−1),`5B3614` | `5B304B`,`5B3570`,`5B3605`,`5B39A8` | **排队/Next Mission**（−1=无；QueueMission 写此处） | 已证 |
| +0xB8 | 1 | bool | `5B2FF9`,`5B35BF`,`5B361A`,`5B3681`,`5B3698`,`5B36CB`（均写 0） | 全镜像 byte 读点未能可靠归属（dword 同名偏移干扰） | Mission 标志位（切换时清零） | 静态推断 |
| +0xBC | 4 | int | `5B2FFF`,`5B359C`(写 0) | `5B39A8`,`4DA2C6`(Foot.Retreat 用作子状态计数) | 子状态/计时器 | 已证 |
| +0xC0 | 4 | frame | `5B300A`,`5B35B3`(写 frame@`0xA8ED84`) | `5B39E1` | Mission 设定帧戳 | 已证 |
| +0xC4 | 4 | int | `5B3010`,`5B35B9`(写 0),`6FA64E`(inc) | `6FA646` | Mission tick 计数（TechnoClass::AI 每帧 ++） | 已证 |
| +0xC8 | 4 | frame | 32 个派发 stub 写 `frame` | `5B307A`,`5B3A20` | 上次 handler 执行帧（节流起点） | 已证 |
| +0xCC | 4 | int | 派发 stub 写栈参 | 未定位 | handler 参数槽 | 静态推断 |
| +0xD0 | 4 | int | 派发 stub 写 handler 返回值 | `5B3080`,`5B3A26` | handler 返回节流值（帧数）；`frame−[C8]<[D0]` 则跳过 | 已证 |
| +0x6C | 4 | int | 外部 | `5B30A7`(`test/jle`) | Mission::AI 使能门（≤0 则跳过派发） | 静态推断 |

**字段数 = 11**（其中 9 项 writer+reader 双支撑 `[已证]`，2 项 `[静态推断]`）。独立交叉：序列化块 `0x5B397E..0x5B3A26` 顺序读 `+0xAC,+B0,+B4,+BC,+C8,+D0,+C0`（`field_trace.txt`），与写点集合一致。

## 3 · Mission 派发机制（核心问题 3 答案）

**不是"每 Mission 一个独立虚函数入口"，也不是纯跳转表——是两级混合：**

```
TechnoClass::AI (0x6F9E50)
  └─ call 0x5B3060 @ 0x6FA655        ; 先 inc [esi+0xC4]
       └─ MissionClass::AI (0x5B3060) v[23]
            ├─ 门控: [+0x90]!=0, frame−[+0xC8]>=[+0xD0], [+0x6C]>0
            ├─ mov eax,[edi+0xAC] ; cmp eax,0x1F ; ja default @ 0x5B30B8/BB
            └─ jmp [eax*4 + 0x5B34E8] @ 0x5B30C1   ← 派发点
                 → 32 个 stub (0x5B30C8..0x5B34C4)
                     → mov edx,[edi]; mov ecx,edi; call [edx+slot]  ; slot=0x204..0x270 = v[129]..v[156]
```

- **派发表地址 `0x5B34E8`，项数 32**（`dump_ai_dispatch.txt`；表后 `0x5B3568` 起为 `0x90909090` 填充，且 `0x5B30B8 cmp eax,0x1F / ja` 独立佐证 ≤31）。
- 表项 → stub → **v 槽**：mission 0→v129(0x204)、1→v132(0x210)、2→v139(0x22C)、5/6→v135(0x21C)、8/17→v133(0x214)、10→v137(0x224)、12→v141(0x234)、13→v142(0x238)、7→v144(0x240)……完整 32 项见 `mission_dispatch_map.txt`。
- stub 统一形态：`call [vptr+slot]` 后写回 `[+0xC8]=frame, [+0xCC]=arg, [+0xD0]=返回值`；基类默认实现 = 28 个 `mov eax,0x1C2; ret` 空桩（`0x5B2E10..0x5B2FC0`，每 0x10B）。`[已证]`

## 4 · 核心 Mission_* 实现清单

非桩实现 **43 个**（7 张 vtable 的 v[129..156] 去重，排除 `0x5B2E10..0x5B2FD0` 空桩；`rtti_and_counts.txt`）。下表为任务点名核心 Mission 的**首选实现**（FootClass/派生类，详见 `mission_dispatch_map.txt` 全 32×7 矩阵）：

| Mission | FootClass | InfantryClass | AircraftClass | BuildingClass |
|---|---|---|---|---|
| Attack(1) | `4D4DC0` | `51F3E0` | `417FE0` | `44ACF0` |
| Move(2) | `4D4200` | `51F660` | `4166C0` | (桩) |
| Guard(5)/Sticky(6) | `4D5070` | `51F620` | `41A5C0` | `4496B0` |
| Capture(8)/Sabotage(17) | `4D4B20` | `4D4B20` | `4D4B20` | `44B760` |
| Harvest(10) | (桩) | `522E70` | (桩) | `44B770` |
| Return(12) | (桩 `5B2ED0`) | 桩 | 桩 | 桩 |
| Stop(13) | (桩 `5B2EE0`) | 桩 | 桩 | 桩 |
| Enter(7) | `4D9290` | `4D9290` | `419C80` | (桩) |
| Hunt(15) | `4D5350` | `51F540` | `414A80` | 桩 |
| Retreat(4) | `4DA2C0` | `4DA2C0` | `415A50` | 桩 |
| Unload(16) | `4DA2B0` | `51F6E0` | `4151E0` | `44D880` |
| Area Guard(11) | `4D6AA0` | `51F640` | `41A940` | `449A40` |
| Patrol(25) | `4D4280` | `4D4280` | `417300` | 桩 |

`Foot.Move 0x4D4200` 读 loco `[esi+0x674]`、调 `[loco+0x10]`、`[esi+0xB4]==-1` 门控（`disasm_mission_handlers.txt`）——语义与 Move 一致。`[已证]`

## 5 · Guard → Attack 状态机触发点

链路（均有反汇编证据；`ga_final.txt`/`mission_call_sites.txt`/`queue_mission_xrefs.txt`）：

1. **判据采集**：`0x709290`（auto-acquire 判定）内含 `[esi+0xAC]==2(Move)/0xA(Harvest)/5(Guard)` 的 mission 门（`0x7092E6` 对 Move；`0x7094E0` 函数对 `2/0xA/5` 返回 true），并查 `[+0x2B4]`(当前目标)、`[+0x21C]`、`[+0x5D4]` 等，调 `0x7091d0`（威胁/可攻击判定，含 `[edx+0x2AC]` 判定）。
2. **包装**：`0x709480` 调 `0x709290` @ `0x709489`；命中则取 `[0xA8ED84]`(frame) 写 `[+0x4FC]`，通过 `[edi+0x48]`/`[edi+0x39C]` 设定新目标；若 `[+0x2B4]` 目标改变则写 `byte [+0x50C]=1` @ `0x7094C8`。
3. **Mission 切换调用点**：`call [vptr+0x1E8]`（QueueMission, v[122]）@ **`0x414B9E`**：`push 0; push 1; mov ecx,esi; call` ⇒ `QueueMission(MISSION_ATTACK=1, 0)`；前置判据 `[esi+0x2B4]!=0`（有目标）。同族还有 `0x415C05`(push 2)、`0x419CF9`(push 2) 等按目标类型分派。
4. **落地**：`QueueMission (0x5B35E0)` 把 1 写入 `[+0xB4]`（queued）@ `0x5B3614`；随后 `SetMission2 (0x5B3570, v[123])` 把 `[+0xB4]→[+0xAC]` 并清 queued（`0x5B357F/0x5B3585`）⇒ 下一帧派发走 Attack 的 v[132] 槽。
- 限定：`0x709290`/`0x414B9E` 的具体"敌对判据语义"（WhatAmI/关系位）未逐位展开，标 `[静态推断]`；Mission 号切换与派发链为 `[已证]`。

## 6 · 与 FootClass::AI (0x4DA530) 的关系

- `FootClass::AI` v[23]=`0x4DA530`（size 2520B/722 指令，atlas）；其**首段** `0x4DA539: call 0x6F9E50` → `TechnoClass::AI`。
- `TechnoClass::AI (0x6F9E50)` 在 `0x6FA655` 直接 `call 0x5B3060`（MissionClass::AI），前一句 `0x6FA64C..0x6FA64F: inc [esi+0xC4]`（mission tick++）。
- 因此 Mission 派发位于 **FootClass::AI → TechnoClass::AI 的前段调用链内**，不在 `frame%N` 门控的 60 条（`0x4DA56E..0x4DA63B`，应答/声音）里；**每帧都跑**。
- 纪律 10：本结论依据"该 call 位于函数序言后无条件执行路径 + 不在被门控区间"，**不依据 EIP 权重**。
- 附：`FootClass::AI` 内 `0x4DAEF3 call [edx+0x5C]`（v[23]）是对子对象 `esi=[old+0x694]→[+0x69C]` 的调用，非本单元自身 AI（`footai_tail.txt`）。`0x4DA877 call [ecx+0x40]`（locomotion slot16）在 `0x4DA63B` 之后，亦每帧。
