# ARCHITECTURE_ATLAS 悬空 VA 机器断言与缺等级小节标签 · P1 报告

> **任务来源**：`docs/RE_COORDINATION.md` 派工 v93 / P1  
> **执行范围**：只读 `ra2youli/gamemd.exe` + `docs/re/ARCHITECTURE_ATLAS.md`（及 REV 报告）；产物仅写 `out/re_work/va_claims/**` 与本文件  
> **基线二进制**：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（本批校验一致）  
> **ImageBase**：`0x00400000`；`.text/.rdata/.data` 上 `FileOffset = VA - 0x00400000`（与 `tools/audit_bytes.py` 段映射等价）  
> **真机**：0 启动 / 0 注入 / 二进制未写

---

## 0. 交付物清单

| 产物 | 路径 | 说明 |
|---|---|---|
| 机器断言库 | `out/re_work/va_claims/claims_va_p1.txt` | 417 条，格式对齐 `claims_s23.txt` / `claims_R1.txt` |
| 字节审计 JSON | `out/re_work/va_claims/audit_va_p1.json` | `tools/audit_bytes.py` 输出 |
| 断言元数据 | `out/re_work/va_claims/claims_va_p1_meta.json` | VA/FileOff/汇编/优先级/章节归属 |
| 46 节标签建议 | `out/re_work/va_claims/grade_tags_p1.json` / `.md` | 人工校正后建议清单 |
| 生成脚本 | `out/re_work/va_claims/gen_claims_va_p1.py`、`gen_grade_tags_p1.py` | 可复跑 |
| 本报告 | `docs/re/va_claims_p1.md` | 方法 / 覆盖 / 标签 / 关键表 / §九草稿 |

---

## 1. 方法（离线静态，可复算）

1. **悬空 VA 来源**：直接采用 Lead 已产出的 `out/re_work/atlas_rev/lead/atlas_va_crosscheck.json` 中 `dangling` 字段（**482** 条唯一 VA），不重新定义“悬空”。
2. **映射与读字节**：按 PE 节表段映射（同 `tools/audit_bytes.py`）：
   - `.text`  base `0x00401000` raw `0x1000` size `0x3E0000`
   - `.rdata` base `0x007E1000` raw `0x3E1000` size `0x31000`
   - `.data`  base `0x00812000` raw `0x412000` size `0x6C000`（VirtualSize `0x367BE4`，**超出 raw 的部分为 BSS，无文件字节**）
   - `.rsrc` / `.detour` 的 `VA-rawptr ≠ 0x400000`，一律段映射；本批悬空 VA 未落入这两段。
3. **断言内容**：每条 = `VA + FileOffset + 期望 hex（原始字节）+ 首条汇编/dword 判读 + 章节归属 + atlas 行号`。
4. **反汇编**：capstone 5.0.7 x86-32，仅对 `.text` 指令流；`.rdata/.data` 对齐 dword 解出指针目标。
5. **证据等级**：本批断言全部可离线复算字节，统一标 **[实证]**（VA+FileOffset+原始字节+汇编）；**不伪造「实测」**（未启动游戏）。
6. **审计**：`python tools/audit_bytes.py out/re_work/va_claims/claims_va_p1.txt --json out/re_work/va_claims/audit_va_p1.json`。
7. **46 节标签**：以 `tools/atlas_audit.py` F4 口径（标题或其后 3 行须含 `[实证]`/`[推演]`/`[待实测]` 单标签）为准；组合标签 `[实证 + 推演]` 不被识别。建议清单经人工校正，**不改 atlas 本体**。

---

## 2. 覆盖率与审计结果

### 2.1 总量

| 指标 | 数值 |
|---|---:|
| 悬空 VA（crosscheck 唯一） | **482** |
| 本批已补机器断言 | **417** |
| 未能补断言 | **65** |
| 覆盖率 | **86.5%** |
| audit_bytes 总条数 | 417 |
| audit_bytes **OK** | **416** |
| audit_bytes **MISMATCH/NOREAD** | **1** |
| 机器断言真实不匹配 | **0** |

### 2.2 按类型

| kind | 条数 | 含义 |
|---|---:|---|
| code | 343 | .text 指令流入口/站点 |
| ptr-or-vtable | 50 | .rdata/.data 对齐 dword，解出代码/只读指针（虚表槽候选） |
| data | 19 | .rdata/.data 其余原始字节 |
| ret-stub | 4 | 以 C3 开头的返回桩 |
| pe-base | 1 | ImageBase / PE 头 |

### 2.3 按优先级（决策价值）

| 优先级 | 条数 | 定义 |
|---|---:|---|
| P1 | 154 | 补丁目标 / 虚表·单例 / 开火伤害 / 存档触发 / CRC·同步 / Hook 规格 |
| P2 | 91 | 章节关键词命中（加载/MIX/迷雾/分配/工厂等） |
| P3 | 172 | 其余悬空（结构仍有字节锚定价值） |

### 2.4 按 atlas 章节（悬空→已补，Top 20）

| 章节（截断） | 已补断言 |
|---|---:|
| 16. §16 武器/弹头/伤害与生产经济 (Weapons, Warheads | 60 |
| 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  | 59 |
| 17. §17 MIX 虚拟文件系统加载链 (MIX Virtual Files | 43 |
| 5. §5 战术 AI 与小队调度 (Tactical AI & Team Sc | 39 |
| 1. §1 软件渲染与 Blitter 微内核族 (Software Raste | 38 |
| 4. §4 索敌与威胁评估系统 (Targeting & Threat Asse | 29 |
| 21. §21 侧栏/选择 UI 与黑幕点击输入交互 (Sidebar/Sele | 21 |
| 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin | 21 |
| 11. 全局关键单例与类虚表地址速查总表 (Master VTable & Si | 19 |
| 10. §10 内存管理与对象生命周期 (Memory Management & | 19 |
| 7. §7 超级武器状态机与持久化 (Superweapon State Mac | 18 |
| 6. §6 音频引擎与 EVA 战术广播 (Audio Engine & EVA | 14 |
| 8. §8 帧时钟循环与 Win32 消息驱动 (Frame Clock Loo | 13 |
| 0. 架构综述与方法论准则 | 11 |
| 9. §9 联机确定性与帧校验同步 (Multiplayer Determini | 6 |
| 12. 系统间交互与并发/确定性契约总则 (Inter-System Inter | 3 |
| 22. §22 CRT 调用图、池风险与内联断言 (CRT Callgraph, | 2 |
| (none) | 1 |
| 目录 | 1 |

### 2.5 未能覆盖的 65 条及原因

**唯一原因：`.data` 虚拟段无文件字节（BSS）**。

- `.data` VirtualSize=`0x367BE4`，SizeOfRawData=`0x6C000`，raw 覆盖 VA 上界 = `0x0087E000`。
- 未覆盖 VA **全部 ≥ `0x0087E180`**，落在 BSS：文件中不存在可断言的原始字节。
- `tools/audit_bytes.py` 对这些地址同样报「虚拟段/无文件数据」，无法做 hex 断言（工具口径一致，非本批疏漏）。
- **替代取证路径**（供 Lead/后续流，需真机，本批未执行）：
  1. 运行时 dump `.data` BSS 页（调试器/注入读内存）；
  2. 或从 xref 反推：对引用这些全局的 `.text` 指令做绝对地址断言（间接锚定）；
  3. 存档/触发路径中 BSS 对象可改为断言**写点指令**（如 `mov [0x87E8xx], ...`）而非对象本体。

未覆盖 VA 清单（全部 virtual-no-raw）：

| VA | 段 | 所属章节 |
|---|---|---|
| `0x0087e180` | .data(virtual/no raw) | 6. §6 音频引擎与 EVA 战术广播 (Audio Engine & EVA |
| `0x0087e28c` | .data(virtual/no raw) | 6. §6 音频引擎与 EVA 战术广播 (Audio Engine & EVA |
| `0x0087e2a8` | .data(virtual/no raw) | 0. 架构综述与方法论准则 |
| `0x0087e75c` | .data(virtual/no raw) | 12. 系统间交互与并发/确定性契约总则 (Inter-System Inter |
| `0x0087e7f8` | .data(virtual/no raw) | 6. §6 音频引擎与 EVA 战术广播 (Audio Engine & EVA |
| `0x0087e828` | .data(virtual/no raw) | 8. §8 帧时钟循环与 Win32 消息驱动 (Frame Clock Loo |
| `0x0087e82c` | .data(virtual/no raw) | 8. §8 帧时钟循环与 Win32 消息驱动 (Frame Clock Loo |
| `0x0087e848` | .data(virtual/no raw) | 8. §8 帧时钟循环与 Win32 消息驱动 (Frame Clock Loo |
| `0x0087e8a4` | .data(virtual/no raw) | 1. §1 软件渲染与 Blitter 微内核族 (Software Raste |
| `0x0087e8b8` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0087f658` | .data(virtual/no raw) | 21. §21 侧栏/选择 UI 与黑幕点击输入交互 (Sidebar/Sele |
| `0x0087f770` | .data(virtual/no raw) | 21. §21 侧栏/选择 UI 与黑幕点击输入交互 (Sidebar/Sele |
| `0x0087f778` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x0087f7e8` | .data(virtual/no raw) | 7. §7 超级武器状态机与持久化 (Superweapon State Mac |
| `0x0087f7ec` | .data(virtual/no raw) | 16. §16 武器/弹头/伤害与生产经济 (Weapons, Warheads |
| `0x0087f7f0` | .data(virtual/no raw) | 16. §16 武器/弹头/伤害与生产经济 (Weapons, Warheads |
| `0x0087f7f4` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x00884d90` | .data(virtual/no raw) | 17. §17 MIX 虚拟文件系统加载链 (MIX Virtual Files |
| `0x00886b88` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x00886fa8` | .data(virtual/no raw) | 0. 架构综述与方法论准则 |
| `0x008871e0` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x00887314` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x00887324` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x00887330` | .data(virtual/no raw) | 8. §8 帧时钟循环与 Win32 消息驱动 (Frame Clock Loo |
| `0x00887640` | .data(virtual/no raw) | 11. 全局关键单例与类虚表地址速查总表 (Master VTable & Si |
| `0x00887644` | .data(virtual/no raw) | 目录 |
| `0x00887888` | .data(virtual/no raw) | 4. §4 索敌与威胁评估系统 (Targeting & Threat Asse |
| `0x0089c568` | .data(virtual/no raw) | 1. §1 软件渲染与 Blitter 微内核族 (Software Raste |
| `0x0089c8e8` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x0089c900` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x0089e3a0` | .data(virtual/no raw) | 17. §17 MIX 虚拟文件系统加载链 (MIX Virtual Files |
| `0x0089e790` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x0089e794` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x0089e7c6` | .data(virtual/no raw) | 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewport  |
| `0x0089ea40` | .data(virtual/no raw) | 15. §15 存档块与序列化全景 (Savegame Blocks & Ser |
| `0x0089f688` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f68c` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f690` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f694` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f698` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f69c` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f6a0` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x0089f6a4` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x008a0000` | .data(virtual/no raw) | 0. 架构综述与方法论准则 |
| `0x008a0360` | .data(virtual/no raw) | 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw |
| `0x008a0370` | .data(virtual/no raw) | 0. 架构综述与方法论准则 |
| `0x008a0394` | .data(virtual/no raw) | 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw |
| `0x008a03a0` | .data(virtual/no raw) | 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw |
| `0x008a0e88` | .data(virtual/no raw) | 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw |
| `0x008a0e8c` | .data(virtual/no raw) | 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw |
| `0x008a0e98` | .data(virtual/no raw) | 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw |
| `0x008a38e0` | .data(virtual/no raw) | 15. §15 存档块与序列化全景 (Savegame Blocks & Ser |
| `0x008b40c8` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x008b40cc` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x008b40d8` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x008b40e8` | .data(virtual/no raw) | 5. §5 战术 AI 与小队调度 (Tactical AI & Team Sc |
| `0x008b40ec` | .data(virtual/no raw) | 5. §5 战术 AI 与小队调度 (Tactical AI & Team Sc |
| `0x008b40f8` | .data(virtual/no raw) | 5. §5 战术 AI 与小队调度 (Tactical AI & Team Sc |
| `0x008b4108` | .data(virtual/no raw) | 11. 全局关键单例与类虚表地址速查总表 (Master VTable & Si |
| `0x008b4120` | .data(virtual/no raw) | 15. §15 存档块与序列化全景 (Savegame Blocks & Ser |
| `0x008b413c` | .data(virtual/no raw) | 3. §3 单位机动与寻路系统 (Locomotion & Pathfindin |
| `0x008b4178` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x008b41a8` | .data(virtual/no raw) | 14. §14 触发器脚本运行时 (Trigger Script Runtime |
| `0x008b41fc` | .data(virtual/no raw) | 9. §9 联机确定性与帧校验同步 (Multiplayer Determini |
| `0x008b4204` | .data(virtual/no raw) | 0. 架构综述与方法论准则 |

### 2.6 唯一 NOREAD 说明（`0x00400000`）

- 断言 `0x00400000 = 4D 5A`（MZ）成立，FileOffset=0；
- 但 `tools/audit_bytes.py` 的 `va2off` 只遍历节表，**不映射 PE 头**（首节之前），故报 NOREAD。
- 这是**工具覆盖缺口**，不是字节错误。手工核验：`gamemd.exe[0:2] == 4D 5A`。
- 如需门禁 100% PASS，可将该行移入附注；本批保留并在此声明。

---

## 3. 46 个缺证据等级小节 · 前置标签建议清单

`tools/atlas_audit.py` F4 要求每个 `###` 小节的标题或其后 3 行内出现单标签 `[实证]` / `[推演]` / `[待实测]`。
下列 46 节因使用组合写法（如 `[实证 + 推演]`）或完全未写标签而未命中。
**本批只给建议，不改 `ARCHITECTURE_ATLAS.md`（只读）**；Lead 可按「建议插入文本」列直接粘贴。

| # | 行号 | 小节 | 建议标签 | 一句依据 | 建议插入（标题下一行） |
|---:|---:|---|:---:|---|---|
| 1 | L205 | 0.1 逆向目标与可复算工程公理 | **[推演]** | 方法论公理与工程规约，非字节实证 | `证据等级：[推演] —— 方法论公理与工程规约，非字节实证` |
| 2 | L229 | 0.2 引擎核心分层与数据总线架构全景拓扑 | **[推演]** | 分层拓扑示意（mermaid），结构陈述为主 | `证据等级：[推演] —— 分层拓扑示意（mermaid），结构陈述为主` |
| 3 | L310 | 0.3 Lead v20–v22 终审裁决与落地准则吸收 | **[实证]** | Lead 裁决含可复算机器码纠正（如 83 E0 FF 符号扩展） | `证据等级：[实证] —— Lead 裁决含可复算机器码纠正（如 83 E0 FF 符号扩展）` |
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-HD5】改前：83 E0 FF；改后：0F B6 C0 (movzx eax, al) [严禁使用历史草案 83 E0 FF 符号扩展指令]；依据：errata_sync_master_table.md:25 (R-E10); ARCHITECTURE_ATLAS.md:315, 2196, 2665；分级：P2
| 4 | L441 | 1.2 对象内存布局差异与指针投毒隐患 [实证 + 推演] | **[实证]** | 主体为分配尺寸/入口字节实证，投毒项另注推演 | `证据等级：[实证] —— 主体为分配尺寸/入口字节实证，投毒项另注推演` |
| 5 | L608 | 1.6 吞吐量瓶颈评估与 SSE2 向量化设计 | **[推演]** | 撤回旧瓶颈口径后仅剩方向性评估与 SSE2 设计 | `证据等级：[推演] —— 撤回旧瓶颈口径后仅剩方向性评估与 SSE2 设计` |
| 6 | L2334 | 10.4 P-M1 ~ P-M5 五重加固架构规范 [推演 + 实证] | **[推演]** | P-M1~M5 加固架构规范，落地未实测 | `证据等级：[推演] —— P-M1~M5 加固架构规范，落地未实测` |
| 7 | L2539 | 12.2 联机确定性红线隔离总则 (Multiplayer Synchronizatio | **[推演]** | 联机确定性红线/隔离墙契约 | `证据等级：[推演] —— 联机确定性红线/隔离墙契约` |
| 8 | L2601 | 12.4 全项目补丁生命周期管理与回滚规范 (Patch Lifecycle & Rol | **[实证]** | 18 项补丁机器码等长平齐已字节级复算 | `证据等级：[实证] —— 18 项补丁机器码等长平齐已字节级复算` |
| 9 | L2675 | 13.1 真机挂起状态（当前闸门 = 关闭） | **[待实测]** | GATE-v1.6.0/MP 闸门均未放行 | `证据等级：[待实测] —— GATE-v1.6.0/MP 闸门均未放行` |
| 10 | L2686 | 13.2 UNVERIFIED / 未闭环清单 | **[待实测]** | UNVERIFIED 清单条目全部待真机 | `证据等级：[待实测] —— UNVERIFIED 清单条目全部待真机` |
| 11 | L2698 | 13.3 阈值新口径（2026-09-28 Lead 裁定，**取代**旧唯一色数阈值） | **[实证]** | Lead 2026-09-28 裁定生效阈值口径 | `证据等级：[实证] —— Lead 2026-09-28 裁定生效阈值口径` |
| 12 | L2710 | 13.4 两级过滤机制与放闸硬指标（放闸唯一合法路径） | **[推演]** | 两级过滤/放闸流程规格，非地址实证 | `证据等级：[推演] —— 两级过滤/放闸流程规格，非地址实证` |
| 13 | L2720 | 13.5 联机放闸前置（与 §9.4 / §12.2 联读） | **[待实测]** | Gate2/Gate3 未闭环，不得宣判 MP 可发布 | `证据等级：[待实测] —— Gate2/Gate3 未闭环，不得宣判 MP 可发布` |
| 14 | L2745 | 14.1 结论速览 | **[实证]** | 结论表条目带 VA 与 claims 锚点 | `证据等级：[实证] —— 结论表条目带 VA 与 claims 锚点` |
| 15 | L2896 | 14.10 与其它子系统的契约（点名） | **[实证]** | 跨系统契约点名含可复算地址 | `证据等级：[实证] —— 跨系统契约点名含可复算地址` |
| 16 | L2907 | 14.11 未闭环项 | **[待实测]** | 未闭环项均需真机/反汇编补证 | `证据等级：[待实测] —— 未闭环项均需真机/反汇编补证` |
| 17 | L2921 | 14.12 关键 VA 速查表（供 Lead 并入 §11） | **[实证]** | VA 速查表条目均可复算 | `证据等级：[实证] —— VA 速查表条目均可复算` |
| 18 | L2948 | 14.13 R5 勘误登记（本章范围内，源文档侧） | **[实证]** | 勘误登记含字节级改前改后 | `证据等级：[实证] —— 勘误登记含字节级改前改后` |
| 19 | L2962 | 15.1 结论速览 | **[实证]** | 存档结论含 OLE2 签名与调用点字节 | `证据等级：[实证] —— 存档结论含 OLE2 签名与调用点字节` |
| 20 | L3118 | 15.9 与其它子系统的契约（点名） | **[实证]** | 契约点名含块序/调用点 VA | `证据等级：[实证] —— 契约点名含块序/调用点 VA` |
| 21 | L3129 | 15.10 未闭环项 | **[待实测]** | 类名 RTTI 等需真机断点回填 | `证据等级：[待实测] —— 类名 RTTI 等需真机断点回填` |
| 22 | L3141 | 15.11 关键 VA 速查表（供 Lead 并入 §11） | **[实证]** | VA 速查表可复算 | `证据等级：[实证] —— VA 速查表可复算` |
| 23 | L3160 | 15.12 R5 勘误登记（本章范围内，源文档侧） | **[实证]** | 勘误登记字节级 | `证据等级：[实证] —— 勘误登记字节级` |
| 24 | L3355 | 16.6 §11 速查表并入建议：关键 VA 速查表（§16） | **[实证]** | §16 VA 速查表可复算 | `证据等级：[实证] —— §16 VA 速查表可复算` |
| 25 | L3382 | 16.7 §16 未闭环项（附可执行取证方法） | **[待实测]** | Verses 施加点等静态未闭环 | `证据等级：[待实测] —— Verses 施加点等静态未闭环` |
| 26 | L3528 | 17.6 §11 速查表并入建议：关键 VA 速查表（§17） | **[实证]** | §17 VA 速查表可复算 | `证据等级：[实证] —— §17 VA 速查表可复算` |
| 27 | L3555 | 17.7 §17 未闭环项（附可执行取证方法） | **[待实测]** | Cache 填充点等静态未定位 | `证据等级：[待实测] —— Cache 填充点等静态未定位` |
| 28 | L3716 | 18.6 Z 序两层模型与 Z 梯度 [实证 + 推演] | **[实证]** | Z 梯度/列表序有地址实证，模型含推演 | `证据等级：[实证] —— Z 梯度/列表序有地址实证，模型含推演` |
| 29 | L3756 | 18.9 落地 Hook 面（**仅纸面规格**，未落地）与确定性红线 | **[待实测]** | Hook 面仅纸面规格未落地 | `证据等级：[待实测] —— Hook 面仅纸面规格未落地` |
| 30 | L3769 | 18.10 未闭环清单 | **[待实测]** | 缓存池语义等未闭环 | `证据等级：[待实测] —— 缓存池语义等未闭环` |
| 31 | L3782 | 18.11 关键 VA 速查表 | **[实证]** | VA 速查表可复算 | `证据等级：[实证] —— VA 速查表可复算` |
| 32 | L3939 | 19.8 成本中心与仅绘制层限频点 [实证 + 推演] | **[实证]** | 包围盒尺寸/写点可复算，占比为推演 | `证据等级：[实证] —— 包围盒尺寸/写点可复算，占比为推演` |
| 33 | L3950 | 19.9 归因红线 | **[推演]** | 归因红线为契约性禁改清单 | `证据等级：[推演] —— 归因红线为契约性禁改清单` |
| 34 | L3956 | 19.10 未闭环清单 | **[待实测]** | v[65] 归属等未闭环 | `证据等级：[待实测] —— v[65] 归属等未闭环` |
| 35 | L3968 | 19.11 关键 VA 速查表 | **[实证]** | VA 速查表可复算 | `证据等级：[实证] —— VA 速查表可复算` |
| 36 | L4051 | 20.3 【勘误】两代口径收口表（以冲刺定谳为准） | **[实证]** | 两代口径收口表为定谳勘误 | `证据等级：[实证] —— 两代口径收口表为定谳勘误` |
| 37 | L4140 | 20.6 交叉引用与**落地状态**（与 §7.6 的关系）[实证 + 待实测] | **[实证]** | 落地状态检索可复算（ra2render 0 命中） | `证据等级：[实证] —— 落地状态检索可复算（ra2render 0 命中）` |
| 38 | L4149 | 20.7 确定性红线与联机门控 [实证 + 推演] | **[实证]** | 三处 6B NOP 目标 VA 字节可复算 | `证据等级：[实证] —— 三处 6B NOP 目标 VA 字节可复算` |
| 39 | L4160 | 20.8 未闭环清单 | **[待实测]** | 3×NOP 是否已被外部安装需真机读字节 | `证据等级：[待实测] —— 3×NOP 是否已被外部安装需真机读字节` |
| 40 | L4170 | 20.9 关键 VA 速查表 | **[实证]** | VA 速查表可复算 | `证据等级：[实证] —— VA 速查表可复算` |
| 41 | L4381 | 21.7 与其他子系统的契约与未闭环 [推演 + 待实测] | **[推演]** | 契约与红线以推演为主，含未闭环项 | `证据等级：[推演] —— 契约与红线以推演为主，含未闭环项` |
| 42 | L4392 | 21.8 关键 VA 速查表（并入 §11 用） | **[实证]** | VA 速查表可复算 | `证据等级：[实证] —— VA 速查表可复算` |
| 43 | L4482 | 22.2 调用者归属、模式归类与热路径契约 [实证 + 推演] | **[实证]** | CRT 簇站点字节可复算 | `证据等级：[实证] —— CRT 簇站点字节可复算` |
| 44 | L4497 | 22.3 sprintf 格式串治理三层契约 [实证 + 推演] | **[实证]** | sprintf 治理依据静态扫描命中 | `证据等级：[实证] —— sprintf 治理依据静态扫描命中` |
| 45 | L4509 | 22.4 池化落地风险契约（八威胁 ↔ 五加固 ↔ 四步验证）[推演 + 待实测] | **[推演]** | 八威胁↔五加固风险契约 | `证据等级：[推演] —— 八威胁↔五加固风险契约` |
| 46 | L4550 | 22.7 关键 VA 速查表（并入 §11 用） | **[实证]** | VA 速查表可复算 | `证据等级：[实证] —— VA 速查表可复算` |

### 3.1 标签分布

- **[实证]** × 26
- **[待实测]** × 11
- **[推演]** × 9

### 3.2 标签语义口径（对齐 EVIDENCE_STANDARD）

| 标签 | 含义 | 本批使用边界 |
|---|---|---|
| `[实证]` | VA + FileOffset + 原始字节 + 汇编，可离线复算 | 字节级断言、VA 速查、勘误前后字节 |
| `[推演]` | 由实证出发的结构/契约/设计推论 | 红线、规范、拓扑、风险模型 |
| `[待实测]` | 静态无法闭环，需真机/注入 | 闸门状态、未闭环项、纸面 Hook 规格 |

---

## 4. 关键地址表（补丁落地 / 结构理解决策向）

### 4.1 Size() 虚函数桩（对象物理尺寸直接实证）

形态：`B8 xx xx 00 00 C3` = `mov eax, imm32; ret`。对结构体声明与补丁越界判断为 P0 级。

| VA | FileOff | 期望 hex | 汇编 | 归属 |
|---|---|---|---|---|
| `0x0040d280` | `0x0000D280` | `8B 81 64 55 00 00 C3 90` | mov eax, dword ptr [ecx + 0x5564]; ret  | 21.1 类层次、单例与虚表槽机器复核 [实证] |
| `0x0041c170` | `0x0001C170` | `B8 D8 06 00 00 C3 90 90` | mov eax, 0x6d8; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x00426530` | `0x00026530` | `B8 C8 01 00 00 C3 90 90` | mov eax, 0x1c8; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x00459e70` | `0x00059E70` | `B8 20 07 00 00 C3 90 90` | mov eax, 0x720; ret  | 10.3 战场对象尺寸分布 Top 15 实证总表 [实证] |
| `0x0046b540` | `0x0006B540` | `B8 60 01 00 00 C3 90 90` | mov eax, 0x160; ret  | 10.3 战场对象尺寸分布 Top 15 实证总表 [实证] |
| `0x00487e70` | `0x00087E70` | `B8 48 01 00 00 C3 90 90` | mov eax, 0x148; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x00504730` | `0x00104730` | `B8 B8 60 01 00 C3 90 90` | mov eax, 0x160b8; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x005232f0` | `0x001232F0` | `B8 F0 06 00 00 C3 90 90` | mov eax, 0x6f0; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x0062d970` | `0x0022D970` | `B8 38 01 00 00 C3 90 90` | mov eax, 0x138; ret  | 10.3 战场对象尺寸分布 Top 15 实证总表 [实证] |
| `0x00630200` | `0x00230200` | `B8 00 01 00 00 C3 90 90` | mov eax, 0x100; ret  | 10.3 战场对象尺寸分布 Top 15 实证总表 [实证] |
| `0x006f0430` | `0x002F0430` | `B8 A0 00 00 00 C3 90 90` | mov eax, 0xa0; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x00746dd0` | `0x00346DD0` | `B8 E8 08 00 00 C3 90 90` | mov eax, 0x8e8; ret  | 11.2 核心类虚表与实例物理尺寸总表 [实证] |

### 4.2 虚表槽 / 代码指针（`.rdata` 对齐 dword，节选 25）

| VA | FileOff | 期望 hex | dword 目标 | 归属 |
|---|---|---|---|---|
| `0x007e1000` | `0x003E1000` | `F6 07 41 00` | dword=0x004107F6 (code/rodata ptr) | 0.1 逆向目标与可复算工程公理 |
| `0x007e11d8` | `0x003E11D8` | `2C F9 40 00` | dword=0x0040F92C (code/rodata ptr) | 8.2 时钟源架构：QPC 与 `timeGetTime`  |
| `0x007e1964` | `0x003E1964` | `40 42 4F 00` | dword=0x004F4240 (code/rodata ptr) | 21.1 类层次、单例与虚表槽机器复核 [实证] |
| `0x007e22a4` | `0x003E22A4` | `90 42 41 00` | dword=0x00414290 (code/rodata ptr) | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残影  |
| `0x007e23b8` | `0x003E23B8` | `B0 44 41 00` | dword=0x004144B0 (code/rodata ptr) | 1.8 Blitter Hook 覆盖率、接管优先级与真机插 |
| `0x007e2a50` | `0x003E2A50` | `60 02 41 00` | dword=0x00410260 (code/rodata ptr) | 11.2 核心类虚表与实例物理尺寸总表 [实证] |
| `0x007e5544` | `0x003E5544` | `20 68 49 00` | dword=0x00496820 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e5580` | `0x003E5580` | `E0 A7 49 00` | dword=0x0049A7E0 (code/rodata ptr) | 1.2 对象内存布局差异与指针投毒隐患 [实证 + 推演] |
| `0x007e55a4` | `0x003E55A4` | `50 62 49 00` | dword=0x00496250 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e55b0` | `0x003E55B0` | `80 A7 49 00` | dword=0x0049A780 (code/rodata ptr) | 1. §1 软件渲染与 Blitter 微内核族 (Soft |
| `0x007e55c4` | `0x003E55C4` | `A0 60 49 00` | dword=0x004960A0 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e56f0` | `0x003E56F0` | `20 A4 49 00` | dword=0x0049A420 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e56f4` | `0x003E56F4` | `60 4B 49 00` | dword=0x00494B60 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e5888` | `0x003E5888` | `40 A1 49 00` | dword=0x0049A140 (code/rodata ptr) | 1.8 Blitter Hook 覆盖率、接管优先级与真机插 |
| `0x007e594c` | `0x003E594C` | `20 2D 49 00` | dword=0x00492D20 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e5978` | `0x003E5978` | `00 A0 49 00` | dword=0x0049A000 (code/rodata ptr) | 1. §1 软件渲染与 Blitter 微内核族 (Soft |
| `0x007e597c` | `0x003E597C` | `00 2B 49 00` | dword=0x00492B00 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e59a8` | `0x003E59A8` | `C0 9F 49 00` | dword=0x00499FC0 (code/rodata ptr) | 1.8 Blitter Hook 覆盖率、接管优先级与真机插 |
| `0x007e59c0` | `0x003E59C0` | `A0 9F 49 00` | dword=0x00499FA0 (code/rodata ptr) | 1.2 对象内存布局差异与指针投毒隐患 [实证 + 推演] |
| `0x007e59d8` | `0x003E59D8` | `80 9F 49 00` | dword=0x00499F80 (code/rodata ptr) | 1.8 Blitter Hook 覆盖率、接管优先级与真机插 |
| `0x007e59f4` | `0x003E59F4` | `70 26 49 00` | dword=0x00492670 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e5a08` | `0x003E5A08` | `40 9F 49 00` | dword=0x00499F40 (code/rodata ptr) | 1.8 Blitter Hook 覆盖率、接管优先级与真机插 |
| `0x007e5a20` | `0x003E5A20` | `A0 9C 49 00` | dword=0x00499CA0 (code/rodata ptr) | 1. §1 软件渲染与 Blitter 微内核族 (Soft |
| `0x007e5a24` | `0x003E5A24` | `B0 12 49 00` | dword=0x004912B0 (code/rodata ptr) | 1.1 核心微内核虚表分发与拓扑全景 [实证] |
| `0x007e5a38` | `0x003E5A38` | `20 9F 49 00` | dword=0x00499F20 (code/rodata ptr) | 1.8 Blitter Hook 覆盖率、接管优先级与真机插 |

（完整 50 条见 `claims_va_p1.txt` / `claims_va_p1_meta.json`）

### 4.3 补丁/Hook 规格相关（P1 代码站点，节选）

| VA | FileOff | 期望 hex | 首条汇编 | 小节 |
|---|---|---|---|---|
| `0x004144b0` | `0x000144B0` | `A0 6B ED A8 00 81 EC C4` | mov al, byte ptr [0xa8ed6b] | 1.8 Blitter Hook 覆盖率、接管优先级与真 |
| `0x00415ee0` | `0x00015EE0` | `55 8B EC 83 E4 F8 83 EC` | push ebp; mov ebp, esp | 16.1 开火链拓扑与 v[243] 分发契约 [实证] |
| `0x004165c0` | `0x000165C0` | `8B 44 24 1C 83 EC 0C 8B` | mov eax, dword ptr [esp + 0x1c]; sub esp | 16.4 伤害结算两条路径、子类覆写矩阵与 RNG 消费 |
| `0x0042302c` | `0x0002302C` | `8B 16 8B CE FF 52 6C 85` | mov edx, dword ptr [esi]; mov ecx, esi | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残 |
| `0x0043d38c` | `0x0003D38C` | `33 FF 85 C0 0F 84 9A 00` | xor edi, edi; test eax, eax | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残 |
| `0x0043d3e4` | `0x0003D3E4` | `C1 E7 06 8A C3 0B F8 C1` | shl edi, 6; mov al, bl | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残 |
| `0x0043d3eb` | `0x0003D3EB` | `C1 E7 05 0B F9 66 0F B6` | shl edi, 5; or edi, ecx | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残 |
| `0x00442230` | `0x00042230` | `81 EC 8C 00 00 00 53 55` | sub esp, 0x8c; push ebx | 16.4 伤害结算两条路径、子类覆写矩阵与 RNG 消费 |
| `0x0044ff00` | `0x0004FF00` | `44 24 10 00 00 00 00 8B` | inc esp; and al, 0x10 | 16.5 FactoryClass 生产时钟 [实证]（ |
| `0x00450400` | `0x00050400` | `00 8B 96 14 07 00 00 4A` | add byte ptr [ebx + 0x71496], cl | 16.5 FactoryClass 生产时钟 [实证]（ |
| `0x0045b789` | `0x0005B789` | `A3 48 CD 89 00 66 89 5C` | mov dword ptr [0x89cd48], eax | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残 |
| `0x0045b79c` | `0x0005B79C` | `89 0D 4C CD 89 00 A3 50` | mov dword ptr [0x89cd4c], ecx | 2.5 虚表槽 69 多态对象视距剔除与建筑 50% 残 |
| `0x004664c8` | `0x000664C8` | `89 91 0C 01 00 00 8B 54` | mov dword ptr [ecx + 0x10c], edx | 16.2 BulletClass：装配 → 飞行 → 引 |
| `0x004664d2` | `0x000664D2` | `89 91 10 01 00 00 8B 54` | mov dword ptr [ecx + 0x110], edx | 16.2 BulletClass：装配 → 飞行 → 引 |
| `0x004664dc` | `0x000664DC` | `89 91 28 01 00 00 8A 54` | mov dword ptr [ecx + 0x128], edx | 16.2 BulletClass：装配 → 飞行 → 引 |
| `0x004664e6` | `0x000664E6` | `88 91 E0 00 00 00 8B 54` | mov byte ptr [ecx + 0xe0], dl | 16.2 BulletClass：装配 → 飞行 → 引 |
| `0x004664f6` | `0x000664F6` | `89 51 6C 33 D2 89 81 AC` | mov dword ptr [ecx + 0x6c], edx; xor edx | 16.2 BulletClass：装配 → 飞行 → 引 |
| `0x0046655d` | `0x0006655D` | `C2 1C 00 51 56 8B F1 B2` | ret 0x1c; push ecx | 16.2 BulletClass：装配 → 飞行 → 引 |

---

## 5. 抽样独立复算（非 audit_bytes 路径）

对 3 条断言用独立 Python 读文件核验（不经 claims 解析器）：

```
0x0041C170  FileOff=0x0001C170  B8 D8 06 00 00 C3 90 90   # mov eax, 0x6d8; ret
0x007F4730  FileOff=0x003F4730  60 02 41 00               # dword=0x00410260
0x00415EE0  FileOff=0x00015EE0  55 8B EC 83 E4 F8 83 EC   # push ebp; mov ebp, esp
```

与 `claims_va_p1.txt` 期望 hex 完全一致。

---

## 6. §九 台账草稿（供 Lead 合并，勿由本轨直接写顶层台账）

```text
[v1.x.x] P1 悬空 VA 机器断言补全 + atlas 缺等级小节标签建议
  范围: docs/re/ARCHITECTURE_ATLAS.md 悬空 VA 482 + F4 缺标签小节 46
  基线: gamemd.exe MD5 4f37486e5b0dbe2ae5f45aeee0f98367（只读，未写）
  产物:
    - out/re_work/va_claims/claims_va_p1.txt      （417 条机器断言）
    - out/re_work/va_claims/audit_va_p1.json      （audit_bytes: OK 416 / NOREAD 1）
    - out/re_work/va_claims/claims_va_p1_meta.json
    - out/re_work/va_claims/grade_tags_p1.json|.md （46 节标签建议）
    - docs/re/va_claims_p1.md                     （本报告）
  覆盖: 417/482 = 86.5%；未补 65 条全部为 .data BSS（无文件字节）
  证据等级: 断言全部 [实证]（VA+FileOff+hex+汇编，离线复算）；未启动真机
  标签建议: 46 节 → [实证]26 / [推演]9 / [待实测]11（建议插入文本已给）
  风险/残留:
    - 0x00400000 NOREAD 为 audit_bytes 不映射 PE 头（字节本身正确）
    - BSS 65 条需真机 dump 或写点指令间接锚定（方法见报告 §2.5）
    - 标签清单待 Lead 写入 atlas 后复跑 atlas_audit.py F4 归零
  自证:
    python tools/audit_bytes.py out/re_work/va_claims/claims_va_p1.txt --json out/re_work/va_claims/audit_va_p1.json
    → 417 条：OK=416 MISMATCH/NOREAD=1（NOREAD=PE 头工具缺口）
```

---

## 7. 残留风险与后续建议

| # | 残留 | 影响 | 建议 |
|---|---|---|---|
| 1 | 65 条 BSS VA 无 hex 断言 | 全局单例实例本体未锚定 | 真机 dump 或改为断言 `.text` 写点 |
| 2 | `audit_bytes` 不映射 PE 头 | 门禁差 1 条 | 可在工具侧补 PE 头映射，或将 `0x400000` 移出主 claims |
| 3 | 46 节标签仅建议未落盘 | F4 仍报 46 | Lead 按清单粘贴后复跑 `atlas_audit.py` |
| 4 | 语义归因未逐条展开 | 断言锚定字节，不锚定“函数名” | 各主题流按需在 claims 注释上追加符号名 |
| 5 | 本批未跑 `verify_anchors.py` 全库 | 与既有 323 条锚点无交叉 | 若需合库，先做同址字节一致性再合并 |

---

## 8. 越界与红线自证

- **未写** `ra2render/**`、`ra2youli/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/re/ARCHITECTURE_ATLAS.md`、`docs/re/ARCHITECTURE_ATLAS_REV.md` 及他人主题文档。
- **未启动**游戏 / 未注入 / 未改二进制（MD5 复核一致）。
- 证据用语：本批只标 `[实证]`（静态字节）与 `[推演]`/`[待实测]` 建议；**无任何伪造「实测」**。

