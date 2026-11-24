# W47 · UNKNOWNS.md · 判不了 / 缺什么 / 待运行验证

> 纪律：**若某门判不了，写 UNKNOWN 并说明缺什么，不为了凑成 PASS 而降低判据**。本文逐条列出本卡**没有**闭合的项；已闭合的不写在这里（见 `BASELINE_ADJUDICATION_RESULT.md`）。
> 总判定仍 `UNDETERMINED`；`is_clean_retail_gold=false`（D4 const false）；无任何条目自称零售金标准。

---

## A · 六门中判不了的四门（P6）

### U-W47-1 · G1 来源链 = `UNKNOWN`
- **缺什么**：① 外部零售介质本体（YR 1.001 原盘镜像 / 官方发行件 / 官方补丁分发包）；② 该介质的 SHA-256；③ **保管链**（从哪个介质、经哪几步只读复制、由谁、何时）。
- `[本次实测]` 本卡在仓库 582,702 个文件中检索 `.iso/.cue/.mdf/.nrg/.img/.vhd/.vhdx/.cab/.7z/.rar` = **0 个**（`EVIDENCE\media_paths.txt` 为空）；按文件名 `yuri|disc[0-9]|retail|1001|1.001` 命中的全是 `.mimosa` 事件日志 JSON，无介质。
- **为什么不写 FAIL**：「枚举范围内没有」不等于「本机任意位置（其他盘符、光驱、未挂载镜像）都没有」；且保管链是**文档/流程证据**，本卡纯离线无法取得。判据要求**正向证据**，故 UNKNOWN。
- **如何闭合**：Lead 提供外部介质 + 其 SHA-256 + 可追的复制/保管记录，再跑 P1 与本卡 C01/C02/C04 逐字段比对。
- `[本次读码]` `RE-N00\BASELINE.json:59` 亦记「来源/『官方未修改原版』身份未证」。

### U-W47-2 · G2 独立权威指纹 = `UNKNOWN`
- **缺什么**：一个**不是由本机这批样本算出**的独立权威登记值（发行商公布的校验和、可信第三方版本库等）。
- `[本次读码]` 现存登记全部是**仓内自证**：`ra2opt\__init__.py:19-27` `KNOWN_GAMEMD`（`db264305…`）、`FINAL_RULING.md §5:93-101`（从 `ra2youli\.ra2opt\orig\` 实算）、`RE-N00\BASELINE.json:53-71`、`W7_load_baseline\load_baseline_probe.py:70-79`。它们的输入都是本机同一批样本。
- **不得计入**：把 `KNOWN_GAMEMD` 的 `db264305…` 当「独立权威」就是 W42 §2 P6 G2 明令禁止的**自证**。
- **如何闭合**：Lead 提供外部独立登记值原文与出处，再与本卡 C01/C02/C08 逐字节精确比对（禁前缀/禁宽匹配）。

### U-W47-3 · G4 零售版节表 = `UNKNOWN`
- **缺什么**：G1 介质**自身**的节表 / `SizeOfImage` / `checksum`，用于对照。
- `[本次实测]` 我方已测：5 段（`.text/.rdata/.data/.rsrc/.detour`）、`SizeOfImage=7,954,432 (0x796000)`、`checksum=0`，113/114 份逐字段一致，唯一例外 `gamemd_vsize0.exe` 对抗件。
- **为什么仍然 UNKNOWN**：跨副本**内部一致** ≠ 与**外部零售介质**一致。W42 G4 判据写死「与 G1 介质的节表一致」，没有对照物就无法评估。
- **如何闭合**：取得 G1 介质后跑同一套固定 PE 解析器，逐字段比对（含 `.detour` 是否原生同字节）。

### U-W47-4 · G6 双源互证 = `UNKNOWN`
- **缺什么**：≥2 个**物理独立**的零售介质（各带保管链）。
- `[本次实测]` 95 份 `73201cc0…` + 15 份 `db264305…` + 仓库外 `D:\Red2\ra2youli\gamemd.exe`（仍是 `db264305…`），共 111 个不同父目录——**都是同两条字节身份的本地复制品**，出自同一条本地来源链。
- **不得降低判据**：把 95 份副本当「2 个独立来源」会直接违反 G6；副本数 ≠ 独立介质数。
- **如何闭合**：两个独立零售介质各自给出同一字节 + 各自保管链。

> **已闭合、不列为 UNKNOWN 的两门**：G3 = **FAIL**（`game.components()` 实测 cnc_ddraw 等第三方组件在位）；G5 = **FAIL**（C07 `85e0f7d5…` 经字节+版本资源定性为 cnc-ddraw 7.1.0.0）。二者是**正向失败证据**，不是「判不了」。

---

## B · `.detour` 决定性判据

### U-W47-5 · D3 零售介质对照（决定性）= `UNDETERMINED`
- W42 §2 P4 把 D3 定为**决定性**判据：外部零售原版是否也带同字节 `.detour`。本卡无外部介质 ⇒ 无法执行。
- **后果（必须如实说）**：D1（112 份跨副本一致）+ D2（`.text` 完整、入口在 `.text`、IAT 未改道）**单独不能定谳「原生」**。`detour_classification = westwood_native` 是按 `LEAD_DECISIONS_W42.md D2` 的**默认裁决**保留，不是本卡凭字节证明的。
- **如何闭合**：取得 G1 介质后重跑 D3；若零售原版不带 `.detour`，应改判 `third_party_injected` 并回写 `DISAGREE.md`。

### U-W47-6 · 无签发者级密码学证据
- `[本次实测]` 114/114 份 `IMAGE_DIRECTORY_ENTRY_SECURITY` size = **0**，**无 Authenticode 嵌入签名**；`VS_VERSION_INFO` 虽 114/114 存在，但只能描述，不能证明 Westwood 来源（W38-S1 C03「不得单独放行」）。
- **缺什么**：可验证的发行商签名 / 官方校验和公布件。与 U-W47-2 同源。

---

## C · Track A 签发（P5）

### U-W47-7 · `TARGET_BASELINE` **未签发**（本卡只给推荐）
- `[本次实测]` P3 = `MULTI_COPY_AMBIGUOUS`（6 组）。W42 §2 P3 要求 Lead 显式 `--target-dir <realpath>` + `--baseline-id`，**禁止自动挑最像的那份**；P5 机检第 ⑥ 条要求 `provenance.source` 非空且可追。
- **缺什么**：① Lead 的 `--target-dir` / `--baseline-id`；② 一条**可追的来源链**（离线只能用本地复制链，不能是零售来源链，见 U-W47-1）；③ 签发动作本身（本卡不是 Lead）。
- **当前状态**：`adjudicated_target_baseline_signed=false`；`guard_state` 按 W38-S1 R6 仍应落 `UNKNOWN` + `NO_ADJUDICATED_BASELINE`。

### U-W47-8 · 写靶目录在「写入时刻」究竟是哪条字节身份，未定
- `[本次实测]` 盘上同时存在 `73201cc0…`（95 份，写靶当前态）与 `db264305…`（15 份，pre-ra2opt 态），两者只差 2 个 PE 头字节。
- **未定**：将来是否会对 `ra2youli` 执行 `ra2opt restore`（一旦执行，写靶字节变为 `db264305…`，已登记的 `TARGET_BASELINE` 会 `MISMATCH`）； Lead 也未指定基线应取「安装战役补丁前的现状」还是「pre-ra2opt 原始态」。
- **如何闭合**：Lead 明确基线语义 + 签发前在精确路径上重跑 P0/P1（W38-S1 R9：运行时每次写入口调用前重新实算 L1，本卡结果**不得**复用为运行时缓存）。

---

## D · 边界 / 时点 / 范围

### U-W47-9 · W45 并发活跃 ⇒ 枚举为时点快照
- `[本次实测]` 观察到 `W45_b_line_equivalence\tools\w45_dual_track.py --phase run --arms A1,A2,B1` 正在运行；20:41 首次枚举 1624 份 `gamemd*.exe`，21:01 用 `-Filter` 枚举为 1702 份 ⇒ 仓库在**变化**。
- **未定**：W45 沙盒的最终字节状态、以及它是否会在本卡交付后继续新增/改写副本。本卡对 W45 沙盒只做只读哈希，**不对 W45 的结论作任何判断**。
- 关键写靶 `ra2youli\gamemd.exe` / `ra2bench\gamemd.exe` mtime 稳定在 2026-09-25 16:10:48，但签发前须重算。

### U-W47-10 · 「本机所有物理副本」的边界
- `[本次实测]` 本卡枚举了 `D:\Project\ra2-campaign-forge` 全树 + 显式加入的 `D:\Red2\ra2youli\gamemd.exe`（由 `W42 §1.1` / `FINAL_RULING §5.1:115` 点名）。
- **未枚举**：其他盘符、光驱、未挂载镜像、系统目录、网络位置。因此 U-W47-1 不能写 FAIL。
- `[本次实测]` `gamemd*.exe` 中 0 个 reparse point / symlink；但**硬链接**未做完整物理 inode 归并（`st_dev/st_ino/st_nlink` 已记录在 `candidates.csv`，未据此塌缩路径数）。

### U-W47-11 · 4 个对抗 fixture 的精确改写位点未逐一刻画
- `[本次实测]` 已知：4 份与主流共享 `.text`/`SizeOfImage`/`C03`；`gamemd_vsize0.exe` 节表不同；`gamemd_gi3_tampered.exe` 与 `gamemd_corrupt_window.exe` 的 `.detour` raw SHA 不同；`gamemd_corrupt_window.exe` 的 PE 头是 orig 型（`dllchar=0` / `stack=1MB`）。
- **未做**：逐字节 diff 定位每份的全部改写偏移。它们属测试夹具、不参与定谳，故登记为未展开，不影响结论。

### U-W47-12 · 第二份 `ddraw.dll` 字节身份的保管链未追
- `[本次实测]` `1fd305a99eb5b75e10b50ad7e90474bfaccdcce1137c5f00ea97c2557e3bf294`（11 份，`FileVersion=4.4.7.0`）同属 cnc-ddraw 序列（`ra2opt\__init__.py:34-41`），但其来源/复制链未追。不影响 G5 = FAIL（C07 已定性）。

### U-W47-13 · `W38 VERSION_GUARD_CONTRACT.md:22` 未直读
- `[转引]` 该条「Westwood Detours，原生」经 `W42 §2 P4 D4` 转引，本卡未打开原文件核对逐字措辞。D5 已如实标 `[转引]`，未按 `[本次读码]` 冒充。

---

## E · 明确不在本卡范围内（`[待运行验证]`）

### U-W47-14 · 零真机
- 未启动 `gamemd.exe` / `ra2md.exe` / `YURI.exe` / loader；未 attach；未读活进程内存；未跑 `ra2opt apply/restore`；未部署任何补丁。
- 一切**行为对拍**（改造前后 `RETAIL_ORACLE` 对照、启动/进图、五臂真机结论）均 `[待运行验证]`，由持锁的 W45 / Lead 负责。本卡只判**磁盘字节**。
- 按 W42 §2 P6 末段：`PATCH_CONTRACT.md` 版本矩阵「干净零售 1.001 oracle」该行应继续标 `[待运行验证]`（本卡不改他人文档）。

---

## 汇总表

| 编号 | 项 | 状态 | 缺什么（一句话） |
|---|---|---|---|
| U-W47-1 | G1 来源链 | UNKNOWN | 外部零售介质 + SHA-256 + 保管链 |
| U-W47-2 | G2 独立权威指纹 | UNKNOWN | 非自证的外部权威登记值 |
| U-W47-3 | G4 零售版节表 | UNKNOWN | G1 介质自身的节表/`SizeOfImage`/`checksum` |
| U-W47-4 | G6 双源互证 | UNKNOWN | ≥2 个独立零售介质 |
| U-W47-5 | D3 `.detour` 决定性对照 | UNDETERMINED | 外部零售介质的 `.detour` 字节 |
| U-W47-6 | 发行商签名 | 无 | Authenticode / 官方校验和公布件 |
| U-W47-7 | P5 签发 | 未签 | Lead 的 `--target-dir`+`--baseline-id` + 可追来源链 |
| U-W47-8 | 写入时刻的写靶字节身份 | 未定 | Lead 对基线语义的决定 + 签发前重算 |
| U-W47-9 | W45 并发 / 时点 | 快照 | W45 结束后复核 |
| U-W47-10 | 全机枚举边界 | 部分 | 其他盘符/光驱/镜像 |
| U-W47-11 | 对抗 fixture 改写位点 | 未展开 | 非必要 |
| U-W47-12 | `1fd305a9…` 保管链 | 未追 | 非必要 |
| U-W47-13 | `W38 …:22` 逐字 | `[转引]` | 直读该文件 |
| U-W47-14 | 真机行为 | `[待运行验证]` | W45/Lead 持锁执行 |

**不为凑 PASS 降判据的显式声明**：G3/G5 有正向失败证据故判 FAIL；G1/G2/G4/G6 缺正向证据故判 UNKNOWN；61 个「`components()` 全 false」的目录是只有 `gamemd.exe` 的夹具目录，**未**被拿来把 G3 抬成 PASS；95 份本地副本**未**被算作 G6 的 2 个独立来源；`KNOWN_GAMEMD` **未**被算作 G2 的独立权威。
