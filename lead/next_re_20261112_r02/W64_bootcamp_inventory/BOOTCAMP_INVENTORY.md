# W64b · Boot Camp / `tut1` 战役数据盘点（纯离线只读）

> 执行者：Hy4（逆向工程重派卡 W64b；原 W64 派 GLM-5.3-Flash 零产出静默失败）｜开始 `STARTED.txt` 2026-11-13T23:32:45+08:00｜时间盒 45 min
> **I launched 0 / attached 0**：未启动 `gamemd.exe`、未 attach、未读活进程内存、**未取 `.game_instance.lock`**（真机卡 W63 可能正在跑；观察到 `gamemd.exe` 属其他卡，未触碰）。
> 只写本卡目录；未写 `ra2youli` / `ra2bench` / `ra2forge` / `ra2opt` / `ra2bench\gamemd.exe` / W21–W63；`git` 只读。
> 分级：`[本次实测]`（本卡脚本/解析读出的）、`[本次读码]`（本卡读出的既有码/字节语义）、`[静态推断]`、`[转引]`、`[待运行验证]`。
> **本卡不写「官方 Boot Camp 战役可用」这类未经真机的断言。**
> 复用工具：`ra2forge\mixlib.py`（`westwood_decrypt_key_block` / `Blowfish` / `crc_hash` / `classic_hash`）+ W34 `ra2forge_patched_v11\ra2forge\mixlib.py` 的 `ts_crc_hash`；MIX 递归解析器本卡自写（`w64b_analyze.py` 的 `parse_ts` / `parse_classic` / `looks_like_mix`），因需校验式递归 + 去掉 W61 的 2 MB 条目上限。另复用 W61 `EVIDENCE\q2_scan_stdout.txt`、W34 `EVIDENCE\MAPSELMD.OFFICIAL.INI`、项目根 `extracted\all_inis\` 作交叉核对。

---

## 0 · 一句话结论

`[本次实测]` **YR 可加载的 `tut1` 战役数据（battle 条目 / 地图 / 阶段表）三类全缺**；安装里确有一份 **vanilla RA2 的 `BATTLE.INI`** 带 `[Battles] 1=TUT1` + `[TUT1] Scenario=trn01t.MAP`，但它藏在 `ra2.mix/LOCAL.MIX` 里，`gamemd.exe` 只枚举 `BATTLEMD*.INI` / `BATTLEMD.INI`（exe 内 `BATTLE.INI` 字面量 **0 次**）⇒ **不会被 YR 加载，是死数据**。CSF 文案 / 音效 / 引擎字符串属 UI 层，已在（W61 已证），不是战役数据。

---

## 1 · Q1：有没有 `TUT1` battle 条目？

### 1.1 判定

`[本次实测]` **YR 加载路径上不存在。** `BATTLEMD*.INI`（散装 + MIX 内）全部 `[Battles]` 无 `N=tut1`、全部段表无 `[TUT1]`。
`[本次实测]` **但物理上存在一份不会被加载的 vanilla RA2 `BATTLE.INI`**：`ra2.mix` → 嵌套 `LOCAL.MIX`（`id=0xA8548FD9`，`ts_crc_hash("LOCAL.MIX")`）→ 条目 `id=0x889C5B31`（`ts_crc_hash("BATTLE.INI")`，4,054 B），含 `[Battles] 1=TUT1` 与 `[TUT1] CD=0 / Scenario=trn01t.MAP / FinalMovie= / Description=DESC:TUT1`。
`[本次实测]` 该文件的 `1=TUT1` 前后 40 字节解码片段见 §3「新增命中 N1」；全文已存 `EVIDENCE\extracted\MIX_ra2_LOCAL_MIX_BATTLE.INI`。

### 1.2 查过的文件清单 + 每个文件的 SHA-256

`[本次实测]` 全部由 `EVIDENCE\w64b_analyze.py` S1 阶段逐字节读出（`EVIDENCE\S1_q1_stdout.txt` / `S1_q1.json`）。

| # | 文件（`<ROOT>` = `D:\Project\ra2-campaign-forge`） | 大小 B | SHA-256 | `[TUT1]` 段 | `[Battles] N=tut1` | `tut1` 出现次数 |
|---|---|---:|---|---|---|---|
| 1 | `ra2bench\BATTLEMD.INI`（官方原版，W47 无副本） | 2,733 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | ✗ | ✗ | 0 |
| 2 | `ra2youli\BATTLEMD.INI` | 2,733 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | ✗ | ✗ | 0 |
| 3 | `ra2youli\BATTLEMD98.INI`（ra2forge 生成件，非官方） | 453 | `4e3417568924891792520ad8c3ab44f42e11fdc9934fb453d4db7210bf3d2c74` | ✗ | ✗（`15=RA2F1`） | 0 |
| 4 | `ra2md.mix/LOCALMD.MIX` → `BATTLEMD.INI`（`id=0x07E280DD`，abs `0x7766B0`） | 2,733 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | ✗ | ✗ | 0 |
| 5 | `ra2md.mix/LOCALMD.MIX` → `MAPSELMD.INI`（`id=0x922B8CE7`，abs `0x71D050`） | 5,573 | `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52` | ✗ | n/a | 0 |
| 6 | `ra2.mix/LOCAL.MIX` → `BATTLE.INI`（`id=0x889C5B31`，abs `0x742DCB0`）**vanilla RA2 死数据** | 4,054 | `a5752a8d49e1c3823fe01a55e0057f91f2996d8b4a78804f197251a79b552a1d` | **✓** | **✓ `1=TUT1`** | 3 |
| 7 | `ra2bench\RA2MD.INI`（对照，非 battle 表） | 1,752 | `16a21f054a0f58fa9958104cbef8aca9344b6abdaa705ac0af480bad5a455d1d` | ✗ | — | 0 |
| 8 | `ra2youli\RA2MD.INI`（对照） | 1,754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | ✗ | — | 0 |
| 9 | `ra2youli\.ra2opt\orig\RA2MD.INI`（对照） | 1,611 | `8b28ddd7fcc77b71f8845a50dd895c5f64c86b58fe46eeaea517d65612c09262` | ✗ | — | 0 |
| 10 | `ra2youli\.ra2opt\orig\ra2.ini` / `ddraw.ini`（对照） | 1,769 / 14,350 | `f4c41e7b0b1c2ae550442e7588a72d4a47ce1bd2acb64ee9ffed589487813c92` / `c98bbefa96e432ee311bcf99e813f44211bbefb5fa4a2bb140673f17b1a07199` | ✗ | — | 0 |

`[本次实测]` 补充：
- `ra2bench\BATTLEMD.INI` == `ra2youli\BATTLEMD.INI` == MIX 内 `BATTLEMD.INI`，三者 SHA-256 相同 ⇒ `ra2bench` 侧就是官方原版（**W47 `W47_baseline_adjudication` 卡内无 `BATTLE*.INI` 副本**，已递归查过）。
- `[Battles]` 官方 14 条：`1=ALL1, 2=SOV1, 3..8=ALL02..ALL07, 9..14=SOV02..SOV07`；15 个段：`[Battles],[ALL1],[SOV1],[ALL02..07],[SOV02..07]`。
- MIX 内 `BATTLEMD98.INI` / `BATTLEMD00/01/02/03.INI` / `MAPSEL.INI` / `MAPSELMD98.INI` / `SOUND.INI`（按 crc32 名字反查）**0 处命中**（`S1_q1_stdout.txt` L28–43）。
- `BATTLE.INI` 用的是 **Westwood 尾部填充哈希** `ts_crc_hash("BATTLE.INI")=0x889C5B31`，不是 `crc32("BATTLE.INI")=0x000F70E4`（`EVIDENCE\S6_id_resolution_stdout.txt`）——这解释了为何按普通 crc32 反查会漏掉它。

### 1.3 为什么这份 `BATTLE.INI` 对 YR 不算「自带可用战役」

`[本次实测]` `EVIDENCE\S5_exe_strings_stdout.txt`（读 `ra2bench\gamemd.exe` 4,825,360 B / `73201cc0…67476` 字节，未运行）：

| 字面量 | 命中数 | 文件偏移 |
|---|---:|---|
| `BATTLEMD*.INI` | 1 | `0x4261A8` |
| `BATTLEMD.INI` | 1 | `0x426198` |
| `MAPSELMD.INI` | 2 | `0x43035F`, `0x430370` |
| `BATTLE.INI` | **0** | — |
| `BATTLE*.INI` / `BATTLEMD98.INI` | 0 | — |
| `tut1` | 1 | `0x425C90`（`.data` 里的 battle 名，非 INI 文件） |

`[本次读码]` + `[转引 W37/W33/ra2forge\mixlib.py:311-315]`：`Battle::Read_INI` 用 `FindFirstFileA("BATTLEMD*.INI")` 在**游戏目录文件系统**枚举，回退 `BATTLEMD.INI`；同名文件打包在 MIX 里也不会被该通配符匹配。`BATTLE.INI` 不匹配 `BATTLEMD*.INI` ⇒ YR 永不加载。
`[本次实测]` 另外，该文件引用的 `trn01t.MAP` / `trn02t.MAP` 在任何 MIX 条目 CRC 中 **0 命中**（§2.3），即便强行加载也进不了图。
`[待运行验证]` 未做真机；"不加载"是静态链结论。

---

## 2 · Q2：有没有官方 tutorial 地图？

### 2.1 先确认 MIX 有没有 name table

`[本次实测]` `EVIDENCE\S2_q2_stdout.txt` §2.1，逐个字节级检查 **33 个顶层 MIX**（`ra2bench` 16 + `ra2youli` 17，两目录 16 个同名 MIX SHA-256 全同；`ra2youli` 另有 `expandmd98.mix`）：

- TS/RA2 MIX 索引布局：`<H 0><H flags><H count><I size>` + `N × (<I id><I off><I size>)` —— **只有 32 位 CRC id、偏移、尺寸**；**没有文件名字段、没有 name-table 偏移/长度字段、头部没有 ASCII 文件名串**。
- 检查 XCC 的可选 name table 约定 `local mix database.dat`：每个 MIX 顶层条目 id 与 `crc_hash`/`classic_hash` 比对 → **`has_localdb_entry=False` 全部 33 个**；全文件扫 `b"XCC by Olaf van der Spek"` → **`xcc_sig_in_raw=False` 全部 33 个**；两个游戏目录也**没有散装** `local mix database.dat`。
- ⇒ **MIX 文件带有任何 name-table 标记：0 / 33**。`theme.mix` / `thememd.mix` 是 C&C 旧格式（`first=0x0010` / `0x000A`，非 TS MIX，W61 也跳过），本卡用 `parse_classic` 校验后仍未发现名字表。
- `[转引 ra2forge\mixlib.py:304-318]` 引擎自身不读 `local mix database.dat`；`MixFileClass` 查表是纯 CRC32 命中。

**结论 `[本次实测]`：这些 MIX 没有 name table。因此「文件名」不可从归档内读出，只能靠「内容特征 + 猜测名字做 CRC32/crc_hash 成员测试」；不能证明某个条目确切叫什么名字。**

### 2.2 地图清单（容器文件 / 容器内 id / 尺寸）

`[本次实测]` `EVIDENCE\S2_q2_stdout.txt` §2.3：生成 **1,003 个**候选名（`TUT*`/`BOOT*`/`*TUTOR*`/`SCG0*`/`TRN*` × 编号/后缀/扩展名，含 `TUT01.MAP`、`BOOTCAMP.MAP`、`SCG01.MAP`、`TRN01T.MAP` 等），对递归枚举出的 **13,007 个不同 CRC id**（2,125 个校验通过的嵌套容器）做成员测试：

| 类别 | 候选名数 | CRC 命中 |
|---|---:|---:|
| `TUT*.MAP` | ~400 | 0 |
| `BOOT*.MAP` | ~300 | 0 |
| `*TUTOR*.MAP` | ~50 | 0 |
| `SCG0*.MAP` | ~200 | 0 |
| `TRN*.MAP`（含 `trn01t.MAP`/`trn02t.MAP`） | ~50 | 0 |
| **合计** | **1,003** | **0** |

**⇒ 官方 tutorial 地图清单：空（无任何 `TUT*.MAP` / `BOOT*.MAP` / `*TUTOR*.MAP` / `SCG0*.MAP` 条目）。**

`[本次实测]` 内容特征兜底（§2.4）：扫出 **635 个**像 RA2 `.MAP`（文本、含 `[Map]`/`[Basic]`/`[Header]`/`Waypoint`）的条目，**其中 198 个**含 `TRN0*`/`TUT*`/`SCG0*` 字样，共 288 处匹配，但性质都是 vanilla RA2 教程**遗留字符串**，不是教程地图：

```
[Basic]
Briefing=Brief:TRN01
NextScenario=GDI2A.map
AltNextScenario=GDI9C.MAP
...
07B72F3C=4,11,4,MISSION:TRN01j,...
Mis_T1_DrillSearg09 ...
```

它们分布在 `multi.mix` / `multimd.mix` / `maps01.mix` / `maps02.mix` / `expandmd01.mix` 的**多人/遭遇战地图**里，尺寸 57 KB–420 KB，`Briefing=Brief:TRN01` 是地图编辑器默认模板遗留。`[静态推断]` 这些是 vanilla RA2 训练关的 briefing/任务标签被烤进了后续地图，**不构成可进图的教程战役地图**。

`[本次实测]` §2.5：`ra2.mix` 原始字节里确有字面 `TRN01T.MAP` / `TRN02T.MAP` / `trn01t.MAP` / `trn02t.map` 5 个字符串 —— 来源正是 §1 那份 vanilla `BATTLE.INI` 的 `[TUT1] Scenario=trn01t.MAP` / `[TRN02] Scenario=trn02t.MAP` 等 INI 文本，**不是 name table**，且这些名字对应的条目 CRC 全不命中（即地图实体不在）。

`[本次实测]` 覆盖度说明：本卡用**校验式**递归（`looks_like_mix` 要求条目自洽）得 2,125 容器 / 13,007 id；W61 用宽松递归（凡首 2 字节 `00 00` 即当 MIX）报 5,630 容器 / 1,168,759 id。后者大概率含大量非 MIX 误递归产生的噪声 id；两者在"候选名 CRC 成员测试"上结论一致（W61 也只命中 `CAMPAIGN.PCX`）。见 `DISAGREE.md` D2。

---

## 3 · Q3：`TUT1` 那 7 处命中的性质

### 3.1 口径先说清

`[转引]` 题面/W61 说 `TUT1` 出现在 `expandmd01/langmd/language/maps01/maps02/multi/multimd` **7 个容器**。
`[本次实测]` W61 `EVIDENCE\q2_scan_stdout.txt` 实际列的是 **8 个条目**（`multimd.mix` 有 2 条：`03A45E74` 与 `1152557E`）——「7 个容器 / 8 个条目」。
`[本次实测]` 本卡独立全量扫描（无 W61 的 2 MB 上限、两安装都扫、按物理偏移去重）：**21 个不同字节位置 / 17 个 (容器,id) 组 / 10 个顶层 MIX 文件**（`EVIDENCE\S3_q3_stdout.txt`）。比 W61 多出的 3 个顶层文件是 `ra2.mix`、`ra2md.mix`、`movmd03.mix`，多出的命中全是二进制图像/视频里的巧合字节，加上**1 个 W61 完全漏掉的真 INI 命中**（§3.3 N1）。

### 3.2 W61 那 8 处（7 容器）逐条定位 + ±40 字节解码片段

`[本次实测]` 全部片段摘自 `EVIDENCE\S3_q3_stdout.txt`（`before40` / `hit` / `after40`，`\r\n` 显示为换行；完整 hexdump 见该文件）。分类口径：(a) 文件名 (b) INI 键值 (c) CSF 标签 (d) 地图内部字符串 (e) 巧合字节。

| # | 容器 / 条目 id / 尺寸 | 性质 | before40 | hit | after40 |
|---|---|---|---|---|---|
| 1 | `expandmd01.mix` `03A45E74` 236,298 | **(e)** `.MAP` 内 base64 打包数据行的巧合字节（该条目是 INI 文本 `.MAP`，`438=…` 行是编码块） | `oKQBvSQGLpQhwSAElkU9xSQGPtQJySAElkU9zSQH` | `TuT1` `54 75 54 31` | `0SA` `\r\n` `336=HBtHUoKQB2SAHBBHdJAdWtBXhJAY2xC` |
| 2 | `langmd.mix` `BD835079` 332,973（`ra2md.csf`） | **(c) CSF 标签** `DESC:TUT1` | `....................... LBL....\t...DESC:` | `TUT1` `54 55 54 31` | ` RTS....O....u.. ........o8.....&.....-.` |
| 3 | `language.mix` `7F6FBCDF` 283,368 | **(c) CSF 标签** `DESC:TUT1`（另一份 CSF） | `....................... LBL....\t...DESC:` | `TUT1` | ` RTS....O....u.. ........o8.....&.....-.` |
| 4 | `maps01.mix` `179782BB` 220,010 | **(e)** `.MAP` 编码行巧合（`438=BxSQG…`） | `EgB3SBtSAHdIG4oKQBvKCkAcEgB3S` `\r\n` `438=BxSQG` | `tuT1` `74 75 54 31` | `ySAHVLnPIAV0VdMgBVQ11SAHNBXZIAcU/d0gB1Tl` |
| 5 | `maps02.mix` `179782BB` 220,010 | **(e)** 与 #4 同一张图（同 id / 同尺寸 / 同偏移内容） | 同 #4 | `tuT1` | 同 #4 |
| 6 | `multi.mix` `49D8008E` 154,668 | **(e)** `.MAP` 编码行巧合（`58=kAZigp…`） | `KCkAYygpAGQoKQBlKC` `\r\n` `58=kAZigpAGcoKQBoSQG` | `tuT1` | `pSAHdCmpJATJsAXdEGgBXqQFsVQKMqQFtSAHDRjo` |
| 7 | `multimd.mix` `03A45E74` 236,298 | **(e)** 与 #1 同一个文件（同 id / 同尺寸 / 同字节） | `oKQBvSQGLpQhwSAElkU9xSQGPtQJySAElkU9zSQH` | `TuT1` | `0SA` `\r\n` `336=HBtHUoKQB2SAHBBHdJAdWtBXhJAY2xC` |
| 8 | `multimd.mix` `1152557E` 413,242 | **(e)** `.MAP` 编码行巧合（`476=pYFkg…`） | `RE` `\r\n` `476=pYFkgARNRbAai0SEAKWAdcAsRNdH4i9F` | `tUt1` `74 55 74 31` | `h/aDaEtqyLJKRFU1O4uFhuW5RAXI9wNUGI` `\r\n` `477=` |

`[本次实测]` 注：`#1/#7`、`#4/#5` 分别是同一份 `.MAP` 被打包进两个不同 MIX（id 与 size 完全一致），不是两份教程地图。
`[静态推断]` 8 处里 **2 处是真语义命中（都是 CSF 标签）**，**6 处是 `.MAP` 内 base64 编码行里恰好出现 `TUT1` 大小写变体的巧合字节**（既不是文件名、不是 INI 键值、不是 CSF、也不是有意义的地图内部字符串）——这解释了 W61 §2.2-7 说的「`TUT1` 只出现在 CSF/地图 INI/MULTI 相关条目」。

### 3.3 本卡新增：W61 漏掉的第 9 处（真 INI 命中，最重要）

`[本次实测]` `ra2.mix/A8548FD9`（= `LOCAL.MIX`）条目 `889C5B31`，4,054 B，INI 文本，**3 个 `TUT1` 字面量**：

| 子命中 | 性质 | before40 | hit | after40 |
|---|---|---|---|---|
| N1-a | **(b) INI 键值** `[Battles] 1=TUT1` | ` only) identifier name.` `\r\n` `[Battles]` `\r\n\r\n` `1=` | `TUT1` | `\r\n` `2=ALL1` `\r\n` `3=SOV1` `\r\n` `;everything below this` |
| N1-b | **(b) 段名** `[TUT1]` | `FinalMovie=` `\r\n` `Description=DESC:E32` `\r\n\r\n\r\n\r\n` `[` | `TUT1` | `]` `\r\n` `CD=0` `\r\n` `Scenario=trn01t.MAP` `\r\n` `FinalMovie` |
| N1-c | **(b) INI 键值** `Description=DESC:TUT1` | `n01t.MAP` `\r\n` `FinalMovie=` `\r\n` `Description=DESC:` | `TUT1` | `\r\n\r\n\r\n` `[ALL1]` `\r\n` `CD=0` `\r\n` `Scenario=ALL01t.MAP` `\r\n` `F` |

`[本次实测]` `EVIDENCE\S6_id_resolution_stdout.txt`：`ts_crc_hash("LOCAL.MIX")=0xA8548FD9`、`ts_crc_hash("BATTLE.INI")=0x889C5B31`，容器在 `ra2.mix` 顶层 `off=0x70BCE60 size=34,793,784`（33.18 MB）。
`[本次读码]` **W61 为什么漏**：`q2_scan.py:27` 跳过 `size>2,000,000` 的条目，33 MB 的 `LOCAL.MIX` 被整块 skip，既不递归也不扫内容。本卡无此上限 ⇒ 命中。见 `DISAGREE.md` D1。

### 3.4 其余 12 个不同字节位置（本卡额外发现，全是巧合）

`[本次实测]` `EVIDENCE\S3_q3_stdout.txt`：`movmd03.mix 1F204132`（BIK 视频 19.8 MB，`TUt1` 在像素/码流里）、`ra2.mix/0F5D1D99 B86CE22B`、`ra2.mix/40B4C119 0D84A4DD` + `E6C5C154`、`ra2.mix/A226651E 0E700B17` + `3BE0042E` + `E44F37F7`（3 处）、`ra2md.mix/FF6808D5 D7604CAE` —— 全是 SHP/PCX/BIK **二进制像素/视频数据里的 `(e) 巧合字节序列**（hexdump 显示 `TUT1` 夹在调色板/压缩字节中，如 `…65554G%)DF-EDDCDCCBABCA(TUT12.,.1.X…`）。与 `(a)(b)(c)(d)` 均无关，无一条是文件名。

---

## 4 · Q4：`MAPSELMD.INI` 有没有 tutorial 阶段？

`[本次实测]` `EVIDENCE\S4_q4_stdout.txt`：从 `ra2bench\ra2md.mix` 文件偏移 `0x71D050` 切出 5,573 B，SHA-256 `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52`，与 W34 `EVIDENCE\MAPSELMD.OFFICIAL.INI` **逐字节相同**；`crc32("MAPSELMD.INI")=0x922B8CE7` ✓（题面给的 `LOCALMD.MIX` 是嵌套容器名 `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")` `[转引 W34/W37]`；本机磁盘**没有**独立的 `LOCALMD.MIX` 文件）。

**全部段名（20 个）`[本次实测]`：**

```
[GDI] [GDISFX] [Nod] [NODSFX] [Anims]
[ALL00] [ALL01] [ALL02] [ALL03] [ALL04] [ALL05] [ALL06] [ALL07]
[Sov01] [Sov02] [Sov03] [Sov04] [Sov05] [Sov06] [Sov07]
```

- **没有 `[Scen]` 段**（`[本次实测]`）。题面「`[Scen]` 与各阵营段」的措辞与该文件不符；`[Scen]` 是 `.MAP` 文件里的段名。本卡按实际文件作答：阵营段 = `[GDI]` / `[Nod]`，另有 `[GDISFX]` / `[NODSFX]` / `[Anims]` 配置段。见 `DISAGREE.md` D4。
- **全部阶段名（14 个，`[本次实测]`）**：`[GDI] 1=ALL01 … 7=ALL07`；`[Nod] 1=Sov01 … 7=Sov07`。
- 阶段段共 **15 个**（多一个 `[ALL00]` 起始段，`Scenario=` 为空；`[Sov00]` 在文件里被注释掉）：
  `[ALL00] Scenario=(空)`、`[ALL01] Scenario=ALL01umd.MAP`、`[ALL02] ALL02umd.MAP`、`[ALL03] ALL03umd.MAP`、`[ALL04] ALL04dmd.MAP`、`[ALL05] ALL05umd.MAP`、`[ALL06] ALL06umd.MAP`、`[ALL07] ALL07smd.MAP`、`[Sov01] Sov01umd.MAP`、`[Sov02] sov02smd.MAP`、`[Sov03] sov03umd.MAP`、`[Sov04] sov04dmd.MAP`、`[Sov05] sov05umd.MAP`、`[Sov06] sov06lmd.MAP`、`[Sov07] sov07tmd.MAP`。
- **全文 `TUT*` / `SCG*` / `TRN*` / `BOOT*` / `TUTORIAL*` 匹配：NONE**（`[本次实测]`）。

**⇒ `[本次实测]` 官方 `MAPSELMD.INI` 没有任何 tutorial 阶段；`tut1` 战役未在阶段表登记。**
`[转引 W31/W33/W39/W40]` 战役推进必须先过 `MapSelect::Init` 的 `MAPSELMD.INI` 反查（`0x5CF760`），未登记即 `MapSelect: Invalid stage!` → `MSG:UnableMapSelect`；W39 真机三臂已证"追加阶段后可 A2_loaded"。**故对 `tut1` 而言这是硬缺口，不是可选项。**

---

## 5 · Q5：三分结论 + 「要造多少」

### 5.1 三分判定

**`[本次实测]` 判定：`部分自带`（写明缺哪些）。** 但按题面「**可用的** Boot Camp 战役」这一更严口径，**等价于 `完全没有`**——没有任何一条 YR 能加载的 `tut1` 战役数据。

| 层 | 是否自带 | 说明 |
|---|---|---|
| 引擎第三槽代码 / battle 名 `tut1` / 音效 `BootCampSelect` / CSF `STT:CampaignAnimTutorial` / `DESC:TUT1` | ✅ `[转引 W61]` | UI/文案层，非本卡范围（战役数据） |
| vanilla RA2 `BATTLE.INI` 的 `[Battles] 1=TUT1` + `[TUT1]` 段 | ✅ 但**死数据** `[本次实测]` | 在 `ra2.mix/LOCAL.MIX`，`gamemd.exe` 不加载；引用的 `trn01t.MAP` 也不存在 |
| **YR 可加载的 `BATTLEMD*.INI` `[TUT1]` 段 / `[Battles] N=tut1`** | ❌ **不存在** `[本次实测]` | 散装 + MIX 内 4 份全查，SHA 见 §1.2 |
| **官方 tutorial `.MAP`（`TUT*`/`BOOT*`/`*TUTOR*`/`SCG0*`）** | ❌ **不存在** `[本次实测]` | 1,003 候选名 CRC 0 命中；MIX 无 name table，靠内容特征亦无 |
| **`MAPSELMD.INI` tutorial 阶段** | ❌ **不存在** `[本次实测]` | 20 段 / 14 阶段全为 `ALL0x` / `Sov0x` |
| 第三徽章美术 | ❌ `[转引 W61]` | 全 MIX 递归无 `TUT*`/`BOOT*`/`BADGE*` 资源 |

**明确一句话 `[本次实测]`**：这台 YR 安装**没有官方自带可用的 Boot Camp 战役**；`tut1` 只有 UI 文案/音效/代码残骸和一份 YR 不会读的 vanilla RA2 `BATTLE.INI`，battle 登记、地图、阶段表三样**都要我们自己造**。

### 5.2 若要用 (c) 路线开第三槽，`tut1` 战役的数据要造多少

> **一句话**：`[本次实测/静态推断]` **要造 1 条 `[Battles]` 登记（`15=TUT1`）+ 1 个 `[TUT1]` 段（5 键）+ 至少 1 张全新 `.MAP` + 1 组 `MAPSELMD.INI` 阶段登记（克隆官方 5,573 B 后追加约 10 行）；`DESC:TUT1` / `STT:CampaignAnimTutorial` / `GUI:TutorialCampaign` / `BootCampSelect` 音效已自带，可零改动复用。**

`[静态推断]` 量化清单（不含 W61 的 exe 补丁与第三徽章美术，那两项属 (c) 路线的其余门槛）：

| # | 要造的东西 | 最小量 | 依据 / 现成可复用的 |
|---|---|---|---|
| 1 | `BATTLEMD.INI`：`[Battles]` 追加 + `[TUT1]` 段 | **2 处 / ~8 行**：`15=TUT1`；`[TUT1] CD=-1(or 2) / Scenario=<新图>.MAP / FinalMovie= / Description=DESC:TUT1`（不要写 `DebugOnly`） | `[转引 W61 §4]` `Battle::Read_INI 0x46CCD0` 全带缺省读；`DESC:TUT1` 在 `ra2md.csf` 已存在 ⇒ **不用造 CSF 标签** |
| 2 | 首关 `.MAP` | **≥1 张全新地图，从零创作**（多关链则 N 张） | `[本次实测]` `trn01t.MAP`/`trn02t.MAP`/`TUT*`/`SCG0*` CRC 全 0 命中，官方无任何可复用教程图 |
| 3 | `MAPSELMD.INI` 阶段登记 | **完整克隆官方 5,573 B + 追加 1 条阵营阶段行 + 1 个新阶段段**（`Scenario=` / `Description=` / `VoiceOver=` / `MapVQ=` / `Overlays=` / `Targets=` / `ClickMap=` + 数字后继子项），约 10 行 | `[转引 W34 MAPSELMD_SPEC.md / W39 真机]` 必须 whole-file 克隆，不能只给最小文件；可直接复用官方 `GDIMAP01.VQA` / `GDICLK01.PCX` / `RG*.SHP` / `GDI-0x.AUD` ⇒ **MapSelect UI 资源零新增** |
| 4 | （可选）教程专属 MapSelect 视觉 | 0（若复用官方）或 N 个 VQA/PCX/SHP/AUD 资产 | `[静态推断]` 属资产创作，非逆向 |
| 5 | （(c) 路线其余）exe 补丁 + 第三徽章美术 | W61 已量化：`RT_DIALOG 148` +1 控件、61 个 RVA 修正；美术须新造并重绘菜单背景 | `[转引 W61 §5 / LEAD_RULING §5]` |

`[待运行验证]` 以上全部是静态结论：造完之后能不能进图、能不能推进第二关、第三徽章点击是否不越界，**都要真机验**（W63 口径），本卡未运行任何东西。

---

## 6 · 证据路径（三条主证据）

1. `EVIDENCE\S1_q1_stdout.txt` + `S5_exe_strings_stdout.txt` + `S6_id_resolution_stdout.txt` — Q1：文件清单/SHA-256、MIX 内 `BATTLEMD.INI` 无 `[TUT1]`、vanilla `BATTLE.INI` 的 `ts_crc_hash` 身份、`gamemd.exe` 只认 `BATTLEMD*.INI`。
2. `EVIDENCE\S2_q2_stdout.txt` — Q2：0/33 MIX 有 name table、1,003 候选地图名 0 命中、635 个 map-like 条目的内容特征。
3. `EVIDENCE\S3_q3_stdout.txt` + `S4_q4_stdout.txt` — Q3/Q4：21 个 `TUT1` 字节位置的 ±40 解码 + hexdump；官方 `MAPSELMD.INI` 20 段 / 14 阶段全表。

全部脚本 stdout 与退出码：`EVIDENCE\MAIN_stdout.txt` / `MAIN_exitcode.txt`（0）、`S0_skeleton_*`（0）、`S5_exe_strings_*`（0）、`S4_only_*`（0）、`S6_id_resolution_*`（0）。脚本：`w64b_inventory.py`（骨架）、`w64b_analyze.py`（主）、`w64b_exe_strings.py`、`w64b_s4_only.py`、`w64b_id_resolution.py`。逐阶段 JSON：`S1_q1.json` / `S2_q2.json` / `S3_q3.json` / `S4_q4.json` / `ALL.json` / `S5_exe_strings.json` / `S6_id_resolution.json`。提取件：`EVIDENCE\extracted\`。

---

## 7 · 纪律自检

- `I launched 0 / attached 0`；观察到 `gamemd.exe` 属其他卡，未触碰；**未取 `.game_instance.lock`**。
- 只读 `ra2bench` / `ra2youli` / `ra2forge`（只读 import）/ `extracted` / `lead` 既有卡；未写任何上述目录。
- 未写 `ra2forge` / `ra2opt` / `ra2bench` / W21–W63；`git` 只读。
- 全程分级标注；未写「官方 Boot Camp 战役可用」。
