# W54 · 存档非确定性字节定位与「可事先声明」白名单

> 卡：`W54_save_determinism`｜run_id `NEXT_RE_20261112_R02`
> 开始：`2026-11-13T21:37:48+08:00`（`STARTED.txt`）
> 模式：**纯离线只读分析已有产物**。未启动游戏、未 attach、未写 `ra2youli`、未改仓库、未动 W21–W53、git 只读、**未取 `.game_instance.lock`**；只写 `W54_save_determinism\`。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。

---

## 0 · 先把不能说的话说清楚

- **本卡不作、也不得被读作任何「存档层面的字节等价已成立」的声称。** 只产出白名单与掩码比较结果；真正的等价判定要等 W45 那套框架在修好 `frame` 对齐后重跑（W45 `EQUIVALENCE_RESULT.md:193` 自己列的第一条待办）。
- 同臂两次存档**本来就不同** —— `[本次实测]` 确认 W45 §2.4 的观察成立，**没有出现「反证」**（A1 vs A2 的 size / sha256 全不同，掩码前 1,345,043 个差异字节）。
- **白名单对「元数据平面」充分，对「全文件」不足**：掩码后元数据平面 `A1==A2==B1==B2`（0 差异字节），但掩码后全文件 `A1≠A2`（仍有 1,344,989 个未掩码差异字节）。按任务书要求「照实说并给出还差什么」，见 §5.3。

**最关键的发现（会改变后续卡的做法）**：`.SAV` **不是平面字节流，而是 OLE2 / MS-CFB 复合文档容器**。`[本次实测]` 因此「按 raw file 绝对偏移做全字节比对」这个坐标系本身是错的：DIFAT/FAT 扇区位置随 `CONTENTS` 长度漂移，四份存档尺寸全不同。正确做法是解析 CFB、按具名 stream 比较。

---

## 1 · 材料与配对（先用 `Get-ChildItem` 摸清，不假设）

`[本次实测]` `W45_b_line_equivalence\out\` 下实际有 **8** 份 `.SAV`（W45 §2.4 只列了 4 份主产物）：

| tag | 文件 | size (B) | sha256[:8] | 存档时刻（Root mtime, UTC） | `CONTENTS` 大小 |
|---|---|---:|---|---|---:|
| A1 | `save_A1_SAVE2147.SAV` | 1,405,384 | `01ed2755` | 2026-11-13 13:18:58.596 | 1,389,512 |
| A2 | `save_A2_SAVE2EB9.SAV` | 1,382,212 | `dea9d7ef` | 13:21:19.117 | 1,366,340 |
| B1 | `save_B1_SAVE7DBC.SAV` | 1,382,156 | `bd7138ac` | 13:23:52.242 | 1,366,284 |
| B2 | `save_B2_SAVE27BB.SAV` | 1,366,595 | `a6fefe73` | 13:26:38.586 | 1,351,235 |
| A1_x | `save_A1_SAVE31D9.SAV` | 1,397,199 | `d49c7927` | 13:01:09.824 | 1,381,327 |
| A2_x | `save_A2_SAVE6C99.SAV` | 1,399,419 | `14034367` | 13:12:22.469 | 1,383,547 |
| B1_x | `save_B1_SAVE161E.SAV` | 1,398,096 | `fb2c797b` | 13:05:27.611 | 1,382,224 |
| A1test2 | `save_A1test2_SAVE3CD8.SAV` | 1,395,201 | `516f1114` | 12:57:22.357 | 1,379,329 |

配对依据 `[本次读码]`：`out\analysis.json` 的 `per_comparable[3].copies` 明确指定 4 份主产物 = A1/A2/B1/B2；`A1_result.json` 等各自 `save.copy` 字段与之逐字一致。后 4 份是 W45 `EQUIVALENCE_RESULT.md:45-46` 所述 Round 1/2 缺陷趟与 test 趟留下的副本 `[转引]`，本卡把它们当作**同臂附加样本**用于加宽时间戳的经验观测（见 §3.2），不冒充主判据。

**「同一臂的两次存档」的读法**：W45 的概念是 2 条臂（A 对照 / B 装包），每条臂跑 2 次 ⇒ 同臂 diff = `A1 vs A2`（噪声基线 N）与 `B1 vs B2`。`[转引]` W45 `EQUIVALENCE_SPEC.md:168-170`：A1 vs A2 的差异 = 环境噪声带 N；`EQUIVALENCE_SPEC.md:218-226` §3.4 与 `DISAGREE.md:26-31` D4 要求开跑前声明白名单 + `frame` 对齐 ≤1 拍。

参考结构（只读）`[本次实测]`：`W44_c_line_e2e\out\save_SAVE4823.SAV` 627,453 B、`W27_campaign_live\out\save_SAVE4823.SAV` 559,553 B、`ra2youli\{ALL01UMD,SOV01UMD,SOV01T,SAVE0029,ECH01,...}.sav`。**全部 8+7 份文件头 8 字节相同**，说明下面 §4 的结构是通用格式，不是 W45 特例。

---

## 2 · 同臂逐字节 diff（核心）

### 2.1 raw file 层（`A1 vs A2`）

`[本次实测]` 严格逐字节比较（公共长度 = 1,382,212 B）：

| 量 | 值 |
|---|---|
| 差异字节 | **1,345,043**（97.31%） |
| 严格合并区间数（相邻字节合并，gap=0） | **27,657** |
| gap≤64 再合并后的粗区间数 | **11** |
| LCP（最长公共前缀） | 84 B（首个差异 @0x54，DIFAT[2]） |
| LCS（最长公共后缀） | 123 B（固定 trailer，见 §4.4） |

**A1 vs A2 的 11 个粗区间（起 / 止 / 长度，绝对文件偏移）** `[本次实测]`：

| # | start | end | length | 性质推断 |
|---:|---:|---:|---:|---|
| 1 | 84 | 160 | 77 | CFB 头部 DIFAT：FAT 扇区号（A1 `[0,128,252,383,…]` vs A2 `[0,128,250,380,509,…]`）`[本次读码]` |
| 2 | 1132 | 1135 | 4 | Root Entry `mtime` FILETIME 低 4 字节 `[本次实测]` 解码为墙钟时间 |
| 3 | 2336 | 2363 | 28 | `\x05SummaryInformation` 里 3 个 VT_FILETIME 属性的低 4 字节 `[本次实测]` |
| 4 | 2752 | 2883 | 132 | `Start Time` / `Last Save Time` / `Play Time` 三个 8 B FILETIME 流 `[本次实测]` |
| 5 | 4352 | 4352 | 1 | mini stream 第 3 扇区起始处的 1 字节差异 `[静态推断]` 容器/填充 |
| 6 | 5112 | 6440 | 1329 | 目录第 4 扇区（含 `CONTENTS` size 字段 @5112）+ 其后 FAT/数据 `[本次实测]`/`[静态推断]` |
| 7 | 6697 | 66047 | 59,351 | `CONTENTS` 主体（高熵）`[静态推断]` |
| 8 | 66532 | 603434 | 536,903 | `CONTENTS` 主体（高熵）`[静态推断]` |
| 9 | 603534 | 606817 | 3,284 | `CONTENTS` 低熵窗口区（H≈5.7–5.9）`[本次实测]` |
| 10 | 606974 | 610689 | 3,716 | 同上 `[本次实测]` |
| 11 | 610780 | 1382211 | 771,432 | `CONTENTS` 尾部 + 文件尾 `[静态推断]` |

> 严格区间清单 27,657 行全量太大，已在 `EVIDENCE\step4_probe.stdout.txt` 留存生成方法与首 8 条/统计；机器可读的白名单区间在 `diff_regions.tsv` 与 `SAVE_NONDET_WHITELIST.json`。

同臂 `B1 vs B2` `[本次实测]`：差异 1,324,827 B（96.94%）、严格区间 28,527、gap≤64 区间 20，LCS=125。跨臂 `A1 vs B1` 1,344,909 B、`A2 vs B2` 1,327,909 B —— **与同臂噪声同量级**（见 §5.2）。

### 2.2 CFB stream 层（正确坐标系，`A1 vs A2`）

`[本次实测]` 解析 CFB 后按 stream 名比较：

| stream | size A1 / A2 | 判定 | 差异位置 | 性质 |
|---|---|---|---|---|
| `Scenario Description` | 42 / 42 | **相同** | — | 局内存档描述（UTF-16），四臂全同 |
| `Player House` | 6 / 6 | **相同** | — | — |
| `Version` | 4 / 4 | **相同** | — | `01 00 00 00` |
| `Internal Version` | 4 / 4 | **相同** | — | `98 b8 02 00` = 0x0002b898 |
| `Executable Name` | 16 / 16 | **相同** | — | UTF-16 `"SUN.EXE"` |
| `Player Name` / `Player Name2` | 2 / 2 | **相同** | — | 均为空 (`00 00`) |
| `Scenario Number` | 4 / 4 | **相同** | — | `01 00 00 00` |
| `Campaign` | 4 / 4 | **相同** | — | `01 00 00 00` |
| `GameType` | 4 / 4 | **相同** | — | `00 00 00 00` |
| `\x05SummaryInformation` | 392 / 392 | **不同** | 288–291, 300–303, 312–315 | 3 个 VT_FILETIME 属性：`CreateDateTime` / `LastSaveDateTime` / `EditTime` `[本次实测]` 属性集解码 |
| `Start Time` | 8 / 8 | **不同** | 0–3 | FILETIME 墙钟 `[本次实测]` 解码 |
| `Last Save Time` | 8 / 8 | **不同** | 0–3 | 同上，同文件内与 `Start Time` 同值 |
| `Play Time` | 8 / 8 | **不同** | 0–3 | 同上，同文件内与 `Start Time` 同值 |
| `CONTENTS` | 1,389,512 / 1,366,340 | **不同** | 几乎全体 | 长度可变的游戏状态；LCP=0、0 个相同 512 B 块 `[本次实测]` |

`[本次实测]` 三个时间流的 FILETIME 解码：A1 = `134390495385510000` = 2026-11-13 13:18:58.551 UTC；A2 = `134390496790600000` = 13:21:19.060 UTC。`\x05SummaryInformation` 的 3 个属性解码为同一个值。Root Entry `mtime` = 13:18:58.596（比流内时间戳晚约 45 ms，符合「先写流、后封容器」）。

⇒ **所有非确定性都可归约为「同一个墙钟时间戳被复制到 7 处」** `[本次实测]`：3 个时间流 + 3 个属性集字段 + 1 个 Root Entry mtime。未观察到 W45 猜测的「路径 / RNG 状态 / 指针句柄」在元数据平面上出现（见 `DISAGREE.md`）。

### 2.3 尺寸为何变（含变长字段？）

`[本次实测]` **是，含变长字段**，且可以精确归因：

```
文件尺寸差 (A1 - A2) = 1,405,384 - 1,382,212 = 23,172 B
CONTENTS 流尺寸差   = 1,389,512 - 1,366,340 = 23,172 B   ← 完全相等
```

四臂皆然：`B1` 1,382,156 − `B2` 1,366,595 = 15,561；`CONTENTS` 1,366,284 − 1,351,235 = 15,049。注：`B1`/`B2` 那对不完全相等是因为 `B2` 少 1 个 FAT 扇区（512 B）并在文件尾部有 padding 差，主导项仍是 `CONTENTS` 长度。

`[转引]` W45 `EQUIVALENCE_RESULT.md:122`：四趟存档点 `frame` 冻结值不同（本卡从 `*_result.json` 读到 A1=2404 / A2=2408 / B1=2441 / B2=2412，规格 §3.4 要求差 ≤1 拍）。`[静态推断]` `CONTENTS` 是随游戏 tick 演进的序列化状态（单位/迷雾/触发器/计时器等），存档点未对齐 ⇒ 长度与内容都不同。`[本次实测]` 反证：`A1test2` 在 `frame=698` 存档，`CONTENTS` 头部 4 字节值 11,936 与 `frame≈2400` 的 11,900–12,078 同量级 ⇒ **该 4 字节不是 frame 计数**（见 §4.4）；file 内没有发现可直接读出「存档点 frame」的字段，所以 `frame` 对齐必须由外部驱动脚本在按 Esc 前门控 `frame==N`，不能靠读存档反推。

### 2.4 对齐策略（给后续卡）

`[本次读码]` + `[本次实测]`：

1. **不要用 raw file 绝对偏移比较全文件**。CFB 的 DIFAT 把 FAT 扇区交错放在约每 128 扇区一处（A1 `[0,128,252,383,512,638,765,889,1017,…]`），文件一变长，扇区位置就变，之后所有偏移整体漂移；本卡实测 A1/A2 的 raw LCP 只有 84 B。
2. **解析 MS-CFB → 按 stream 名取 payload → 在 stream 内比较**。目录扇区链 `[1,5,6,8]`、mini stream 扇区链 `[3,4,7]` 在 A1/A2/B1/B2 **四份完全一致** `[本次实测]`，故元数据流在文件里的绝对偏移也是稳定的（`diff_regions.tsv` / 白名单 JSON 的 `abs_offset` 列可直接用）。容器分配表（FAT / DIFAT / miniFAT）按构造排除。
3. **掩码白名单**后比较 14 个非-`CONTENTS` 流 → 这是本卡实际做出来的、可用的「存档元数据字节等价」可比量。
4. **`CONTENTS` 必须先在 `frame` 上对齐**（≤1 拍），再谈逐字节相等；否则任何纯偏移白名单都不够（§5.3）。
5. `size_may_vary=true` ⇒ 比较时按公共长度比较并单独记录尾部长度差，不要用「长度不等」直接判不等价。

---

## 3 · 白名单（机器可读）

文件：`SAVE_NONDET_WHITELIST.json`。格式满足要求：

```json
{ "version": 1, "source_arms": ["A1","A2","B1","B2"],
  "regions": [ { "offset": …, "length": …, "reason": …, "confidence": … }, … ],
  "size_may_vary": true }
```

并补充：`coordinate_space: "cfb_logical"`、每个 region 的 `stream` / `abs_offset` / `abs_end` / `in_primary_same_arm_diff` / `derived_from_pairs` / `bytes_A1_head` / `bytes_A2_head`，以及 `abs_mask_regions`（可直接用于 raw 掩码）。

### 3.1 只覆盖实证不稳区间，不凭猜测扩大

`[本次实测]` 生成规则（写死在 `EVIDENCE\step6_whitelist.py`）：

```
regions = 并集 { 字节位置 i : i 在「任一【同臂】pair」中不同 }
同臂 pair = 臂A组内 [A1,A1_x,A1test2,A2,A2_x] 的全部 10 个无序对
          ∪ 臂B组内 [B1,B1_x,B2] 的全部 3 个无序对   ⇒ 共 13 对
```

- **没有任何猜测扩大的区间**；每个 region 的 `derived_from_pairs` 列出是哪几对实证出来的。
- 只用了「同臂」对，没有把 A↔B 跨臂差异并进来（避免把「装包效应」误当噪声）。
- 结果：**30 个 region，共 68 个绝对字节**（相对 1.38 MB 文件 = 0.0049%）。
- `in_primary_same_arm_diff=false` 的 7 个 region 是「只由附加同臂样本实证、A1/A2 与 B1/B2 两对里没出现」的字节（主要是 FILETIME 第 5 个低字节，因样本时间跨度从 12:57 到 13:26 更宽）；它们仍是**实证**，不是猜测，分级照实标注。
- `confidence`：`high`=已解码为 FILETIME/明确字段（8 个）；`medium`=DIFAT 扇区号，语义由 MS-CFB 规范 `[本次读码]` 推出（20 个）；`low`=仅由附加同臂对实证、且落在 DIFAT 内部无法逐字节定名（2 个）。**所有 low 项已在此说明**：offset 124–125 与 148–149（`header`），来源是 `A1_x/A2_x` 等样本的 FAT 扇区号差异。

### 3.2 白名单区间总表（按绝对偏移）

| abs_start | abs_end | len | locus（CFB 部分 : 内偏移） | 性质 | confidence |
|---:|---:|---:|---|---|---|
| 44 | 44 | 1 | `header:0x2C` | `#FAT sectors`（A1/A2/B1=22, B2=21） | high |
| 80–160 | — | 21 段 | `header:0x50–0xA0` | DIFAT：22 个 FAT 扇区号（交错 ~128 扇区） | medium / 2 段 low |
| 1132 | 1136 | 5 | `directory:108`（Root Entry `mtime`） | FILETIME 墙钟 | high |
| 2336 | 2340 | 5 | `\x05SummaryInformation:288` | VT_FILETIME `CreateDateTime` | high |
| 2348 | 2352 | 5 | `\x05SummaryInformation:300` | VT_FILETIME `LastSaveDateTime` | high |
| 2360 | 2364 | 5 | `\x05SummaryInformation:312` | VT_FILETIME `EditTime` | high |
| 2752 | 2756 | 5 | `Start Time:0` | FILETIME 墙钟 | high |
| 2816 | 2820 | 5 | `Last Save Time:0` | FILETIME 墙钟 | high |
| 2880 | 2884 | 5 | `Play Time:0` | FILETIME 墙钟 | high |
| 5112 | 5114 | 3 | `directory:2040`（entry 15 `stream_size`） | `CONTENTS` 长度（派生量） | high |

> 注：`directory:2040` 的绝对偏移是 **5112**（目录链 `[1,5,6,8]` 的第 4 扇区 = 扇区 8 = abs 4608+504）。`EVIDENCE\step3_streamdiff.stdout.txt` 里曾按「1024+逻辑偏移」朴素算成 3064，是错的；由 `step6b_layout_check.stdout.txt` 用 FAT 链实测纠正。见 `DISAGREE.md` D5。

### 3.3 刻意不覆盖的（写进 JSON 的 `not_covered_deliberately`）

- **`CONTENTS` 全流**：不白名单。它是游戏状态、不是噪声；`[本次实测]` A1/A2 的 LCP=0、0 个相同 512 B 块，把它整段掩掉等于把比较变成空操作。
- **CFB FAT 扇区内容**：按「比较 stream 而非 raw file」的构造排除。raw 文件里残留的 abs 1012–1020（FAT 扇区 0 的 3 个 u32 项）属于这一类，见 §5.2。
- **引擎生成的盘上文件名 / 槽位**：`[转引]` W45 §2.4「文件名由引擎自动生成、各趟不同」；本卡实测存档**内部**的 `Scenario Description` 流四臂全同，故这不属于「文件内字节」，不计入白名单。

---

## 4 · 存档格式结构（有限度，不反序列化）

### 4.1 magic / 版本 / 头部大小 `[本次实测]` + `[本次读码]`

所有 15 份被检文件（8 份 W45 + W44/W27 + 5 份 `ra2youli` 参考）头 8 字节均为：

```
d0 cf 11 e0 a1 b1 1a e1
```

即 **MS-CFB / OLE2 Compound File Binary signature**（`[MS-CFB]` 规范）。头部字段（从 A1 前 128 字节 hexdump，`EVIDENCE\step1_probe.stdout.txt`）：

| abs | 字节 | 字段 | 值 | 推出依据 |
|---:|---|---|---|---|
| 0x00–07 | `d0 cf 11 e0 a1 b1 1a e1` | signature | CFB | `[本次读码]` MS-CFB 2.2 |
| 0x08–17 | 全 0 | CLSID | 0 | 同上 |
| 0x18–19 | `3e 00` | minor version | 0x003E = 62 | 规范值 |
| 0x1A–1B | `03 00` | major version | 3 ⇒ 512 B 扇区 | 规范 + 与 0x1E 互证 |
| 0x1C–1D | `fe ff` | byte order | 0xFFFE little-endian | 规范 |
| 0x1E–1F | `09 00` | sector shift | 9 ⇒ 2⁹=512 | 规范 |
| 0x20–21 | `06 00` | mini sector shift | 6 ⇒ 2⁶=64 | 规范 |
| 0x28–2B | 0 | #directory sectors | 0（v3 必须为 0） | 规范 |
| 0x2C–2F | `16 00 00 00` | **#FAT sectors** | 22（B2=21, W44=10, W27=9） | 实测；随文件尺寸变 |
| 0x30–33 | `01 00 00 00` | first directory sector | 1 | 实测，扇区 1 = abs 1024 |
| 0x38–3B | `00 10 00 00` | mini stream cutoff | 0x1000 = 4096 | 规范 |
| 0x3C–3F | `02 00 00 00` | first miniFAT sector | 2 | 实测 |
| 0x40–43 | `01 00 00 00` | #miniFAT sectors | 1 | 实测 |
| 0x44–47 | `fe ff ff ff` | first DIFAT sector | ENDOFCHAIN（无扩展 DIFAT） | 规范 |
| 0x48–4B | 0 | #DIFAT sectors | 0 | 规范 |
| 0x4C–1FF | 109 × u32 | **DIFAT** | A1 `[0,128,252,383,512,638,765,889,1017,…]` | 实测 |

**头部大小 = 512 B（1 个扇区）**。`[本次实测]` 目录扇区链 `[1,5,6,8]`（4 扇区 × 128 B/entry = 16 个目录项）；mini stream 链 `[3,4,7]`（1,280 B = 20 个 mini 扇区）；miniFAT 在扇区 2。

### 4.2 是否有长度前缀

`[本次实测]` **有，但在容器层，不是文件层**：

- 每个 128 B 目录项的 `0x78–0x7F` 是 8 字节 stream size（v3 只用低 4 字节）。例如 A1 的 `CONTENTS` 项（entry 15）`size=1389512 (0x1533c8)`，其低 3 字节 `c8 33 15` 就落在 abs 5112–5114 —— 这正是白名单里「派生量」那一项。
- 小流（<4096 B）走 mini stream + miniFAT；大流 `CONTENTS` 走 FAT 链，长度由目录项给出。
- 另：`CONTENTS` **流内**开头 4 字节（A1=`0x2e7c`=11900、A2=`0x2e95`=11925、B1=12066、B2=12078）看起来像长度/计数/校验，但 `[本次实测]` 它既不等于流长（1.39 MB），也不与 `frame` 相关（`A1test2` frame=698 时仍为 11,936），`[静态推断]` **不能认定为长度前缀**。见 §4.4。

### 4.3 目录项与 stream 名 `[本次实测]`

16 个目录项（id 0 = Root Entry，id 1–15 = 15 个具名流）：

```
Root Entry, \x05SummaryInformation, Scenario Description, Player House,
Version, Internal Version, Start Time, Last Save Time, Play Time,
Executable Name, Player Name, Player Name2, Scenario Number, Campaign,
GameType, CONTENTS
```

流名以 UTF-16LE 存在目录项 `0x00–0x3F`，`0x40–41` 是名字字节数，`0x42` 是对象类型（5=root / 2=stream），`0x64–73` 是 ctime/mtime FILETIME，`0x74` 是起始扇区，`0x78` 是 size。W44 / W27 / `ra2youli\ALL01UMD.sav` / `SOV01UMD.sav` / `SAVE0029.SAV` 具有**完全相同的 16 项布局与流名** `[本次实测]` ⇒ 结构通用。

`Version` 流值 `01 00 00 00`、`Internal Version` = `98 b8 02 00`（0x0002b898 = 178,328）；`[静态推断]` 后者疑似 YR 内部构建号，**未做符号级证明**，不写进结论。

### 4.4 `CONTENTS`：压缩？LZO？`[静态推断]`（未定谳）

`[本次实测]` 证据：

- 前 0x40 字节是**明文/结构化头**：`0x0C` 起 `03 "GDI2A.map" 00 20`，`0x1C` 起 `"GDI9C.MAP"`，与 `*_result.json` 里的 `scen_next = GDI2A.map` 对得上；`0x04` 恒为 `00 00 01 00`；`0x0B`（A1=0x90 / A2=0xa8 / B1=0xd0 / B2=0xb0）、`0x30–0x3F` 若干字段随趟变。
- 从 `0x40` 起高熵：整流 H≈6.96；4 KiB 滑窗 H 均值 6.62，最小 5.49，最大 7.25 `[本次实测]`。约 585–620 KiB 处有 7–8 个 H<6.0 的窗口 ⇒ **不是均匀压缩流**，更像「大段高熵数据 + 若干重复记录区」混合。
- A1 vs A2：`LCP=0`（首 4 字节就不同）、`LCS=123`（固定 trailer）、**0 个完全相同的 512 B 块（含「在对方任意位置」查找）** `[本次实测]`。
- 反例测试 `[本次实测]`：从 0 / 4 / 8 / 0x3C / 0x40 起始的 `u32 长度 + payload` 块遍历均在第 2–3 块崩掉；`(u16 未压缩长, u16 压缩长)` 的 LZO/LCW 块遍历在 offset 0 得到 `(11900, 0)` 即无法起步；`crc32 / adler32 / 各类加和` 均复现不出 `head4`。

⇒ `[静态推断]` 高熵主体**与压缩或稠密状态数组都相容**，但**本卡未能确认 LZO/LCW，也没有验证出任何块结构**。因此：不宣称「存档是 LZO 压缩」，也不宣称「未压缩」。此项登记进 `UNKNOWNS.md` U1，标 `[待运行验证]`。共同 123 B trailer 内容见 `EVIDENCE\step3_streamdiff.stdout.txt`（末尾含 `… 05 00 00 00 fe ff ff ff 11 00 00`），`[静态推断]` 疑似流结束标记/索引，未解。

> 对「让后续卡能按 `frame` 对齐存档点」的实际结论 `[本次实测]`：**存档文件里没有可直接读出的存档点 `frame` 字段**（`CONTENTS[0:4]` 已排除）。`frame` 必须由驱动脚本在按 Esc 前门控 `frame==N` 并写入 ndjson；W45 四趟的 `frame` 值只存在于 `*_result.json` 的 `counters_after_save.frame`。

---

## 5 · 验证白名单确实够用（§3 要求）

脚本：`EVIDENCE\step6_whitelist.py`；stdout / exit code 在 `EVIDENCE\`。掩码定义：把白名单区域在两份文件里都置 0，再比公共长度。

### 5.1 元数据平面（CFB-logical view：header + directory + miniFAT + 14 个非-`CONTENTS` 流）`[本次实测]`

| 比较 | 掩码后相等 | 未掩码差异字节 |
|---|---|---:|
| **A1 vs A2** | **是** | **0** |
| **B1 vs B2** | **是** | **0** |
| A1 vs B1（跨臂） | 是 | 0 |
| A2 vs B2（跨臂） | 是 | 0 |
| A1 vs 其余 7 份（含 4 份附加样本） | 全部「是」 | 全部 0 |

⇒ **白名单对「存档元数据平面」充分**，且 8 份样本全部落在同一等价类。这是本卡实际把它变成可用的那个可比量。

### 5.2 raw file 层 `[本次实测]`

| 比较 | 掩码后全文件相等 | 比较长度 | 未掩码差异字节 | 首个差异 abs |
|---|---|---:|---:|---:|
| **A1 vs A2** | **否** | 1,382,212 | **1,344,989** | 4352 |
| B1 vs B2 | 否 | 1,366,595 | 1,324,775 | 1012 |
| A1 vs B1（A 臂 vs B 臂） | 否 | 1,382,156 | 1,344,847 | 1012 |
| A2 vs B2 | 否 | 1,366,595 | 1,327,854 | 4352 |

- 前 4096 B 窗口：A1 vs A2 掩码后 **0 差异**；B1 vs B2 与 A1 vs B1 各剩 **6 个差异字节 @1012**，定位为 FAT 扇区 0 的 3 个 u32 分配项（`B1` 把 `7e/7f/81` 写成 `7f/FATSECT/80`）`[本次实测]` —— 属容器分配表，按 §2.4 的构造排除，不是游戏状态。
- **A 臂 vs B 臂掩码后差异**（任务书要求的第二项）：1,344,847 B（A1 vs B1）/ 1,327,854 B（A2 vs B2）。与同臂噪声 1,344,989 / 1,324,775 B **同量级、甚至更小** `[本次实测]` ⇒ 按 W45 `EQUIVALENCE_SPEC.md:169` 的 `D > N` 判据，**没有出现超出噪声带的差异**。但本卡**不**把它写成「等价」：判定要等 W45 框架重跑。

### 5.3 白名单不足，照实说，还差什么 `[待运行验证]`

掩码后 `A1≠A2` ⇒ **白名单对「全文件字节相等」不足**。缺口全部在 `CONTENTS` 流（+随它漂移的容器分配表），具体还差：

1. **`frame` 对齐的存档点** —— `[转引]` W45 `EQUIVALENCE_RESULT.md:122` / `UNKNOWNS.md:99`：Esc 菜单打开后 frame 冻结、四趟冻结值不同；规格 §3.4 要求 ≤1 拍。必须脚本化「等 `frame==N` 再存」。
2. **至少两份「同 frame、同臂」的存档**，用来重测 `CONTENTS` 平面的噪声基线 N。现有 8 份里 `A1test2` 在 frame=698、其余在 frame≈2400，没有可用的同 frame 同臂对 ⇒ `CONTENTS` 平面的 N **从未被测过** `[本次实测]`。
3. **`CONTENTS` 的语义/解压后比较口径** —— 高熵主体 + 未定谳的压缩（§4.4）。若无法解出块结构，可退而求其次只比较「按 frame 对齐后的整流 sha256」，但那仍需第 1、2 条先成立。
4. （可选）把 FAT/DIFAT 扇区整体从 raw 比较中排除，或统一改用 §2.4 的 stream 级比较，以消掉 @1012 那 6 字节。

补齐 1–3 之后，才能把本卡的白名单**事先声明**进 W45 规格 §1.4，并由 W45 框架重跑给出「存档字节等价 / 不等价 / 不可判」。**本卡到此为止。**

---

## 6 · 交付物与证据索引

| 文件 | 内容 |
|---|---|
| `STARTED.txt` | 建卡时间戳（第一步即写） |
| `SAVE_DETERMINISM.md` | 本报告 |
| `SAVE_NONDET_WHITELIST.json` | 机器可读白名单 + `validation` 结果 |
| `diff_regions.tsv` | 白名单区间 / raw 粗区间 / 逐 stream 对照 |
| `UNKNOWNS.md` | 未定谳项 |
| `DISAGREE.md` | 与上游/本卡中间产物的分歧与纠正 |
| `EVIDENCE\step0_inspect.py` | 解析 W45 `*_result.json` / `analysis.json`，确定配对 |
| `EVIDENCE\step1_probe.py` | 头 hexdump / 熵 / LCP-LCS / 文件清单 |
| `EVIDENCE\step2_cfb.py` | 最小 MS-CFB 解析器（被后续脚本 import） |
| `EVIDENCE\step3_streamdiff.py` | 逐 stream diff + FILETIME 解码 + `CONTENTS` 块匹配 |
| `EVIDENCE\step4_probe.py` | 属性集解码 / 8 份 provenance / raw 合并区间 / 校验和假设 |
| `EVIDENCE\step5_format.py` | 熵剖面 / 长度前缀块遍历 / 绝对偏移稳定性 |
| `EVIDENCE\step6b_layout_check.py` | FAT 链实测，纠正目录项绝对偏移 |
| `EVIDENCE\step6_whitelist.py` | **权威**：白名单生成 + 掩码验证 + 写 JSON/TSV |
| `EVIDENCE\*.stdout.txt` / `*.exitcode.txt` | 每步 stdout 与退出码 |

所有证据脚本均为纯读；`SAVE_NONDET_WHITELIST.json` 与 `diff_regions.tsv` 是仅有的两个由脚本写出的分析产物，均在 `W54_save_determinism\` 内。
