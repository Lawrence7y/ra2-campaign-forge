你是 RA2 Campaign Forge 逆向工程的静态分析卡 W33。任务：**纯离线静态定谳 `NextScenario` 的数据流与「打开下一关地图」的实际调用路径**，用以判决假设 H-A 与 H-B。

工作目录：`D:\Project\ra2-campaign-forge`

## 背景：两条互斥假设，本卡要判决

- **H-A「`NextScenario` 是死字段」**：官方 14 张 MD 图的 `[Basic] NextScenario` **全是 `GDI2A.map`**，而该文件在任何 MIX 容器与游戏目录散装中都不存在。若官方自己也走这个字段，官方点 `Continue` 也必然报同样的错。⇒ 战役推进实际可能按 `BATTLEMD.INI [Battles]` 的 `1..14` 序号走，`NextScenario` 是泰伯利亚之日的遗留字段。
- **H-B「`Scenario=` 走文件系统、`Continue` 推进走 MIX/CRC」**：官方图在 MIX 内（CRC 寻址），ra2forge 的 `ECH02.MAP` 是散装。

## 关键前置事实（已由前序卡片确立，Lead 已字节级复核）
- 镜像 `ra2bench\gamemd.exe`，4,825,360 B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
- `ImageBase=0x400000`，`RELOCS_STRIPPED=True`，`.text` 内 **`FileOffset = VA − 0x400000`**
- `CCFileClass::Get_File = 0x473D10`：**磁盘优先**。指令级证据（Lead 已手算复核 rel32）：
  ```
  0x473D1D  F6 44 24 20 02   test byte [esp+0x20],2
  0x473D22  0F 85 11 01 00 00 jne 0x473E39        ; mode&2 → 只走磁盘
  0x473D2D  E8 DE E1 FB FF   call 0x431F10        ; ★ 先试磁盘（散装）
  0x473D34  0F 85 FF 00 00 00 jne 0x473E39        ; ★ 磁盘命中 → 跳过整个 MIX 分支
  0x473D68  E8 C3 06 14 00   call 0x5B4430        ; ★ 失败才回落 MIX 查找
  ```
- `MixFileClass::Find = 0x5B4430`（大写名 → CRC32 → 按 MIX 装载顺序 FIFO 查表）
- 真机现象（W27）：`[SOV1] Scenario=` **直接**指向散装 `ECH02.MAP` ⇒ 正常入局；而链式推进（`ECH01.MAP` 胜利后点 `GUI:Continue`）⇒ 弹「無法啟動選取地圖!」，A2 未启动

## 核心问题（按序回答）
1. **`NextScenario` 这个键名在 `gamemd.exe` 里被谁读取？** 找到读取它的 INI 访问点（键名字符串 xref → 调用方函数），确认该字段在现代（YR/RA2）战役路径上**是否真的被消费**。
2. 顺着数据流追：`NextScenario` 的值（地图名）被存到哪里、之后由谁打开。**最终打开目标图时用的是 `0x473D10`(Get_File) 还是直接 `0x5B4430`(MixFile::Find)，还是别的路径？** 这是判决 H-A/H-B 的关键一刀。
3. 若走 `Get_File`：那么散装的 `ECH02.MAP` 应当能被找到 ⇒ **H-B 不成立**，失败原因在别处（把「别处」尽量收窄，例如地图头/序列号校验）。
4. 若直接走 `MixFileClass::Find`（或任何绕过磁盘的路径）：**H-B 成立** ⇒ 散装图对「下一关推进」不可见，修复方向是把我方地图打进 MIX。
5. 顺带查：`BATTLEMD.INI` 的 `[Battles]` 序号序列是否参与「下一关」决策（即 H-A 的正面证据）。

## 纪律（硬性）
- **纯静态只读**：禁止启动 `gamemd.exe`、禁止 attach/读活进程/注入、禁止写 `ra2youli`、禁止写仓库 `ra2forge/`、禁止 git 写操作、禁止改动 `W21`–`W32` 任何目录
- 不得把项目自带 `ra2forge/mixlib.py` 等模块的实现当引擎行为证据（只能当工具）；CRC 只用 `zlib.crc32` 并与真实 MIX 实测 entry id 交叉核对
- 每条结论标等级：`[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]`
- capstone 反汇编。**`ret` 不是函数结束判据**（存在函数中段的分支尾）；**等距指针表 ≠ vtable**（必须验证目标落在指令边界）；**线性扫描 ≠ 完整 xref**
- `gamemd.exe+0xNNNNNN` 多为 **RVA**；`0xA83CF8`/`0x87E8E0` 这类是 **VA**。算偏移前先声明，别混，也别给已经是 VA 的值再加 ImageBase
- 与前提不符处写 `DISAGREE.md`，不要迁就

## 交付（只写这个目录）
`lead\next_re_20261112_r02\W33_nextscenario_dataflow\`
- `NEXTSCENARIO_FLOW.md`：结论（明确写 H-A 成立 / H-B 成立 / 都不成立 / 证据不足）+ 判定链 + 关键指令字节（VA/RVA/FOFF/原始字节/反汇编并列）
- `EVIDENCE\`：脚本 + 完整 stdout（含 exit code）
- `UNKNOWNS.md`：未覆盖项

报告口径：这是判决性任务，**不要写「可能」了事**。拿到调用点就明确下判；拿不到就明确写「未定位到打开调用，H-A/H-B 均未判决」，并说明还缺什么证据。