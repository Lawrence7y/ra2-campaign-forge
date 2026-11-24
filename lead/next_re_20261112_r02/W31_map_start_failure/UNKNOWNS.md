# UNKNOWNS · W31 未覆盖项与不确定处

> 状态：**纯静态只读，无一次活进程/真机验证** ｜ 2026-11-13

## 1 · 结论口径

本卡**已拿到完整静态判定链**（从 `MSG:UnableMapSelect` 的两个 xref 回溯到
`0x00685A38` 的 `SkipMapSelect` 分派、`MapSelect::Init` 的 5 道判定、以及
`MAPSELMD.INI` 的真实内容与登记情况），但**没有**一次运行时观测来证明 W27 那一帧
（frame=210）具体落在哪一条失败分支、哪条 debug 串被打印。

因此报告口径是：

> **已收窄到 `MapSelect::Init` 的 `MAPSELMD.INI` 阶段登记表分支，并给出完整静态判定链；
> 仍缺运行时断点/调试日志证据来区分 `Invalid side!` / `Unable to initialize choices!` /
> `Invalid stage!` / `Unable to create font!` 四者中实际被触发的那一条。**

按静态证据，`Invalid stage!`（`0x005AE320` / `0x005ADFF3`）是**最可能**的一条
（`MAPSELMD.INI` 中确无 `ECH01.MAP`/`ECH02.MAP`），但这是 `[静态推断]`，不是 `[本次实测]`。

## 2 · 未覆盖 / 不能排除的项

| # | 项 | 等级 |
|---|---|---|
| 1 | W27 结算屏 `GUI:Continue` 的按钮消息处理函数（`WM_COMMAND` / 控件 ID `0x6D1`）到 `0x00685A10` 状态机的**逐跳调用链**未完整反汇编；只证明了 `GUI:Continue` 标签在 `0x0046E8BD` 被创建为控件，以及 wrappers 的 3 个直接调用点在 `0x00685Axx`。 | `[待运行验证]` |
| 2 | 弹窗后 frame 冻结 210、随后引擎自行重置回主菜单的运行时路径，未静态追踪。 | `[待运行验证]` |
| 3 | `[Scen+0x125C]` 在 frame=210 的**实际内容**未观测。本卡按 `0x00686700` 的语义（写入 `[esi+0x125c]`）与 W27 的 A1 已入局推断其为 `ECH01.MAP`。若引擎在胜利后已先清空/改写该字段，则失败点可能前移到 `0x7B4710` 的空串检查或 `Invalid Scene pointer`。 | `[静态推断]` `[待运行验证]` |
| 4 | `SkipMapSelect=yes` 分支中 `[Scen+0x35A0]`（stage 序号）的实际值、`0x005CF810` 的 `count` 实际值未知；本卡只给出该函数的边界检查字节。 | `[待运行验证]` |
| 5 | xref 覆盖度：只做了 `E8/E9 rel32` 的 **call-target 发现** + 指令边界验证的 4 字节立即数扫描。**间接调用**（虚表、函数指针、等距指针表）未覆盖；`0x005ADD10`/`0x005ADE20` 是否还被间接调用，不能排除。本报告未把线性扫描冒充完整 xref。 | `[静态推断]` |
| 6 | 未验证 `0x005CEEF0` 内 `call dword ptr [eax+8]` / `[edx+0x1c]` 两个虚调用的确切语义（按 vtable `0x007E16B0` 推断为 `Set_Name`/`Open`）；未逐条反汇编 `0x00525A10`（INI 解析）与 `0x00528C00`。 | `[静态推断]` |
| 7 | `MAPSELMD.INI` 的 `[GDI]`/`[Nod]` 段名与 `[Scen+0x1C74]` → `[0xA83C9C]` → `[battle+0xBC]` → `[0x8B4124]+0x24` 的**运行时取值映射**未实测（两张全局表由 `0x004E6F60`/`0x004E6FE0` 初始化为 10 容量的 VectorClass，运行时由 BATTLEMD.INI 填充）。 | `[待运行验证]` |
| 8 | 官方 `[Basic]` 精简版（W28 样本）与我方完整 `[Basic]`（W27 sandbox，含 `SkipMapSelect=no`、`Official=no`、`NewINIFormat=4` 等）对 `Read_Scenario_INI` 的其它副作用未评估；本卡只用到 `SkipMapSelect`、`NextScenario`、`EndOfGame` 三键。 | `[静态推断]` |
| 9 | 修复方案（散装 `MAPSELMD.INI` 克隆 14 个官方 stage + 追加我方 stage）**未真机验证**；也未验证行尾 CRLF/LF 对 `0x005CEEF0` 解析的影响。 | `[待运行验证]` |
| 10 | 顶层 33 个 `.mix` 中 `theme.mix`/`thememd.mix` 用 mixlib 解析报 `not a TS/RA2 MIX`（C&C 旧格式）；本卡用自写经典解析器复核过其索引，未发现 `0x922B8CE7`，但未逐条解出其内部文件名。 | `[本次实测]`（有限） |
| 11 | `ra2youli\gamemd.exe` 与 `ra2bench\gamemd.exe` 未逐字节比较 SHA-256（本卡只复核了 `ra2bench\gamemd.exe` = 任务书给定哈希）。W27 真机跑的是 `ra2youli` 下的副本。 | `[待运行验证]` |

## 3 · 明确**已排除**的备选解释（静态）

- ❌ 「`ECH02.MAP` 文件不存在 / 地图头坏」：W27 D3 已实测直接可起 `[转引]`；且失败发生在
  开图之前的 MapSelect 阶段。`[本次读码]`
- ❌ 「`NextScenario` 写法/大小写/行尾不对」：W28 已定谳 `[转引]`；本卡进一步发现在
  `SkipMapSelect=no` 下该键根本不参与。`[本次读码]`
- ❌ 「散装 vs MIX/CRC 寻址」：`CCFileClass`（`0x00473D10`）磁盘优先，两条路径都能读散装；
  且 MapSelect 打开的是 `MAPSELMD.INI` 而非目标 `.MAP`。`[本次读码]`
- ❌ 「`BATTLEMD.INI [Battles]` 序号推进」：`[Battles]` 表只用于战役菜单/首关名/EndOfGame，
  不参与通关后下一关决策 `[转引 W33]`；本卡在 `0x00683AF0..0x00683AF8` 独立看到它只提供
  首关 `Scenario=`。`[本次读码]`
- ❌ 「`EndOfGame` 标记」：写侧 `0x0068B143`、读侧 `0x0068A10E`，映射到 `[Scen+0x34AC]`，
  不在弹窗判定链上。`[本次读码]`

## 4 · 纪律自查

- 纯静态只读 ✔（未启动 `gamemd.exe`、未 attach/读活进程/注入、未写 `ra2youli`、
  未写仓库 `ra2forge/`、未 git 写、未改 W21–W30）
- CRC 只用 `zlib.crc32` 直接算，与真实 MIX 实测 entry id 交叉核对 ✔
  （`ra2md.csf`→`0xBD835079`；`MAPSELMD.INI`→`0x922B8CE7`，嵌套 MIX 内）
- `mixlib.py` 仅作 MIX 索引解码工具，未作引擎行为证据 ✔
- 反汇编用 capstone 5.0.7 ✔；`ret` 未作函数结束判据 ✔；等距指针表未当 vtable ✔；
  多锚点指令边界一致性验证后才认 xref ✔；未用线性扫描冒充完整 xref ✔
- 所有地址声明 VA / RVA / FOFF ✔；`0xA83C9C`/`0x8B4124`/`0xA8B230` 为 VA，
  `.text` 内 `FOFF = VA − 0x400000` ✔
- 每条结论标等级 ✔
