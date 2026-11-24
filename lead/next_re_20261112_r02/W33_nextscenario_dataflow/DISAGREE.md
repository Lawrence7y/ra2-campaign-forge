# 与任务前提不符之处（DISAGREE）

本文件记录 `gamemd.exe`（`4,825,360 B`，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` `[本次实测]`）静态分析结果与任务背景前提假设不符之处。

## 1. H-A 前提冲突：`NextScenario` 不是「完全死字段」，而官方战役进度也不靠 `BATTLEMD.INI [Battles]` `1..14`

1. **`NextScenario` 仍在代码中真实读取、回写与有条件消费** `[本次读码]`：
   - 字符串 `NextScenario` 位于 `VA 0x0083E19C`（`RVA 0x43E19C` / `FOFF 0x43E19C`），存在 2 处代码引用：`ScenarioClass::Read_INI`（`0x00689FCA`）将其读入 `[Scen+0x04]`，`Write_Scenario_INI`（`0x0068B0B3`）将其写回存档/INI。
   - `MPCoop` 流程（`0x005C3847..0x005C390F`）会将 `"%s.MAP"` 写入 `[Scen+0x04]` 并显式置 `byte ptr [Scen+0x34B0] = 1`（`SkipMapSelect`）。
   - 通关跳转逻辑 `0x00685A32..0x00685A61` 检视 `[Scen+0x34B0]`（`SkipMapSelect`）：仅当其为 **非 0**（`SkipMapSelect=yes`）时，才将 `[Scen+0x04]`（或分支后的 `[Scen+0x108]` `AltNextScenario`）送入 `0x005ADE20` -> `0x005ADF20` 消费。
2. **官方 14 张 YR 地图不因 `NextScenario=GDI2A.map` 报错，并不是因为改走 `BATTLEMD.INI [Battles]`，而是因为它们全设 `SkipMapSelect=no` 且由 `MAPSELMD.INI` 驱动** `[本次实测]` `[本次读码]`：
   - 14 张官方 YR 战役地图 `[Basic]` 均含 `SkipMapSelect=no`、`NextScenario=GDI2A.map`、`AltNextScenario=GDI9C.MAP` `[本次实测]`（见 `step9_exhaustive_checks.stdout.txt` 及 `W28` `*.MAP.basic.txt`）。
   - 当 `SkipMapSelect == 0` 时，`0x00685A40`（`je 0x685a63`）跳过 `NextScenario` 消费，改为调用 `0x005ADD10` -> `0x005AE100` -> `0x005AE220` -> `0x005CEEF0` 读取 `ra2md.mix` 内的 `MAPSELMD.INI` `[本次读码]`。
   - 真实提取 `MAPSELMD.INI`（`id=0x922B8CE7` / `0xFBE0D09D`）可见完整分阵营阶段树：`[GDI]`（`1=ALL01`..`7=ALL07`）与 `[Nod]`（`1=Sov01`..`7=Sov07`），将官方 14 图完整串联 `[本次实测]`。
   - 遍历 `0x00A83CFC`（`Battles` 数组，19 处交叉引用）与 `0x00A83D08`（`Battles.Count`，21 处交叉引用），`BATTLEMD.INI [Battles]` 仅用于战役列表 UI、首关无文件名时定位入口图、阵营/CD 检查及 `EndOfGame` 统计，不参与通关后的「下一关」选图 `[本次读码]`。

## 2. H-B 前提冲突：`Continue` 并不直接用 `MixFileClass::Find` 打开 `ECH02.MAP`，且 `NextScenario` 从未作为文件名传给开图函数

1. **`Continue` 链路上并未尝试打开 `ECH02.MAP`** `[本次读码]`：
   - `W27` 实测所用 `ECH01.MAP` 同样设置了 `SkipMapSelect=no`、`EndOfGame=no`、`NextScenario=ECH02.MAP` `[本次实测]`（`step8` stdout）。
   - 因 `SkipMapSelect=no`，胜利点击 `GUI:Continue` 后进入 `0x005ADD10` -> `0x005AE100` -> `0x005AE220`。该函数根据当前阵营（如 Soviet -> `Nod`）加载 `MAPSELMD.INI`，再调用 `0x005CF760` 用 **当前地图文件名** `[Scen+0x125C]`（`"ECH01.MAP"`）反查 `MAPSELMD.INI` 阶段表 `[本次读码]`。
   - `MAPSELMD.INI` 中无 `ECH01.MAP`（也没有 `ECH02.MAP` 或 `RA2F1`），故 `0x005CF760` 返回 `0`，`0x005AE320` 输出调试日志 `"MapSelect: Invalid stage!\n"` 并返回失败，`0x005ADD95..0x005ADDCF` 立即弹窗 `MSG:UnableMapSelect`（`langmd.mix` 中 `RA2MD.CSF` 对应 `"無法啟始選取地圖！\n"`） `[本次实测]` `[本次读码]`。
   - 在此之前，`[Scen+0x125C]` 未被更新为 `"ECH02.MAP"`，也从未到达 `Start_Scenario` 或文件打开函数 `[本次读码]`。
2. **即便假定把 `SkipMapSelect` 改为 `yes`，`NextScenario` 也仍然不是文件打开路径** `[本次读码]`：
   - `0x005ADE20` -> `0x005ADF20` 仍然首先打开 `MAPSELMD.INI`（`0x005ADFA0 call 0x5ceef0`），用当前阶段号 `[Scen+0x35A0]`（`0x005CF810`）取出候选列表，再逐项把 `MAPSELMD.INI` 中的 `Scenario=`（`[choice+4]`）与 `[Scen+0x04]`（`NextScenario`）做字符串比对（`0x005AE073 call 0x7b4780`）。只有命中时才把命中的 `Scenario=` 拷贝进 `[Scen+0x125C]`（`0x005AE0A7 call 0x686700`）；未命中同样在 `D:\ra2mdpost\MapSel.CPP` 第 `0x98` 行弹 `MSG:UnableMapSelect` `[本次读码]`。
   - 因此，**`NextScenario` 在整个引擎中从未被直接交给 `0x473D10`（`CCFileClass::Open`）或 `0x5B4430`（`MixFileClass::Find`）打开**，它至多只是 `MAPSELMD.INI` 阶段内的一枚「目标 `Scenario=` 匹配键」 `[本次读码]`。
3. **关于 `CCFileClass` 与散装盘图可见性**：
   - `Start_Scenario`（`0x00683C56..0x00683C67`）与 `Read_Scenario_INI`（`0x0068679F..0x006867BE`）均通过 `CCFileClass`（虚表 `0x007E16B0`）加载 `.MAP` 文件，而非绕过磁盘直调 `MixFileClass::Find` `[本次读码]`。
   - 虚表 `0x007E16B0` 中 `+0x1C = 0x00473D10`（`Open`）先试磁盘（`0x431F10`）再回落 MIX（`0x5B4430`）；补充确认 `+0x14 = 0x00473C50`（`Is_Available`）虽先查 MIX（`0x5B4430`）再查磁盘（`0x431F10`），但**两条虚函数都支持命中散装磁盘文件** `[本次读码]`。仅把 `ECH02.MAP` 打入 MIX 并不能使 `MAPSELMD.INI` 选图逻辑通过 `[静态推断]`。
