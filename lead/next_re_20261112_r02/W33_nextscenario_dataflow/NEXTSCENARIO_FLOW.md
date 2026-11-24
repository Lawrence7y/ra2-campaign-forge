# W33 静态判决报告：`NextScenario` 数据流与下一关地图打开路径

- **目标镜像**：`D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe`（`4,825,360 B`，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`） `[本次实测]`
- **PE 节区基址映射**：`ImageBase = 0x400000`；`.text` 节 `RVA = 0x1000, FOFF = 0x1000`（`RVA = FOFF = VA - 0x400000`），`.rdata` `RVA = FOFF = 0x3E1000`，`.data` `RVA = FOFF = 0x412000` `[本次实测]`

---

## 一、最终判决

**H-A 与 H-B 均不成立。** `[本次读码]` `[本次实测]`

1. **H-A（"`NextScenario` 是死字段，推进按 `BATTLEMD.INI [Battles]` `1..14` 走"）不成立**：
   - `NextScenario`（`[Scen+0x04]`）并非死字段：`ScenarioClass::Read_INI`（`0x00689FCA`）读取、`Write_Scenario_INI`（`0x0068B0B3`）写回、`MPCoop`（`0x005C3853`）动态写入；当 `[Scen+0x34B0]`（`SkipMapSelect`）非 0 时，通关后在 `0x00685A59..0x00685A5C` 真正进入 `0x005ADE20` -> `0x005ADF20` 被消费 `[本次读码]`。
   - 官方 14 张 YR 地图不因 `NextScenario=GDI2A.map` 失败，也不是因为改走 `BATTLEMD.INI [Battles]` 序号推进——遍历 `0x00A83CFC`/`0x00A83D08` 全部引用，`[Battles]` 不参与通关后的下一关决策 `[本次读码]`。真正原因是官方 14 张图全部设置了 **`SkipMapSelect=no`** `[本次实测]`，使 `0x00685A40`（`je 0x685a63`）绕开 `NextScenario`，改走 **`MAPSELMD.INI`** 的分阵营阶段树（`[GDI]` `ALL01`..`ALL07` / `[Nod]` `Sov01`..`Sov07`） `[本次读码]` `[本次实测]`。
2. **H-B（"`Continue` 直接走 `MixFileClass::Find` 绕过散装盘，打进 MIX 即可"）不成立**：
   - 无论 `SkipMapSelect=no` 还是 `SkipMapSelect=yes`，引擎**从未把 `NextScenario` 的值直接传给 `0x473D10`（`CCFileClass::Open`）或 `0x5B4430`（`MixFileClass::Find`）打开地图** `[本次读码]`。
   - 实际加载 `.MAP` 的 `Start_Scenario`（`0x00683AB0`）与 `Read_Scenario_INI`（`0x00686730`）均使用 `CCFileClass`（虚表 `0x007E16B0`），支持散装磁盘文件与 MIX 双路寻址，并不存在「`Continue` 绕过磁盘直调 `MixFileClass::Find`」的分支 `[本次读码]`。
   - `W27` 中 `ECH01.MAP` 设为 `SkipMapSelect=no` `[本次实测]`，点击 `GUI:Continue` 后走 `0x005ADD10` -> `0x005AE100` -> `0x005AE220` -> `0x005CEEF0` 加载 `MAPSELMD.INI`，再调用 `0x005CF760` 用**当前地图名 `ECH01.MAP`**（`[Scen+0x125C]`）去 `MAPSELMD.INI` 中反查阶段失败，从而触发 `"MapSelect: Invalid stage!\n"` 并弹窗 `MSG:UnableMapSelect`（`"無法啟始選取地圖！\n"`），根本没有进入下一关文件名赋值与开图流程 `[本次读码]` `[本次实测]`。**仅把 `ECH02.MAP` 打进 MIX 不能修复该报错。** `[静态推断]`

---

## 二、五大核心问题逐项作答

### 1. `NextScenario` 这个键名在 `gamemd.exe` 里被谁读取？它在 YR/RA2 战役路径上是否真的被消费？
- **唯一读取点**：字符串 `'NextScenario'`（`VA 0x0083E19C`）全二进制仅被引用 2 次，其中唯一 INI 读取点在 `ScenarioClass::Read_INI`（`0x00689FCA push 0x83e19c` -> `0x00689FD6 call 0x528a10`），将 `[Basic] NextScenario=` 写入 `[Scen + 0x04]`；紧随其后 `0x00689FE8..0x00689FF4` 读取 `AltNextScenario` 到 `[Scen + 0x108]` `[本次读码]`。另 1 次引用在 `Write_Scenario_INI`（`0x0068B0B3..0x0068B0BB`），用于写回保存 `[本次读码]`。此外仅 `MPCoop` 逻辑（`0x005C3847..0x005C386F`）会把 `"%s.MAP"` 写入 `[Scen + 0x04]` 并置 `[Scen + 0x34B0] = 1` `[本次读码]`。
- **是否真的被消费**：**条件消费，且非直接开图** `[本次读码]`。在战役结算继续点（`CampScor` 处理 `GUI:Continue` 后由 `0x0055D14A` 调用 `0x00685670`），`0x00685A38..0x00685A61` 读取 `[Scen + 0x34B0]`（`SkipMapSelect`）：
  - 当 `SkipMapSelect=no`（`0`）时：`0x00685A40`（`je 0x685a63`）直接跳过 `[Scen+0x04]`/`[Scen+0x108]`，改调 `0x005ADD10` -> `0x005AE100`（**不读取 `NextScenario`**） `[本次读码]`。
  - 当 `SkipMapSelect=yes`（`1`）时：才进入 `0x00685A4C`/`0x00685A59`，按 `[Scen+0x1CD9]` 选择 `[Scen+0x108]` 或 `[Scen+0x04]`（即 `NextScenario`）送入 `0x005ADE20` -> `0x005ADF20` 消费 `[本次读码]`。

### 2. `NextScenario` 的值存到哪里、由谁打开？最终打开目标图用的是 `0x473D10` 还是 `0x5B4430`？
- **存储位置**：`Scenario` 单例（`*[0x00A8B230]`）偏移 `+0x04`（长度 `0x104` 缓冲区） `[本次读码]`。
- **在 `SkipMapSelect=yes` 下的数据流转**：
  1. `0x00685A59 lea edx, [ecx+4]` -> `call 0x5ade20` -> `0x005ADE85 call 0x5adf20` `[本次读码]`。
  2. `0x005ADF20` 先调用 `0x005CEEF0` 加载 **`MAPSELMD.INI`**（按当前 `Side` 如 `GDI`/`Nod`），再以 `[Scen + 0x35A0]`（当前阶段索引）通过 `0x005CF810` 取出阶段对象，**先用 `0x00686700` 清空 `Scen->FileName`（`[Scen+0x125C]`）**（`0x005AE00C..0x005AE013`） `[本次读码]`。
  3. 循环该阶段在 `MAPSELMD.INI` 中的候选子项（`0x005AE032 call 0x5cf6b0`），将候选子项的 `Scenario=` 字段（`[choice+4]`）与传入的 `NextScenario` 统一转大写后做字符串相等比对（`0x005AE073 call 0x7b4780`） `[本次读码]`。
  4. **仅当比对命中时**，`0x005AE0A7 call 0x686700` 把**命中项的 `Scenario=` 字符串**写入 **`[Scen + 0x125C]`（`Scen->FileName`）** 并更新 `[Scen + 0x35A0]`；若未命中则清理并返回 `0`，`0x005ADEFA call 0x5d3490` 弹窗 `MSG:UnableMapSelect`（`D:\ra2mdpost\MapSel.CPP` 第 `0x98` 行） `[本次读码]`。
- **在 `SkipMapSelect=no` 下的数据流转**：`NextScenario` 全程不进入选图逻辑；`0x005AE100` -> `0x005AE220` 加载 `MAPSELMD.INI`，改用**当前 `[Scen + 0x125C]`** 通过 `0x005CF760` 查找当前阶段，弹出选关面板/默认子项后调用 `0x00686700` 更新 `[Scen + 0x125C]` `[本次读码]`。
- **最终真正打开 `.MAP` 文件的调用点**：
  - `0x00685C4E lea ecx, [eax+0x125c]` -> `0x00685C54 call 0x683ab0`（`Start_Scenario`） `[本次读码]`。
  - `Start_Scenario`（`0x00683C56 call 0x4739f0` + `0x00683C67 call 0x4741f0`）及其调用的 `Read_Scenario_INI`（`0x0068679F call 0x4739f0` + `0x006867BE call 0x4741f0`）均构造 `CCFileClass`（虚表 **`0x007E16B0`**）并经 `CCINIClass::Load` / `INIClass::Load` 读取地图 `[本次读码]`。
  - 虚表 `0x007E16B0` 的 `+0x1C` 即 **`0x00473D10`（`CCFileClass::Open`，先磁盘 `0x431F10` 后 MIX `0x5B4430`）**，`+0x14` 即 **`0x00473C50`（`CCFileClass::Is_Available`，先 MIX `0x5B4430` 后磁盘 `0x431F10`）**，**二者均非只走 `0x5B4430` 的纯 MIX 路径** `[本次读码]`。

### 3. 为何 `W27` `[SOV1] Scenario=ECH01.MAP` 能正常入局，而通关点 `Continue` 弹「無法啟動選取地圖!」且 A2 未启动？
- **`[SOV1] Scenario=ECH01.MAP` 正常入局**：新建战役时首关名称直接取自 `BATTLEMD*.INI` 项的 `Scenario=`，由 `Start_Scenario`（`0x00683AB0`）通过 `CCFileClass`（`0x007E16B0`）加载散装磁盘上的 `ECH01.MAP`，完全不经过 `MAPSELMD.INI` `[本次读码]`。
- **点 `GUI:Continue` 必弹「無法啟動選取地圖!」**：
  1. `ECH01.MAP` 的 `[Basic]` 含 `SkipMapSelect=no`、`EndOfGame=no`、`NextScenario=ECH02.MAP` `[本次实测]`。
  2. 因 `SkipMapSelect=no`，`0x00685A40` 跳向 `0x005ADD10` -> `0x005AE100` -> `0x005AE220` `[本次读码]`。
  3. `0x005AE2BE` 读取 `MAPSELMD.INI`（仅含官方 `[GDI]` `ALL01`..`ALL07` 与 `[Nod]` `Sov01`..`Sov07` `[本次实测]`），随后 `0x005AE2F5..0x005AE30C` 将 `[Scen + 0x125C]`（`"ECH01.MAP"`）送入 `0x005CF760` 匹配 `MAPSELMD.INI` 中任一阶段的 `Scenario=` `[本次读码]`。
  4. `MAPSELMD.INI` 中没有任何阶段的 `Scenario=` 等于 `"ECH01.MAP"`，`0x005CF760` 返回 `0` -> `0x005AE320` 报错 `"MapSelect: Invalid stage!\n"` -> `0x005ADD95..0x005ADDCF` 在 `MapSel.CPP:0x86` 弹窗 `MSG:UnableMapSelect`（`langmd.mix` 中 `RA2MD.CSF` 对应 `"無法啟始選取地圖！\n"`） `[本次读码]` `[本次实测]`。
  5. 失败分支根本未触及 `NextScenario`，也从未调用 `0x00686700` 将 `[Scen + 0x125C]` 改写为 `ECH02.MAP`，因此 `ECH02.MAP`（A2）从未被选中或打开 `[本次读码]`。

### 4. 若改走 MIX 打包能否解决？
- **不能。** `[静态推断]`
- `CCFileClass::Open`（`0x00473D10`）与 `CCFileClass::Is_Available`（`0x00473C50`）本就能读取散装磁盘 `.MAP`；卡死点发生在**开图之前**的 `MapSelect` 阶段校验（`MAPSELMD.INI` 中不存在 `ECH01.MAP` 对应的 Stage，且即使强制 `SkipMapSelect=yes`，`0x005ADF20` 也要求 `MAPSELMD.INI` 当前阶段的某条选择项 `Scenario=` 匹配 `ECH02.MAP`） `[本次读码]`。

### 5. `BATTLEMD.INI [Battles]` 序号序列是否参与「下一关」决策？
- **不参与。** `[本次读码]`
- 对 `0x00A83CFC`（`Battles` 指针数组，19 处 xref）与 `0x00A83D08`（`Battles.Count`，21 处 xref）全量核查，其用途仅限：战役选择菜单填充、`Start_Scenario` 在传入空文件名时按 `BattleIdx` 取首关 `Scenario=`（`0x00683AF0..0x00683AF8`）、阵营/CD/电影查表、以及 `EndOfGame` 标记战役胜利 `[本次读码]`。官方 YR 14 关的有序推进完全由 **`MAPSELMD.INI`**（`[GDI]`/`[Nod]` 的 `1=..7` 与各段内 `Scenario=`）驱动 `[本次读码]` `[本次实测]`。

---

## 三、完整判定链与关键指令字节（VA / RVA / FOFF / 原始字节 / 反汇编并列）

### 链路 1：`NextScenario` INI 读写与动态赋值点
| 功能定位 | VA | RVA | FOFF | 原始字节 | 反汇编指令 | 来源等级 |
|---|---|---|---|---|---|---|
| 字符串 `'NextScenario'` | `0x0083E19C` | `0x43E19C` | `0x43E19C` | `4e 65 78 74 53 63 65 6e 61 72 69 6f` | `"NextScenario"` | `[本次实测]` |
| Read_INI 目的缓冲 `[Scen+4]` | `0x00689FC0` | `0x289FC0` | `0x289FC0` | `8d 46 04` | `lea eax, [esi + 4]` | `[本次读码]` |
| Read_INI 键名入栈 | `0x00689FCA` | `0x289FCA` | `0x289FCA` | `68 9c e1 83 00` | `push 0x83e19c ; 'NextScenario'` | `[本次读码]` |
| Read_INI 读字符串 | `0x00689FD6` | `0x289FD6` | `0x289FD6` | `e8 35 ea e9 ff` | `call 0x528a10` | `[本次读码]` |
| Read_INI 读 `AltNextScenario` | `0x00689FDB` | `0x289FDB` | `0x289FDB` | `8d 86 08 01 00 00` | `lea eax, [esi + 0x108]` | `[本次读码]` |
| Read_INI 读 `AltNextScenario` 键 | `0x00689FE8` | `0x289FE8` | `0x289FE8` | `68 8c e1 83 00` | `push 0x83e18c ; 'AltNextScenario'` | `[本次读码]` |
| Write_Scenario_INI 源缓冲 | `0x0068B0AF` | `0x28B0AF` | `0x28B0AF` | `8d 43 04` | `lea eax, [ebx + 4]` | `[本次读码]` |
| Write_Scenario_INI 键名 | `0x0068B0B3` | `0x28B0B3` | `0x28B0B3` | `68 9c e1 83 00` | `push 0x83e19c ; 'NextScenario'` | `[本次读码]` |
| Write_Scenario_INI 写字符串 | `0x0068B0BB` | `0x28B0BB` | `0x28B0BB` | `e8 a0 d5 e9 ff` | `call 0x528660` | `[本次读码]` |
| MPCoop 取 `[Scen+4]` | `0x005C3853` | `0x1C3853` | `0x1C3853` | `8d 51 04` | `lea edx, [ecx + 4]` | `[本次读码]` |
| MPCoop 置 `SkipMapSelect=1` | `0x005C390F` | `0x1C390F` | `0x1C390F` | `c6 81 b0 34 00 00 01` | `mov byte ptr [ecx + 0x34b0], 1` | `[本次读码]` |

### 链路 2：通关后分派（`SkipMapSelect` 分支 -> `MapSelect` -> `Start_Scenario`）
| 功能定位 | VA | RVA | FOFF | 原始字节 | 反汇编指令 | 来源等级 |
|---|---|---|---|---|---|---|
| 取 `Scenario` 单例 | `0x00685A32` | `0x285A32` | `0x285A32` | `8b 0d 30 b2 a8 00` | `mov ecx, dword ptr [0xa8b230]` | `[本次读码]` |
| 读 `SkipMapSelect` 标志 | `0x00685A38` | `0x285A38` | `0x285A38` | `8a 81 b0 34 00 00` | `mov al, byte ptr [ecx + 0x34b0]` | `[本次读码]` |
| `SkipMapSelect==0` 跳转 | `0x00685A40` | `0x285A40` | `0x285A40` | `74 21` | `je 0x685a63` | `[本次读码]` |
| 取主/备路线标志 | `0x00685A42` | `0x285A42` | `0x285A42` | `8a 81 d9 1c 00 00` | `mov al, byte ptr [ecx + 0x1cd9]` | `[本次读码]` |
| 支线时取 `AltNextScenario` | `0x00685A4C` | `0x285A4C` | `0x285A4C` | `8d 91 08 01 00 00` | `lea edx, [ecx + 0x108]` | `[本次读码]` |
| 调 Skip 选图函数 | `0x00685A52` | `0x285A52` | `0x285A52` | `e8 c9 83 f2 ff` | `call 0x5ade20` | `[本次读码]` |
| 主线时取 `NextScenario` | `0x00685A59` | `0x285A59` | `0x285A59` | `8d 51 04` | `lea edx, [ecx + 4]` | `[本次读码]` |
| 调 Skip 选图函数 | `0x00685A5C` | `0x285A5C` | `0x285A5C` | `e8 bf 83 f2 ff` | `call 0x5ade20` | `[本次读码]` |
| `SkipMapSelect==0` 重载单例 | `0x00685A6E` | `0x285A6E` | `0x285A6E` | `8b 0d 30 b2 a8 00` | `mov ecx, dword ptr [0xa8b230]` | `[本次读码]` |
| 调交互 MapSelect 包装 | `0x00685A74` | `0x285A74` | `0x285A74` | `e8 97 82 f2 ff` | `call 0x5add10` | `[本次读码]` |
| 取 `BattleIdx` 参数 | `0x00685C47` | `0x285C47` | `0x285C47` | `8b 88 cc 34 00 00` | `mov ecx, dword ptr [eax + 0x34cc]` | `[本次读码]` |
| 取 `Scen->FileName`（`+0x125C`） | `0x00685C4E` | `0x285C4E` | `0x285C4E` | `8d 88 5c 12 00 00` | `lea ecx, [eax + 0x125c]` | `[本次读码]` |
| 调用 `Start_Scenario` | `0x00685C54` | `0x285C54` | `0x285C54` | `e8 57 de ff ff` | `call 0x683ab0` | `[本次读码]` |

### 链路 3：`0x005ADD10` 与 `0x005ADE20` 内部均强依赖 `MAPSELMD.INI`
| 功能定位 | VA | RVA | FOFF | 原始字节 | 反汇编指令 | 来源等级 |
|---|---|---|---|---|---|---|
| `0x5add10` 调 MapSelect 主流程 | `0x005ADD63` | `0x1ADD63` | `0x1ADD63` | `e8 98 03 00 00` | `call 0x5ae100` | `[本次读码]` |
| 失败时构造弹窗消息 | `0x005ADDB5` | `0x1ADDB5` | `0x1ADDB5` | `b9 08 c1 82 00` | `mov ecx, 0x82c108 ; 'MSG:UnableMapSelect'` | `[本次读码]` |
| 失败时弹出提示框（行 `0x86`） | `0x005ADDCF` | `0x1ADDCF` | `0x1ADDCF` | `e8 bc 56 02 00` | `call 0x5d3490` | `[本次读码]` |
| `0x5ae100` 初始化 Stage | `0x005AE10A` | `0x1AE10A` | `0x1AE10A` | `e8 11 01 00 00` | `call 0x5ae220` | `[本次读码]` |
| `0x5ae220` 加载 `MAPSELMD.INI` | `0x005AE2BE` | `0x1AE2BE` | `0x1AE2BE` | `e8 2d 0c 02 00` | `call 0x5ceef0` | `[本次读码]` |
| 取当前 `[Scen+0x125C]` | `0x005AE2F5` | `0x1AE2F5` | `0x1AE2F5` | `81 c5 5c 12 00 00` | `add ebp, 0x125c` | `[本次读码]` |
| 按当前文件名匹配 Stage | `0x005AE30C` | `0x1AE30C` | `0x1AE30C` | `e8 4f 14 02 00` | `call 0x5cf760` | `[本次读码]` |
| 找不到 Stage 日志失败 | `0x005AE320` | `0x1AE320` | `0x1AE320` | `68 34 c1 82 00` | `push 0x82c134 ; 'MapSelect: Invalid stage!\n'` | `[本次读码]` |
| `0x5ceef0` 打开 `MAPSELMD.INI` | `0x005CEF62` | `0x1CEF62` | `0x1CEF62` | `68 70 03 83 00` | `push 0x830370 ; 'MAPSELMD.INI'` | `[本次读码]` |
| `0x5ceef0` 调 `CCFileClass::Open` | `0x005CEF78` | `0x1CEF78` | `0x1CEF78` | `ff 52 1c` | `call dword ptr [edx + 0x1c]` | `[本次读码]` |
| `0x5ade20` 调 `NextScenario` 查找 | `0x005ADE85` | `0x1ADE85` | `0x1ADE85` | `e8 96 00 00 00` | `call 0x5adf20` | `[本次读码]` |
| `0x5adf20` 加载 `MAPSELMD.INI` | `0x005ADFA0` | `0x1ADFA0` | `0x1ADFA0` | `e8 4b 0f 02 00` | `call 0x5ceef0` | `[本次读码]` |
| 取当前阶段索引 `[Scen+0x35A0]` | `0x005ADFE1` | `0x1ADFE1` | `0x1ADFE1` | `e8 2a 18 02 00` | `call 0x5cf810` | `[本次读码]` |
| 先清空 `Scen->FileName` | `0x005AE013` | `0x1AE013` | `0x1AE013` | `e8 e8 86 0d 00` | `call 0x686700` | `[本次读码]` |
| 遍历候选对比 `NextScenario` | `0x005AE073` | `0x1AE073` | `0x1AE073` | `e8 08 67 20 00` | `call 0x7b4780` | `[本次读码]` |
| 命中后写入 `[Scen+0x125C]` | `0x005AE0A7` | `0x1AE0A7` | `0x1AE0A7` | `e8 54 86 0d 00` | `call 0x686700` | `[本次读码]` |
| 未命中同样弹窗（行 `0x98`） | `0x005ADEFA` | `0x1ADEFA` | `0x1ADEFA` | `e8 91 55 02 00` | `call 0x5d3490` | `[本次读码]` |

### 链路 4：地图文件打开路径（`CCFileClass` 虚表 `0x007E16B0`）
| 功能定位 | VA | RVA | FOFF | 原始字节 | 反汇编指令 | 来源等级 |
|---|---|---|---|---|---|---|
| `Start_Scenario` 构造 `CCFileClass` | `0x00683C56` | `0x283C56` | `0x283C56` | `e8 95 fd de ff` | `call 0x4739f0` | `[本次读码]` |
| `Start_Scenario` 读地图 INI | `0x00683C67` | `0x283C67` | `0x283C67` | `e8 84 05 df ff` | `call 0x4741f0` | `[本次读码]` |
| `Read_Scenario_INI` 构造 `CCFileClass` | `0x0068679F` | `0x28679F` | `0x28679F` | `e8 4c d2 de ff` | `call 0x4739f0` | `[本次读码]` |
| `Read_Scenario_INI` 读地图 INI | `0x006867BE` | `0x2867BE` | `0x2867BE` | `e8 2d da de ff` | `call 0x4741f0` | `[本次读码]` |
| `Is_Available` 先查 MIX | `0x00473C8B` | `0x073C8B` | `0x073C8B` | `e8 a0 07 14 00` | `call 0x5b4430` | `[本次读码]` |
| `Is_Available` 再查磁盘 | `0x00473CA2` | `0x073CA2` | `0x073CA2` | `e8 69 e2 fb ff` | `call 0x431f10` | `[本次读码]` |
| `Open`（`+0x1C`）先查磁盘 | `0x00473D2D` | `0x073D2D` | `0x073D2D` | `e8 de e1 fb ff` | `call 0x431f10` | `[本次读码]` |
| `Open`（`+0x1C`）失败回落 MIX | `0x00473D68` | `0x073D68` | `0x073D68` | `e8 c3 06 14 00` | `call 0x5b4430` | `[本次读码]` |

---

## 四、证据脚本与日志索引（均含 `EXIT_CODE=0`）

- [step8_check_ini_csf_and_remaining_code.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step8_check_ini_csf_and_remaining_code.py) / [stdout](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step8_check_ini_csf_and_remaining_code.stdout.txt)（`BATTLEMD.INI`、`BATTLEMD98.INI`、`ECH01.MAP`、`ECH02.MAP` 与 `MPCoop`）
- [step9_exhaustive_checks.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step9_exhaustive_checks.stdout.txt)（14 张官方图 `SkipMapSelect=no`、全量 `Battles` 引用、`CCFileClass` 虚表与交叉引用）
- [step10_close_gaps.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step10_close_gaps.stdout.txt)（`zlib.crc32` 交叉核对、`MAPSELMD.INI` 全文、`Start_Scenario` / `Read_Scenario_INI` / `0x005CEEF0`）
- [step11_final_detail.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step11_final_detail.stdout.txt)（`MPCoop` 与 `Write_Scenario_INI`）
- [step12_verbatim_blocks.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step12_verbatim_blocks.stdout.txt)（`CampScor` `GUI:Continue`、`0x005AE100..0x005CF5E0`、`langmd.mix` 中 `RA2MD.CSF` 字符串）
- [step13_missing_links.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step13_missing_links.py) / [stdout](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step13_missing_links.stdout.txt)（`EXIT_CODE=0`，补齐 `0x00686700`、`0x00685A30..0x00685C65`、`0x00683AB0..0x00683DA0`、`0x005CF6B0..0x005CF8E0`、`0x004741F0`、`0x00525A10`、`0x006C9890` 与 `0x007E16B0` 虚表）
- [step14_verbatim_tables.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step14_verbatim_tables.py) / [stdout](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step14_verbatim_tables.stdout.txt)（`EXIT_CODE=0`，逐条字节核验 `ScenarioClass::Read_INI`、`Write_Scenario_INI`、`MPCoop`、`0x005ADD10`、`0x005ADF20`、`Read_Scenario_INI`、`CCFileClass`）
- [DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/DISAGREE.md) · [UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/UNKNOWNS.md)
