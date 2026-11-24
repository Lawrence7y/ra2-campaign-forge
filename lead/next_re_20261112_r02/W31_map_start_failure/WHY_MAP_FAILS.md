# WHY_MAP_FAILS · W31 静态定谳「無法啟始選取地圖！」

> 状态：**已拿到完整静态判定链；未做真机验证（本卡纯静态只读）**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02`
> 目标镜像：`ra2bench\gamemd.exe`，4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`

---

## 0 · 结论（先给答案）

**「`[SOV1] Scenario=` 直接指向能起」与「`[Basic] NextScenario` 推进起不来」的差异，落在
`0x00685A38` 的 `SkipMapSelect` 分派 → `MapSelect::Init` 的 `MAPSELMD.INI` 阶段表反查判定上，
具体是 `0x005CF760`（按**当前地图文件名** `[Scen+0x125C]` 在 `MAPSELMD.INI` 各 stage 的
`Scenario=` 中做字符串相等比对）返回 0 → `0x005AE320` 打印 `MapSelect: Invalid stage!`
→ `MapSelect::Init` 返回 `AL=0` → `0x005ADD95..0x005ADDCF` 弹 `MSG:UnableMapSelect`。** `[本次读码]` `[本次实测]`

一句话：`NextScenario=ECH02.MAP` **在这条路径上根本没有被当作文件名去打开**；引擎打开的是
硬编码的 `MAPSELMD.INI`，并用「当前地图名」或「当前 stage 序号」在该 INI 的阶段树里查表。
我方 `ECH01.MAP` / `ECH02.MAP` 没有登记在 `MAPSELMD.INI` 的 `[GDI]`/`[Nod]` 阶段树里 ⇒ 查表失败。
`[SOV1] Scenario=ECH02.MAP` 走的是 `Start_Scenario(0x00683AB0)` 直接把该字符串交给
`CCFileClass` 开图（磁盘优先），**完全不经过 MapSelect**，所以能起。 `[本次读码]` `[本次实测]`

> 口径说明：本卡拿到了**静态判定链**（每一跳都有指令字节），但没有活进程/日志证据来证明
> W27 那一帧具体是哪一条 debug 串被打印。故表述为「已收窄到 `MapSelect::Init` 的
> `MAPSELMD.INI` 阶段登记表分支并给出完整判定链，仍缺运行时断点/日志证据」。
> 未写「已定位根因」的绝对化措辞；见 `UNKNOWNS.md`。 `[待运行验证]`

---

## 1 · 文字 → CSF 标签（方法第 1 步，成功，无需改道 UTF-16LE）

- 官方 `ra2md.csf` 从 `ra2youli\langmd.mix` 提取：
  `ts_crc_hash("RA2MD.CSF")` = **`0xBD835079`**（此处用 `zlib.crc32` 直接算，非 mixlib 结论），
  与真实 MIX `entry[2]` 的 id 逐字节一致；payload 332,973 B，与 W30 `sandbox\extracted\ra2md.csf`
  完全相同。直接 CRC（无 4 字节尾填充）= `0x42CBEDCB`，**不命中**。`[本次实测]`（`s01`）
- CSF v3，5,211 标签，语言码 9（中文）。`[本次实测]`
- 用 `read_csf` 全量遍历：`選取地圖` 命中唯一标签 **`MSG:UnableMapSelect`**，
  文本 **`無法啟始選取地圖！\n`**。`[本次实测]`
- 任务书写的是「無法啟動選取地圖!」——**字面不一致**（`啟始` vs `啟動`、全角 `！` vs 半角 `!`、
  尾部 `\n`）。用任务书原串检索会得到 0 命中，改用子串 `選取地圖` 才命中。见 `DISAGREE.md`。
  `[本次实测]`
- 因为 CSF 里检索到了，**没有**改道 exe 内 UTF-16LE 中文串检索（方法第 5 步的 fallback 未触发）。
  `[本次实测]`
- 弹窗按钮「確定」对应 `TXT_OK`（`.data` VA `0x00825FB0`），两个 xref 站点都先
  `mov ecx,0x825fb0; call 0x734E60` 再 `mov ecx,0x82c108; call 0x734E60`，最后
  `call 0x5D3490` 出框。`[本次读码]`

## 2 · 标签 → exe 字符串 xref（方法第 2 步）

- `MSG:UnableMapSelect` ASCII 串在 `.data` **FOFF `0x0042C108` / VA `0x0082C108` / RVA `0x0042C108`**，
  全文件仅 1 处；同区还有 `D:\ra2mdpost\MapSel.CPP`（`0x0082C11C`）。`[本次实测]`（`s02`）
- 对该 VA 做 4 字节 LE 值候选扫描，得 2 个候选；再用 capstone 从多个锚点
  （`-0x60/-0x40/-0x30/-0x20/-0x18/-0x10/-0x8/0`）解码，要求 4 字节恰好落在指令立即数/位移
  且落在指令边界内 —— **两处都确认**为 `mov ecx, 0x82c108`：
  - **VA `0x005ADDB5`**（FOFF `0x001ADDB5`）
  - **VA `0x005ADEE0`**（FOFF `0x001ADEE0`）
  `[本次实测]`（`s02`/`s03` 的 6 锚点一致性检查：`distinct decodings=1`）
- 全 `.text` `E8/E9 rel32` 目标发现：调用两个 wrapper 的直接调用点**只有 3 处**，
  全在 `0x00685A52 / 0x00685A5C / 0x00685A74`（`Scenario.CPP` 状态机 `0x00685A10` 附近）。
  间接调用（虚表/函数指针）不在覆盖范围内，见 `UNKNOWNS.md`。`[本次实测]`（`s04`/`s05`）

> 纪律核对：`ret` 未被当作函数结束判据 —— `0x00685A0F` 的 `ret` 之后 `0x00685A10` 是同一
> 状态机里的分支尾（由 `0x00685A19 jne` 等汇入），本卡用 NOP 填充 + call-target 发现 + 多锚点
> 一致性来定界，未做「线性扫描冒充完整 xref」。`[本次读码]`

## 3 · 判定链（方法第 3 步）：走到弹窗前的全部前置判定

### 3.1 顶层分派 `0x00685A10`（`Scenario.CPP`）

| VA | 原始字节 | 反汇编 | 作用 |
|---|---|---|---|
| `0x00685A38` | `8a 81 b0 34 00 00` | `mov al, byte ptr [ecx+0x34b0]` | 读 `[Scen+0x34B0]` |
| `0x00685A3E` | `84 c0` | `test al, al` | |
| `0x00685A40` | `74 21` | `je 0x685a63` | **`SkipMapSelect==0` → wrapper1** |
| `0x00685A42` | `8a 81 d9 1c 00 00` | `mov al, byte ptr [ecx+0x1cd9]` | 另一 bool（Alt 选择） |
| `0x00685A4C` | `8d 91 08 01 00 00` | `lea edx, [ecx+0x108]` | `AltNextScenario` 缓冲区 |
| `0x00685A52` | `e8 c9 83 f2 ff` | `call 0x5ade20` | **wrapper2** |
| `0x00685A59` | `8d 51 04` | `lea edx, [ecx+4]` | `NextScenario` 缓冲区 |
| `0x00685A5C` | `e8 bf 83 f2 ff` | `call 0x5ade20` | **wrapper2** |
| `0x00685A74` | `e8 97 82 f2 ff` | `call 0x5add10` | **wrapper1** |

`[Scen+0x34B0]` 就是 `[Basic] SkipMapSelect`：读侧在 **`0x0068A200`**
（`68 e0 e0 83 00` = `push 0x83e0e0` = `"SkipMapSelect"`；`0x0068A205` `push 0x82bf9c`
= `"Basic"`；`0x0068A20C` `call 0x5295f0`；**`0x0068A211` `88 86 b0 34 00 00`
= `mov byte ptr [esi+0x34b0], al`**），写侧在 `0x0068B191`。W27 sandbox 的 `ECH01.MAP` / `ECH02.MAP` **都显式写了
`SkipMapSelect=no`** ⇒ 该字节为 0 ⇒ `je` 命中 ⇒ 走 wrapper1。 `[本次读码]` `[本次实测]`（`s07`/`s12`）

`[Scen+4]` / `[Scen+0x108]` 就是 `NextScenario` / `AltNextScenario` 缓冲区：读侧
`0x00689FCA / 0x00689FE8` 用 `push 0x83e19c` / `push 0x83e18c` + `push 0x82bf9c`(`"Basic"`)
+ `call 0x528a10`（INI GetString，长度 `0x104`）写入。 `[本次读码]`（`s05`/`s07`/`s08`）

### 3.2 wrapper → validator → 弹窗

| 路径 | VA | 原始字节 | 反汇编 |
|---|---|---|---|
| wrapper1 调用 validator1 | `0x005ADD63` | `e8 98 03 00 00` | `call 0x5ae100` |
| 取反结果 | `0x005ADD68` | `84 c0` | `test al, al` |
| | `0x005ADD71` | `0f 94 c3` | `sete bl` （`AL==0` → `bl=1`） |
| 失败分支 | `0x005ADD8B` | `84 db` | `test bl, bl` |
| | `0x005ADD8D` | `74 50` | `je 0x5adddf` （成功则跳过弹窗） |
| 弹窗文本 | `0x005ADDB5` | `b9 08 c1 82 00` | `mov ecx, 0x82c108` (`MSG:UnableMapSelect`) |
| | `0x005ADDC0` | `68 1c c1 82 00` | `push 0x82c11c` (`MapSel.CPP`) |
| | `0x005ADDC5` | `e8 96 70 18 00` | `call 0x734e60` |
| | `0x005ADDCF` | `e8 bc 56 02 00` | `call 0x5d3490` （出框） |
| wrapper2 调用 validator2 | `0x005ADE85` | `e8 96 00 00 00` | `call 0x5adf20` |
| | `0x005ADE8A` | `84 c0` | `test al, al` |
| | `0x005ADE93` | `0f 94 c3` | `sete bl` |
| | `0x005ADEB8` | `74 51` | `je 0x5adf0b` |
| 弹窗文本 | `0x005ADEE0` | `b9 08 c1 82 00` | `mov ecx, 0x82c108` |
| | `0x005ADEF0` | `e8 6b 6f 18 00` | `call 0x734e60` |
| | `0x005ADEFA` | `e8 91 55 02 00` | `call 0x5d3490` |

⇒ **弹窗的充要条件：对应 validator 返回 `AL == 0`。** `[本次读码]`（`s03`/`s08`）

### 3.3 validator1 `0x005AE100 → 0x005AE220`（`SkipMapSelect=no` 的实际路径）

按顺序的全部前置判定（`MapSel.CPP` 的 debug 串即失败原因）：

| # | 判定 | 失败时 VA / 原始字节 / debug 串 |
|---|---|---|
| 1 | `arg1`（Scenario 对象）非 NULL | `0x005AE22E` `3b e8` `cmp ebp,eax`；`0x005AE245` `push 0x82c200` → `MapSelect: Invalid Scenario pointer!` |
| 2 | `[Scen+0x1C74]` → `[0xA83C9C]` 表 → `[battle+0xBC]` → `[0x8B4124]` 表 得到非 NULL side 描述符 | `0x005AE25E..0x005AE27E`；`0x005AE280` `push 0x82c190` → `MapSelect: Invalid side!` |
| 3 | 以该描述符 `+0x24` 的名字为节名、`0x005CEEF0` 装载 **`MAPSELMD.INI`** | `0x005AE2BE` `e8 2d 0c 02 00` `call 0x5ceef0`；`test al,al; sete bl` → 失败 `push 0x82c150` → `MapSelect: Unable to initialize choices!` |
| 4 | **以「当前地图名」`[Scen+0x125C]` 去 `MAPSELMD.INI` 各 stage 的 `Scenario=` 反查阶段** | `0x005AE2F5` `81 c5 5c 12 00 00` `add ebp,0x125c`；`0x005AE30C` `e8 4f 14 02 00` `call 0x5cf760`；`0x005AE31C` `85 ff` `test edi,edi`；失败 `0x005AE320` `68 34 c1 82 00` `push 0x82c134` → **`MapSelect: Invalid stage!`** |
| 5 | 分配 0x20 字节 choice/font 对象 | `0x005AE327..0x005AE34A`；失败 `push 0x82c1dc` → `MapSelect: Unable to create font!` |
| — | 全过 → `mov al,1; ret 4` | `0x005AE448` `b0 01` |

`0x005CF760` 是纯字符串相等查表：`mov eax,[edi+0x10]`（阶段数），循环取
`[edi+4][i*4]+4`（每个 stage 的 `Scenario=` 字符串），与传入名（`0x7B5B30` 统一大写后
`0x7B4780` 比较）；找不到返回 `xor eax,eax`（`0x005CF7DB`）。 `[本次读码]`（`s04`/`s06`/`s12`）

### 3.4 validator2 `0x005ADF20`（`SkipMapSelect=yes` 的路径，反事实）

| # | 判定 | 失败点 |
|---|---|---|
| 1 | `arg1 != NULL` | `0x005ADF2D` `85 ed` / `0x005ADF2F` `74 3e` |
| 2 | `NextScenario`/`AltNextScenario` 字符串非空（`0x7B4710` 与 NULL 比较） | `0x005ADF37` `call 0x7b4710`；`0x005ADF3E` `jne fail` |
| 3 | battle/side 表查得非 NULL（`[Scen+0x1C74]` → `[0xA83C9C]` → `[+0xBC]` → `[0x8B4124]`） | `0x005ADF40..0x005ADF60`；`0x005ADF62` `push 0x82c190` → `Invalid side!` |
| 4 | `0x005CEEF0` 装载 `MAPSELMD.INI` | `0x005ADFA0` `call 0x5ceef0`；`0x005ADFBE` `push 0x82c150` → `Unable to initialize choices!` |
| 5 | `[Scen+0x35A0]`（**stage/序号**）经 `0x005CF810` 越界检查 | `0x005ADFD7` `66 8b 85 a0 35 00 00`；`0x005ADFE1` `call 0x5cf810`；`0x005ADFF3` `push 0x82c134` → `Invalid stage!` |
| 6 | 遍历当前 stage 的候选子项，逐条把子项 `Scenario=` 与 `NextScenario` 大写比对（`0x005AE073 call 0x7b4780`），命中才 `0x00686700` 写回 `[Scen+0x125C]` | 未命中同样走到失败返回 → 弹窗 |

`0x005CF810` 是纯序号边界判定：
`mov eax,[esp+4]; and eax,0xffff; cmp [ecx+0x10],eax; jg ok; xor eax,eax; ret 4`。
`[本次读码]`（`s03`/`s06`/`s08`）

### 3.5 `MAPSELMD.INI` 的真实位置与内容（CRC 交叉核对）

- `0x005CEF62` `68 70 03 83 00` = `push 0x830370` = `"MAPSELMD.INI"`；
  `0x005CEF6B` `ff 50 08` / `0x005CEF78` `ff 52 1c` 是 `CCFileClass` 虚调用（vtable `0x007E16B0`，
  `+0x1C = 0x00473D10`，磁盘优先），失败时 `0x005CEF8E` `push 0x830350` →
  `"Failed to load MAPSELMD.INI\n"`。`[本次读码]`（`s07`/`s08`）
- **`zlib.crc32(b"MAPSELMD.INI") = 0x922B8CE7`**（12 字节，4 对齐，plain == padded）。
  该 id **不在任何顶层 `.mix` 索引**，也不在游戏目录散装 —— 我最初（`s09`）据此误判「文件缺失」。
  `[本次实测，已被 s10/s11 推翻，见 EVIDENCE/CORRECTION_s09.md]`
- 正确位置：`ra2bench\ra2md.mix` 顶层 `entry[14] id=0xFBE0D09D`（offset `0x5F2C20`，4,819,480 B）
  是一个**嵌套的加密头 MIX**（头 4 字节 `00 00 03 00`，first=0 / flags=3）；
  用 W30 `mixlib` 仅作**解码工具**展开其 187 条索引后，`[20] id=0x922B8CE7 offset=0x129980 size=5573`
  正是 `MAPSELMD.INI`，SHA-256 `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52`。
  **CRC 与真实 MIX 实测 entry id 交叉核对成立**。`[本次实测]`（`s10`/`s11`）
- 全文 5,573 B：`[GDI]` `1=ALL01..7=ALL07`、`[Nod]` `1=Sov01..7=Sov07`，每个 stage 段内
  `Scenario=ALL01umd.MAP` … `Scenario=sov07tmd.MAP`。
  **`contains ECH01 / ECH02 / RA2F1 = False`**。`[本次实测]`（`s11`）
- 旁证：`ra2md.csf` 的 `ts_crc_hash=0xBD835079` 与 `langmd.mix` `entry[2]` 的真实 id 一致，
  说明本卡使用的 `zlib.crc32` 口径与容器实测 id 是自洽的。`[本次实测]`（`s01`）

## 4 · 差异点落在哪一个判定（方法第 4 步，本卡唯一目标）

| | `[SOV1] Scenario=ECH02.MAP` 直接起 | `[Basic] NextScenario=ECH02.MAP` 推进 |
|---|---|---|
| 入口 | `Start_Scenario` `0x00683AB0`：`cmp edx,-1` → `mov eax,[0xa83cfc]; mov ebp,[eax+edx*4]; add ebp,0x9c` 取 battle 项的 `Scenario=` 字段；`0x00683B04` 起经 `CCFileClass` 直接开图 | 结算屏 `GUI:Continue` → `0x00685A10` 状态机 → `MSG:UnableMapSelect` 分支 |
| 是否进 MapSelect | **否** | **是**（`SkipMapSelect=no` → `0x005ADD10`；`=yes` → `0x005ADE20`） |
| 目标文件名来源 | BATTLEMD.INI 的 `Scenario=` 字符串，直接交给 `CCFileClass`（磁盘优先，散装 `ECH02.MAP` 命中） | `NextScenario` 只读进 `[Scen+4]`；`SkipMapSelect=no` 时**完全不消费**；`=yes` 时仅作为 `MAPSELMD.INI` 当前 stage 候选 `Scenario=` 的**字符串匹配键** |
| 决定性判定 | 文件能否被 `CCFileClass` 打开（能，W27 实测） | **`0x005CF760` 用 `[Scen+0x125C]`（当前图 `ECH01.MAP`）反查 `MAPSELMD.INI` 阶段表** → 表中只有 14 张官方图 ⇒ 返回 0 ⇒ `MapSelect: Invalid stage!` ⇒ `MSG:UnableMapSelect` |
| 结果 | 正常入局 | 弹窗、frame 冻结、A2 未启动 |

**答：差异不在「目标文件是否存在 / 地图头是否合法 / theater 资源 / 战斗表登记 / EndOfGame」，
而在 `MapSelect::Init` 对 `MAPSELMD.INI` 阶段树的登记判定上** —— 具体是
`0x005AE30C call 0x5cf760` 后的 `0x005AE31C test edi,edi`（失败即 `0x005AE320`
`MapSelect: Invalid stage!`）。`NextScenario=ECH02.MAP` 无论写得多规范，都改变不了
「当前地图 `ECH01.MAP` 不在 `MAPSELMD.INI` 阶段表里」这一事实；
`SkipMapSelect=yes` 也只把失败点换成「stage 序号 `[Scen+0x35A0]` / 候选 `Scenario=`
比对」，同样要求我方图登记进 `MAPSELMD.INI`。 `[本次读码]` `[静态推断]`

**由此也解释了任务书里的两个既有事实** `[转引 W27/W28]`：
- 官方 14 图 `NextScenario=GDI2A.map`（文件根本不存在）却不影响官方战役 —— 因为官方图
  `SkipMapSelect=no`，推进走的是 `MAPSELMD.INI` 阶段树，`NextScenario` 不参与。 `[静态推断]`
- D3 把 `Scenario=` 直接指向 `ECH02.MAP` 能起 —— 因为开图路径根本不查 `MAPSELMD.INI`。 `[静态推断]`

**修复方向（非本卡授权范围，仅静态推断）**：把 `ECH01.MAP`/`ECH02.MAP` 作为新 stage
追加到一份散装 `MAPSELMD.INI`（`CCFileClass` 磁盘优先，会覆盖 MIX 内官方版），且必须
**克隆官方 14 个 stage 后追加**，否则官方战役链全断。`[静态推断]` `[待运行验证]`

## 5 · 地址口径与关键指令速查（VA / RVA / FOFF / 原始字节 / 反汇编并列）

全部为 **VA**；`.text` RVA == FOFF == `0x1000` ⇒ `FOFF = VA − 0x400000`；
`.data`/`.rdata` 同样 RVA==FOFF；`.rsrc`/`.detour` 不是（本卡未用）。
`0xA83C9C`、`0x8B4124`、`0xA8B230` 这类是 **VA**（全局量）。

| VA | RVA | FOFF | 原始字节 | 反汇编 | 含义 |
|---|---|---|---|---|---|
| `0x00401940` | `0x00001940` | `0x00001940` | `8b 41 18 c3` | `mov eax,[ecx+0x18]; ret` | GetFileName（任务书事实复核）`[本次实测]` |
| `0x00473D2D` | `0x00073D2D` | `0x00073D2D` | `e8 de e1 fb ff` | `call 0x431f10` | 磁盘尝试（任务书事实复核）`[本次实测]` |
| `0x00473D32` | `0x00073D32` | `0x00073D32` | `84 c0` | `test al,al` | 命中即越过 MIX 分支 `[转引]` |
| `0x005ADD63` | `0x001ADD63` | `0x001ADD63` | `e8 98 03 00 00` | `call 0x5ae100` | wrapper1 → validator1 |
| `0x005ADD71` | `0x001ADD71` | `0x001ADD71` | `0f 94 c3` | `sete bl` | `AL==0` ⇒ 弹窗 |
| `0x005ADDB5` | `0x001ADDB5` | `0x001ADDB5` | `b9 08 c1 82 00` | `mov ecx,0x82c108` | xref #1 |
| `0x005ADE85` | `0x001ADE85` | `0x001ADE85` | `e8 96 00 00 00` | `call 0x5adf20` | wrapper2 → validator2 |
| `0x005ADEE0` | `0x001ADEE0` | `0x001ADEE0` | `b9 08 c1 82 00` | `mov ecx,0x82c108` | xref #2 |
| `0x005AE25E` | `0x001AE25E` | `0x001AE25E` | `8b 8d 74 1c 00 00` | `mov ecx,[ebp+0x1c74]` | battle/side 表索引 |
| `0x005AE2BE` | `0x001AE2BE` | `0x001AE2BE` | `e8 2d 0c 02 00` | `call 0x5ceef0` | 装载 MAPSELMD.INI |
| `0x005AE2F5` | `0x001AE2F5` | `0x001AE2F5` | `81 c5 5c 12 00 00` | `add ebp,0x125c` | 取**当前**地图名 |
| `0x005AE30C` | `0x001AE30C` | `0x001AE30C` | `e8 4f 14 02 00` | `call 0x5cf760` | **决定性查表** |
| `0x005AE31C` | `0x001AE31C` | `0x001AE31C` | `85 ff` | `test edi,edi` | 0 ⇒ 失败 |
| `0x005AE320` | `0x001AE320` | `0x001AE320` | `68 34 c1 82 00` | `push 0x82c134` | `MapSelect: Invalid stage!` |
| `0x005CF810` | `0x001CF810` | `0x001CF810` | `8b 44 24 04` | `mov eax,[esp+4]` | stage 序号边界 |
| `0x005CF81C` | `0x001CF81C` | `0x001CF81C` | `3b d0` | `cmp edx,eax` | `jg` 才有效 |
| `0x005CEF62` | `0x001CEF62` | `0x001CEF62` | `68 70 03 83 00` | `push 0x830370` | `"MAPSELMD.INI"` |
| `0x00685A38` | `0x00285A38` | `0x00285A38` | `8a 81 b0 34 00 00` | `mov al,[ecx+0x34b0]` | `SkipMapSelect` |
| `0x00685A40` | `0x00285A40` | `0x00285A40` | `74 21` | `je 0x685a63` | 分派点 |
| `0x00685A59` | `0x00285A59` | `0x00285A59` | `8d 51 04` | `lea edx,[ecx+4]` | `NextScenario` 缓冲 |
| `0x00689FCA` | `0x00289FCA` | `0x00289FCA` | `68 9c e1 83 00` | `push 0x83e19c` | 读 `[Basic] NextScenario` |
| `0x0068A200` | `0x0028A200` | `0x0028A200` | `68 e0 e0 83 00` | `push 0x83e0e0` | 读 `SkipMapSelect` → `[Scen+0x34B0]`（写回在 `0x0068A211` `88 86 b0 34 00 00`） |
| `0x00683AF8` | `0x00283AF8` | `0x00283AF8` | `81 c5 9c 00 00 00` | `add ebp,0x9c` | 直接取 battle 项 `Scenario=` |

`.data` 常量（VA / FOFF 同值 − `0x400000`）：
`0x0082C108` `MSG:UnableMapSelect`；`0x0082C11C` `MapSel.CPP`；
`0x0082C134` `MapSelect: Invalid stage!`；`0x0082C150` `MapSelect: Unable to initialize choices!`；
`0x0082C190` `MapSelect: Invalid side!`；`0x0082C200` `MapSelect: Invalid Scenario pointer!`；
`0x00825FB0` `TXT_OK`；`0x00830350` `Failed to load MAPSELMD.INI`；`0x00830370` `MAPSELMD.INI`；
`0x0083E0E0` `SkipMapSelect`；`0x0083E138` `EndOfGame`；`0x0083E19C` `NextScenario`；
`0x0082BF9C` `Basic`。 `[本次实测]`（`s04`/`s06`/`s08`）

## 6 · 与任务书前提不符处

见 `DISAGREE.md`。未覆盖项与待验证项见 `UNKNOWNS.md`。
