# BASELINE_ADJUDICATION.md · W42 / S2 · 「哪份物理副本才是金标准」判定程序

> 卡：`W42_b_line_s2`｜承接 **`W38_version_guard_s1\UNCOVERED.md` U-W38-1**（移交 S2 的 BASELINE 定谳项）｜2026-11-13｜**纯离线**
> **本文件给的是「可执行的判定程序 + 判据」，不是结论。** 本卡**未实际计算任何哈希**、未枚举真机全部副本、未签 `BASELINE.json`、未指定任何一份物理副本为金标准。全部实算步骤标 `[待运行验证]`，由 **Lead 直接执行** 后签发。
> 与 `FEATURE_SUBSET_CONTRACT.md` 的关系：S2 的 feature-set 决定「写哪些文件」；本文件决定「S1 `guard_state=KNOWN_GOOD` 到底认哪一份字节」。二者正交，互不改写对方的判定结论。

---

## 0 · 先把「金标准」拆成两个不同的角色（关键，罪恶一段）

题面中「哪份物理副本才是金标准」其实指代**两个不同对象**，混在一起一事就会出错。`[静态推断]`，依据 W38-S1 / RE-N09 / FINAL_RULING：

| 角色 | 定义 | 用途 | 归属 |
|---|---|---|---|
| **R-A `TARGET_BASELINE`**（已登记目标字节） | 「安装补丁前，这**一个绝对路径**上这**一份具体字节**是什么」。身份三态 `KNOWN_GOOD` 比对的就是它 | W38-S1 §3 `classify()` 的 L1 精确比对；Ｓ2 判断能不能写游戏目录 | **W38-S1 `BASELINE.json`**，oked `adjudicated=true` |
| **R-B `RETAIL_ORACLE`**（干净零售金标准） | 「未经任何改动的官方 YR 1.001 零售原版」。用于改造前后行为对拍 | RE-N09 L280-282 / `REWRITE_ROADMAP.md:163` / 任务书 L89「原版对照」 | **不是** `BASELINE.json` 条目，设想 S4/S5 真机行为对照 |

**两条硬约束（避免定谳越界）**

1. `RA` 的「是不是登记的那份」**不等于**「是不是干净零售原版」。W38-S1 §0 红线 3、§5 R8：即使 `.detour` 段属原生，也**不能**当「干净零售金标准」；任务书 L89：分析镜像不能只凭游戏名就视作官方未修改原版（`[转引]`）。
2. W38-S1 §6.1 `baselineEntry.provenance.is_clean_retail_gold` 是 **`const:false`** ⇒ 在 S1 的 schema 里**没有任何** `BASELINE.json` 条目可以被标记为「干净零售金标准」。`RETAIL_ORACLE` 若定谳，必须落在**另立工件**里，不可塞进 `baselineEntry`（S3 若需要，须先扩展 schema，见 `DISAGREE.md` D-W42-3 / `UNCOVERED.md` U-W42-4）。

> 因此本文件的可执行产出是 **两轨**：`ADJUDICATION_TRACK_A`（签 `TARGET_BASELINE`）＋ `ADJUDICATION_TRACK_B`（判 `RETAIL_ORACLE` 是否可持续）。本卡**不**替 Lead 下任何一棵的是/否结论。

---

## 1 · 已知候选与账面值（只作对账口径，不是本卡实算）

### 1.1 本机已知的物理副本 `[转引]`

| 来源 | 说明 |
|---|---|
| `ra2bench\gamemd.exe` / `ra2youli\gamemd.exe` | 任务书 L83-84 两者整文件 SHA-256 同为 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` `[转引·本次实测]`（由题面已签发，本卡未复算） |
| `ra2youli\.ra2opt\orig\gamemd.exe` | FINAL_RULING.md §5 实算的「原始态」 `db264305…` 三重吻合 `[转引]` |
| `D:\Red2\ra2youli\gamemd.exe` | ZCode 报告也等于 `db264305…`，**Lead 未复算**（FINAL_RULING.md §5 / §7 第 3 条 `[转引]`） |
| 两个 `73201cc0…` 留痕态 + 至少两个 `db264305…` 原始态 | W36 §3.1.1 / FINAL_RULING.md §5 `[转引]` ⇒ **多副本歧义已证存在** |

### 1.2 账面判据值（对账用，`[转引]`，本卡未实算）

| 判据 | 值 | 出处 |
|---|---|---|
| C01 整文件 SHA-256 | `db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa` | `FINAL_RULING.md:97` / `ra2opt\__init__.py:23` `[转引]`＋本卡 `[本次读码]` 核对该常量行 |
| C08 字节数 | `4,825,360` | `FINAL_RULING.md:98` / `ra2opt\__init__.py:22` |
| C02 `.text` 段 SHA-256 | `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`（raw `0x1000` / size `4,063,232`） | `FINAL_RULING.md:99` / `ra2opt\__init__.py:24`（且是 `KNOWN_GAMEMD` 字典键 `:20`） |
| C07 `ddraw.dll` | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | 任务书 L85 `[转引]` |
| C03 签名时间 | `2001-10-31` | `ra2opt\__init__.py:25` / W36 §3.1.1 `[转引]` |
| C04 节表（该快照） | 5 段：`.text` / `.rdata` / `.data` / `.rsrc` / **`.detour`** | `FINAL_RULING.md §5.1:105` `[转引]` |

> **绝不**把这些值写成「S2 已实算/已定谳」。任务书 L79 明写「后续执行前仍须重新比对」（W36 §1.1 `[转引]`）。

---

## 2 · 判定程序（Lead 可直接执行，逐步给「命令 / 输出 / 判据 / 分支」）

全部步骤的**写域** = `lead\next_re_20261112_r02\W42_b_line_s2\EVIDENCE\` 或 Lead 另立的新卡目录；**只读** `ra2youli\` / `ra2bench\` / `ra2opt\` / `W21`–`W41`，不写游戏目录、不启动游戏、不 attach。

### P0 · 冻结只读副本（禁止改原盘） `[待运行验证]`

```
# 仅只读枚举；把候选字节复制到卡内副本后再做任何解析
Get-ChildItem -Path <每个已知根> -Filter gamemd.exe -Recurse -File |
  ForEach-Object {
    [pscustomobject]@{
      AbsPath    = (Resolve-Path $_.FullName).Path
      Volume     = $_.PSDrive.Name
      Length     = $_.Length
      Sha256     = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      ObservedAt = (Get-Date).ToString('o')
    }
  } | Export-Csv -NoTypeInformation <卡内>\EVIDENCE\candidates.csv
```

输出：`candidates.csv`（每行 = C13 绝对路径 + 卷标 + C08 + C01 + `observed_at`）。判据：**每行带绝对路径**，禁止「本机那份 1.001」式无路径指代（W38-S1 §5 R7 `[转引]`）。若需改字节，**先复制到卡内副本**再改。

### P1 · 对每个副本固定 PE 解析口径，取 L1 五判据 `[待运行验证]`

用**同一个** PE 解析器（W38-S1 C02 要求「口径固定」`[转引]`）；现成只读实现：`ra2opt\pe.text_section_sha256()`（`pe.py:364-380`）、`ra2opt\game.identity()`（`game.py:104-124`）、`ra2opt\pe.PEInfo`（`pe.py:80-101`）。本卡 `[本次读码]` 核对这些位置存在。

```
# 用 bundled python 逐副本跑（只读，不写游戏目录），stdout 留档
& <python> <卡内>\EVIDENCE\pe_probe.py --candidate-csv <卡内>\EVIDENCE\candidates.csv
```

`pe_probe.py`（S2 只给**规格**，不实现）须输出每份：
`C01` 整文件 SHA、`C02` `.text` raw SHA（记录 `raw_offset/raw_size`）、`C04`(`SizeOfImage`, `number_of_sections`, 每段 `{name, VA, virtual_size, raw_offset, raw_size, characteristics}`, `has_detour_section`)、`C08` 字节数、`C13` 绝对路径、`C03` `TimeDateStamp`。**任何一项不可读 ⇒ 该副本标 `CRITERION_UNREADABLE`，不参与定谳**（W38-S1 R1）。

### P2 · 三方对账 `[待运行验证]`

把 P1 结果与 §1.2 账面值逐字段精确比对（**禁止宽匹配/前缀哈希/文件名**，W38-S1 §3 硬规则）：
- 与任务书 L83-85（`73201cc0…` / `ddraw 85e0…`）；
- 与 `ra2opt\__init__.py:19-27` `KNOWN_GAMEMD`（`db264305…` 三重吻合）；
- 与 `FINAL_RULING.md §5` 三重吻合表。

输出 `reconciliation.tsv`：`{AbsPath, C01, C02, C04, C08, match_KNOWN_GAMEMD, match_TASKBOOK, match_FINAL_RULING, conflicts[]}`。`[静态推断]`：`73201cc0…` 与 `db264305…` 是**不同字节**这一事实必须保留为「多副本」，不得合并。

### P3 · 分组 + 多副本歧义消解 `[待运行验证]`

按 `(C01,C02,C04,C08)` 精确分组：
- 若**恰 1 组**且全部 L1 可读 ⇒ 进入 P4；
- 若 **≥2 组** ⇒ 输出 `MULTI_COPY_AMBIGUOUS`，要求显式 `--target-dir <realpath>` + `--baseline-id`（W38-S1 R7），**不自动挑「看起来最像」的那份**；Lead 未指定前，Track A 停在此步；
- 若**任一组**如需解释「为何整文件哈希不同」 ⇒ 用 `_candidate_+PE 头` 字段（`C04` 节表 / COFF Characteristics / `checksum`）区分「只改头字段」伪差异（W38-S1 C04 `[转引]`）；C03 时间戳**仅描述**，不得单独放行。

### P4 · `.detour` 段来源定谳（**题面移交项的核心**） `[待运行验证]`

题面已签发口径：**`db264305…` 含的是 Westwood Detours，属原生，不是污染**（`[转引·题面]`）。但 W38-S1 §5 R8 / 任务书 L89 要求的是**证据**，不能靠文档措辞直接放行。因此把「原生 vs 第三方注入」做成**可复算的 5 条判据**，全部落在字节上：

| 判据 | 可执行动作 | 「支持原生」的观测 | 弱/反证 |
|---|---|---|---|
| **D1 跨副本一致** | 对所有含 `.detour` 的副本，抽取该段 raw bytes 全量比对（P1 的 `C04.sections[]` 已给 `raw_offset/raw_size`） | ≥2 个**独立来源**副本的 `.detour` 段逐字节相同，且与「原始态」同现 ⇒ 与「随 exe 一起发行」一致 | 某副本独有 `.detour` ⇒ 疑第三方追加 |
| **D2 `.text` 完整性** | 核 `C02` == `c0368a17…`，且检 `AddressOfEntryPoint` 仍在 `.text`、IAT 未被改指向 `.detour` | 代码段被引擎自己登记的值精确命中、入口未重定向 ⇒ 不是「靠改 `.text` 注入 hook」 | `.text` 失配 / 入口改道 ⇒ 疑第三方 Detours |
| **D3 零售介质对照（决定性）** | 从**外部零售来源**（原盘镜像 / 官方发行件）取同一 YR 1.001 的 `gamemd.exe`，跑 P1 比较节表 | 零售原版**也**带同字节 `.detour` ⇒ 原生定谳成立 | 零售原版不带 ⇒ 判第三方追加；**无外部介质 ⇒ 本项 = 证据不足，`undetermined`** |
| **D4 元数据侧证（弱）** | `C03` `TimeDateStamp`、VS_VERSION_INFO、嵌入签名；`ra2opt\__init__.py:25` 的 phrasing 是「含第三方 Detours 段（.detour）」、W38 `VERSION_GUARD_CONTRACT.md:22` 是「Westwood Detours，原生」、FINAL_RULING §5.1 写「已被第三方追加过 .detour 段」 | 只作**冲突排查线索**，处置该措辞分歧见下 | W38-S1 C03 规定「不得单独放行」 |
| **D5 措辞分歧登记** | 把 D1–D4 的观测与三处措辞并列写入 `provenance.detour_classification` | 取值 ∈ `{westwood_native, third_party_injected, undetermined}` + 每条 `file:line` 证据 | **禁止以文档措辞替代字节证据**；本卡不选边，见 `DISAGREE.md` D-W42-13 |

**处理规则（题面要求明确写）** `[静态推断]`：
1. `.detour` **属原生** ⇒ 登记 `provenance.contains_native_detour = true`；`has_detour_section = true` 本身 **不构成** `MISMATCH`、不构成 `PATCHED_BY_THIRD_PARTY`（W38-S1 §5 R8 / §3 步骤 4 `[转引]`）。仅当基线 `provenance` 声明「不含第三方段」而实测与之冲突时，才判 `MISMATCH`。
2. 「原生」**不**等价于「干净零售金标准」：即使 D1–D3 全支持原生，`RETAIL_ORACLE` 仍要走 §3 的 G1–G6；L89 的外部来源证据是独立门槛。
3. 要让这就是「官方未经修改」还必须在基线 `provenance.source` 里写**来源链**（§3 G1），而 `is_clean_retail_gold` 仍须 `false`（§0 约束 2）。

### P5 · Track A 签发 `TARGET_BASELINE`（可执行的落盘模板） `[待运行验证]`

**仅当** P0–P4 全部完成、L1 全可读、多副本歧义已由 Lead 显式 `--target-dir` + `--baseline-id` 消解后，Lead 才签 `adjudicated=true`。模板（`schema_version="w38-s1-1"`、`$defs/baselineEntry`，**`<…>` 必须由 P1 实算回填，§1.2 账面值只作对账口径**）：

```json
{
  "id": "<baseline-id，例如 yr1001-detour-native-<abs-path-hash前8>>",
  "adjudicated": true,
  "provenance": {
    "source": "<零售/备份链：从哪个介质、经哪几步只读复制、由谁、何时>",
    "contains_native_detour": true,
    "detour_classification": "westwood_native | third_party_injected | undetermined",
    "detour_evidence": ["<D1..D4 的 file:line / stable 观测>"],
    "is_clean_retail_gold": false,
    "adjudicated_by": "Lead",
    "adjudicated_at": "<ISO8601>"
  },
  "identity": {
    "c01_full_sha256": "<P1 实算 64hex>",
    "c02_text_sha256": "<P1 实算 64hex>",
    "c04_size_of_image": "<P1 实算 int>",
    "c04_number_of_sections": "<P1 实算 int>",
    "c04_has_detour_section": true,
    "c04_sections": [ {"name":"<...>","virtual_address":0,"virtual_size":0,"raw_offset":0,"raw_size":0,"characteristics":0} ],
    "c08_size": "<P1 实算 int>",
    "c13_abs_path": "<Resolve-Path 的绝对路径>"
  },
  "l2_edition": {"ddraw_sha256":"<C07>", "c09_mix_entries":"<...>", "c10_csf_mapselmd":"<...>"},
  "allowed_write_entries": ["E1","E2a","E2b","E3","E5"]
}
```

**判签（机检）**：① `adjudicated===true`；② `is_clean_retail_gold===false`；③ `contains_native_detour` 与 P4 结论一致；④ 所有 L1 字段与 P1 逐字段相等；⑤ `c13_abs_path` 是 P0 `candidates.csv` 里存在的一行；⑥ `provenance.source` 非空且可追。**任一不满足 ⇒ 不签**，回 `UNKNOWN` + `NO_ADJUDICATED_BASELINE`。

### P6 · Track B 判 `RETAIL_ORACLE`（干净零售金标准） `[待运行验证]`

**六门全通过**才允许标注 `RETAIL_ORACLE_ELIGIBLE=true`；任一门 `FAIL`/`UNKNOWN` ⇒ 整体 `UNDETERMINED`、不写「是金标准」：

| 门 | 判据 | 当前盘面证据（本卡不实算） |
|---|---|---|
| **G1 来源链** | 有外部零售介质（原盘镜像 / 官方发行件）的哈希与保管链；任务书 L89 要求「另行确认来源与指纹」 | **本机只有副本，无介质证据 ⇒ 预期 FAIL/UNKNOWN** |
| **G2 独立权威指纹** | 与「不是该样本自身」的独立权威登记值逐字节吻合；禁止自证 | 需 Lead 提供外部登记 |
| **G3 无第三方组件** | `ra2opt\game.components()`（`game.py:127-142`）无 cnc_ddraw / ares / phobos / syringe / ra2opt 留痕 | `[待运行验证]` |
| **G4 零售版节表** | 与 G1 介质的节表一致（含 `.detour` 若原生）；C04 `SizeOfImage` / `checksum` 等 | `[待运行验证]` |
| **G5 `ddraw.dll`** | C07 为官方 wrapper 而非 cnc-ddraw（任务书 L85 只给一个哈希，未定性） | `[待运行验证]` |
| **G6 双源互证** | ≥2 个独立零售介质给出同一字节 | `[待运行验证]` |

**与 `FINAL_RULING.md §5.1` 对账** `[转引]`：该文件已裁「`REWRITE_ROADMAP.md:163` 要求干净零售 1.001 作 oracle — 该需求**至今未被满足**，`orig/` 快照不能充当它」。本程序的作用是给 Lead 一条**可复跑的路径去满足或继续明确不满足**，而不是翻案。若 G1 仍缺，程序输出应保持 `RETAIL_ORACLE=UNDETERMINED`，并在 `PATCH_CONTRACT.md` 版本矩阵该行标 `[待运行验证]`（W36 §3.1.3 第 4 条 `[转引]`）。

---

## 3 · 程序输出清单（Lead 执行后应得到的东西）

| 工件 | 内容 | 防误读约束 |
|---|---|---|
| `EVIDENCE\candidates.csv` | P0 全副本绝对路径 + C01/C08/C13/observed_at | 无路径指代 |
| `EVIDENCE\pe_probe.stdout.txt` + `exit_codes.txt` | P1 每副本 L1 五判据 + 不可读清单 | 不得沉默跳过不可读 |
| `EVIDENCE\reconciliation.tsv` | P2 三方对账 + conflicts[] | 禁宽匹配 |
| `EVIDENCE\detour_classification.json` | P4 D1–D5 + `detour_classification` + 三处措辞分歧登记 | 不能以措辞替代字节 |
| `EVIDENCE\TrACK_A_signoff.md` | P5 已签/未签 + 6 条机检结论 | `is_clean_retail_gold=false` |
| `EVIDENCE\TRACK_B_gates.json` | P6 G1–G6 逐门 `PASS/FAIL/UNKNOWN` + 总判定 | 期望 `UNDETERMINED` 时不得写 PASS |
| `BASELINE.json`（Lead 另立卡写域） | 仅 Track A 的 `adjudicated=true` 条目 | 不得塞入 `RETAIL_ORACLE` |

---

## 4 · 与 W38-S1 契约的接口（不重造）

- `guard_state` 的计算仍按 W38-S1 §3 `classify()`；本程序**只**负责给它 `BASELINE.json` 里的一条 `adjudicated=true` 条目，**不改**判定算法、不改 13 判据、不改三态×7 写入口决策表。
- `provenance.is_clean_retail_gold: const false` 是 **S1 schema 既有约束**；本程序明确 `RETAIL_ORACLE` 不进 `baselineEntry`（§0 约束 2），如 Lead 认为需要，须走 `DISAGREE.md` D-W42-3 的 schema 扩展流程，属 S3。
- 「每次写入口调用前重新实算 L1」（W38-S1 R9）仍适用；本程序只做**一次性定谳**，不复用为运行时缓存。
- 「不得把契约完备写成能力已具备」：本文件是**判定程序**，程序跑完并签完 `BASELINE.json` 之前，`guard_state` 仍应落 `UNKNOWN` + `NO_ADJUDICATED_BASELINE`（W38-S1 R6）。

---

## 5 · 纪律复核

- 纯离线：未启动游戏、未 attach、未写 `ra2youli`、未改 `ra2forge/`、未动 `W21`–`W41`、`git` 只读。
- 未写生产代码：`pe_probe.py` 是**给 Lead 的规格**（本卡未创建、未运行）；本卡唯一运行的脚本是 `EVIDENCE\s2_shape_check.py`（只读 JSON 结构自检）。
- 未实算任何哈希：§1.2 全部 `[转引]`，P0–P6 全部 `[待运行验证]`。
- 三处 `.detour` 措辞分歧（题面/W38 主契约「原生」 vs `ra2opt\__init__.py:25`/W38 `DISAGREE.md` D-W38-11/FINAL_RULING §5.1「第三方」）**如实并列**，不替 Lead 选边：`DISAGREE.md` D-W42-13。
