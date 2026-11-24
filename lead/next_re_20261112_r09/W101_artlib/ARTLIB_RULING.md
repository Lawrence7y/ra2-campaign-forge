# W101 · ARTLIB_RULING —— 引擎实际读哪份 art 库

> 卡号 W101｜离线静态分析（零启动、零注入、零写入 `ra2youli\`）｜2026-11-14
> 目标镜像 `ra2youli\gamemd.exe`（SHA-256 `73201CC0…67476`，`.text` raw SHA-256 与 `docs/re/fs_mix_load_chain_deep.md` §9.2 基线**全等**，故该文档全部 [实证] 地址可直接引用）。

---

## 0 · 一句话裁决

**(b) 引擎实际读的 art 库 = `ra2md.mix` 内嵌套的 `LOCALMD.MIX`（加密索引）中的 `ARTMD.INI`（引擎 id `0x5B47D8D5`，336,535 B，SHA-256 `E1F03783…BA31`）——即 W97 提取的那份文件。分级：[已证]。**

**对 §632-1 的影响：NAPOWR=3×2 不仅仍是文件事实，而且现在[已证]就是引擎真实读取的配置。**

底座 §5 与 W97 U1 的「引擎按 `0xAF902833` 取 ARTMD.INI、发行版把三个大 INI 换了名」**两条都不成立**：名字从未换过，换的是哈希算法——引擎用的是 **count-pad CRC32**（尾块补 `L` 再重复首字节），不是未填充的 zlib crc32。详见 §2 与 DISAGREE.md。

---

## 1 · 问题界定（两个不要混的事）

- (a) 「W97 那份 336,535 B art 文件里 TESLA=1×1、NAPOWR=3×2」——**文件事实，本卡复核成立且不受 (b) 影响**。
  本卡普查直接给出该文件 markers：`Foundation=×580, Image=×383, Cameo=×248, [NAPOWR]×1, [NATSLA]×1`
  （产出：`work\w101_step3_mix_census.py` → `EVIDENCE\step9_tables.txt` 末段 art/rules 类条目表）。
- (b) 「引擎实际用哪份」——本卡回答，结论在 §6。

---

## 2 · 引擎哈希算法（全案钥匙）[已证]

`MixFileClass::Find`（VA `0x5B4430`）对请求名做：`strupr`（`0x7DCFC4`）→ **CRC 类 `0x4A1DE0`** → 对每个已挂载 MIX 的平坦 12 字节索引二分（先装载者优先）。

`0x4A1DE0` 反汇编（`EVIDENCE\step5_disasm.txt`、`step6_hash.txt`）：
- CRC 表 `0x81F7B4` 前 8 双字 == zlib 标准表（`00000000 77073096 EE0E612C 990951BA …`，逐字节全等）；
- 数据按 **4 字节块**流式处理（每块 `not` → 4 次查表 → `not`，等价 zlib 连续计算）；
- **尾块（剩 1–3 字节）终结规则**（`0x4A1F40–0x4A1F61`）：`buf[L] = L`（把剩余字节数本身写进缓冲），再用 `buf[0]` 重复填满 4 字节，然后按普通块处理。

即 `hash(X)` = zlib-crc32 连续计算，但**最后一个不完整块补 `[b0..bL-1, L, b0, b0…]`**。python 复刻（`work\w101_step7_engine_hash.py::engine_hash`）对**五个零售观测 id 全中**：

| 引擎哈希名 | 值 | 零售观测命中（普查） |
|---|---|---|
| `ARTMD.INI` (9B) | `0x5B47D8D5` | `ra2md.mix:FBE0D09D/5B47D8D5`（336,535 B）|
| `RULESMD.INI` (11B) | `0x8218F9F4` | `expandmd01.mix:8218F9F4`（743,215 B）＋ `ra2md.mix:FBE0D09D/8218F9F4`（742,958 B）|
| `LOCALMD.MIX` (11B) | `0xFBE0D09D` | `ra2md.mix` 顶层（4,819,480 B）|
| `LOCAL.MIX` (9B) | `0xA8548FD9` | `ra2.mix` 顶层（34,793,784 B）|
| `ART.INI` (7B) | `0xF91B2C8B` | `ra2.mix:A8548FD9/F91B2C8B`（245,825 B）|

另有多重独立印证：`CACHEMD.MIX`→`0x68EEC99A`、`GENERMD.MIX`→`0xA9FED5B2`、`CONQMD.MIX`→`0xBA5EA181`、`NTRLMD.MIX`→`0xC93B27A0`、`LOADMD.MIX`→`0xDF966243`、`ISOGENMD.MIX`→`0xF5590C4A`、`TEMPERAT.MIX`→`0x51FC6863`（ra2md 内）等全部与 `ra2md.mix`/`ra2.mix` 顶层条目 id 命中（`EVIDENCE\step9_tables.txt`）。而 `0xAF902833`/`0x1F674573`（未填充 zlib crc32 值）在**全镜像五段字节中零命中**（`work\w101_step2_exe_scan.py` → `EVIDENCE\step2_imm_census.json`），在**全部 15,603 个 MIX 条目 id 中零命中**（`EVIDENCE\mix_census_entries.csv`）。

---

## 3 · 引擎怎么请求 art [已证]

字符串与代码引用（`work\w101_step2_exe_scan.py`、`step4_disasm.txt`）：
- `"ARTMD.INI"` @VA `0x826254`，`push` 于 **`0x52D034`**（主装载）与 **`0x679EF6`**（重载函数 `0x679EE0`，对同一全局 INIClass `0x887180` 重读，无失败检查）；
- 失败串 `"Failed to load ARTMD.INI!"` push 于 `0x52D05D` → `call 0x4068E0`（**单条 ret 打印桩**，1.001 无输出）→ 置 `al=0` 返回；
- 全镜像**不存在** `ART.INI`/`artmd.ini`（小写）/`ARTMD*.INI` 字面量 ⇒ art 只有一条显式名通道。
- rules 侧：`"RULEMD*.INI"` 通配（`FindFirstFileA`，纯文件系统，push @`0x52CD98`）→ 枚举件装载入列表；列表里若没有恰名 `RULESMD.INI` → 回退 `CCFileClass("RULESMD.INI")`（push @`0x52CF39`，MIX 感知）；**列表为空则直接 return 0，连 ARTMD 都不会去读**（`0x52D00F` 分支）。
- INI 块函数 `0x52CD70` 的唯一调用点 `0x52C95C`（Init 内）：失败 → `"Failed to initialize Rules!"`（同样是打印桩）→ **继续启动**（非致命）。
- `CCFileClass::Open`（`0x473C50`）：磁盘打开 → `MixFileClass::Find` → 磁盘 helper。净效果 = **散装优先、MIX 其次**。

---

## 4 · 嵌套 LOCALMD.MIX 怎么被引擎够到 [已证]

`MixFileClass::ctor`（`0x5B3C20`）自己经 `CCFileClass::Open` 打开 MIX 文件——即**按名字打开一个只存在于别的 MIX 内部的条目是合法通路**。装载器实证（`EVIDENCE\step8_mount_loose.txt`）：

```
0x5303CD  push 0x826644        ; "LOCALMD.MIX"
0x5303C8  push 0x886980        ; ← blowfish 密钥全局（加密索引用）
0x5303D4  call 0x5B3C20        ; MixFileClass::ctor
0x5303DB  mov [0x884E50], eax
0x5303F9  push 0x826638        ; "LOCAL.MIX"  → 0x530400 call ctor → [0x884E54]
```

本机磁盘上**没有** `localmd.mix`/`local.mix`（`ra2youli` 目录清单），于是 `CCFileClass("LOCALMD.MIX")` 走 `MixFileClass::Find(0xFBE0D09D)` → **在 `ra2md.mix` 的平坦索引里命中**（普查：`ra2md.mix` 顶层 25 条目含 `FBE0D09D`）→ 构造器读取其头 `00 00 03 00`（加密索引）→ 用 `0x886980` 密钥解密出 **187 条目**的索引 → 作为独立 MixFileClass 挂入优先级链。`ra2md.mix` 顶层其余命名子 MIX（`GENERMD/CONQMD/NTRLMD/DESERT/LOADMD/SNOWMD/ISOGENMD/UBN/LUNAR/CACHEMD`）同理。

## 5 · 全量普查（17 个顶层 MIX，15,603 条目，任意深度嵌套）

自写解析器（复用 mixlib 的 RSA/blowfish 原语）：TS 明文/加密索引 + 严格 TD 判据 + 内容嗅探 + 六套命名方案（**engine countpad** 为准）。产物：`EVIDENCE\mix_census_entries.csv`（15,603 行）、`step3_mix_census.txt`、`step9_tables.txt`。

art/rules 类条目全集（Foundation=/Image= 规模级命中，按 id+名字双重确认）：

| 引擎可见性 | 位置 | id | 名字（引擎哈希） | 大小 | 特征 |
|---|---|---|---|---|---|
| **YR art，唯一** | `ra2md.mix → FBE0D09D(LOCALMD.MIX)/5B47D8D5` | `5B47D8D5` | **ARTMD.INI** | 336,535 | Foundation=×580 |
| YR rules，**胜者** | `expandmd01.mix` 顶层 | `8218F9F4` | **RULESMD.INI** | 743,215 | Image=×358 |
| YR rules，被遮蔽 | `ra2md.mix → LOCALMD.MIX/` | `8218F9F4` | RULESMD.INI | 742,958 | 同上结构 |
| RA2 art（RA1 代名字，MD 引擎按名字请求的只有 ARTMD.INI，这份不被读取） | `ra2.mix → A8548FD9(LOCAL.MIX)/` | `F91B2C8B` | ART.INI | 245,825 | Foundation=×469 |
| RA2 rules（同上，不被读取） | `ra2.mix → LOCAL.MIX/` | `F025A96C` | RULES.INI | 541,915 | Image=×295 |

`LOCALMD.MIX` 其余已命名成员（本卡新解析）：`AIMD.INI`(138,538) `EVAMD.INI`(79,889) `SOUNDMD.INI`(99,292) `THEMEMD.INI` `MAPSELMD.INI` `UIMD.INI` `RMGMD.INI` `MISSIONMD.INI` `COOPCAMPMD.INI` `MPMODESMD.INI` `BATTLEMD.INI`(2,733) 剧场 INI（`TEMPERATMD/SNOWMD/URBANMD/DESERTMD/LUNARMD`）＋ MP 模式 Rules override 若干 + UI PCX/SHP/PAL + `VOXELS.VPL`。`LOCAL.MIX`（RA2 侧）同样成套（`AI.INI`/`EVA.INI`/`SOUND.INI`/`THEME.INI`/`BATTLE.INI`/`KEYBOARD.INI`/`GAME.FNT`…）。

**「MIX 里有没有 art 类条目」的答案：有，且只有上表前两份 YR art/rules 与两份 RA2 代文件；其余上千个 INI 全是地图/MP 地图。**

## 6 · 判定 (b)：引擎读哪份 —— [已证]

推理链（每一环都有产出命令，见 §7 复算命令汇总）：

1. 镜像同一性：`.text` raw SHA-256 == deep doc 基线 → 其 [实证] 地址适用。
2. 引擎按**名字字面量** `"ARTMD.INI"` 请求（`0x52D034`），id 运行时由 `0x4A1DE0` 计算；`hash("ARTMD.INI") = 0x5B47D8D5`（算法 §2，五零售 id 反向验证）。
3. `CCFileClass::Open`：本机散装无 `artmd.ini`（step8 目录普查：`(none)`）→ 走 `MixFileClass::Find(0x5B47D8D5)`。
4. `Find` 只搜**已挂载 MIX 的平坦索引**（FIFO）。按装载序：`langmd → language → expandmd98 → expandmd01 → ra2md(→挂载 LOCALMD.MIX) → ra2(→挂载 LOCAL.MIX) → …`（deep doc §1.5 + 本卡挂载点）。
5. 普查（15,603 条目、全深度）：`0x5B47D8D5` **全局唯一命中** `ra2md.mix:FBE0D09D/5B47D8D5`；更早挂载的 langmd/language/expandmd98/expandmd01 皆无此 id。
6. ⇒ 唯一命中 = `ra2md.mix → LOCALMD.MIX → ARTMD.INI`，336,535 B。
7. 字节级自检：本卡解析器重新抽取该条目，SHA-256 `E1F03783…BA31` 与 W97 提取文件**全等**（`step3_mix_census.txt` `MATCH: True`）。
8. ⇒ **引擎读的就是 W97 那份文件。无回退、无第二来源。**（若装载失败，唯一后果 = 打印桩 + return 0，Init 继续，但本机不会走到这一步，因为命中存在。）

**顺带裁决 rules**：`hash("RULESMD.INI")=0x8218F9F4` 有两份，先装载的 `expandmd01.mix` 份（743,215 B，即 W89 的 `rulesmd_exp01.ini`）按 FIFO 赢，`LOCALMD.MIX` 份（742,958 B）被遮蔽。W97 U4 的倾向由此升级为机制级 [已证]（Find 的早者胜分支见 `0x5B44FD` 链表回退）。

## 7 · 复算命令汇总（每张表/每个数字）

```
cd D:\Project\ra2-campaign-forge
C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe lead\next_re_20261112_r09\W101_artlib\work\w101_step0_probe.py       # 哈希/crc 变体/MIX 头
…\work\w101_step2_exe_scan.py        # 字符串/串 xref/立即数普查（0 命中证据）
…\work\w101_step4_disasm.py          # 0x52CD70 INI 块 / Find / ctor 反汇编
…\work\w101_step5_disasm2.py         # 0x4A1DE0 哈希主体 / 0x7DCFC4 / Open / 调用者
…\work\w101_step6_hash.py            # 哈希尾块 + CRC 表对照
…\work\w101_step7_engine_hash.py     # ★count-pad 哈希 + 五 id 全中
…\work\w101_step3_mix_census.py      # 15,603 条目全普查 + W97 sha 自检 MATCH:True
…\work\w101_step8_mount_loose.py     # LOCALMD/LOCAL 挂载点反汇编 + 散装 INI 普查
…\work\w101_step9_tables.py          # 报告用全部表格
python tools\verify_anchors.py       # 323/323（deep doc 既有门禁，镜像未变）
```

## 8 · 给 ra2forge 的可行动项（本卡顺带发现，非本卡任务）

`mixlib.crc_hash`（未填充 zlib crc32）只在 `len(name)%4==0` 时与引擎一致。**ra2forge 用 `write_mix` 写入的非 4 倍长度文件名（如 `ECH01.MAP`，9 字符）在游戏里查不到**——今日战役仍能加载纯靠散装 `ECH01.MAP` 兜底。修复：mixlib 写入与查询都改用 count-pad 哈希（`work\w101_step7_engine_hash.py::engine_hash`）。

## 9 · 表达纪律声明

- 本文每个数字均有 §7 命令可复算；[已证]/[静态推断]/[未证] 分级见各节标注。
- 查不到之处（theme.mix 等）的搜索范围声明在 `UNKNOWNS.md`。
- 只读纪律：`ra2youli\` 全程只读（MIX 以 `rb` 打开，零写入）；未启动游戏、未注入、未附加调试器；主台账未动。
