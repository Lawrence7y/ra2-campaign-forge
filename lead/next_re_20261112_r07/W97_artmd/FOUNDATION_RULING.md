# W97 · `artmd.ini` 裁决卡：`TESLA` 底座 = 1×1

- **卡**：`lead\next_re_20261112_r07\W97_artmd`　**时间**：2026-11-14 17:21（`Get-Date`）
- **性质**：离线裁决。**未启动游戏、未注入、未改任何二进制**。`ra2youli` 与别卡原件只读（复制到本卡后再改）。
- **要裁的矛盾**：W89 记 `TESLA=1×1`（称来自 artmd.ini）vs W95 按 `TESLA=3×2` 算并称"步长 3 后仍剩 14 格重叠"。

---

## 结论（先给答案）

| 问题 | 裁决 | 依据等级 |
|---|---|---|
| `TESLA` 底座 | **`1×1`** | `[本次实测]` + 独立几何复算交叉 |
| W89 的 `1×1` | **对** | `[本次实测]` |
| W95 的 `3×2` 前提 | **错** | `[本次实测]` + `[静态推断]` |
| W95 的"14 格重叠" | **其错误前提下的正确算术**（我可逐格复现 14） | `[本次实测]` |
| `§625-1` 的"NAPOWR 相邻重叠 10 格" | **对**，我独立复算**逐格吻合** | `[本次实测]` |
| 能否写"零重叠" | **不能**，但**理由要换**（不是 TESLA） | 见 ⑤ |

**一句话**：`artmd.ini` 拿到了 —— `[NATSLA] Foundation=1x1`（`TESLA` 在 rules 里 `Image=NATSLA`，artmd 里**根本没有 `[TESLA]` 节**）。W89 对、W95 错。而 `§625-1` 的"10 格"恰好**只在 3×2 下成立**（2×2 下是 0），所以那条数字反而是 `NAPOWR=3×2` 的独立佐证。

---

## ① `ra2forge/mixlib.py` 的真实 API —— 以及"为什么 `get('artmd.ini')` 必然是 `None`"

### 1.1 API 事实（`[静态读码]`，`mixlib.py` 行号）

| 成员 | 真实语义 | 行 |
|---|---|---|
| `MixFile(path)` | **只接受路径**（位置参数），`__init__` 里 `open(path,'rb')` 并解析索引 | 231-235 |
| `mf.entries` | `list[MixEntry(id, offset, size)]` | 224-230 |
| `mf.read_entry(entry)` | 取字节。**参数是 `MixEntry` 对象，不是文件名** | 292-294 |
| `mf.get(filename)` | 用 `crc_hash(name)` **和** `classic_hash(name)` 命中 `entry.id` 才返回字节，否则 `None` | 286-290 |
| `crc_hash(name)` | `zlib.crc32(name.upper())` | 205-207 |
| `classic_hash(name)` | TS 时代另一套 hash（本项目这批文件里未命中过） | 210-217 |
| `mf.names()` | **存根**：`return {id: f"_{id:08X}"}`。**不解析任何文件名** | 279-284 |
| `mf.all_entries()` | `list(self.entries)` | 296-297 |
| 嵌套 MIX | **没有 API**。`ra2md.mix` 的 entry 本身就是 MIX，必须自己 `MixFile(entry字节)` 递归 | — |
| XCC local mix database | **不支持**（`xcc_local_database()` 只用于**写**；且本机这批零售 mix 里**根本没有**该 entry） | 304-329 |

> Lead 看到"`.names()` 返回 int"是因为它返回的是 **`{id:int → "_XXXXXXXX":str}` 字典**，int 是**键**不是返回值。

### 1.2 所以 Lead 的失败不是"用法错"，而是"名字假设错"（`[本次实测]`）

三组硬证据：

1. **hash 方案确实是 `crc32(UPPER(name))`**。我从 `gamemd.exe` 里抽出引擎自己的文件名字符串，逐个算 crc32 去撞 archive 的 entry id，**命中 100+ 条**（`EVIDENCE/probe11`）：

   | 名字（引擎字符串） | crc32 | 命中位置 |
   |---|---|---|
   | `LOAD.MIX` | `0xBC80C10F` | `ra2.mix` (25,478,184 B) |
   | `ISOGENMD.MIX` | `0xF5590C4A` | `ra2md.mix` (6,637,126 B) |
   | `ISOTEMMD.MIX` | `0x51FC6863` | `ra2md.mix` (5,053,802 B) |
   | `TEMPERAT.MIX` | `0x5AA5B016` | `ra2.mix` (2,728,266 B) |
   | `BATTLEMD.INI` | `0x07E280DD` | `ra2md.mix` 嵌套 (2,733 B) |
   | `AIMD.INI` | `0x116F3F76` | `ra2md.mix` 嵌套 (138,538 B) |
   | `UIMD.INI` | `0xE99E00A7` | `ra2md.mix` 嵌套 (885 B) |
   | `MAPSELMD.INI` | `0x922B8CE7` | `ra2md.mix` 嵌套 (5,573 B) |

   ⇒ **`mixlib` 的 hash 实现是对的。**

2. **但引擎自己声明的 `ARTMD.INI` / `RULESMD.INI` 的 crc32 在这台机器上不存在**（`EVIDENCE/probe13`，扫了 **17 个顶层 `.mix` + 每个的一层嵌套**）：

   ```
   0xAF902833  ARTMD.INI    (引擎字符串)  -> NOT PRESENT anywhere
   0x1F674573  RULESMD.INI  (引擎字符串)  -> NOT PRESENT anywhere
   ```
   且 `ra2youli` 下**没有任何** loose 的 `artmd.ini/rulesmd.ini/art.ini/rules.ini/artmd98.ini`。

3. **那些 payload 确实在，只是名字不是 `artmd.ini`**。三个大 INI 的 xor 差异互不相同（`0x9D7FBC87` / `0xF4D7F0E6` / `0x5482B832`）⇒ 不是"同一函数换了种子"，而是**换了名字**（`EVIDENCE/probe14`）。

**⇒ 裁决**：`MixFile.get('artmd.ini')` 返回 `None` 是**正确行为**，不是 API 误用。W89 能拿出 743,215 B 的 `rulesmd_exp01.ini`，也只能是**按内容/按大小枚举**出来的 —— 我已证明它与 `expandmd01.mix:0x8218F9F4` **sha256 全等**（`3d341ef8…`），确实拿对了。

### 1.3 可用的取法（`[本次实测]`，脚本 `EVIDENCE/w97_mixget.py`）

```python
from ra2forge.mixlib import MixFile

mf = MixFile(r"...\ra2youli\ra2md.mix")     # 只给路径
for e in mf.entries:                        # 枚举，不靠名字
    blob = mf.read_entry(e)                 # 传 entry 对象
    if blob[0:2] == b"\x00\x00":            # 这是个嵌套 MIX
        ...                                 # 自己写盘再 MixFile() 递归
mf.close()
```
- 嵌套判定：TS/RA2 MIX 头 = `[u16 0][u16 flags∈{0,1,2,3}]`。`ra2md.mix` 的 25 个 entry **全是**嵌套 MIX。
- **识别靠内容**：art 库的特征是 `Foundation=`/`Cameo=`/`Height=` 极多而 `BuildCat=`/`Prerequisite=`/`Strength=`/`Armor=`/`Cost=` **全为 0**。
- 递归实现见 `EVIDENCE/w97_mixget.py`（自检输出＝恰好两行，见 §2.1）。

---

## ② 五个建筑的 `Foundation=` —— 原文 / 行号 / sha256

**提取链（`[本次实测]`，完整 sha256 见 `EVIDENCE/foundation_evidence.json`）**：

```
ra2youli\ra2md.mix                       204,527,696 B  sha256 69d886defad9114dd440a013b364c8c004e369b5221d1889957b49d00058559d
  └ entry 0x FBE0D09D (嵌套 MIX)           4,819,480 B  sha256 cd181596b2deaeacf7bba77e661ae4438d3f778efc0e38ae2b967c410bf3f931
      └ entry 0x5B47D8D5 = artmd.ini       336,535 B  sha256 e1f0378394313c04ebbd5073f47785ee3e46f1b3c62d65724e8f3c310ee7ba31
```

本卡留存副本：`EVIDENCE/cand_ra2md_0xFBE0D09D_0x5B47D8D5.ini`

**"这就是 artmd.ini" 的判据（`[本次实测]`，`probe15` 的 key 普查）**：
- 首行 `; ART.INI`（+ Tiberian Sun 的 artwork 说明段），19,605 行；
- art 专属键充裕：`Foundation=`×580、`Cameo=`×248、`Height=`×648、`Buildup=`×330、`Image=`×383；
- **rules 专属键全为 0**：`BuildCat=` `Prerequisite=` `Strength=` `Armor=` `Cost=` `Owner=` `TechLevel=` = 0。
- 旁证：`ra2.mix` 里对称位置有同构的 RA2 版 art 库（245,825 B，469×`Foundation=`），两者互为 `ra2.md` / `ra2` 一对。

### 关键结构性事实：`Foundation` 走 `Image=` 间接

> `§630-3-2` 与 W89 都按"建筑 id = art 节名"去查，**这一步对 `TESLA` 是错的**。
> `rulesmd.ini` 的 `[TESLA]` 节第 **12937** 行是 **`Image=NATSLA`**（节头在第 12934 行），因此它的 art 节是 **`[NATSLA]`**；`artmd.ini` 里**根本不存在 `[TESLA]` 节**（我 grep 了 `^\[.*TSLA.*\]`，只有 `[NATSLA]` 及其 `_A/_AD/_B/_BD` 动画节）。
> 同理 `[ATESLA]`（第 12142 行）是 **`Name=Allied Prism Cannon`**（12144）、**`Image=GAPRIS`**（12145）⇒ 它的 art 节是 **`[GAPRIS]`**（不是"磁暴"）。
>
> 上述行号针对本卡 `work/rulesmd_exp01.ini`（743,215 B，sha256 `3d341ef8…`，＝`expandmd01.mix:0x8218F9F4` 逐字节全等）。`ra2md.mix` 嵌套里那份同 id 的 742,958 B 副本行号会略有偏移，`[本次实测]` 未逐行对照（见 UNKNOWNS U4）。

### 五建筑原表

| 建筑 | art 节 | art 节来源 | `Foundation=` 原文 | 行号 | 字节偏移 | 判定 |
|---|---|---|---|---|---:|---|
| `NAPOWR` | `[NAPOWR]` | rules 无 `Image=` ⇒ 节名=建筑名 | `Foundation=3x2` | **3262** | 63964 | `[本次实测]` |
| **`TESLA`** | **`[NATSLA]`** | rules `Image=NATSLA`（12937 行） | **`Foundation=1x1`** | **4445** | 83574 | `[本次实测]` |
| `ATESLA` | `[GAPRIS]` | rules `Image=GAPRIS`（12145 行） | `Foundation=1x1` | **4551** | 85990 | `[本次实测]` |
| `NACNST` | `[NACNST]` | rules 无 `Image=` | `Foundation=4x4` | **1653** | 35114 | `[本次实测]` |
| `GAPOWR` | `[GAPOWR]` | rules 无 `Image=` | `Foundation=2x2` | **3210** | 62961 | `[本次实测]` |

> 上表"行号/字节偏移"指 **artmd.ini**（sha256 `e1f03783…`）。`Image=` 的行号指 `rulesmd.ini`（sha256 `3d341ef8…`）。
> `[本次实测]` 五座建筑的 rules 节内**都没有** `Foundation=`（`foundation_in_rules_section=false`，见 `foundation_evidence.json → rules_indirection`）。

> **没有"未设 ⇒ 引擎默认"的情形**：五个都在其上文的 art 节里显式给了 `Foundation=`。
> （`[已证-反向]`：`rulesmd.ini` 全文 `Foundation=` 出现 **0 次** ⇒ 在 YR 里这个键只走 art，不走 rules，这也印证了"必须去 artmd"。）

`TESLA` 的完整 art 节（`EVIDENCE/cand_ra2md_…ini` 第 4441-4460 行）：
```ini
[NATSLA]              ; line 4441
Cameo=TSLAICON
Image=NATSLA
Remapable=no
Foundation=1x1        ; line 4445   <<<
Height=5
Buildup=NATSLAMK
...
```

---

## ③ 几何交叉验证（用 `C6` 的真实坐标）

### 3.0 先纠一处：任务书给的坐标在产物里不存在

任务书说"12 座 `TESLA` 在 `rows 180/182`、`cols 154..169`（步长 3）"。**这不是本项目的产物**（`[本次实测]`）：

| 来源 | 12 座 TESLA 的实际位置 |
|---|---|
| `W88_envelope\out\inputs\C6\w88_design_C6.json` | 设计坐标 `(row,col)` = rows **61/62/63**，cols **42..58 步长 4**（3 行 × 4/5/3 座，砖砌错位） |
| 同目录 `RA2F_M1.MAP` `[Structures]` | 存的是 iso 坐标：`X=79..95`、`Y=62..64` |
| `w88_build.py:52-54` `TESLA_CELLS` | 同 design 坐标 |

我用 `ra2forge/maplib.py:68` 的投影 `cell(row,col) = (W + col − row, row + 1)`（`W=100`）复算，与 `.MAP` 里 `X/Y` **逐座吻合**（`EVIDENCE/probe07` §0）。所以 `rows 180/182, cols 154..169` 是**别的卡/口述里混进来的数字**，不是 W88 的几何。下面主表用**真坐标**，任务书那组也照算一遍作对照。

> 附带：`maplib.py` **完全没有** `Foundation` 概念（grep 无 `Foundation` 符号），占位必须自己算。投影本身是双射，所以我在 **iso 格**（`.MAP` 存的坐标系，引擎面对的空间）里数占格。

### 3.1 自检：哪个底座模型能重现 "步长 2 重叠 / 步长 3 不重叠"？

`NAPOWR` 的 `3×2` 是独立已知的（artmd:3262、且 6 座 reactors 一次排开）。用它当试金石：

| 模型 | 臂 | 占格 | 唯一格 | **重叠格** |
|---|---|---:|---:|---:|
| **3×2（真）** | step2 (col 46,48,…,56) | 36 | 26 | **10** |
| **3×2（真）** | step3 (col 46,49,…,61) | 36 | 36 | **0** |
| 2×2（**工具原来用的**） | step2 | 24 | 24 | **0** |
| 2×2 | step3 | 24 | 24 | **0** |

⇒ **3×2 精确重现 `§625-1` 的"相邻重叠 10 格"**；2×2 让两臂都是 0 ⇒ 工具的那个断言**必然为真**（④/⑤ 的工具缺陷由此坐实）。

### 3.2 `TESLA`：假设 A vs 假设 B

| 假设 | 空间 | 占格 | 唯一格 | **重叠格** |
|---|---|---:|---:|---:|
| **A：1×1（artmd:4445）** | iso | 12 | 12 | **0** |
| **A：1×1** | design | 12 | 12 | **0** |
| **B：3×2（W95）** | iso | 72 | 58 | **14** |
| **B：3×2** | design | 72 | 63 | 9 |

- 假设 A：1×1 不可能重叠（12 个锚点互不相同）⇒ **0**，与任务书预期一致。
- 假设 B：iso 空间 **14 格** —— **正是 W95 报的那个 14**。W95 的算术没问题。
- 任务书那组伪造坐标 `rows 180/182`：A → 0，B → **0**（步长 3、3 格宽刚好不撞）⇒ 与"仍剩 14 格"**自相矛盾**，进一步说明那组数字不可用。

### 3.3 底座锚点约定：`[未证]`，但结论不依赖它

我扫了 4 种锚点约定（footprint 从锚点向 ±x/±y 生长）：

| 假设 | `+x/+y` | `+x/−y` | `−x/+y` | `−x/−y` |
|---|---:|---:|---:|---:|
| A（1×1） | 8（NACNST×NAPOWR） | **0** | 8 | **0** |
| B（3×2） | 22（8 + **14 TESLA**） | **14（纯 TESLA）** | 22 | **14** |

- **`TESLA`-vs-`TESLA` 的计数与锚点约定无关**：A 恒 0、B 恒 14。
- 唯一随约定变的是 `NACNST×NAPOWR` 的 8 格交叉占格 —— 这条我只作**条件性**事实登记（见 ⑤），不做论据。
- W95 的"合计 24 → 14"（`AUDIT.md:134-137`）在 `+x/−y` 约定下**完全复现**（24 = 10 NAPOWR + 14 TESLA；14 = 0 + 14）⇒ 它用的就是这个约定。**我们与它唯一的分歧就是 `TESLA` 的底座。**

### 3.4 "能跑" 能不能否证 B？—— 不能，但要说得更准

`§630-3` 已记录"重叠本身不崩（零交战对照同样重叠却全绿）"。我补两条读数（`[本次实测]`，`EVIDENCE/probe08`）：

| 趟 | outcome | 绿 |
|---|---|---|
| `C6`（1200 Hunt，150 s 窗） | `VALID_WINDOW_target_reached` | `ok=true`，`A8ED50` 非零 94.05 % |
| `CTRL_C6`（同布局全 Guard） | `VALID_WINDOW_target_reached` | `ok=true`，`A8ED50` 恒 0 |

⇒ **A 与 B 都"可加载"**，"跑了 150 s 不崩"**不能**用来裁决底座尺寸。裁决靠 ②（原始文件）＋3.1（NAPOWR 自检）。

不过有一个**新的正面对撞**值得记：C6 的 12 座 TESLA 在真值下**根本不重叠**（0 格），所以 `AUDIT.md:144` 那句"**TESLA 重叠+被摧毁也不崩**"**证据基础不存在** —— 该条应撤回（见 ⑤）。

---

## ④ 裁决

**`TESLA` = `1×1`。**

依据强度分层：
1. `[本次实测]` **原始文件**：`artmd.ini`（sha256 `e1f03783…`）`[NATSLA] Foundation=1x1`，而 `TESLA` 的 `Image=NATSLA`。这是**直接读数**，不是推断。
2. `[本次实测]` **同一文件的三条自洽旁证**：`NAPOWR 3x2` / `NACNST 4x4` / `GAPOWR 2x2` 与 W89、与游戏内常识**全部一致**；且 `NAPOWR=3x2` 还能**独立**重现 `§625-1` 的"10 格"。
3. `[本次实测]` **几何**：1×1 ⇒ 0 格；3×2 ⇒ 14 格。W95 的 14 是"3×2 前提下的正确算术"。

**W95 错在哪**：它用 3×2 给全部 22 座建筑做普查，把 `TESLA` 也套了 3×2。这个前提没有出处（`§630-3-3` 自己就写了"`Foundation` 全项目只有 ≈3×2（带波浪号、无出处）"）。**它其实连 `NAPOWR` 的 3×2 都没证过** —— 本卡把两者都证了。

**什么能推翻本裁决**（保留质疑空间）：
- 若引擎在 art 节之外还有第二处 `Foundation` 覆盖（本项目未见），或 `Image=` 间接在 `Foundation` 这个键上不生效。→ 现状 `[未证]`，但 `rulesmd.ini` 零 `Foundation=` 这点使它极不可能（若 rules 也生效，至少会有一处）。
- 若这台机器的 `artmd.ini` **不是**我们取到的这份（见 `UNKNOWNS.md` U1：引擎按 `0xAF902833` 找不到它）。这会影响"引擎实际读的是哪份 art"，**但不影响"这份官方 art 库里 TESLA 是 1×1"这个事实本身**。

---

## ⑤ 对 `§625` / `§630` 措辞的具体修改建议（逐句）

> 下面"改前"引自 `lead\GOAL_THREE_TARGETS_20261018.md`（行号为该文件行号）。

### ⑤-1 `§625-1` 标题（行 10354）

- **改前**：`- **§625-1 [已证] 崩溃边界 = `NAPOWR` 底座重叠（col 步长 2，相邻重叠 10 格）**`
- **改后**：`- **§625-1 [本样本量下成立] 崩溃边界候选 = `NAPOWR` 底座自重叠（col 步长 2，相邻重叠 10 格；底座 3×2 已由 artmd.ini:3262 坐实，10 格已独立复算）**`

理由：① "10 格"现在**有工具与出处**，可以直接写"已复算"；② 按 `§630-4` 已降级，"定谳"字样不该留在标题里。

### ⑤-2 `§625-1` 表内 C3 行（行 10358）

- **改前**：`| **C3** | 仅步长 2 → **3**（重叠 → 0） | **0/3** |`
- **改后**：`| **C3** | 仅步长 2 → **3**（`NAPOWR` **自**重叠 10 → 0；**非"零重叠"**，见 §630-3-2 修订） | **0/3** |`

### ⑤-3 `§625-1` 表内 C6 行（行 10360）

- **改前**：`| **C6** | 去重叠 + **全剂量 1200 Hunt** | **0/1，150.1 s 绿** |`
- **改后**：`| **C6** | 去掉 `NAPOWR` 那 10 格自重叠 + **全剂量 1200 Hunt** | **0/1，150.1 s 绿** |`

### ⑤-4 `§625-1` 推论句（行 10363）

- **改前**：`- ⇒ **去重叠把 1/3 失效率降到 0/3**；…`
- **改后**：`- ⇒ **去掉 `NAPOWR` 那 10 格自重叠后，1/3 失效率在本样本量下降为 0/3**；…`

### ⑤-5 `§630-3-2` —— **最重要的一处**（行 10511）

- **改前**：
  > **「去掉重叠」字面为假 —— 但 `[未证]`**：W95 称步长 3 仍剩 **TESLA 14 格重叠**，而 **W89 曾记 TESLA = `1×1`**，两卡直接矛盾；`Foundation` 在 `artmd.ini`，本会话未能提取（`mixlib.get('artmd.ini'/'rulesmd.ini')` 均 `None`，与 W89 曾抽出 743 KB `rulesmd.ini` 矛盾 ⇒ API 用法有误）。⇒ **在裁决前，一律写「去掉了 NAPOWR 那 10 格重叠」，禁止写"零重叠"。**

- **改后**：
  > **「去掉重叠」字面为假 —— `[已证]`，但原因不是 TESLA**：`artmd.ini` 已提取（W97；`ra2md.mix→0xFBE0D09D→0x5B47D8D5`，sha256 `e1f03783…`）。`TESLA` 的 art 节是 **`[NATSLA]`**（rules `Image=NATSLA`），其 `Foundation=**1x1**`（artmd:4445）⇒ **W89 正确；W95 的 `3×2` 前提错误**。W95 的"14 格"是其 3×2 前提下的**正确算术**（W97 可复现），但在 1×1 下 **`TESLA` 自重叠 = 0 格**。
  > ⇒ 仍然**禁止写"零重叠"**，但理由换成：① 设计层面步长 3 让基地右扩 5 格（W95 (3) 已证）；② `[未证-条件性]` 在 artmd 真值下 base 内可能仍有 `NACNST×NAPOWR` 交叉占格（W97 实测 8 格 @`+x/+y` 锚点，其他锚点约定为 0；锚点约定 `[未证]`）。⇒ 措辞统一为「**去掉了 `NAPOWR` 的 10 格自重叠**」。
  > ⇒ 附带：`mixlib.get()` 返回 `None` **不是 API 用法错**（W97 已证：引擎自带的 `ARTMD.INI`/`RULESMD.INI` 的 crc32 在本机 17 个 mix + 一层嵌套里**都不存在**，payload 存在别的名字下）。

### ⑤-6 `§630-3-2` 第 1 个附带事实（行 10512）

- **改前**：
  > - 顺带两个新事实：**重叠本身不崩**（零交战对照同样重叠却全绿）⇒ 机制是「**重叠 且 被摧毁**」；**TESLA 重叠+被摧毁也不崩** ⇒ 加强 NAPOWR 特异性，但机制仍缺"为什么偏偏是 NAPOWR"这一步。
- **改后**：
  > - 顺带两个新事实：**重叠本身不崩**（零交战对照同样含 `NAPOWR` 10 格自重叠，150 s 全绿）⇒ 机制是「**重叠 且** 该格有建筑被摧毁」；
  > - **~~TESLA 重叠+被摧毁也不崩~~ 撤回**（W97）：`TESLA` = **1×1**，C6 里 12 座 TESLA **根本不重叠**（0 格），因此该实验**从未**检验过"TESLA 重叠"。⇒ NAPOWR 特异性**没有**被这条加强；机制仍缺"为什么偏偏是 NAPOWR"这一步。

### ⑤-7 `§630-3-3`（行 10513，工具缺陷）

- **改前（末尾）**：`…且 `Foundation` 全项目只有"**≈**3×2"（带波浪号、无出处）。**整改项。**`
- **改后**：`…且 `Foundation` 全项目只有"**≈**3×2"（带波浪号、无出处）。**整改项 —— W97 已完成**（`W97_artmd/EVIDENCE/w88_build_patched.py`）：底座收敛到单一常量 `FOUNDATION`（每个值带 artmd.ini 行号 + sha256 出处），断言改为**双向**（step2 必须**有**重叠、step3 必须**无**重叠），并加 `selfcheck_overlap_model()` —— 若模型对两臂都报 0 就直接抛 `AssertionError`（正是本条描述的失效模式）。修补后：**step2 = 10 格重叠（首个碰撞 `(56,48)`）、step3 = 0 格**，与 `§625-1` 的手算一致。`Foundation` 不再是"≈3×2"：`NAPOWR=3x2` 有出处。`

### ⑤-8 `W95 AUDIT.md:372` 的整改建议（风险 #2）可以关闭

- **改前（W95 建议）**：`…若要坐实机制：把 12 座 TESLA 移成零重叠（同几何）再跑全剂量，看是否仍绿。**1–2 趟**`
- **改后**：`…**已作废**（W97）：`TESLA`=1×1，C6 的 12 座 TESLA 本来就是零重叠（0 格），无需再跑。原前提"TESLA 14 格仍在"不成立。`

### ⑤-9 `W95 UNKNOWNS.md:25` 的悬案可以关闭

- **改前**：`- ⇒ `NAPOWR` 是否真是 3 格宽：**`[未证]`**。整条 §625 机制建立在这个数值上。`
- **改后**：`- ⇒ `NAPOWR` 是 3 格宽：**`[已证]`**（W97：`artmd.ini [NAPOWR] Foundation=3x2`，行 3262，sha256 `e1f03783…`；且 3×2 模型精确重现 `§625-1` 的"10 格"，2×2 重现不出）。`

### ⑤-10 `LEAD_VERIFY_W95.md:59` ③

- **改前**：`…③ §625 的「`Crewed=no` 无效」**不成立（零信息）**、「去掉重叠」**字面为假（TESLA 之争 `[未证]`）**、重叠断言**是空检查**；…`
- **改后**：`…③ §625 的「`Crewed=no` 无效」**不成立（零信息）**、「去掉重叠」**字面为假（但原因不是 TESLA —— W97 已证 `TESLA=1×1`，假的原因是 NAPOWR 步长 3 使基地右扩 + 可能残留 NACNST×NAPOWR 交叉占格）**、重叠断言**是空检查（W97 已修补）**；…`

### ⑤-11 建议新增台账条目（`§631`）—— 可直接粘贴

```markdown
## §631 · artmd.ini 取出与 TESLA 底座裁决：1×1（W89 对，W95 的 3×2 前提错）（2026-11-14）

- **性质**：W97（离线裁决卡）＋ Lead 复核。只读，未启动游戏。
- **§631-1 [已证·取文件路径] `artmd.ini` 已取出**：提取链是
  `ra2youli\ra2md.mix`(sha256 69d886de…) → entry `0xFBE0D09D`(4,819,480 B, 嵌套 MIX,
  sha256 cd181596…) → entry `0x5B47D8D5` = **artmd.ini**(336,535 B,
  sha256 e1f0378394313c04ebbd5073f47785ee3e46f1b3c62d65724e8f3c310ee7ba31)。
  判据：首行 `; ART.INI`；art 键 `Foundation=`×580/`Cameo=`×248/`Height=`×648；
  rules 键 `BuildCat=`/`Prerequisite=`/`Strength=`/`Armor=`/`Cost=` 全为 0。
- **§631-2 [已证·五建筑 Foundation]**（artmd.ini，同一 sha256）：
  | 建筑 | art 节 | Foundation | 行 |
  |---|---|---|---:|
  | NAPOWR | [NAPOWR] | 3x2 | 3262 |
  | TESLA | [NATSLA]（rules `Image=NATSLA`） | **1x1** | 4445 |
  | ATESLA | [GAPRIS]（`[ATESLA]`=`Allied Prism Cannon`, `Image=GAPRIS`） | 1x1 | 4551 |
  | NACNST | [NACNST] | 4x4 | 1653 |
  | GAPOWR | [GAPOWR] | 2x2 | 3210 |
  反证：`rulesmd.ini` 全文 `Foundation=` = **0 次** ⇒ 该键在 YR 只走 art。
- **§631-3 [已证·裁决] `TESLA` = 1×1**。W89 对；**W95 的 `TESLA=3×2` 前提错**，
  其"14 格"是错误前提下的正确算术（W97 复现：iso 空间 3×2 → 14、1×1 → 0）。
  `mixlib` 不是用错：引擎自带的 `ARTMD.INI`(0xAF902833)/`RULESMD.INI`(0x1F674573)
  的 crc32 在本机 17 个 mix + 一层嵌套里**都不存在**，payload 在别的名字下。
- **§631-4 [已证·工具整改完成]** `w88_build.py` 的 2×2 底座 → 单常量 `FOUNDATION`
  （带 artmd 行号+sha256），断言双向 + `selfcheck_overlap_model()` 防"两臂皆 0"的空检查。
  修补后 step2=10 格、step3=0 格，与 `§625-1` 一致。
- **§631-5 [撤回]** `§630-3-2` 的"TESLA 重叠+被摧毁也不崩"**撤回**：TESLA 本就 0 重叠。
  连带 `W95 AUDIT.md:372` 建议的"把 12 座 TESLA 移成零重叠再跑 1–2 趟"**作废**（省 1–2 趟真机）。
- **§631-6 [边界]** ① 底座锚点约定 `[未证]`（footprint 从锚点向哪侧生长）；TESLA 自重叠
  与符号无关，但 `NACNST×NAPOWR` 交叉占格在 `+x/+y` 下 8 格、`+x/−y` 下 0 格。
  ② 引擎按 `0xAF902833` 取不到 `ARTMD.INI`（本机），它实际读哪份 art `[未证]`（见 W97 UNKNOWNS U1）。
  ③ 单图单布局单镜像。
```

---

## ⑥ 工具修补前后对照（`§630-3` 第 3 条）

文件：`EVIDENCE/w88_build_patched.py`（原件复制自
`W88_envelope\work\tools\w88_build.py`，sha256 `A76D6A06ECAA130DE4AFD92D7F3E268800F1847F62AE6A8623F1383B4866C50D`；
**原件未改动**）。旁存 `w88_build.py.orig` 供对照。验证脚本 `EVIDENCE/probe10_fixcheck.py`。

**两臂重叠格对照表**（`probe10` §B，iso 空间）：

| 臂 | 修补前（2×2，硬编码） | 修补后（3×2，`FOUNDATION["NAPOWR"]`） |
|---|---|---|
| | 占格 / 唯一 / **重叠** / 返回值 | 占格 / 唯一 / **重叠** / 返回值 |
| `step2` (46,48,…,56) | 24 / 24 / **0** / `None` | 36 / 26 / **10** / `(56, 48)` |
| `step3` (46,49,…,61) | 24 / 24 / **0** / `None` | 36 / 36 / **0** / `None` |

⇒ 修补前**两臂都是 `None`**，所以 `assert overlap_cells(step3) is None` **恒真**（空检查）；
修补后两臂**被区分开**，且 `10` 与 `§625-1` 的手算逐格吻合。

**改动清单**（最小改动，未动其它逻辑）：
1. 新增 `FOUNDATION` 表 + `FOUNDATION_SOURCE` + `ANCHOR_SX/SY` + `ANCHOR_CONVENTION`；
   每个值带 artmd.ini 行号与 sha256，锚点约定显式标 `[未证]`。
   `TESLA_3X2_COUNTERFACTUAL` 单列并标 `[未证-且实测反证]`，只为让反事实对照也从同一张表来。
2. `overlap_cells(cells, foundation, space)`：底座从参数来，**不再硬编码 2×2**；
   `space="iso"` 走 `maplib` 的 `to_cell` 投影（引擎面对的空间），`"design"` 仅作敏感性旁证。
3. `selfcheck_overlap_model()`：两臂皆 0 / step2 不重叠 / step3 仍重叠 —— 三种情形分别抛错。
   （内核即"禁止空检查"这条纪律的代码化；`probe10 §C` 验证它会把 2×2 当场判死。）
4. `step_design()` 与 `verify_pkg()` 的两个断言点改为**双向**且共用同一常量。
5. `verify_pkg()` 顺带**记录**（不断言）`tesla_overlap`：真值下 0，3×2 反事实下 14。

---

## ⑦ 证据清单

| 文件 | 内容 |
|---|---|
| `EVIDENCE/foundation_evidence.json` | 机器可读：完整 sha256 链、五行 Foundation 的行号+字节偏移、art/rules key 普查 |
| `EVIDENCE/cand_ra2md_0xFBE0D09D_0x5B47D8D5.ini` | **取到的 artmd.ini**（336,535 B） |
| `EVIDENCE/cand_ra2_0xA8548FD9_0xF91B2C8B.ini` | 同构的 RA2 版 art 库（245,825 B），作对照 |
| `EVIDENCE/w97_mixget.py` | 可复用取文件器（枚举+嵌套递归+按内容识别），自检输出恰两行 |
| `EVIDENCE/probe01…16_*.py` / `*_stdout.txt` | 每一步的脚本与原始 stdout |
| `EVIDENCE/probe16_stdout.txt` | `Image=` 间接的机器证据（哪座建筑有/没有 `Image=`、rules 节内 `Foundation=` 是否存在） |
| `EVIDENCE/w88_build_patched.py` / `.orig` | 工具修补件 / 原件副本 |
| `EVIDENCE/probe10_stdout.txt` | 修补前后对照表 + 守卫自测 |
| `work/rulesmd_exp01.ini` | 743,215 B 规则文件副本（用于证明 rules 里无 `Foundation=`） |
