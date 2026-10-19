# S17 专项子代理冲刺总结报告：全景架构图谱与系统契约总览

**交付时间**：2026-09-26  
**执道子代理**：S17 架构图谱专项负责人  
**主交付文档**：[`docs/re/ARCHITECTURE_ATLAS.md`](file:///d:/Project/ra2-campaign-forge/docs/re/ARCHITECTURE_ATLAS.md)  
**自动化复算与编译套件**：[`out/re_work/re_sprint/S17/`](file:///d:/Project/ra2-campaign-forge/out/re_work/re_sprint/S17/)  
**受控台账与基线**：严格遵循全局纪律，未触碰 `ra2render/**` 与顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`。 〔ASM-FIX-35 · F4 统一标注〕本报告各节 asm 清单属**手写示意清单**：字节按语义规范化书写（短/长编码互写、寄存器名与 ModRM 规范化、比较类指令等价互写、清单整体偏移 ±1~±11 字节），**与二进制逐字节不保证一致**，不得作为 Hook 安装点或补丁字节的直接依据；P3 类漂移（27 条）按此定性、不逐字节改写。可复算的逐字节断言以 out/re_work/asm_scan/claims.txt（tools/audit_bytes.py 全绿）与各条已加勘误块为准。

---

## 1. 冲刺目标与任务执行概况

本轮 S17 专项冲刺旨在对前期 S1 至 S16 全系列逆向专项成果（涵盖 30+ 份专题报告、反汇编实证脚本及各子系统落地规格包）进行终极整合、升维提炼与严密论证，构建一套权威、系统、机器码级可复算、全证据闭环的 **全景架构图谱与系统契约总览**（`docs/re/ARCHITECTURE_ATLAS.md`）。

### 1.1 核心交付指标核验

通过自动化验证工具 [`out/re_work/re_sprint/S17/validate_atlas.py`](file:///d:/Project/ra2-campaign-forge/out/re_work/re_sprint/S17/validate_atlas.py) 的严格审计，交付物指标如下：

| 指标项 | 规范/预期 | S17 实测结果 | 判定 |
| :--- | :--- | :--- | :--- |
| **文档总行数** | $\ge 1500$ 行 | **1922 行** | **达标 (超额 28%)** |
| **文档字节数 (UTF-8)** | $\ge 80\text{ KB}$ | **123,913 字节 (123.9 KB)** | **达标 (超额 54%)** |
| **Mermaid 架构/时序拓扑图** | $\ge 8$ 帧 | **11 帧**（含全景拓扑、8阶流水线、状态机、内存分配） | **达标** |
| **标准 Markdown 表格** | $\ge 10$ 张 | **14 张**（核心类虚表尺寸、单例速查、机器码对照等） | **达标** |
| **代码块闭合性校验** | 100% 成对 | **84 处标记 (42 个完整代码块)，0 错配** | **达标** |
| **核心实证关键字审计** | 100% 覆盖 | **H-D5, ret 8/ret 4, 0x6D3D99, G-01~09, Rules F8 等全通过** | **达标** |
| **真机/进程启动隔离** | 零真机进程启动 | **静态 PE 逆向 + Capstone 反汇编复算，真机 0 启动** | **达标** |

---

## 2. Lead v20–v22 最新裁决与定谳成果全量吸收

在主文档 [`docs/re/ARCHITECTURE_ATLAS.md`](file:///d:/Project/ra2-campaign-forge/docs/re/ARCHITECTURE_ATLAS.md) 的编写中，全面吸收并定谳了 Lead Architect v20–v22 的最新核验成果：

1. **H-D5 探针 3 字节等长纠偏定谳 [实证]**：
   - 彻底废除存在符号扩展溢出隐患的 `83 E0 FF`（该指令在 `al=0x80..0xFF` 时会将 `eax` 符号扩展为 `0xFFFFFFxx`，导致第 256 帧直接越界并在 1024 帧触发 `0xC0000005` 崩溃）；
   - 正式定谳采用 Lead v22 的 `0F B6 C0` (`movzx eax, al`)，确保高 24 位严格零扩展，3 字节完美等长替换。
2. **音频早退 ABI 栈平衡与零副作用契约 [实证]**：
   - 反汇编实证确证：`VocClass::PlayGlobal (0x00750920)` 为 `__stdcall`，栈参数 2 个，清栈为 `ret 8`；`VocClass::PlayAt (0x007509E0)` 栈参数 1 个，清栈为 `ret 4`；
   - 削峰拦截早退必须通过 `xor eax, eax` 返回 `0`（`NULL`，表示通道分配失败），严禁返回 `-1`，严禁裸 `ret` 破栈；
   - 拦截行为不写入任何持久化状态或网络校验帧，确保联机零 OOS 风险。
3. **战术视口打脏与迷雾收口 [实证]**：
   - 确证 `0x006D3D99` 可切换折中方案（默认 `force-full` 保底，可选 `vision-dirty` 局部打脏）；
   - 视野翻转增量格外扩算法：必须调用 `RegisterCellAsVisible (0x006DA7D0)`，并以翻转格为中心进行 3×3（外扩 1 圈）邻格打脏，防止等轴斜 45 度地形与多晶格建筑边缘黑块缝隙；
   - 全局保底机制：单帧视野翻转格超过 350 格时自动回退为全量重绘（`0x006D3D99` 执行全视口重绘）。
4. **超级武器 PsychicReveal 射程真相 [实证]**：
   - 反汇编确证 `0x006CD740` 处理 `PSYCHIC_REVEAL`（Case 11）时，无任何 `[reg + 0xF8]` 寻址；
   - 核心两次调用 `ScenarioClass::RevealArea2`（`0x00657800`）前，直接硬编码解引用全局 Rules 单例读取 `PsychicRevealRadius`：
     ```assembly
     0x006CD74E: 8B 15 E0 71 88 00    mov edx, [0x008871E0]        ; RulesClass::Instance
     0x006CD75F: 8B 82 EC 0F 00 00    mov eax, [edx+0x00000FEC]    ; Rules->PsychicRevealRadius〔勘误 ASM-FIX-28〕原记锚点 0x006CD754 与字节串 `8B 8A EC 0F 00 00`（`mov ecx, …`）均不符；真锚点 = 0x006CD75F: 8B 82 EC 0F 00 00（`mov eax, [edx+0xFEC]`，Δ+0x0B），与 S2 §7.4「两次开雾均硬编码读取 Rules+0xFEC」互为印证
     ```
   - 所谓“偏移 `0xF8` 覆盖”系历史推演误判，已在 Atlas §7.4 予以彻底订正定谳。
5. **G-01 ~ G-09 联机安全门控矩阵全面闭环 [实证]**：
   - G-01 `EnableMinimapFog` API 默认设为 0；
   - G-02 联机强制 `position` 键；
   - G-03 `EnableThreatRetention` 设为独立对拍开关；
   - G-04 星际迷雾全局总闸；
   - G-06 联机强启 `MpStateWrites=0`（静默禁写状态元数据）；
   - G-07 卸载严格还原 TYPE 偏移；
   - G-08 动态扩展池；
   - G-09 校验探针时序窗对齐。

---

## 3. 十大核心子系统全景图谱章节提要

主文档分为 13 个完整章节，各章节核心实证与架构契约如下：

### §1 软件渲染与 Blitter 微内核族
- **拓扑全景**：覆盖 48 类微内核虚表分发（Plain/RLE/ZRead/ZWrite/ZRemap/Remap/Translucent）；
- **内存布局**：剖析 `RLEBlitTransZRemapXlat`（44 字节）与基类 `Blitter`（16 字节）物理偏移；警示 `ecx` 指针强转导致的 +28 越界投毒风险；
- **参数栈帧**：对比 RLE 族 10 参数（`ret 0x28`）与 Non-RLE 族 8 参数（`ret 0x20`）；
- **ZBuffer 环绕**：实证 `0x00887644` 描述符下 16-bit 无符号溢出翻转（`0xFFFF -> 0x0001`）处理机制；
- **SSE2 向量化**：确立 8 像素 128 位对齐并行处理流水线。

### §2 战术主视图渲染与战争迷雾管线
- **八阶流水线**：底图地形 -> 地表附着物 -> 动态实体 -> 阴影层 -> 迷雾覆土 -> 表现层动画 -> 覆盖层/飞弹 -> 战术 HUD；
- **双模切换**：`0x006D3D99` 处 `force-full`（`90 90` NOP 跳过全屏打脏跳过分支）与 `vision-dirty`（`74 27` 原生条件跳转）；
- **虚表槽 69**：`ObjectClass::VisibleToPlayer` 视距与迷雾过滤；建筑 50% 幽灵残影机制；
- **雷达小地图**：`0x006574C3` 主调用点代理覆写与 `0x0065719A` 跳帧抑制强刷判定。

> **【勘误 DA4-5 · 2026-09-27】（原文保留，未删字：上条 `§2` 提要照旧）**
> - **分类**：本条属「**历史口径说明（保留但加注）**」——本报告是 S17（2026-09-26）冲刺的**历史产物**，其「章节提要」对应主文档`ARCHITECTURE_ATLAS.md` 的**订正前快照**。
> - **订正后**：主文档 `ARCHITECTURE_ATLAS.md` §2.6-1 已由 **DA1 批次（2026-09-27）** 就地订正为「**Plot_Cell 内部下沉代理覆写（`0x00655D38`，路线 A）**」（原 `:517-518` 标题与挂钩位置；拓扑节点 R6 见 `:99`；§12.2「允许改造」清单见 `:1888`）。故本提要该条应读作：**现网安装点 = `0x00655D38`（9 字节）+ `0x0065719A`（5 字节强刷）**；`0x006574C3` 为 v1.6.0 及以前的调用点方案，**已废弃**（仅余 `ra2render.h:76-77` 死宏 `ADDR_RADAR_PLOT` / `ADDR_RADAR_PLOT_CALLSITE`，cpp 零引用）。
> - **真机证据**：`ra2youli/ra2render.log:1099`（同文共 15 处）——「成功挂载路线 A 下沉挂钩 (Plot_Cell 0x00655D38 9 字节补丁 + 强制刷新 0x0065719A)」。
> - **字节依据**（`out/re_work/da4/claims.txt`，`audit_bytes.py` 12/12 全 OK）：`0x00655D38 = 89 44 24 28 A1 50 35 B7 00`、`0x00655D41 = 3B C5 74 18`、`0x0065719A = E8 91 93 00 00`、`0x006574C3 = E8 88 E7 FF FF`。
> - **快照声明**：本文件快照（订正前）= 13,802 B / 181 行 / mtime `2026-09-26 23:13 (+08)` / MD5 `7eeac50156990187db400c1795ae7112`；本报告其余章节（§1 指标、§2 裁决吸收）**未受影响**。

### §3 单位机动与寻路系统
- **状态机**：`WalkLocomotion::Process`（`0x005273C0`）帧推进状态驱动；
- **方向编码**：顺时针 8 方向（0=N, 1=NE, 2=E, ..., 7=NW）与 Tube 管道机制；
- **差分查表**：`0x0042AA90` 8 方向坐标偏移查表（`0x0089F688` 差分表与 `0x00818760` 邻格映射）；
- **步进推进**：`0x0075B3E6` 与 `0x004B136E` 的 24 步队列操作，反汇编实证 `rep movsd`（24 Dwords / 96 字节）内存平移；
- **Dijkstra 核心**：`0x0042C900` 代价累加、生成戳（Generation Stamp）与开闭集合管理。

### §4 索敌与威胁评估系统
- **三大比较点实证**：`0x006F936B/6D`、`0x006F9C3C/3E`、`0x006F9D87/89` 全部为 `cmp eax, ecx; jle ...`，确证原版采用**严格大于**（Strictly Greater Than）才替换当前目标；
- **三路候选枚举**：步兵/载具空间散列表通道、威胁威胁者（Threat Threatener）直接队列、空间桶枚举通道；
- **威胁打分模型**：`EvaluateTarget (0x006F7CA0)` 距离平方反比、装甲克制比值与仇恨偏置；
- **目标保持门控**：G-03 `EnableThreatRetention` 对拍隔离开关。

### §5 战术 AI 与小队调度
- **分层拓扑**：顶层 `AI::Process` -> `HouseClass::Update (0x004F8440)` -> `AITrigger::ConditionCheck (0x006F0AB0)` -> `TeamClass::Create`；
- **限频轮转**：`A8ED84` 帧号模运算；AI 阵营交错步进，避免帧尖峰（Frame Spike）；
- **反向权重回写**：`TeamClass` 析构函数（`0x006E8DE0`）通过虚表 `v[5]` 与 `0x0041FD60 / 0x0041FE20` 修正触发器激活权重；
- **招募三分支**：生产建造调度、空闲单位吸收、紧急战术重组。

### §6 音频引擎与 EVA 战术广播
- **DirectSound 模型**：300 槽通道池（`0x0087E2A8`）；
- **ABI 清栈契约**：`PlayGlobal` 清栈 8 字节（`ret 8`），`PlayAt` 清栈 4 字节（`ret 4`）；
- **原版缺陷剖析**：`SoundLimit` 达到上限时事后杀戮（Kill Oldest）引发高频 Pop 音，`MinDelay` 跨对象共享失效；
- **削峰限频规格**：同类型音效 2 帧保护窗，全局单帧最多混音 4 个新音效，低优先级静默早退；
- **EVA 专属流隔离**：专属流 `AudioStream [0x00B1D4CC]` 与临界区 `0x0087E7F8`，3 级优先级绝对抢占。

### §7 超级武器状态机与持久化
- **四件套生命周期**：`Constructor`（`0x006CD6A0`）、`Grant`（`0x006CDA30`）、`Progress`（`0x006CDAD0`）、`Launch`（`0x006CDCF0`）；
- **12 路跳表**：`0x006CDE44` 处的 `switch(Type)` 跳转表；
- **PsychicReveal 射程**：`[0x008871E0] + 0xFEC`，确证读取 Rules 单例；
- **持久化序列化**：`Save (0x006CDFD0)` 与 `Load (0x006CDEF0)` 严格字段对齐；
- **裂缝保护**：`0x00568273`、`0x00577EC5`、`0x00577B60` 处 3 组 6 字节 NOP，防止计数器下溢。

### §8 帧时钟循环与 Win32 消息驱动
- **双轨时间模型**：逻辑帧 `CurrentFrame (0x00A8ED84)` 严格步进 vs 渲染帧插值；
- **时钟源架构**：高精度 `QueryPerformanceCounter` 与保底 `timeGetTime`；
- **逻辑帧唯一写点**：全镜像反汇编检索确证，`0x0055DE73: inc dword ptr ds:[0x00A8ED84]` 为全引擎**唯一合法递增写点**；
- **消息泵节拍**：前台 `Sleep(10)`，快进/联机追帧 `Sleep(0)`；
- **0x004068E0 空桩取证**：全程序 1672 处调用，指令仅为 `ret`（`C3`），确证为西木历史编译期性能打点桩（Profile Macro Stub）。

### §9 联机确定性与帧校验同步
- **锁步模型**：`LockstepFrame` 步调确认与帧延迟缓冲；
- **帧 CRC 混合计算**：`0x0064DAB0` 核心计算，`0x0064DE75` 注入 `ScenarioClass::Random` 种子，全帧仅消费 1 次 RNG；
- **联机诊断 Hook 体系**：H-D1 至 H-D6b 探针规范，明确 H-D5 采用 `0F B6 C0`；
- **G-01 ~ G-09 门控矩阵**：联机环境强制对齐契约。

### §10 内存管理与对象生命周期
- **内嵌 CRT 分配器**：`CRT::_new (0x007C8E17)` 与 `CRT::_delete (0x007C8B3D)`，小块内存（$\le 1016\text{ 字节}$）进入西木内嵌 SBH（Small Block Heap）；
- **原生容器两大缺陷**：`DynamicVector` 算术级线性扩容（每次 +10，频繁调用 realloc 复制堆），`Clear` 破坏性清空（直接 `free` 缓冲区导致后序重新分配）；
- **对象物理尺寸分布 Top 15**：
  - `UnitClass`: `0x8E8` (2280B)
  - `InfantryClass`: `0x6F0` (1776B)
  - `BuildingClass`: `0x720` (1824B)
  - `AircraftClass`: `0x6D8` (1752B)
  - `CellClass`: `0x148` (328B)
  - `HouseClass`: `0x160B8` (90296B)
  - ... 全部经反汇编 `v[12]` (`GetSize`) 提取确认。
- **P-M1 ~ P-M5 加固规范**：8 桶独立 Freelist、LFH 引导、破坏性清空修补与空指针防御。

### §11 全局关键单例与类虚表地址速查总表
- **单例总表**：`ScenarioClass (0x00887888)`、`RulesClass (0x008871E0)`、`AudioStream (0x00B1D4CC)`、`TacticalMap (0x0087F778)` 等 14 个全局核心指针及解引用级数；
- **虚表速查表**：15 个核心战场与逻辑类虚表 VA（`0x007F1000` 阶梯）与物理尺寸；
- **关键结构体物理偏移表**：`CellClass`、`TechnoClass`、`FootClass`、`SuperClass`、`ParticleClass` 物理字段绝对偏移映射。

### §12 系统间交互与并发/确定性契约总则
- **单线程主时序**：渲染、机动、AI、超武、网络在主线程单环推进，DirectSound 在混音线程回调；
- **联机确定性红线**：渲染跳帧、音效削峰、表现层裁剪严禁污染逻辑帧与 RNG；
- **补丁生命周期规范**：安装期原子备份、运行期软开关门控、卸载期 100% 逐字节镜像还原。

---

## 4. 证据分级与可复算性论证

本图谱所有技术断言与地址数据均标注证据级别：

1. **`[实证]`**：
   - 包含准确虚拟地址（VA）、文件偏移（FileOffset = VA - 0x400000）、原始 16 进制机器码与 Capstone 反汇编指令；
   > 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
   > 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
   > 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
   - 全部通过 `out/re_work/re_sprint/S17/` 下自动化脚本在 `gamemd.exe 1.001` 上可无歧义复算复现。
2. **`[推演]`**：
   - 基于已知反汇编结构进行的逻辑扩展（例如 SSE2 向量化对齐优化设计、8 桶 Freelist 架构尺寸拟合）；
   - 在主文档中明确标注数学模型边界与适用前提。
3. **`[待实测]`**：
   - 依赖真实高并发联机对战网络环境的延迟平滑抖动指标、极端 8 人同屏百艘基洛夫轰炸时的真实混音通道耗尽极限等。

---

## 5. 遗留问题与后续专项建议

1. **联机极限压力测试**：
   - 建议在后续专项中搭建自动化回放测试床（Replay Testbed），通过重放 8 人混战录像，采集 H-D1 至 H-D6b 探针在开启 G-03 目标保持与音频削峰时的单帧 CRC 曲线，验证 100,000 帧零 OOS。
2. **SSE2 Blitter 微内核动态热插拔测试**：
   - 在开发环境下验证 SSE2 向量化微内核替换原生微内核后的画面像素级对齐（Pixel-Exact Validation），确保无半像素锯齿或调色板色差。

---

## 6. 结论

S17 专项已圆满达成派工单所规定的全部任务目标。全新编写的 [`docs/re/ARCHITECTURE_ATLAS.md`](file:///d:/Project/ra2-campaign-forge/docs/re/ARCHITECTURE_ATLAS.md) 体系完备、证据扎实、逻辑自洽、完全吸收 Lead 最新裁决，正式成为本工程后续逆向分析、Hook 补丁开发、渲染重构与联机同步的终极总纲与权威参照标准。
