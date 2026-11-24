# W97 · UNKNOWNS

分級：`[本次实测]` / `[静态读码]` / `[静态推断]` / `[未证]`。
"没找到"一律写清搜索范围。

---

## U1 `[未证]` 引擎实际读的是哪份 art 库 —— 它按 `ARTMD.INI` 查的那个 id 在本机不存在

**已知（`[本次实测]`，`probe12` + `probe13`）**：
- `gamemd.exe` 里存在字符串 `'ARTMD.INI'`（crc32 `0xAF902833`）、`'Failed to load ARTMD.INI!'`、`'RULESMD.INI'`（crc32 `0x1F674573`）⇒ 引擎是**按这两个名字**去加载的。
- 但 `0xAF902833` 与 `0x1F674573` 在下列范围内**都不存在**：
  - `ra2youli\*.mix` 全部 **17 个**顶层 mix 的 entry id；
  - 上述每个 mix 的**一层嵌套**（把每个 ≥4KB 且头为 `00 00 xx 00` 的 entry 当 MIX 再解析）。
  - 例外：`theme.mix`(76,862,662 B) 与 `themedmd.mix`(46,859,102 B) **无法解析** —— 首字为 16 / 10 而非 0，是 **C&C（TD/RA1）格式**，`mixlib` 明确不支持（`mixlib.py:251` "C&C format unsupported"）。二者是主题音频，与 art 无关，但**严格说这两个文件未被检查**。
- 且 `ra2youli` 下**无任何** loose `artmd.ini / rulesmd.ini / art.ini / rules.ini / artmd98.ini`。

**所以**：`[静态推断]` 在这台机器上，引擎按名字取 `ARTMD.INI` 应该失败。它实际用哪份 art（是否回退到硬编码默认、或该 exe 被改过 —— `gamemd.exe` 时间戳 2026-09-25，本项目本身就在改这个二进制）**未知**。

**为什么这条不影响裁决**：我们取到的 336,535 B 文件是**官方 art 数据库本体**（内容判据见 `FOUNDATION_RULING.md §2`），其 `NAPOWR/3x2` 还能被 `§625-1` 的"10 格"**独立**证实。也就是说"这份 art 库的 TESLA 是 1×1"是文件事实，不依赖引擎是否读它。

**要关掉它需要什么**：① 反查 `gamemd.exe` 里 `0xAF902833` 常量的引用点与加载函数，看是否走 MIX 之外的通路（本项目 `re_atlas` 线可做）；② 或真机上用文件访问监视（ProcMon）看开局读了哪个路径 —— 属真机卡，本卡禁止。

---

## U2 `[未证]` 底座锚点约定（footprint 从锚点的哪一侧生长）

`Foundation=WxH` 只给了尺寸，没给"锚点在哪一角"。我按 4 种角约定都算了一遍（`probe09`）：

| 假设 | `+x/+y` | `+x/−y` | `−x/+y` | `−x/−y` |
|---|---:|---:|---:|---:|
| `TESLA`=1×1 | 8 | **0** | 8 | **0** |
| `TESLA`=3×2 | 22 | **14** | 22 | **14** |

- **`TESLA`-vs-`TESLA` 计数与约定无关**（1×1 恒 0；3×2 恒 14）⇒ 裁决不受影响。
- 只有 `NACNST×NAPOWR` 的 8 格交叉占格随约定变化 ⇒ 我在正文里只作**条件性**登记，不当论据。
- W95 的"合计 24→14"在 `+x/−y` 下完全复现，`[静态推断]` 它用的是该约定。

**要关掉它需要什么**：读 `BuildingClass` 放置/占格代码里对 `Foundation` 的展开方向（`re_atlas` 线），或用最小真机实验（放一座 3×2 建筑，看它从点击格往哪边铺）。

---

## U3 `[未证]` `ATPOWR`/`ATESLA` 之外的 `TESLA` 家族是否还有别的 Image 变体

本卡只回答了被点名的 5 座。`artmd.ini` 里 `TSLA` 家族只有 `[NATSLA]` 及其 `_A/_AD/_B/_BD` 动画节（已 grep `^\[.*TSLA.*\]`，`round1` 命中 5 条，全部列出）。**未**逐一核对战役/遭遇战里是否有 mod 覆盖（本机 `expandmd98.mix` 只有 3 个 ECH0x 地图，`probe02` 已列全）。

---

## U4 `[未证]` 同一 id 两份内容不同的规则文件，哪份生效

`0x8218F9F4` 在两处出现且字节不同（`probe13`）：

| 位置 | 大小 | sha256 |
|---|---:|---|
| `expandmd01.mix`（顶层） | 743,215 | `3d341ef8a13a4b5a…` |
| `ra2md.mix` → 嵌套 `0xFBE0D09D` | 742,958 | 未逐字节比对差异 |

差 257 B。按本项目既定认知（`mixlib.py:337-339` 注释：`expandmdNN.mix` 先于 `ra2md.mix` 加载），**倾向** `expandmd01` 那份覆盖后者 ⇒ W89 取的那份是生效的那份。但**本卡未做 diff**，且这条不影响 `Foundation`（rules 里没有 `Foundation=`，art 才是来源）。

---

## U5 搜索范围声明（"没找到"的边界）

- `artmd.ini` 的**正确名字**（crc32 `0xAF902833`）不存在：范围 = `ra2youli\*.mix` 17 个顶层 + 每 mix 一层嵌套；`theme.mix` / `themedmd.mix` 因 C&C 格式**未解析**（见 U1）。
- 全项目是否已有别人抽好的 `artmd.ini`：范围 = `D:\Project\ra2-campaign-forge` 递归 `artmd*.ini` / `rules*.ini`。结果：**只有** W89 的 `rulesmd_exp01.ini`（已证＝`expandmd01.mix:0x8218F9F4` 逐字节全等），**没有任何 artmd.ini**。
- 文件名的 crc32 反查：用 `gamemd.exe` 里抽出的 2,392 条"像文件名的字符串"（ASCII + UTF-16LE）撞 archive id，命中 100+ 条；`artmd.ini`/`rulesmd.ini`/两个 art payload 的 id **无名字串**。
