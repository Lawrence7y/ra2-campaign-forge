# S23 专项冲刺报告：真机恢复后的执行剧本 (execution_runbook.md)

> **任务标识**：S23 专项冲刺 · 真机恢复后的实施与应急 Runbook 编制  
> **责任代理**：Antigravity（逆向工程子代理）  
> **报告时间**：2026-09-27 01:30  
> **交付物**：
> 1. 主设计文档：`docs/re/execution_runbook.md`（全新文档，全长 14,000+ 字符，工程级无脑防呆执行与应急处置剧本）
> 2. 审计产物清单：`out/re_work/re_sprint/S23/claims_s23.txt`（31 条机器码与结构体锚点断言）
> 3. 自动化审计结果：`out/re_work/re_sprint/S23/audit_s23.json`（**31/31 全部 PASS，0 错误**）
> 4. 本总结报告：`docs/re/re_sprint_S23_report.md`

---

## 一、核心工作与研究成果总览

本轮 S23 专项紧密承接 Lead v25 补给单指示与第五波协同规划，针对即将到来的真机解冻阶段，为工程实施团队（ZCode / MiMo）编制了一份操作级、防呆防误的真机执行剧本（`docs/re/execution_runbook.md`）。全篇严格贯彻实证级标准，绝不含有模糊推测或占位伪代码。

### 1. 补丁落地顺序与分阶段实施规程
- **阶段 0 (Pre-Flight)**：确立基于 `tools/audit_bytes.py` / `verify_anchors.py` 的 100% PASS 门禁；明确公认 `.text` 哈希校验口径必须为 `raw(SizeOfRawData)`（长度 4,063,232 字节，SHA256: `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`），与 `out/reverse/symbols.json` 完美吻合；实证确认 PE 偏移 `0xAE`（`0x20` LAA）与 `0xB2`（`0x40`）属 `ra2opt` 正常固化特征，`.text` 纯净度 100%。
- **阶段 1 (P0)**：
  - **M-8 诊断套件**：确立 Cave 独立内存页（`0x01B00000`），严禁写入包含宿主签名 `Dtr\0` 的 `.detour` 节；落实 H-D5 `0F B6 C0`（`movzx eax, al`）防溢出修复，杜绝原版 `83 E0 FF` 符号扩展漏洞在 1024 帧写越 4KB 引发崩溃；落实 H-D1 EFLAGS ZF 无损检测与 H-D2 EAX 快照保护。
  - **M-10 裂缝保护与 SpySat 门控**：落地三处 6 字节 NOP（`0x00568273`, `0x00577EC5`, `0x00577B60`）消除 `Cell+0x134` 误清零副作用；落实 `0x00508F8F` 处的 2 字节 `74 65` $\to$ `EB 65` 无条件跳转；规范 G-07 TYPE 字段备份与卸载还原结构。
- **阶段 2 (P1)**：
  - **M-9 微粒迷雾剔除**：落地虚表槽 69 覆写（Particle `0x007EFA68` $\to$ `0x0062CEC0`, PSys `0x007EFCB0` $\to$ `0x0062E280`），己方微粒放行，敌方非直视微粒执行 `ret 8` 清栈早退。
  - **P-4 CRT 8 桶无锁内存池**：落地 `operator new`（`0x007C8E17`）与 `delete`（`0x007C8B3D`）挂钩；落实 P-M1（8B 头部对齐消灭 SSE/double 崩溃）、P-M2（Double Free 魔数投毒 `0xDEADBEEF`）、P-M3（双重硬件内存范围守卫 100% 穿透原生 free）、P-M4（无锁 CAS 原子入队出队）、P-M5（启动期单次锁定配置，严禁战局内动态热切）。
  - **P-5 音频削峰限频**：严格执行 ABI 平栈契约：`PlayGlobal`（`0x00750920`）早退必须 `xor eax, eax`（返回 NULL）且 `ret 8`；`PlayAt`（`0x007509E0`）早退必须 `xor eax, eax` 且 `ret 4`。
- **阶段 3 (P2)**：
  - **L4 视口局部打脏**：`0x006D3D99` 处支持 `force-full`（`E9 99 00 00 00 90` 全量保底）与 `vision-dirty`（原指令 `0F 8D 98 00 00 00`）双模切换；3×3 外扩打脏累计 $>350$ 格强行回退保底刷新；重申严禁挂钩 `0x0048D000`。

### 2. 逐项验收判据与遥测健康度指标体系
编制了包含 16 项遥测计数器的详细观察表，并制定了量化分级健康度基线：
- `syncEarlyLogCount` 与 `syncSnapshotsWritten`：正常对局恒为 0，一旦 $\ge 1$ 立即触发联机分叉应急处置；
- `gapProtectionPatchesInstalled`（3/3）与 `spysatGatePatchesInstalled`（1/1）：启动后瞬时校验；
- `poolDoubleFreesBlocked`：正常为 0，若检测到 $>0$ 表明成功拦截底层对象重复释放；
- `poolFallbacks / poolAllocs`：健康比率 $<25\%$，超过 $50\%$ 表明桶容量或步长需扩容；
- `fallbackToFullCount`：单帧翻转格超过 350 保底触发频率正常 $\le 2$ 次/分钟（仅超武/卫星）。

### 3. 原子回滚剧本与与 `ra2opt restore` 的交互规程
- **内存动态热卸载规范**：制定严格的五阶段倒序卸载方案（P2 视口 $\to$ P1 音频 $\to$ P1 微粒虚表 $\to$ P1 内存池 $\to$ P0 核心层与 G-07 TYPE 还原）；
- **核心红线**：**已池化内存不得热切**！若在对战局内强行卸载内存池，存活对象后续调 `free` 会跨堆释放直接触发 `0xC0000374` 崩溃。必须在对局结束退回主菜单后方可卸载；
- **与 `ra2opt` 的协同**：阐明 `ra2opt restore` 会将 PE 头 0xAE 处的 LAA 标志还原为 0，并冲刷 `ddraw.dll` 与 `ra2md.ini`。明确规范“先热卸载内存钩子、确认进程退出后，再操作磁盘文件”的标准作业规程。

### 4. 三大灾难性故障应急处置预案 (Disaster Playbooks)
- **故障 A（崩溃故障）**：制定针对 `0xC0000005`（区分 H-D5 符号扩展溢出、音频栈失衡、SSE 内存未对齐、常规空指针）与 `0xC0000374`（区分 P-M5 局内热切违规、P-M3 外部指针未穿透、P-M2 双释放越界）的排查判定树与 MiniDump 转储分析法。
- **故障 B（黑屏/卡死故障）**：制定 DirectDraw 表面 Lock 未配对 Unlock 导致的死锁排查规程、无锁 CAS 活锁排查规程、看门狗线程超时检测规程以及盲操逃生快捷键（`Ctrl+Shift+F12` 强制表面解锁与退回 `force-full`）。
- **故障 C（联机分叉故障 DESYNC）**：制定利用 M-8 H-D1 抓取早期分歧帧、H-D2 自动生成全量快照、提取 `g_MirrorRing[256]` 环二分查找首个差异帧，并逐块比对快照定位逻辑分歧字段（如 `CellClass+0x134` 裂缝保护是否未对齐）的标准排查作业树。

### 5. 真机恢复后首批闭环项清单 (纳入 RE-A 未决项)
将 RE-A 遗留的核心未决问题列为真机解冻首周专项攻坚任务，并制定了详尽的运行时挂钩抓取实施规程：
- **U-1（35 个存档块对象类名）**：在 `0x0067D300` 35 个 call 点或 `0x0067FDF0` 入口挂钩，拦截 `EDX`，解引用 `[EDX]` 虚表并向上寻址 `vtable[-1]` 获取 MSVC RTTI 类描述符，直接输出 `.?AVBuildingClass@@` 等 35 个类名；
- **U-2（魔数 0x2B898 落盘编码）**：在读档入口 `0x0067CF7D call 0x681080` 下硬件断点，单步追踪比较字节，并监控写侧 `0x0067D0C0` 输出流，确定魔数实际编码形态；
- **U-3（CurrentFrame 序列化归属）**：存盘触发时在 `0x00A8ED84` 设置内存读取断点，追踪调用栈定位其写入的流槽位及归属子系统；
- **U-9（[0x7E15C8] API 真实符号定名）**：进程启动动态链接完成后，直接读取 `0x007E15C8` 指向的绝对入口 VA，遍历 `ole32.dll` 导出表完成符号定名。

### 6. 文件系统加载层次与战役注入规程 (吸纳 RE-C 实证)
- **加载优先级铁律**：散装文件（`0x00473D2D`） $>$ `expandmd99.mix` $>$ `expandmd98.mix` $>$ … $>$ `ra2md.mix`；
- **铁律实证**：`0x0052CBA0` 处的 `FindFirstFileA("BATTLEMD*.INI")` 是 Win32 磁盘目录枚举，**无法穿透 MIX 容器**；因此“**MIX 内的 `BATTLEMD98.INI` 永远不会被引擎发现**”；而 MIX 容器内部的战役文件只能命名为 `BATTLEMD.INI`，且仅在**根目录无散装 `BATTLEMD.INI`** 时才通过 `0x0052CCCD` 回退机制加载；
- **战役发布推荐方案**：采用“散装 `BATTLEMD98.INI` + 自定义资源包 `expandmd98.mix`”方案，零侵入官方原版文件，并制定了残留文件检查与卸载清理 PowerShell 脚本。

---

## 二、31 项锚点断言复算与审计对拍表

实施 Python 自动化审计工具 `tools/audit_bytes.py out/re_work/re_sprint/S23/claims_s23.txt --json out/re_work/re_sprint/S23/audit_s23.json`，审计结果全量 100% PASS：

| 序号 | 目标 VA | 文件偏移 | 期望/实际机器码 (Hex) | 判定 | 对应的子系统与指令上下文 | 证据等级 |
|:---:|:---:|:---:|:---|:---:|:---|:---:|
| 1 | `0x0064C6F2` | `0x0024C6F2` | `0F 85 69 05 00 00` | **OK** | P-1.1 M-8 H-D1 (`jne 0x64CC61`) | `[实证]` |
| 2 | `0x0064CC61` | `0x0024CC61` | `A0 80 48 B0 00` | **OK** | P-1.2 M-8 H-D2 (`mov al, [0xB04880]`) | `[实证]` |
| 3 | `0x0064DE75` | `0x0024DE75` | `5F 5E 5D 5B 83 C4 14 C3` | **OK** | P-1.3 M-8 H-D5 尾声平栈指令 | `[实证]` |
| 4 | `0x0064C911` | `0x0024C911` | `E8 9A A3 E7 FF` | **OK** | P-1.4 M-8 H-D6 主事件流调用 (`call 0x4C6CB0`) | `[实证]` |
| 5 | `0x0064CC0A` | `0x0024CC0A` | `E8 A1 A0 E7 FF` | **OK** | P-1.5 M-8 H-D6b 次事件流调用 (`call 0x4C6CB0`) | `[实证]` |
| 6 | `0x00568273` | `0x00168273` | `89 99 34 01 00 00` | **OK** | P-2.1 M-10 Gap1 清零指令 (`mov [ecx+0x134], ebx`) | `[实证]` |
| 7 | `0x00577EC5` | `0x00177EC5` | `89 B8 34 01 00 00` | **OK** | P-2.2 M-10 Gap2 清零指令 (`mov [eax+0x134], edi`) | `[实证]` |
| 8 | `0x00577B60` | `0x00177B60` | `89 98 34 01 00 00` | **OK** | P-2.3 M-10 Gap3 清零指令 (`mov [eax+0x134], ebx`) | `[实证]` |
| 9 | `0x00508F8F` | `0x00108F8F` | `74 65` | **OK** | P-2.4 M-10 SpySat 门控跳转 (`je 0x508FF6`) | `[实证]` |
| 10 | `0x007EFA68` | `0x003EFA68` | `C0 CE 62 00` | **OK** | P-3.1 M-9 ParticleClass 虚表槽 69 (`0x0062CEC0`) | `[实证]` |
| 11 | `0x007EFCB0` | `0x003EFCB0` | `80 E2 62 00` | **OK** | P-3.2 M-9 ParticleSystemClass 虚表槽 69 (`0x0062E280`) | `[实证]` |
| 12 | `0x007C8E17` | `0x003C8E17` | `6A 01 FF 74 24 08` | **OK** | P-4.1 CRT `operator new` 入口指令 | `[实证]` |
| 13 | `0x007C8B3D` | `0x003C8B3D` | `FF 74 24 04 E8 A2 08 00 00` | **OK** | P-4.2 CRT `operator delete` 入口指令 | `[实证]` |
| 14 | `0x00750920` | `0x00350920` | `51 A0 AC 64 84 00` | **OK** | P-5.1 Audio `VocClass::PlayGlobal` 入口指令 | `[实证]` |
| 15 | `0x007509E0` | `0x003509E0` | `A0 AC 64 84 00` | **OK** | P-5.2 Audio `VocClass::PlayAt` 入口指令 | `[实证]` |
| 16 | `0x006D3D99` | `0x002D3D99` | `0F 8D 98 00 00 00` | **OK** | P-6.1 L4 视口模式切换判断 (`jge 0x6D3E37`) | `[实证]` |
| 17 | `0x0083D560` | `0x0043D560` | `98 B8 02 00` | **OK** | Savegame 版本魔数 (`0x0002B898`) | `[实证]` |
| 18 | `0x0055DE73` | `0x0015DE73` | `8B 15 84 ED A8 00` | **OK** | CurrentFrame 读取指令 (`mov edx, [0xA8ED84]`) | `[实证]` |
| 19 | `0x0055DE7E` | `0x0015DE7E` | `42` | **OK** | CurrentFrame 定常自增指令 (`inc edx`) | `[实证]` |
| 20 | `0x0055DE81` | `0x0015DE81` | `89 15 84 ED A8 00` | **OK** | CurrentFrame 写回指令 (`mov [0xA8ED84], edx`) | `[实证]` |
| 21 | `0x0067CF42` | `0x0027CF42` | `FF 15 C8 15 7E 00` | **OK** | U-9 `Game::Load` 调用 IAT `[0x7E15C8]` | `[实证]` |
| 22 | `0x0067DF08` | `0x0027DF08` | `BA 30 3E A8 00` | **OK** | RE-A 存档第 1 块实参传参 (`mov edx, 0xA83E30`) | `[实证]` |
| 23 | `0x0067DF0F` | `0x0027DF0F` | `E8 DC 1E 00 00` | **OK** | RE-A 存档第 1 块直接调用 (`call 0x67FDF0`) | `[实证]` |
| 24 | `0x0067E3A3` | `0x0027E3A3` | `BA D0 4B B0 00` | **OK** | RE-A 存档第 35 块实参传参 (`mov edx, 0xB04BD0`) | `[实证]` |
| 25 | `0x0067E3AA` | `0x0027E3AA` | `E8 41 2B 00 00` | **OK** | RE-A 存档第 35 块直接调用 (`call 0x680EF0`) | `[实证]` |
| 26 | `0x0052CBA0` | `0x0012CBA0` | `68 A8 61 82 00` | **OK** | RE-C `LoadBattleMdIni` 压栈 `"BATTLEMD*.INI"` | `[实证]` |
| 27 | `0x0052CBA9` | `0x0012CBA9` | `FF 15 08 12 7E 00` | **OK** | RE-C 调用 `kernel32!FindFirstFileA` | `[实证]` |
| 28 | `0x0052CCCD` | `0x0012CCCD` | `68 98 61 82 00` | **OK** | RE-C 回退压栈 `"BATTLEMD.INI"` | `[实证]` |
| 29 | `0x0052CCD6` | `0x0012CCD6` | `E8 15 6D F4 FF` | **OK** | RE-C 回退调用 `CCFileClass::CCFileClass` | `[实证]` |
| 30 | `0x00473D2D` | `0x00073D2D` | `E8 DE E1 FB FF` | **OK** | RE-C `CCFileClass` 散装文件优先探测 (`call 0x431F10`) | `[实证]` |
| 31 | `0x00473D68` | `0x00073D68` | `E8 C3 06 14 00` | **OK** | RE-C `CCFileClass` 回退调用 `MixFileClass::Find` | `[实证]` |

---

## 三、基线纯洁度与口径核实结论

本轮通过 Python 脚本对基线执行了交叉校验：
1. **.text 节区口径对齐**：
   - `raw(SizeOfRawData)` 口径：长度 4,063,232 字节（`0x3E0000`），MD5: `18d4815e3f67b0f78887c495b970d0b1`，SHA256: `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`；
   - 对拍：`out/reverse/symbols.json` 中记录的 `text_sha256` 严格为 `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`；
   - 裁定结论：**`raw(SizeOfRawData)` 口径为唯一正确口径**，若用 `Misc_VirtualSize` 计算会导致伪误报。
2. **PE 头差异溯源**：
   - 与 `ra2youli/.ra2opt/orig/gamemd.exe` 全文件逐字节比对，全镜像 4,825,360 字节中仅存在 2 字节差异：
     - 文件偏移 `0xAE`：`0x00` $\to$ `0x20`（COFF 特征位 `IMAGE_FILE_LARGE_ADDRESS_AWARE`，LAA）；
     - 文件偏移 `0xB2`：`0x10` $\to$ `0x40`（Optional Header 字段微调）；
   - `.text` 区段差异数严格为 **0**。这表明游戏原生代码未受任何侵入性篡改，全部逆向锚点 100% 有效。

---

## 四、向 Lead 与父代理报告的提炼要点

1. **交付闭环度**：
   - 目标文档 `docs/re/execution_runbook.md` 编制完成，涵盖：分阶段落地流程、16 项遥测指标健康基线、五阶段原子热卸载与 `ra2opt` 协同、三大灾难应急 Playbook、4 项真机首批闭环项方案、文件系统散装优先与战役注入规范。
   - 编写 scope 严格受控：仅修改目标文档与本报告文档，并在 `out/re_work/re_sprint/S23/` 沉淀了全部测试产物。
2. **重大工程风险提示**：
   - **红线 1**：CRT 内存池补丁（P-4）必须在游戏启动期单次锁定（P-M5），绝不可在战局内动态开关，否则 100% 触发 `0xC0000374`；
   - **红线 2**：散装 `BATTLEMD*.INI` 与 `expandmd98.mix` 具有不同优先级。MIX 内的 `BATTLEMD98.INI` 永远不会被加载，战役注入推荐直接投放散装 `BATTLEMD98.INI`。
3. **下一步行动建议**：
   - 待真机环境解冻后，工程实施方（ZCode）可直接参照 `docs/re/execution_runbook.md` 机械化执行落地测试；
   - 逆向团队根据 §6 规范，在真机调试会话中第一时间挂钩提取 U-1、U-2、U-3、U-9，达成最终大一统闭环。

---

## 【task-11 / `[v1.5.35]` 收尾补录】执行剧本 Phase 0 门禁固化（**不修改本报告原有正文**）

`docs/re/execution_runbook.md §2.1` 的**阶段 0（Pre-Flight）**已按 `[v1.5.35]` 结论固化为显式门禁 **G0**：

> **先跑 `python tools/verify_anchors.py`，要求 `323/323 PASS` 且 `.text` 基线（`raw(SizeOfRawData)` 口径）一致，方可进入 Phase 1。**

- **G0-1**：`断言总数 = 323` 且 `PASS = 323`（100.00%），`FAIL = 0`、`NOREAD = 0`；
- **G0-2**：`.text` 原始段 SHA256 = `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`（口径 `raw(SizeOfRawData = 0x3E0000)`，长度 4,063,232 B）；
- **G0-3**：未命中 `Misc_VirtualSize` 口径哈希 `bf9d56ae...`（命中 = 口径误报，须修正脚本重跑，**不得据此判 FAIL**）；
- **G0-4**：与 `ra2youli/.ra2opt/orig/gamemd.exe` 比对，仅允许偏移 `0xAE`（`0x00`→`0x20`，LAA）与 `0xB2`（`0x10`→`0x40`）两处差异；
- **G0-5**：`.detour` 原生签名 `40 00 00 00 44 74 72 00`（@ VA `0x00B93000`），**严禁写入该节**。

**唯一事实源**：`docs/re/anchor_claims.txt`（**323 条** = 43 + 79 + 77 + 124，去重规则见该文件头部）；
`out/re_work/{save_blocks,triggers,fs_mix}/claims.txt` 降级为来源留档，**不再作为断言基准**。

task-11 亲测：`python tools/verify_anchors.py` → `323/323 PASS`；`python tools/audit_bytes.py docs/re/anchor_claims.txt` → `OK=323, MISMATCH/NOREAD=0`。
