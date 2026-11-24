# LEAD_W33_VERIFY · 「关卡推进失败」根因定谳（Lead 独立复核 + 突破）

> 复核人：Lead（本会话）｜ 日期：2026-11-13 17:50
> W33 卡：**Gemini 4 Hydrogen `high`**，`lead\next_re_20261112_r02\W33_nextscenario_dataflow\NEXTSCENARIO_FLOW.md`（19,779 B）+ `DISAGREE.md` + `UNKNOWNS.md` + 20 份 EVIDENCE

---

## 0. 一句话结论

**C 线阻塞②（「無法啟始選取地圖！」）的真正成因是 `MAPSELMD.INI` 未登记我方地图，不是 `NextScenario` 写法、也不是 MIX/散装寻址。**

---

## 1. Lead 独立验证的前提（全部自己动手，未采信 W33 摘要）

### 1.1 我方地图的关键字段（本次实测）

`ra2forge` 产物 `W27_campaign_live\pkg\W27 Live Campaign\ECH01.MAP`（4,671 B）`[Basic]`：

```
Name=W27 A1
NextScenario=ECH02.MAP
AltNextScenario=
NewINIFormat=4
CarryOverCap=0
EndOfGame=no
SkipMapSelect=no
Official=no
```

### 1.2 官方 14 张 MD 图（本次实测，逐字节提取）

```
file             SkipMapSelect  EndOfGame
ALL01UMD.MAP     no             no
ALL02UMD.MAP     no             no
ALL03UMD.MAP     no             no
ALL04DMD.MAP     no             no
ALL05UMD.MAP     no             no
ALL06UMD.MAP     no             no
ALL07SMD.MAP     no             yes
SOV01UMD.MAP     no             no
SOV02SMD.MAP     no             no
SOV03UMD.MAP     no             no
SOV04DMD.MAP     no             no
SOV05UMD.MAP     no             no
SOV06LMD.MAP     no             no
SOV07TMD.MAP     no             yes      ← 【更正】原误写为 no
```

> **更正（19:40，据 W43 审计 MAJOR-1 复查）**：上表 `SOV07TMD.MAP` 的 `EndOfGame` 原被我写成 `no`，**实为 `yes`**（我重新逐字节提取确认：`EndOfGame=yes`、`SkipMapSelect=no`、`NextScenario=GDI2A.map`）。
> 影响：苏军战役的**终局关是 `SOV07TMD`**，与盟军 `ALL07SMD` 对称。主结论（官方 14 图 `SkipMapSelect` 全为 `no`）**不受影响**。
> 教训：这列的错来自我早前那个一次性提取脚本，属"我自己的工具给出的错值被我当实测引用"——与 W43 审出的同类问题一致。

⇒ **官方图与我们地图的 `SkipMapSelect` 都是 `no`**，所以差异不在这个标志上，而在别处。

### 1.3 `MAPSELMD.INI` 的真实内容（本次实测，从 `ra2bench\ra2md.mix` 取出，5,573 B）

```
[GDI]            [Nod]
1=ALL01          1=Sov01
2=ALL02          2=Sov02
…                …
7=ALL07          7=Sov07

[ALL01] Scenario=ALL01umd.MAP   2=ALL02
[ALL02] Scenario=ALL02umd.MAP   3=ALL03
[ALL03] Scenario=ALL03umd.MAP   4=ALL04
[ALL04] Scenario=ALL04dmd.MAP   5=ALL05
[ALL05] Scenario=ALL05umd.MAP   6=ALL06
[ALL06] Scenario=ALL06umd.MAP   7=ALL07
[ALL07] Scenario=ALL07smd.MAP   ;Scenario=
[Sov01] Scenario=Sov01umd.MAP   2=Sov02
…（同上结构）
[Sov07] Scenario=sov07tmd.MAP
[ALL00] Scenario=  / 1=ALL01
[GDISFX] [NODSFX] [Anims] …（UI 相关，与推进无关）
```

文件头自述：**"This is a scenario progression control file."**（作者 Denzil E. Long, Jr.，1998）

⇒ **官方 14 张图逐一登记在此表中；我方 `ECH01.MAP` 不在表内。这是唯一的实质差异。**

---

## 2. 根因链（W33 逆向，Lead 已按上述前提核对自洽）

结算点 `GUI:Continue` → `0x0055D14A` → `0x00685670` → 读 `[Scen+0x34B0]`(`SkipMapSelect`)：

| 分支 | 行为 | 结果 |
|---|---|---|
| `SkipMapSelect=no`（官方与我方都是） | `0x00685A40 je 0x685a63` → `0x005ADD10` → `0x005AE100` → `0x005AE220` 加载 `MAPSELMD.INI`，用**当前地图名** `[Scen+0x125C]` 经 `0x005CF760` 反查阶段 | 我方 `ECH01.MAP` 查不到 → `"MapSelect: Invalid stage!\n"` → CSF 标签 `MSG:UnableMapSelect` |
| `SkipMapSelect=yes` | `0x005ADF20` 加载 `MAPSELMD.INI`，取当前阶段 `[Scen+0x35A0]`，遍历候选子项（`0x005CF6B0`）用 `Scenario=` 与 `NextScenario` **转小写后**比较（`0x7B5B30`→`0x7CAFF4` 对 `A..Z` 加 `0x20`；原写「大写」有误，W34/W43 均已指出） | 同样需要表内登记，未命中同样弹窗 |

`[签发]` **两条路径都要求 `MAPSELMD.INI` 认识我方地图** ⇒
- 仅改 `NextScenario` 写法 ✗ 无效（W28 已否证形式问题）
- 仅把 `ECH02.MAP` 打进 MIX ✗ 无效（寻址不是问题，`Get_File` 本就磁盘优先）
- 仅设 `SkipMapSelect=yes` ✗ 不足（仍需表内阶段匹配）

`[本次实测]` 这条也**解释了 W27 的 D2/D3 非对称**：`Scenario=` 直接指向能进（`Start_Scenario` 走 `CCFileClass`，不查表）；而 `Continue` 推进必须先过表校验——与观测完全一致。

`[转引]` 顺带否证：`BATTLEMD.INI [Battles]` 序号**不参与**通关后的下一关决策（W33 对 `0x00A83CFC`/`0x00A83D08` 全量 xref 核查，用途仅限菜单填充/首关取名/阵营与电影查表/`EndOfGame` 判胜）。

---

## 3. 由此得到的修法（已派 W34 实现）

**在包里附带一份「完整的 `MAPSELMD.INI`」= 官方全部阶段 + 我方追加阶段**，安装时散装投放。

依据：
- `[签发]` 散装文件优先于 MIX 内同名条目（W29 字节级自证：`Get_File` 磁盘命中即跳过 MIX 查找）⇒ 散装投放可生效
- `[本次实测]` `MAPSELMD.INI` 现存于 `ra2md.mix` 内，故必须**克隆后再追加**，否则官方 14 关全部失效
- `[静态推断·强]` 这与 W29 对 CSF 的警告同构：**「完整合法文件」是硬前提**，最小文件会打断官方战役

**两个必须先解决的工程坑**（已写进 W34 任务）：
1. `mixlib.MixFile("ra2md.mix").get("MAPSELMD.INI")` 返回 `None`，尽管 `crc32=0x922B8CE7`；W33 日志显示条目**存储 id 是 `0xFBE0D09D`** ⇒ 不能靠 `get()`，要自己解码容器条目表；Lead 已实测「裸字节搜 `0x922B8CE7` LE」也搜不到（条目表加密/异或）。
2. 阵营段与阶段段的 `N=名字` 语义尚未完全定谳（阵营段键是阶段序号？阶段段里的 `N=` 是"下一阶段"？`SkipMapSelect=yes` 路径要求的"候选子项"具体是哪几个键？）——W34 需从 `0x005CF760`/`0x005CF810`/`0x005CF6B0`/`0x005AE220` 反推并标级。

### 3.1 Lead 已把 MAPSELMD.INI 的物理位置钉死（供 W34 直接使用）

`[本次实测]` 我不靠任何 `get()`，用**文本搜索**在 `ra2bench\ra2md.mix` 原始字节里先定位到内容线索：

```
b"scenario progression control file"  -> 文件偏移 0x71D0DE   （注意：这是文件内第 12 行左右，不是起点）
b"[GDISFX]"                           -> 0x71D2D3
b"Sov01umd.MAP"                       -> 0x71E170
b"MAPSELMD"（作为文件名字符串）        -> 命中 0（MIX 不存明文名，符合预期）
```

`[本次实测]` **真实起点用哈希反查钉死**：扫 `0x71D0DE` 附近窗口，找 SHA-256 命中值 ⇒

```
起点 = 文件偏移 0x71D050（十进制 7,458,896）
长度 = 5,573 B
SHA-256 = 074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52
首 60 字节 = b';***********************************************************'
末 60 字节 = b'2A.SHP,TG02A.SHP\r\nTargets=1,190,100\r\nClickMap=NODCLK01.PCX\r\n'
行尾 = CRLF
```

`[本次实测]` 我最初把「`scenario progression control file`」那一行当成了文件头，导致连续切片偏移 142 字节、算出错误的 SHA-256（`5db8b5ad…`）。**以 0x71D050 为准。**
`[本次实测]` 该 SHA-256 与 **W34 声称的提取结果逐字节一致** ⇒ W34 的提取产物是对的。

### 3.1b 【已撤回】我此前对 `0xFBE0D09D` 的「证伪」是错的

> 本节原文称「W34 对 `0xFBE0D09D` 的解释不成立（结果对、理由错）」。**该判断已撤回** —— 被打脸的是我。

`[本次实测]` 用项目内真实实现 `mixlib.ts_crc_hash()`（Westwood 规则：先追加「长度余数」字节、再重复「末组首字节」，**不是补 `\x00`**）复算：

```
ts_crc_hash("LOCALMD.MIX")  = 0xFBE0D09D   ← 与 W34 完全一致
ts_crc_hash("MAPSELMD.INI") = 0x922B8CE7   ← 已知值，一致
ts_crc_hash("RA2MD.CSF")    = 0xBD835079   ← langmd.mix 实测 entry id，一致
```

⇒ `[签发]` **`0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")` 成立，W34 原本就对。**
⇒ 我先前 15 个变体（`pad0->4=0x62E98127` 等）**全部用错填充规则**，所以必然全不匹配。这不是 W34 的错，是我不懂这套哈希。
⇒ 我下的「不得当事实引用」禁令**作废**；正确写法就是该等式。
详见 `REVIEW\LEAD_VERIFY_W34.md` §3（完整复算与方法论反思）。

### 3.2 W31 与 W33 不冲突（我判过一次假冲突）

`[本次实测]` W31 的 `s09` 扫了全部 33 个 MIX 的**顶层**条目找 `0x922B8CE7`，`ra2md.mix`（25 条）**零命中**；它同时确认两处游戏目录**都没有散装** `MAPSELMD.INI`。
`[本次实测]` 我用 `mixlib` 列 `ra2md.mix` 的 25 条顶层 id：`0x922B8CE7` 确实**不在顶层**，而 `0xFBE0D09D` **在**。
⇒ 两者都对，差别只是 **W31 没做递归、W33 做了递归**。**不构成冲突**，但 W31 的「零命中」不可被引用成「容器里没有这个文件」。

`[本次实测]` 附带一个坑：`mixlib.MixFile` 解析**嵌套/加密头**的容器时给出 `entries=0`（我实测内层解出 0 条），所以「用 mixlib 列条目为空」**不能**推出「容器是空的」。定位内容应优先用文本搜索这类与容器格式无关的手段。

---

## 4. 我**不**签发 / 仍缺的部分

- `[待运行验证]` **整条链尚未真机验证**。本卡是静态逆向 + Lead 前提复核，**没有任何一次「加了 MAPSELMD.INI 后真的推进成功」的观测**。不得写「已修复」。
- `[待运行验证]` 我方地图该注册在哪个阵营段（`[GDI]` / `[Nod]`，YR 可能还有第三阵营）——取决于战役 side 语义，未定谳。
- `[待运行验证]` 行尾（官方 CRLF vs ra2forge LF）对 `MAPSELMD.INI` 解析的影响未测。
- `[转引]` W33 的部分指令级结论我按前提核对了自洽性，但**未逐条复算其 rel32 与反汇编**（与 W29 那次不同，那次我全部手算过）。

---

## 5. 与其它卡的交叉

- **W28**：`NextScenario` 形式相同 ⇒ 不是成因。**与 W33 不冲突**，两者互补（形式对但表里没登记）。
- **W29**：散装优先 + CSF 必须完整合法。**支持本修法**。
- **W31**（同期在跑）：从 `MSG:UnableMapSelect` 反推触发分支。**应能独立印证 §2**，待其报告出来后对撞。
- **W32**（同期在跑）：菜单徽章生成条件，属另一个正交阻塞（Q1）。

---

## 6. 复现入口

- W33 报告：`W33_nextscenario_dataflow\NEXTSCENARIO_FLOW.md`
- `MAPSELMD.INI` 原文：`W33_nextscenario_dataflow\EVIDENCE\step10_close_gaps.stdout.txt` 第 10–533 行
- Lead 的 CSF 标签真值：`REVIEW\LEAD_FACT_map_error_label.md`（`MSG:UnableMapSelect` = 「無法啟始選取地圖！」）
- 我方地图 `[Basic]` 提取脚本与官方 14 图对照：本文件 §1 的命令可直接重跑
