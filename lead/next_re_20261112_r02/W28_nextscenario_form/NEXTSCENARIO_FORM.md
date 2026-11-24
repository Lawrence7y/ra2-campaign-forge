# W28 · `[Basic] NextScenario` 形式定谳（零成本 / 纯离线只读）

- run_id：`NEXT_RE_20261112_R02`；执行：W28 子代理；日期：2026-11-13
- 任务：确认官方战役图 `[Basic] NextScenario` 的写法与 ra2forge 生成的写法是否不同，
  以判定 W27 真机「無法啟動選取地圖!」是否由**取值形式**造成。
- 授权边界：全程 **未启动游戏、未 attach、未读活进程、未挂起线程**；
  `ra2youli\` 与 `W21`–`W27` 只读；无 git 写操作；所有写入落在 `W28_nextscenario_form\`。
- 标级：`[本次实测]` 本次离线读取/枚举所得｜`[本次读码]` 本次读源码所得｜
  `[静态推断]` 由实测+读码推得、未经运行验证｜`[待运行验证]` 需真机/沙箱才能定

---

## 0 · 一句话结论

> **`[形式相同]` ⇒ `[Basic] NextScenario` 的取值形式不是「無法啟動選取地圖!」的成因。**
> 官方图与 ra2forge 图写的都是**「裸文件名 + 扩展名」**：无路径、无前导反斜杠、带 `.map`/`.MAP`。
> 详见 §3 定谳与 §4 证据。`[本次实测]`

---

## 1 · T1 提取结果：mixlib 能用，官方图在 `mapsmd03.mix`

### 1.1 mixlib 可用性

使用项目自带 `lead\next_re_20261112_r02\W26_dlc_unseal_fix\ra2forge_patched_v9\ra2forge\mixlib.py`
（SHA-256 `b320e89b4cba4f75a4ebab39b50f9b68c6404f4fde6ec1588fc2532ec9a34418`）。
通过 `importlib.util.spec_from_file_location` 直接装载，调用
`MixFile(path)` / `.all_entries()` / `.get(name)` / `.read_entry(e)` / `crc_hash()` / `classic_hash()`。
**未自己写 MIX 解析**。`[本次实测]`

| 容器 | 大小 (B) | 打开 | 条目数 | 备注 |
|---|---:|:---:|---:|---|
| `maps01.mix` | 3,823,604 | ✅ | 18 | 明文头，未加密 |
| `maps02.mix` | 3,170,324 | ✅ | 18 | 明文头，未加密 |
| `mapsmd03.mix` | 4,419,780 | ✅ | 14 | **官方 MD 战役图所在容器** |
| `expandmd01.mix` | 4,813,968 | ✅ | 33 | 含 ALL02UMD 的异版 |
| `expandmd98.mix` | 43,361 | ✅ | 3 | |
| `ra2md.mix` / `ra2.mix` / `multi.mix` / `multimd.mix` / `langmd.mix` / `language.mix` / `wdt.mix` | — | ✅ | 25 / 21 / 97 / 173 / 10 / 6 / 126 | |
| `movies01.mix` / `movies02.mix` / `movmd03.mix` | — | ✅ | 44 / 41 / 57 | |
| `theme.mix` / `thememd.mix` | — | ❌ | — | **未能打开**：`ValueError: not a TS/RA2 MIX (C&C format unsupported)`，见 `UNCOVERED.md` |

17 个容器中 **15 个成功打开**，均为 TS/RA2 明文 MIX 头（`flags & 0x2` 未置位，无需 RSA/Blowfish 解密）。
`[本次实测]`

### 1.2 提取到的官方图（`mapsmd03.mix`，逐字节原样复制，未修改）

| 名字 | CRC id | 容器内 offset/size | 提取字节数 | SHA-256 (前16) | `[Basic]` 偏移 | `NextScenario=` 原始字节 |
|---|---|---:|---:|---|---:|---|
| `SOV01UMD.MAP` | `73220E81` | 2,368,608 / 329,188 | 329,188 | `498b989a4b6f579d` | 6,350 | `47 44 49 32 41 2e 6d 61 70` = `GDI2A.map` |
| `ALL01UMD.MAP` | `3A6F0AC2` | 0 / 301,077 | 301,077 | `dee38769f2247a85` | 7,544 | `47 44 49 32 41 2e 6d 61 70` = `GDI2A.map` |
| `SOV02SMD.MAP` | `9E7D3C58` | 2,697,808 / 327,808 | 327,808 | `139a7f17a17cefc2` | 3,798 | `GDI2A.map` |
| `ALL02UMD.MAP` | `B4E00D21` | 301,088 / 465,825 | 465,825 | `168ed42024991b6c` | 3,747 | `GDI2A.map` |
| 其余 10 张（`ALL03UMD` … `SOV07TMD`） | 见 `out\mix_enumeration.txt` | — | — | — | — | 全部 `GDI2A.map` |

`BATTLEMD.INI:55` `[SOV1] Scenario=SOV01umd.MAP`、`BATTLEMD.INI:49` `[ALL1] Scenario=ALL01umd.MAP`
⇒ 两张任务指定图确在该容器内。`[本次实测]`

**名字解析无 hash 碰撞**（`out\_probe2.json`）：`SOV01UMD.MAP` → crc `73220E81`
`crc_hit=True / classic_hit=False / get_len=329188`；`ALL01UMD.MAP` → crc `3A6F0AC2`
`crc_hit=True / classic_hit=False / get_len=301077`。14 张图 SHA-256 两两不同，
`[Basic]` 内 `Player=Russians`/`Americans`、`Intro=S01_F00e`/`A01_F00e` 与阵营吻合
⇒ 提取的是真官方战役图，不是误命中。`[本次实测]`

MIX 索引只存 CRC32 id，无明文名；`crc_hash()` 对名字 `upper()` 后再算 CRC
（`mixlib.py:205-207`），故**引擎按名查 MIX 时大小写不敏感**。`[本次读码]`

---

## 2 · T2 逐字节对照

### 2.1 对照表（任务指定格式）

| 项 | 官方 SOV01UMD | 官方 ALL01UMD | ra2forge ECH01 | 是否一致 |
|---|---|---|---|---|
| 原始取值 | `GDI2A.map` | `GDI2A.map` | `ECH02.MAP` | **形式一致**（同类：裸文件名+扩展名）；字面值本就不同 |
| 带扩展名 | 是，`.map`（小写） | 是，`.map`（小写） | 是，`.MAP`（大写） | **一致**（都带） |
| 带路径/前导反斜杠 | 无 | 无 | 无 | **一致**（都无） |
| 大小写与容器条目一致 | MIX 条目只有 CRC32 id、无明文名 ⇒ 无法字面比较；但 `crc_hash` 先 `upper()`，大小写不影响命中 | 同左 | 目标为散装 `ECH02.MAP`，与取值同形（全大写）；NTFS 大小写不敏感 | **一致 / N-A** |
| 目标图在哪个容器 | `GDI2A.map` 不在任何已开容器（crc `B639B8AC`，17 容器全不命中），也不在游戏目录散装 | 同左 | **散装**：`ra2youli\ECH02.MAP`（13,606 B）/ W27 pkg `ECH02.MAP`（4,647 B）；不在任何 MIX | — |
| （附加）行尾分隔符 | `CRLF`（`b'NextScenario=GDI2A.map\r\n'`） | `CRLF` | `LF`（`b'NextScenario=ECH02.MAP\n'`） | **不同**（但是文件级行尾，不是取值形式）；见 `UNCOVERED.md` |

补充：`AltNextScenario` 官方为 `GDI9C.MAP`（crc `A63E1B0F`，同样全容器不命中），
ra2forge 为 `AltNextScenario=`（空）。`[本次实测]`

### 2.2 ra2forge 生成值来源

- 原始生成物：`W27_campaign_live\pkg\W27 Live Campaign\ECH01.MAP`（4,671 B，
  SHA `870ec2c07713f82b`，`[Basic]@247`），`b'NextScenario=ECH02.MAP\n'`
- 部署副本：`W27_campaign_live\sandbox_game\ECH01.MAP`（4,671 B，同 SHA）、
  `ra2youli\ECH01.MAP`（14,226 B，SHA `f363818f410d2bd5`，文本被本地化，但 `NextScenario` 行不变）
  三处**取值完全相同**；`ECH02.MAP` 的 `NextScenario=`（空）+ `EndOfGame=yes`。`[本次实测]`
- 生成代码：`maplib.py:220` `w(f"NextScenario={self.next_scenario}")`，
  `builder.py:177` `names = [f"{m['name'].upper()}.MAP" for m in missions]`
  ⇒ ra2forge 是**有意**写全大写 `*.MAP`。`[本次读码]`

### 2.3 形式相同结论所依据的**全部**官方样本（非只读一张）

1. **按名提取 14 张**（`mapsmd03.mix`）：`SOV01UMD.MAP`, `ALL01UMD.MAP`,
   `SOV02SMD.MAP`, `ALL02UMD.MAP`, `ALL03UMD.MAP`, `ALL04DMD.MAP`, `ALL05UMD.MAP`,
   `ALL06UMD.MAP`, `ALL07SMD.MAP`, `SOV03UMD.MAP`, `SOV04DMD.MAP`, `SOV05UMD.MAP`,
   `SOV06LMD.MAP`, `SOV07TMD.MAP` —— 全部 `NextScenario=GDI2A.map`。`[本次实测]`
2. **盲枚举 64 个 INI 地图条目**（不依赖名字，逐条目 `read_entry`）：
   `maps01.mix`(18) + `maps02.mix`(18) + `mapsmd03.mix`(14) + `expandmd01.mix`(33)。
   得到 9 种取值：`GDI2A.map`(48), `ALL02T.map`(4), `ALL10S.map`(3),
   `All12u.map`, `All08u.map`, `All09t.map`, `All07T.map`, `SOV03U.map`, `ALL01T.MAP`(各 1)。
   **9 种全部是裸文件名 + 扩展名，无一例外；无路径、无前导 `\`、无缺扩展名**。
   `maps01/02` 里的 `ALL10S.map`/`All12u.map`/`SOV03U.map` 等是真实关卡名，
   证明官方确实把「下一关文件名」写在这个键上。`[本次实测]`
3. **仓库既有独立提取副本**（第三方交叉印证）：
   `extracted\ALL01UMD.MAP:437`、`extracted\SOV01UMD.MAP:356`、
   `extracted\yr_maps\ini_73220E81.ini:356`、`ini_3A6F0AC2.ini:437`、
   `ini_310709FC.ini:565`、`ini_784A0DBF.ini:464` —— 全部 `GDI2A.map` +
   `AltNextScenario=GDI9C.MAP`。`[本次实测]`

证据文件：`out\official_maps\`（14 张原样副本）、`out\basic_sections\`、
`out\basic_sections_dump.txt`、`out\blind_enumeration.txt/.json`、
`out\nextscenario_raw.json`、`out\ra2forge_ech01_basic.txt`。

---

## 3 · T3 定谳

### **`[形式相同]` —— `NextScenario` 的取值形式不是成因。**

依据：

1. 语法类完全相同：官方 **14 张按名提取图 + 64 个盲枚举 INI 地图条目**（两组有重叠，
   合计去重后覆盖 9 种不同的 `NextScenario` 取值）与 ra2forge 生成值都是
   `<裸文件名>.<扩展名>`；无路径、无前导反斜杠、都带扩展名。`[本次实测]`
2. 大小写不是变量：官方样本里同时存在 `.map`（`GDI2A.map`）与 `.MAP`（`ALL01T.MAP`、
   `GDI9C.MAP`），即官方自身没有统一大小写约定；且 MIX 查名 `crc_hash` 先 `upper()`
   （`mixlib.py:205-207`），散装在 NTFS 上亦大小写不敏感 ⇒ `ECH02.MAP` 与 `ECH02.map`
   对引擎等价。`[本次读码]` + `[本次实测]`
3. 因此 **ra2forge 不需要改 `NextScenario` 的写法**。若硬要「贴官方字面」，
   唯一可做的是把扩展名改成小写 `ECH02.map`，但按 2 预计**无效**，不建议作为修复。
   `[静态推断]`

### 排除这条路后，实测顺带暴露的两条更强线索（**非本卡定谳**）

- **A. 本安装里官方战役图的 `NextScenario` 全是 TS 时代占位值，指向不存在的图。**
  `GDI2A.map`（crc `B639B8AC`）/ `GDI9C.MAP`（crc `A63E1B0F`）在 17 个容器
  与 `ra2youli\` 散装中均不存在。也就是说，`[SOV1]`/`[ALL1]` 指向的官方图
  **并没有可用的 `NextScenario` 链** ⇒ 不能拿它们当「能工作的链」的正对照，
  也不能据此推断引擎一定靠这个键推进。`[本次实测]`
- **B. 官方图在 MIX 内（CRC 寻址），ra2forge 目标图是散装文件。**
  W27 的 D2/D3 显示：`Scenario=ECH02.MAP` 直接加载成功，而 `NextScenario=ECH02.MAP`
  推进失败。若引擎的 `Scenario=` 走文件系统、而 `NextScenario` 推进走 MIX/CRC 查找，
  则散装 `ECH02.MAP` 在推进路径上就找不到 —— 这与「形式相同」不矛盾，且能同时解释 D2/D3。
  **这是推断，未验证**。`[静态推断]` / `[待运行验证]`

⇒ 建议下一卡直接做 Lead 已规划的 **T2**：目标图是否必须同时在 `BATTLEMD*.INI` 战役链里登记；
并并行验证 **A/B**（把 ECH02.MAP 打进 `expandmd*.mix` 再试 Continue）。
本卡按授权**未启动游戏**，以上均待运行验证。

---

## 4 · 证据索引与可重跑性

| 文件 | 内容 |
|---|---|
| `extract_maps.py` | 可重跑主脚本：装载 mixlib、枚举 17 容器、按名提取 14 图、盲枚举 64 条目、读 ra2forge 生成/部署图 |
| `out\mix_enumeration.txt` | 15 个成功容器的逐条目 `id / offset / size` |
| `out\official_maps\*.MAP` | 14 张官方图**原样字节副本**（未修改） |
| `out\basic_sections\*` | 每张图 `[Basic]` 段的逐行 `repr`（保留大小写/CRLF） |
| `out\blind_enumeration.txt/.json` | 64 个官方 INI 地图条目的 NS 原始字节 + 目标 CRC 解析 |
| `out\nextscenario_raw.json` | 全部结构化结果（含 mixlib sha256、哈希命中、目标探测） |
| `out\ra2forge_ech01_basic.txt` | ra2forge 5 份 ECH01 副本的 `[Basic]` 原文 |
| `out\_probe*.json/.stdout.txt` | 探针原始输出（含 hash 碰撞核查、9 容器名解析） |
| `out\COMMANDS_AND_EXITCODES.md` | 实际命令与退出码 |

重跑：`python extract_maps.py`（默认仓库布局；支持 `--root/--game/--mixlib/--out`）。
脚本对源文件只读 `'rb'` / `Path.read_bytes()`，只写自己的 `out\`。
