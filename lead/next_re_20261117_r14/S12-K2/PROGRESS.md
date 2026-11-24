# S12-K2 PROGRESS（静态支撑卡，②-b 同格判据）

| # | 结论 | 等级 | 证据路径 |
|---|---|---|---|
| T1-a | `0x47C620` = CellClass thiscall 逐格 can-place；3 栈参 (`ret 0xc`)；`[esp+d]` 集合 {0x10,0x14,0x1C,0x20,0x24}，max 0x24；参数区起点 0x1C，参数访问 0x1C/0x20/0x24 全部 ≥ 起点 | `[已证]` | `EVIDENCE/t1_47C620_full.txt`, `EVIDENCE/T1_SEMANTICS.md`, `work/t1_dump_47C620.py` |
| T1-b | `this` = `CellClass*`：10 个调用点中 `0x43F2AC` 等 `mov ecx,eax` 的 eax 来自 `0x5657A0 GetCellAt`（MapClass `0x87F7E8`）| `[已证]` | `EVIDENCE/t1_callers_and_t2_attach.txt`, `EVIDENCE/T1_SEMANTICS.md` |
| T1-c | 返回值仅 AL：1=可放（`0x47CA70`），0=拒绝（8 处 `xor al,al`）；调用方只 `test al,al` | `[已证]` | `EVIDENCE/t1_47C620_full.txt`, `EVIDENCE/T1_SEMANTICS.md` |
| T1-d | 占用判据 = **只扫 `[cell+0xE4]` 头 A 单链表**（next=`+0x30`），逐节点 `call [vptr+0x2C]` WhatAmI；6/0x24 直接拒，2 走附加检查；**全函数从不读 `[cell+0xE8]`** | `[已证]` | `EVIDENCE/t1_47C620_full.txt:24-52,67-84,120-183`, `EVIDENCE/T1_SEMANTICS.md` |
| T1-e | `0x43F218` can-place#1 先于 `0x43F2AE` 逐格校验、先于 `0x43F678` can-place#2、先于 `0x43F691` 挂链；#1 失败→`0x43F5D8` 调 base slot73 mode0 后 `al=0 ret`；#2 失败→`0x43F5E0` 直接 `al=0 ret`；逐格失败→`0x43F504` 跳回循环(跳过该格) | `[已证]` | `EVIDENCE/t1_43F180_and_wrappers_and_whatami.txt`, `EVIDENCE/T1_SEMANTICS.md` |
| T2-a | 链入格链的 worker `0x47E8A0` 全镜像只有 1 个调用者 `0x5684BB`（wrapper `0x5683C0` 内）；摘链 worker `0x47EA90` 只有 `0x5688EB`。无 `jmp [reg+0x124]`; `[reg+0x124]` 派发全镜像 **181 call / 0 jmp** | `[已证]` | `EVIDENCE/t2_all_attach_paths.txt`, `EVIDENCE/core_numbers.txt`, `EVIDENCE/t2_wrapper_and_8c_cellclass.txt` |
| T2-b | wrapper `0x5683C0` 恰 4 调用者：`0x415565`/`0x43F691`/`0x4D37DD`/`0x71BFF8`；名下有 RTTI：BuildingClass(`0x43F180`)、Aircraft/Foot/Infantry/Unit(`0x4D3780`)、TerrainClass(`0x71BFB0`)；`0x4151E0` RTTI fail-closed 不猜名 | `[已证]` | `EVIDENCE/t2_all_attach_paths.txt`, `EVIDENCE/t4_rtti_getsize.txt` |
| T2-c | `0x47E8A0` **不查占用**：按对象 `[+0x8C]` byte 选 `[cell+0xE8]`(非零)/`[cell+0xE4]`(零)；仅防“第二个节点等于本对象”，无全域去重；不同对象可直接链入同格 → “静态可能同格多对象” | `[静态推断]` | `EVIDENCE/t1_callers_and_t2_attach.txt:505-662`, `EVIDENCE/t2_wrapper_and_8c_cellclass.txt` |
| T2-d | 静态旁路条件：head B 对象不会被 `0x47C620` 扫描；`[0xA8E7AC]!=0` 时 `0x47C620` 立即返回 1；`[0xA8E9A0]==0` 时跳过两个 WhatAmI 扫描 | `[静态推断]` | `EVIDENCE/t1_47C620_full.txt:5-14,21-40,52-55`, `FEED_W177D.md` |
| T3 | `[+0x81]` = Limbo 标志（1=已 Limbo/不在世界；0=在世界）：写点 `0x5F4E9E mov byte [esi+0x81],1`（Limbo 成功尾，且 `0x5F4D45` 入口读它作幂等门控）；SetOwner `0x70158A/0x701664/0x701681/...` 读它门控 `[vptr+0x124]` 摘/挂 | `[已证]` | `EVIDENCE/t3_81_census.txt`, `EVIDENCE/T3_SEMANTICS.md` |
| T4 | RTTI 实测 + GetSize 双向：BuildingClass `vt 0x7E3EBC → 0x720`(15 处 push)、CellClass `vt 0x7E4EEC → 0x148`(12 处 push)、TerrainClass `vt 0x7F522C → 0xE0`(9 处 push) 全闭合；FactoryClass `0x74` 仅 v[12]，push 点 0 ⇒ 不闭合 | `[已证]`（前三）/`[未证]`（Factory 双向） | `EVIDENCE/t4_factory_getsize.txt`, `EVIDENCE/t4_rtti_getsize.txt`, `LAYOUT.md` |

### 给审计员的核心数字（可独立复算）
1. **`0x47C620` 判据读点 = 80**（全函数非栈内存 READ 操作数、80 个唯一指令点；脚本 `work/core_numbers.py`，输出 `EVIDENCE/core_numbers.txt`）。复算：`python work/core_numbers.py`；capstone `skipdata=True`、`detail=True`，过滤 `[esp]/[ebp]` 与 `op.access` 非 READ。
2. **“能进同一格”的静态路径条数 = 4 条 attach 实现路径 / 1 个 worker**（`0x5683C0` 的 4 个调用者；worker `0x47E8A0` 唯一调用者 `0x5684BB`；等价形式已查：`jmp [reg+0x124]`=0、数据段无 worker 指针）。复算：`python work/t2_paths.py` 看 `CALLERS of`/`DATA-SEGMENT` 段；`python work/t2_v73_modes.py` 给出 176 个 atlas 内 `call [reg+0x124]` 站点的 push-mode 分布（含 3 的站点 4 个），见 `EVIDENCE/t2_v73_mode_combos.txt`。
3. **`[+0x81]` byte 读/写 = 238/34（RMW=0）；dword `[+0x80]` 访问 = 905**。复算：`python work/t3_81_census.py`；全 `.text` capstone `skipdata=True`，遍历全部 op（不只 op0），`mem.disp==0x81 && op.size==1` 与 `disp==0x80 && size==4`。

### 结论一句话
静态上同格多对象**可能**（worker 不查占用且只扫 head A），但真机正常放置仍受 can-place + `0x47C620` head-A 校验约束；W177-D 应重点构造 head B / 绕过 can-place 路径。
