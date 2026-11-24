# W47 · BASELINE_ADJUDICATION_RESULT.md · Track B 实算裁决

> 卡：`W47_baseline_adjudication`｜承接 `W42_b_line_s2\BASELINE_ADJUDICATION.md` §2 **P0–P6 判定程序**｜2026-11-13｜**纯离线只读**
> 只读规格：`W42...BASELINE_ADJUDICATION.md`（程序/P4 D1–D5/P6 G1–G6）、`W43_b_line_s3\TRACK_B_gates.json`（现状）、`REVIEW\LEAD_DECISIONS_W42.md` **D2 / D4**、`docs\re\baseline_integrity_note.md:118-144`
> 纪律：**不启动 `gamemd.exe`、不 attach、不读活进程内存、不取 `.game_instance.lock`**（仅列过它的文件名/大小/mtime 元数据；W45 正在持锁跑真机，`w45_dual_track.py --phase run --arms A1,A2,B1`，本卡完全未碰）；不写 `ra2youli`、不改 `ra2forge/`、不动 `W21`–`W46`、git 只读。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。本文所有哈希、PE 字段、节表、段字节均为 `[本次实测]`，**不再标 `[转引]`**。

---

## 0 · 速览

| 项 | 结论 |
|---|---|
| P0–P6 | **全部实际执行完成**（P5 仅到「推荐」，未签发） |
| 候选物理副本 | **1703** 份 `gamemd*.exe` 路径（含 1 份仓库外 `D:\Red2\...`），1703/1703 哈希成功、0 不可读 |
| 真实 PE32 游戏二进制 | **114** 份，全部 4,825,360 B；其余 1589 份为 0–70 B 惰性/对抗测试占位件 |
| 不同整文件 SHA-256 | **21** 个（PE 内 6 个 + 惰性件 15 个） |
| P3 分组 | **6 组 ⇒ `MULTI_COPY_AMBIGUOUS`**；Track A 按 W42 §2 P3 **停在此步**，本卡**不签** `adjudicated=true` |
| `db264305…` | `[本次实测]` **本机存在**（15 份），且 `D:\Red2\ra2youli\gamemd.exe` 由本卡独立复算命中 —— `FINAL_RULING.md §5.1:115` 的「Lead 未复算/标未验」闭合 |
| `.detour` | `[本次实测]` 114/114 `Characteristics=0xC0000040`，**无 `MEM_EXECUTE`**；独立解析器复核通过；`detour_classification = westwood_native`（D2 默认），**D3 仍 undetermined** |
| G1–G6 | G1 **UNKNOWN**、G2 **UNKNOWN**、G3 **FAIL**、G4 **UNKNOWN**、G5 **FAIL**、G6 **UNKNOWN** |
| overall | **`UNDETERMINED`** / `retail_oracle_eligible=false` / **`is_clean_retail_gold=false`（D4 const false）** |
| TARGET_BASELINE 推荐 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` = `73201cc0…`（**推荐 ≠ 签发，≠ 干净零售金标准**） |

**与 W43/W46 的差异**：那两张卡自述「未实算任何哈希」，六门全 `UNKNOWN`、全部 `[待运行验证]`。本卡把可算的全部实算，六门由「6×UNKNOWN」细化为「**2 FAIL + 4 UNKNOWN**」，总判定仍 `UNDETERMINED`——**是证据升级，不是翻案**。

---

## 1 · 执行的规格与口径

| 来源 | 本卡取用的内容 |
|---|---|
| `W42_b_line_s2\BASELINE_ADJUDICATION.md` | §0 R-A `TARGET_BASELINE` / R-B `RETAIL_ORACLE` 双轨；§2 P0–P6；P4 表 D1–D5；P6 表 G1–G6；§3 输出清单；§5 纪律 |
| `W43_b_line_s3\TRACK_B_gates.json` | 现状：`adjudicated:true` / `is_clean_retail_gold:false` / G1–G6 全 `UNKNOWN` / `overall UNDETERMINED` / `detour_classification` 默认 `westwood_native` |
| `REVIEW\LEAD_DECISIONS_W42.md` **D2** | 裁决 `westwood_native`；`Characteristics=0xC0000040` **无执行位**；保留 D1–D5 字节判据；「原生 ≠ 干净零售金标准」 |
| `REVIEW\LEAD_DECISIONS_W42.md` **D4** | 维持 `provenance.is_clean_retail_gold: const false`；第二轨放**独立工件**，**不扩** `BASELINE.json` schema |
| `docs\re\baseline_integrity_note.md:118-144` | `.detour` 为 Westwood 2001 构建原生 Microsoft Detours 1.x；VA `0xB93000`、raw `0x497000`、vsize `0x2718`、rawsize `0x3000`、首 32 字节 `"Dtr\0"` 签名 |

**固定 PE 解析口径（W42 P1「用同一个 PE 解析器」）**：`ra2opt\pe.py:80-101` `PEInfo`、`:170-246` `read()`、`:364-380` `text_section_sha256()`；`.text` 一律用 `raw(SizeOfRawData)` 口径（`baseline_integrity_note.md:65` 硬规约）。**另写一套独立的 `struct.unpack_from` 解析器**做交叉验证与 `.detour` 独立复核（见 §6）。两条路径 C02 结果 **0 处不一致**。

**枚举方法**：仓库共 **582,702** 个文件，Python `os.walk` 双趟在此规模上不可用（v1 两次尝试均被终止，见 `EVIDENCE\exit_codes.txt`）。改用 PowerShell 文件系统级 `-Filter`（`Get-ChildItem -Recurse -File -Filter '*gamemd*.exe'` / `'ddraw.dll'`，7.8 s / 5.2 s），路径清单落 `EVIDENCE\gamemd_paths.txt` / `ddraw_paths.txt`，Python 只消费清单、按整文件 SHA-256 缓存 PE 解析（114 份同尺寸副本塌缩成 21 个字节身份，3.0 s 完成，`EXIT=0`）。

---

## 2 · P0 · 候选枚举（每一份的路径 / 大小 / SHA-256 / mtime）

`[本次实测]` **1703 份逐行全表**：`EVIDENCE\CANDIDATE_ENUMERATION.md`（A 段 114 份真实 PE + B 段 1589 份惰性件，每行含绝对路径、字节数、完整 64-hex SHA-256、mtime、字节身份组）；机器可读同源数据在 `EVIDENCE\candidates.csv`（1703 行）与 `BASELINE_CANDIDATES.json` 的 `candidates` + `non_candidate_inert_fixtures.items`。

### 2.1 规模分布 `[本次实测]`

| 大小(B) | 份数 | 性质 |
|---:|---:|---|
| 4,825,360 | **114** | 真实 PE32 游戏二进制（`gamemd.exe` / `pristine_gamemd.exe` / `.ra2opt\orig\gamemd.exe` / 4 件对抗 fixture） |
| 9 | 963 | 惰性占位（`"No Name\0"` 类） |
| 35 | 465 | 惰性占位 |
| 16 / 41 / 42 / 53 / 70 / 34 / 29 / 23 / 6 / 3 / 1 / 0 / 7 | 161 | 惰性/对抗测试占位件 |
| **合计** | **1703** | 21 个不同整文件 SHA-256 |

无 reparse point / symlink（`-Filter` 枚举中 0 个 ReparsePoint）；按绝对路径去重。

### 2.2 关键副本（完整字段；其余 1691 份见全表）

| 绝对路径 | 大小(B) | SHA-256 | mtime(本地 +08:00) | 组 | 角色 |
|---|---:|---|---|---:|---|
| `D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe` | 4,825,360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 2026-09-25 16:10:48 | G2 | 分析镜像 |
| `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` | 4,825,360 | `73201cc0…f67476` | 2026-09-25 16:10:48 | G2 | **写靶目录；推荐 TARGET_BASELINE** |
| `D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe` | 4,825,360 | `db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa` | 2026-09-25 16:10:48 | G3 | ra2opt 原始态备份 |
| `D:\Red2\ra2youli\gamemd.exe`（**仓库外**） | 4,825,360 | `db264305…55aa` | 2020-11-30 15:56:40 | G3 | ZCode 报告副本；`FINAL_RULING §5.1:115` 标「未复算」，**本卡已独立复算命中** |
| `…\W27_campaign_live\sandbox_game\gamemd.exe` | 4,825,360 | `73201cc0…f67476` | 见全表 | G2 | 真机卡 sandbox |
| `…\W27_campaign_live\sandbox_game\.ra2opt\orig\gamemd.exe` | 4,825,360 | `db264305…55aa` | 见全表 | G3 | 真机卡 orig 快照 |
| `…\W27_campaign_live\out\pristine_gamemd.exe` | 4,825,360 | `73201cc0…f67476` | 见全表 | G2 | pristine 留档 |
| `…\W44_c_line_e2e\baseline_clean\gamemd.exe` | 4,825,360 | `73201cc0…f67476` | 见全表 | G2 | 基线净目录 |
| `…\W44_c_line_e2e\baseline_clean\.ra2opt\orig\gamemd.exe` | 4,825,360 | `db264305…55aa` | 见全表 | G3 | 基线净目录 orig |
| `…\W45_b_line_equivalence\sandbox_A1\.ra2opt\orig\gamemd.exe` | 4,825,360 | `db264305…55aa` | 见全表 | G3 | **W45 活跃卡** sandbox（只读哈希，未改动） |
| `.tmp\review5\inj_data\gamemd_overlay_flip.exe` | 4,825,360 | `6a061d9d56798ff7b85f3f3a466dd29d1c1e355978905366977f90a7e1ee9856` | 2026-11-10 13:44:51 | G1 | 对抗 fixture（非候选） |
| `out\re_work\work_chain\CONTINUE_20261003\main\worker\adversarial\fixtures\gamemd_vsize0.exe` | 4,825,360 | `36a7a63701bd5401f88aff85ee18e47c7b5a0f6a115724b3a791a395d0872d7c` | 见全表 | G4 | 对抗 fixture（非候选） |
| `out\re_work\work_chain\CONTINUE_20261003\main\worker\repro\fixtures\gamemd_gi3_tampered.exe` | 4,825,360 | `47b80e4909fbaa72686ce88bef661738a03305780ed1f5bea014e443b3c7d303` | 见全表 | G5 | 对抗 fixture（非候选） |
| `out\re_work\work_chain\EXP001\exp_p1b_guard_spec\fixtures\gamemd_corrupt_window.exe` | 4,825,360 | `3b1d71399f3fb36f689133f5a697869d3ae740846c74e9cd44e4a7f21b8086a3` | 见全表 | G6 | 对抗 fixture（非候选） |

**时点声明 `[本次实测]`**：枚举于 2026-11-13 ~21:01+08:00、哈希于 21:10:55+08:00。W45 真机卡并发活跃并持续创建 sandbox 副本（20:41 首次枚举 1624 份 → 21:01 为 1702 份）。故本表为**时点快照**；`ra2youli\gamemd.exe` 与 `ra2bench\gamemd.exe` 的 mtime 稳定在 2026-09-25 16:10:48（UTC `2026-09-25T08:10:48.595117+00:00`，与 `RE-N00\BASELINE.json:58,69` 同值）。

---

## 3 · P1 · 固定 PE 解析器 L1 五判据（逐副本实算）

`[本次实测]` 114 份 PE32 全部可读，**无 `CRITERION_UNREADABLE`**。以下为两个主态代表值（完整 114 份逐副本输出：`EVIDENCE\pe_probe.stdout.txt`；机器可读：`EVIDENCE\probe_data.json`、本文 `BASELINE_CANDIDATES.json` 的 `candidates[]`）。

| L1 判据 | `db264305…`（G3 原始态，15 份） | `73201cc0…`（G2 留痕态，95 份） | 口径 |
|---|---|---|---|
| C01 整文件 SHA-256 | `db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 全文件流哈希 |
| C02 `.text` SHA-256 | `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738` | 同左 | `raw(SizeOfRawData)`：`raw_offset=0x1000`、`raw_size=4,063,232 (0x3E0000)` |
| C03 `TimeDateStamp` | `0x3BDF544E` = `2001-10-31T01:30:54Z` | 同左 | COFF 文件头偏移 +4；本地 +08 为 09:30:54 |
| C04 `SizeOfImage` | `7,954,432 (0x796000)` | 同左 | Optional Header +56 |
| C04 `NumberOfSections` | `5` | 同左 | `.text/.rdata/.data/.rsrc/.detour` |
| C08 字节数 | `4,825,360` | 同左 | `os.stat().st_size` |
| C13 绝对路径 | 见 §2.2 / 全表 | 同左 | `os.path.abspath` |
| COFF `Characteristics` | `0x032F`（LAA 位 0x20 出厂已置） | 同左 | `ra2opt/pe.py:46-51` 口径 |
| `ImageBase` | `0x00400000` | 同左 | |
| `AddressOfEntryPoint` | `0x003CD80F`（落在 `.text` 内） | 同左 | |
| `DllCharacteristics` | `0x0000` | `0x0020` | 差异字节 ① |
| `SizeOfStackReserve` | `1,048,576 (1 MB)` | `4,194,304 (4 MB)` | 差异字节 ② |
| `SizeOfStackCommit` / `HeapReserve` / `HeapCommit` | `4,096 / 1,048,576 / 4,096` | 同左 | |
| `CheckSum` | `0` | `0` | 用户态 exe 加载器忽略 |
| `Subsystem` / `SectionAlignment` / `FileAlignment` | `2 / 4,096 / 4,096` | 同左 | |
| `NumberOfRvaAndSizes` | `16` | 同左 | |
| `VS_VERSION_INFO` | 有（114/114） | 同左 | |
| 嵌入签名（Authenticode） | **无**（cert table size = 0，114/114） | 同左 | D4 见 §6 |

### 3.1 节表（113/114 份完全相同；完整逐段哈希见 `EVIDENCE\pe_probe.stdout.txt`）`[本次实测]`

| # | 段名 | VA(RVA) | VirtualSize | PointerToRawData | SizeOfRawData | Characteristics | 段 raw SHA-256 |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | `.text` | `0x001000` | 4,060,045 (`0x3DF38D`) | `0x001000` | 4,063,232 (`0x3E0000`) | `0x60000020` | `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738` |
| 2 | `.rdata` | `0x3E1000` | 196,724 | `0x3E1000` | 200,704 (`0x31000`) | `0x40000040` | `efce5b84ebf6fbb2dce20c3a065b35c5681e41fdd5185b10fcde17d21974d2d7` |
| 3 | `.data` | `0x412000` | 3,570,660 | `0x412000` | 442,368 (`0x6C000`) | `0xC0000040` | `c67eaa0fffa56fe7f2ef2eaaccfd1e1c7e0b5078cc36666a9c674323d7d5d465` |
| 4 | `.rsrc` | `0x77A000` | 98,600 | `0x47E000` | 102,400 (`0x19000`) | `0x40000040` | `02259fd60cbdbd5b7526e51618f4f7058837bda1a4c8f3df1d93481d97a5a31b` |
| 5 | **`.detour`** | `0x793000` | 10,008 (`0x2718`) | `0x497000` | 12,288 (`0x3000`) | **`0xC0000040`** | `5caa9431b4fca0b07f12e1d2154d4b36bb01649c6ce7357f8249b93a616a4ab5` |

> 与 `docs\re\baseline_integrity_note.md:122-131` 的 VA `0xB93000`（= `ImageBase 0x400000` + RVA `0x793000`）、`vsize 0x2718`、`rawsize 0x3000`、首 32 字节 **逐字节吻合**。
> `[本次读码]` 交叉核对：`RE-N00\BASELINE.json:1127-1204` 记录的 5 段 RVA/raw_offset/raw_size 与本表一致。
> 唯一节表例外：`gamemd_vsize0.exe`（对抗 fixture），故 P3 中它单列一组。

### 3.2 数据目录（D2 判据用）`[本次实测]`

| 索引 | 名称 | RVA | Size | 落点 |
|---:|---|---:|---:|---|
| 1 | Import Directory | `0x795380` | 340 | 在 `.detour` VA 范围 `0x793000–0x795718` **内**（113/114） |
| 2 | Resource Directory | `0x77A000` | 98,600 | `.rsrc` |
| 6 | Debug Directory | `0x3E1370` | 28 | `.rdata` |
| 12 | **IAT** | `0x3E1000` | 1,544 | `.rdata` —— **不在 `.detour`**（114/114） |
| 4 | Security / Certificate | — | **0** | 无嵌入签名（114/114） |

---

## 4 · P2 · 三方对账（精确比对，禁宽匹配 / 前缀哈希 / 文件名）

`[本次实测]` 输出：`EVIDENCE\reconciliation.tsv`（114 行，逐路径精确布尔值）。

| 对账对象 | 账面值 `[转引→本次实测复核]` | 本卡实测 | 结论 |
|---|---|---|---|
| 任务书 L83-84 / `W42 §1.1` `73201cc0…` / 4,825,360 B | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` / 4,825,360 | 完全一致，**95 份** | **MATCH** |
| `ra2opt\__init__.py:19-27` `KNOWN_GAMEMD` C01 `full_sha256` | `db264305…55aa` | 完全一致，**15 份** | **MATCH** |
| `KNOWN_GAMEMD` C02 `text_sha256`（字典键） | `c0368a17…b738` | 114/114 | **MATCH** |
| `KNOWN_GAMEMD` C08 `size` | 4,825,360 | 114/114 | **MATCH** |
| `FINAL_RULING.md §5:97-99` 三重吻合（C01 + C08 + C02） | `db264305…` / 4,825,360 / `c0368a17…` | `ra2youli\.ra2opt\orig\gamemd.exe` 三重全中 | **MATCH（本卡独立复算，非转引）** |
| `FINAL_RULING.md §5.1:115` `D:\Red2\ra2youli\gamemd.exe = db264305…`（原标「Lead 未复算，标未验」） | `db264305…55aa` | **本卡独立复算命中**，mtime 2020-11-30 15:56:40 | **未验项闭合** |
| 任务书 L85 / `W7_load_baseline\load_baseline_probe.py:75` C07 `ddraw.dll` | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | 38/49 份命中，411,648 B | **MATCH（并已定性，见 §8 G5）** |
| `db264305…` 出现在 `seed --verify` 语境 | — | `[本次读码]` `ra2opt\cli.py:307-312`：`if args.verify: expected = {"gamemd.exe": next(iter(KNOWN_GAMEMD.values()))["full_sha256"]}` ⇒ 期望值正是 `db264305…55aa` | **已知事实核实** |

**冲突登记（不得合并）**：`73201cc0…` 与 `db264305…` 是**不同字节**（整文件差 2 字节，见 §5），按 W42 §2 P2 要求**保留为多副本**，不用前缀/文件名宽匹配合并。另有 4 个未登记字节身份（对抗 fixture），同样逐组保留。

---

## 5 · P3 · 分组 + 多副本歧义消解

`[本次实测]` `EVIDENCE\candidate_groups.json`。按 `(C01, C02, C04[SizeOfImage + 完整节表], C08)` **精确**分组：

| 组 | C01 整文件 SHA-256 | C02 | SizeOfImage | 段数 | 大小 | 份数 | 定性 |
|---|---|---|---:|---:|---:|---:|---|
| G1 | `6a061d9d56798ff7…e1ee9856` | `c0368a17…` | 7,954,432 | 5 | 4,825,360 | 1 | 对抗 fixture `gamemd_overlay_flip.exe` |
| **G2** | **`73201cc0…f67476`** | `c0368a17…` | 7,954,432 | 5 | 4,825,360 | **95** | **任务书/留痕态（ra2opt perf 已施）** |
| **G3** | **`db264305…55aa`** | `c0368a17…` | 7,954,432 | 5 | 4,825,360 | **15** | **KNOWN_GAMEMD / 原始态** |
| G4 | `36a7a63701bd5401…0872d7c` | `c0368a17…` | 7,954,432 | 5 | 4,825,360 | 1 | 对抗 fixture `gamemd_vsize0.exe`（节表唯一例外） |
| G5 | `47b80e4909fbaa72…3b7d303` | `c0368a17…` | 7,954,432 | 5 | 4,825,360 | 1 | 对抗 fixture `gamemd_gi3_tampered.exe` |
| G6 | `3b1d71399f3fb36f…8086a3` | `c0368a17…` | 7,954,432 | 5 | 4,825,360 | 1 | 对抗 fixture `gamemd_corrupt_window.exe` |

**`VERDICT_P3 = MULTI_COPY_AMBIGUOUS`（6 组 ≥ 2）**。按 W42 §2 P3：**不自动挑「看起来最像」的那份**；需 Lead 显式 `--target-dir <realpath>` + `--baseline-id`；**Lead 未指定前 Track A 停在此步**。

### 5.1 「为何整文件哈希不同」——PE 头字段解释（W42 §2 P3 要求的伪差异区分）`[本次实测]`

`EVIDENCE\header_diff.txt`：`db264305…`（orig）与 `73201cc0…`（留痕态）逐字节全量比对，长度同为 4,825,360 B，**恰好 2 个字节不同**：

```
offset 0x0000AE : orig=0x00  patched=0x20     -> DllCharacteristics 0x0000 -> 0x0020
offset 0x0000B2 : orig=0x10  patched=0x40     -> SizeOfStackReserve 0x00100000(1MB) -> 0x00400000(4MB)
.text raw SHA  orig = c0368a17…b738
.text raw SHA  patched = c0368a17…b738   (identical=True)
```

即：**只改 PE 头字段、零代码字节改动**，与 `docs\re\baseline_integrity_note.md:69-114` 及 `ra2youli\.ra2opt\manifest.json` 的 `ra2opt apply perf` 归因一致；C03 `TimeDateStamp` 两态相同（按 W42 §2 P3，C03 仅描述、**不得单独放行**）。4 个对抗 fixture 的头部字段见 `EVIDENCE\probe_data.json`，其中 `gamemd_corrupt_window.exe` 反而是 orig 型头（`dllchar=0` / `stack=1MB`）却带被改过的 `.detour` 段——属刻意构造的测试件，不参与定谳。

---

## 6 · P4 · `.detour` 段 D1–D5 字节判据

`[本次实测]` 输出：`EVIDENCE\detour_classification.json`。`detour_classification = westwood_native`（裁决 D2 默认值，本卡不推翻）；**D1–D5 全部照留**，不以文档措辞替代字节证据。

| 判据 | 实测观测 | 结论 |
|---|---|---|
| **D1 跨副本一致** | 114/114 含 `.detour`。段 raw SHA-256 = `5caa9431…4ab5` 出现在 **112 份**（含全部 95 份 `73201cc0…` 与全部 15 份 `db264305…`），分布在 **111 个不同父目录**，且与「原始态」同现。2 个离群：`gamemd_gi3_tampered.exe` = `7f94d808…2e`、`gamemd_corrupt_window.exe` = `810ba62c…92` | **支持原生**（与「随 exe 一起发行」一致）；2 个离群是**刻意构造的对抗 fixture**，非独立来源，如实登记、**不合并**。此判据非决定性 |
| **D2 `.text` 完整性** | C02 = `c0368a17…b738` **114/114**；`AddressOfEntryPoint=0x3CD80F` 落在 `.text` **114/114**；**IAT（数据目录[12]）RVA `0x3E1000` 在 `.rdata`，不在 `.detour` 114/114**；`ra2opt.pe.text_section_sha256()` 与独立解析器 **0 处不一致** | **PASS**。附加观测（如实登记、不判 MISMATCH）：Import **Descriptor** 目录[1] RVA `0x795380` 落在 `.detour` VA 内 **113/114** —— 这是 Microsoft Detours 1.x「追加导入描述符」的原生形态，**不是 IAT 改道、不是 `.text` hook**；唯一例外是 `gamemd_vsize0.exe` 对抗件 |
| **D3 零售介质对照（决定性）** | 仓库 582,702 文件中 **0 个** `.iso/.cue/.mdf/.nrg/.img/.vhd/.vhdx/.cab/.7z/.rar`（`EVIDENCE\media_paths.txt` 为空）；无任何外部零售介质 / 官方发行件 / 原盘镜像 | **UNDETERMINED（证据不足）**。**决定性判据未满足**：D1+D2 单独不能定谳「原生」；离线环境无法补做 |
| **D4 元数据侧证（弱）** | `TimeDateStamp=0x3BDF544E` = `2001-10-31T01:30:54Z` 114/114（与账面 C03 `2001-10-31` 一致）；`VS_VERSION_INFO` 有 114/114；**Authenticode 嵌入签名 0/114**（cert table size=0） | 仅描述，**不得单独放行**（W38-S1 C03）。无签发者级密码学证据可证明 Westwood 来源 |
| **D5 措辞分歧登记** | 见下表；取值 ∈ `{westwood_native, third_party_injected, undetermined}` | 登记 `westwood_native`（D2），并列全部 `file:line`，不选边、不改他人文档 |

### 6.1 ★ `.detour` Characteristics 独立复核（题面点名要求）

`[本次实测]` 使用**与 `ra2opt.pe` 无关**的 `struct.unpack_from` 解析器，直接从 `opt + opt_size + 40*i + 36` 读 `IMAGE_SECTION_HEADER.Characteristics` 原始 4 字节：

```
observed = 0xC0000040   on 114/114 PE copies
flags    = CNT_INITIALIZED_DATA (0x00000040)
         | MEM_READ             (0x40000000)
         | MEM_WRITE            (0x80000000)
MEM_EXECUTE (0x20000000) = ABSENT   -> has_MEM_EXECUTE = False  (114/114)
first16  = 40 00 00 00 44 74 72 00 c0 25 00 00 c0 25 00 00   -> b'Dtr\0' @ +4
first32  = 40 00 00 00 44 74 72 00 c0 25 00 00 c0 25 00 00
           e0 f0 40 00 40 01 00 00 00 00 00 00 00 00 00 00
```

**结论：CONFIRMED** —— `0xC0000040` = `MEM_READ|MEM_WRITE|CNT_INITIALIZED_DATA`，**无 `MEM_EXECUTE` 位**。首 32 字节与 `docs\re\baseline_integrity_note.md:127-131` 逐字节一致。这是对 Lead W42 签发 §4 / `LEAD_DECISIONS_W42.md:36` 的**独立复核**，不是转引。W43/W46 中该条标注 `[本次实测/转引]`，本卡升级为纯 `[本次实测]`。

### 6.2 D5 措辞分歧并列（不替 Lead 选边）

| 出处 | 措辞 | 侧 | 分级 |
|---|---|---|---|
| `docs\re\baseline_integrity_note.md:136` | 2001 年工程管道**原生集成** Microsoft Research Detours 1.x | 原生 | `[本次读码]` |
| `REVIEW\LEAD_DECISIONS_W42.md:28-38`（D2） | 裁决 `westwood_native`；「第三方 Detours」属**未更正旧口径，应改** | 原生 | `[本次读码]` |
| `W38 VERSION_GUARD_CONTRACT.md:22` | 「Westwood Detours，原生」 | 原生 | `[转引]`（经 `W42 §2 P4 D4`，本卡未直读该文件） |
| `ra2opt\__init__.py:25` | 「含**第三方** Detours 段（`.detour`）」 | 第三方 | `[本次读码]` |
| `ra2opt\pe.py:128` | 「是否带**第三方** Detours 补丁段…说明 exe 已被改过」 | 第三方 | `[本次读码]` |
| `ra2opt\game.py:121` | 「exe 被**第三方** Detours 补丁改过」 | 第三方 | `[本次读码]` |
| `lead\patch_capability_audit_20261112\FINAL_RULING.md:111`（§5.1） | 「已被**第三方追加过** `.detour` 段」 | 第三方 | `[本次读码]` |
| `W42_b_line_s2\BASELINE_ADJUDICATION.md:113`（D5） | 本卡不选边，见 `DISAGREE.md D-W42-13` | 弃权 | `[本次读码]` |

**处理规则（W42 §2 P4 处理规则 1–3）**：`contains_native_detour=true`；`has_detour_section=true` 本身**不构成** `MISMATCH` / `PATCHED_BY_THIRD_PARTY`；「原生」**不**等价于「干净零售金标准」，`RETAIL_ORACLE` 仍须过 §8 六门，`is_clean_retail_gold` 仍为 `const false`。

---

## 7 · P5 · Track A `TARGET_BASELINE`：推荐（**未签发**）

> **W42 §2 P5：仅当 P0–P4 完成、L1 全可读、且多副本歧义由 Lead 显式 `--target-dir` + `--baseline-id` 消解后，Lead 才签 `adjudicated=true`。**
> 本卡 P3 = `MULTI_COPY_AMBIGUOUS`，本卡不是 Lead ⇒ **不签 `adjudicated=true`**，只给 1 份推荐 + 签发所需参数。

### 7.1 推荐

| 字段 | 值 |
|---|---|
| `c13_abs_path` | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| C01 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` |
| C02 | `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738` |
| C04 | `SizeOfImage=7,954,432`；5 段；`has_detour_section=true`；节表见 §3.1 |
| C08 | `4,825,360` |
| C03 | `0x3BDF544E` / `2001-10-31T01:30:54Z` |
| mtime | `2026-09-25 16:10:48 +08:00` |
| 组 / 互证 | G2；**95 份**同字节物理副本 |
| `is_clean_retail_gold` | **`false`（D4，const）** —— 推荐**不等于**证明是零售金标准 |

### 7.2 理由

1. `[本次实测]` **绝对路径绑定**：W38-S1 §5 R7 / W42 §2 P0 要求每条判据绑绝对_path。R-A `TARGET_BASELINE` 定义是「**安装补丁前，这一个绝对路径上这一份具体字节是什么**」——`ra2youli\gamemd.exe` 正是 S2/S3 要写入的游戏目录靶件，不是「盘上改动最少的那份字节」。
2. `[本次读码]` **本轮运行口径一致**：`lead\next_re_20261112\RE-N00\BASELINE.json:63-71`（R01 轮）把 `ra2youli/gamemd.exe` 登记为 `73201cc0…`；`lead\next_re_20261112_r02\W7_load_baseline\load_baseline_probe.py:74` 的 `BASELINE_HASHES["gamemd.exe"]` 同为 `73201cc0…`；所有真机卡 W27/W39/W40/W44/W45 都跑在该身份上。
3. `[本次实测]` **本机互证最强**：95 份同字节 vs `db264305…` 的 15 份。
4. `[本次实测]` **引擎身份稳定**：与 `db264305…` 仅差 2 个非代码 PE 头字节，`.text` raw SHA 完全相同、节表相同（§5.1），符合 `ra2opt/__init__.py:16-18` 「用 `.text` 段哈希做版本键」的设计。
5. `[本次实测]` `.detour` 为原生段（D2 字节证据），112 份真实副本段字节一致，`Characteristics=0xC0000040` 无执行位。
6. `[本次实测]` 题面 `[本次实测] 基线 ra2youli\gamemd.exe = 73201cc0… / 4,825,360 B` 由本卡独立复现。

### 7.3 **不**推荐的替代（须并列，避免误读）

`D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe` = `db264305…`：它匹配 `KNOWN_GAMEMD` 三重登记、是盘上**改动最少**的字节态，但它是 **ra2opt 备份快照**、不是写靶路径；`FINAL_RULING.md §5.1:113` 已裁「`orig/` 快照不能充当干净零售 oracle」。若登记它，实际写靶目录（`73201cc0…`）会在 L1 C01 上被判 `MISMATCH`。

### 7.4 残余风险（如实登记）

| # | 风险 |
|---|---|
| R1 | `[本次实测]` `73201cc0…` 是 **ra2opt perf 已施态**（2 个头字节）。登记它把工具特定补丁烘进基线；一旦 `ra2opt restore` 作用于游戏目录，文件变回 `db264305…`，守卫将报 `MISMATCH`。Lead 须决定基线是否应取「pre-ra2opt」态。 |
| R2 | `[本次实测]` P3 = `MULTI_COPY_AMBIGUOUS`（6 组）；W42 §2 P3 **禁止自动挑最像的那份**。`adjudicated=true` 在 Lead 给出 `--target-dir` + `--baseline-id` 前**不得签**。本卡仅推荐。 |
| R3 | `[本次实测]` 无外部零售介质/保管链（G1 UNKNOWN）⇒ W42 §2 P5 机检第 ⑥ 条「`provenance.source` 非空且可追」在此只能用**本地复制链**满足，不能是零售来源链。 |
| R4 | `[本次实测]` G3/G5 = FAIL：安装目录并非原始安装（cnc-ddraw 7.1.0.0 + `ddraw.ini` + `ipxwrapper` + `xwis`）。这不改 `gamemd.exe` 字节，但说明该安装是**被改造过的**。 |
| R5 | `[本次实测]` W45 真机卡**并发活跃**、持续创建 sandbox 副本；本枚举为时点快照。`ra2youli\gamemd.exe` mtime 稳定，但签发前必须**重跑 P0/P1 实算**（W38-S1 R9：每次写入口调用前重新实算 L1，不可复用为运行时缓存）。 |
| R6 | `[本次实测]` 4 个对抗 fixture 与主流共享 `.text` / `SizeOfImage` / 节表，却有不同的整文件 SHA。前缀哈希或按文件名判定会误收；只能用 **64-hex C01 精确绑定**（W38-S1 §3 硬规则）。 |
| R7 | `[本次读码]` `RE-N00\BASELINE.json:59` 已注「来源/『官方未修改原版』身份未证」；本卡**未**推翻。 |

**签发所需 Lead 动作**：给出 `--target-dir D:\Project\ra2-campaign-forge\ra2youli` + `--baseline-id`，在该精确路径上重跑 P0/P1，然后签 `BASELINE.json`：`adjudicated=true`、`provenance.is_clean_retail_gold=false`、`contains_native_detour=true`、`detour_classification=westwood_native`，且所有 L1 字段与 P1 逐字段相等、`c13_abs_path` 是 P0 表中存在的一行。

---

## 8 · P6 · Track B `RETAIL_ORACLE` 六门 G1–G6

**判据（W42 §2 P6）：六门全 PASS 才允许 `RETAIL_ORACLE_ELIGIBLE=true`；任一 `FAIL`/`UNKNOWN` ⇒ 整体 `UNDETERMINED`、不写「是金标准」。**

| 门 | 判据 | 结论 | 依据（一句话） |
|---|---|---|---|
| **G1** 来源链 | 外部零售介质哈希 + 保管链 | **UNKNOWN** | 仓库内 0 个盘镜像/发行档；无介质、无保管链；`RE-N00\BASELINE.json:59` 亦记「来源…未证」 |
| **G2** 独立权威指纹 | 与「不是该样本自身」的独立权威登记值逐字节吻合 | **UNKNOWN** | 唯一登记值 `ra2opt\__init__.py:19-27` `KNOWN_GAMEMD`、`FINAL_RULING §5`、`RE-N00\BASELINE.json`、`W7_load_baseline` **全部由本机同一批样本算出 ⇒ 自证，禁止计入** |
| **G3** 无第三方组件 | `ra2opt\game.components()` 无 cnc_ddraw / ares / phobos / syringe / ra2opt 留痕 | **FAIL** | 真实游戏目录 `cnc_ddraw=true, ddraw_ini=true, ipxwrapper=true, xwis=true`（`ares/phobos/syringe=false`）；61 个「干净」目录只是仅含 `gamemd.exe` 的夹具目录，**不得挑它们凑 PASS** |
| **G4** 零售版节表 | 与 G1 介质的 `SizeOfImage`/节表/`checksum` 一致 | **UNKNOWN** | 我方节表已测（5 段 / `SizeOfImage=7,954,432` / `checksum=0`，113/114 一致），但**没有 G1 介质可对照**；跨副本内部一致 ≠ 与零售介质一致 |
| **G5** `ddraw.dll` | C07 为官方 wrapper 而非 cnc-ddraw | **FAIL** | C07 `85e0f7d5…` 定性为 **cnc-ddraw 7.1.0.0**（详见下） |
| **G6** 双源互证 | ≥2 个**独立零售介质**给出同一字节 | **UNKNOWN** | 95+15+… 份本地副本都是同两条字节身份的**复制品**（含 `D:\Red2\` 那条也是 `db264305…` 的副本），**不是**独立零售介质；不得把 95 份算作 2 个来源 |

### 8.1 G3 实算细节 `[本次实测]`

`EVIDENCE\components.json`：`ra2opt\game.GameDir(dir).components()` 在 111 个不同父目录上实跑。

- `ra2youli` / `ra2bench` / 各 `sandbox_game`：`cnc_ddraw=true, ddraw_ini=true, ipxwrapper=true, xwis=true, expandmd98=true, battlemd=true, ra2md_ini=true, ra2_ini=true`；`ares=false, phobos=false, syringe=false`。
- 各 `.ra2opt\orig\`：`cnc_ddraw=true, ddraw_ini=true, ra2md_ini=true, ra2_ini=true`。
- 61 个 `components()` 全 false 的目录（如 `…\W27_campaign_live\out\`、`out\forge2_verify\_gamedirs\audit_empty\`）**只有 `gamemd.exe` 一个文件**，是夹具/独立留档目录，不是可运行游戏安装 ⇒ 按 W42 判据**不能**据此判 PASS。

### 8.2 G5 实算细节（本卡新增定性，任务书 L85「未定性」）`[本次实测]`

`EVIDENCE\ddraw_probe.json`：49 份 `ddraw.dll`，2 个字节身份。

| SHA-256 | 份数 | 大小 | `read_version_resource()` | 命中 C07 |
|---|---:|---:|---|---|
| `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | 38 | 411,648 B | `7.1.0.0` | ✅（`ra2youli\ddraw.dll`、`ra2bench\ddraw.dll` 在内） |
| `1fd305a99eb5b75e10b50ad7e90474bfaccdcce1137c5f00ea97c2557e3bf294` | 11 | — | `4.4.7.0` | ❌ |

对 `ra2youli\ddraw.dll` 的**原始字节**扫描：`cnc-ddraw` = True、`CnCNet` = True、`cnc_ddraw` = True、`ddraw.ini` = True；`VS_VERSIONINFO` 内 `FileDescription = "DirectDraw replacement"`、`FileVersion = "7.1.0.0 (git~541b5de, master)"`。`[本次读码]` `ra2opt\__init__.py:34-41` `CNCDDRAW_RA2_FIXES` 记录的正是 cnc-ddraw v4.4.7 → v7.1.0 的 RA2 修复序列，`ra2opt\cddraw.py` 即 cnc-ddraw 升级模块。

⇒ **C07 是第三方 cnc-ddraw v7.1.0.0 包装器，不是官方 Westwood `ddraw.dll` ⇒ G5 = FAIL**。W43/W46 因「L85 只给一个哈希、未定性」留 `UNKNOWN`；本卡以字节 + 版本资源定性后不再 UNKNOWN。

### 8.3 六门总判定

```
G1 UNKNOWN | G2 UNKNOWN | G3 FAIL | G4 UNKNOWN | G5 FAIL | G6 UNKNOWN
=> overall = UNDETERMINED ; retail_oracle_eligible = false
```

`[本次读码]` 与 `FINAL_RULING.md §5.1:113` 对账：该文件已裁「`REWRITE_ROADMAP.md:163` 要求干净零售 1.001 作 oracle —— 该需求**至今未被满足**，`orig/` 快照不能充当它」。本卡跑完 P0–P6 后**仍不满足**，不翻案；按 W42 §2 P6 末段，`PATCH_CONTRACT.md` 版本矩阵该行应继续标 `[待运行验证]`（本卡不改他人文档）。

---

## 9 · 总体裁决与 D4 合规

| 字段 | 值 |
|---|---|
| `schema_version` | `w47-baseline-candidates-1` |
| `adjudicated_target_baseline_signed` | **`false`**（本卡不签；P3 `MULTI_COPY_AMBIGUOUS`） |
| `track_b_gates_evaluated` | **`true`**（P6 六门全部实算/实判，非 `[待运行验证]`） |
| `p3_verdict` | `MULTI_COPY_AMBIGUOUS` |
| `retail_oracle_eligible` | `false` |
| **`is_clean_retail_gold`** | **`false`** —— D4 `const false`，**任何条目不得自称金标准** |
| `baseline_json_schema_extended` | `false` |
| `baseline_json_entry_added` | `false` |
| `detour_classification` | `westwood_native`（D2 默认保留；D3 仍 undetermined） |
| `overall_verdict` | **`UNDETERMINED`** |
| `clean_retail_gold_claim` | **NONE** —— 全文、JSON、脚本、stdout 均**无任何条目自称零售金标准**、均不作金标准声称 |

**D4 落实**：R-B 第二轨结果只落在**独立工件** `BASELINE_CANDIDATES.json`（及本文），**未**写入 `BASELINE.json`、**未**扩展其 schema；`provenance.is_clean_retail_gold` 维持 `const false`。「推荐 `TARGET_BASELINE`」严格**不等于**「证明是零售金标准」：推荐的是 R-A 的**写靶字节身份**，R-B 的 `RETAIL_ORACLE` 仍 `UNDETERMINED`。

---

## 10 · 分级、证据与边界

### 10.1 分级统计

| 分级 | 覆盖内容 |
|---|---|
| `[本次实测]` | 1703 份全文件 SHA-256 / 大小 / mtime；114 份 PE32 的 C01/C02/C03/C04(含完整节表)/C08/C13；全部 PE 头字段；5 段 raw SHA；`.detour` 独立复核；2 字节差异定位；49 份 `ddraw.dll` 哈希与版本资源；111 个目录的 `game.components()`；零售介质/归档文件计数 0 |
| `[本次读码]` | `W42 §2 P0–P6`、`W43 TRACK_B_gates.json`、`REVIEW\LEAD_DECISIONS_W42.md D2/D4`、`docs\re\baseline_integrity_note.md:118-144`、`FINAL_RULING.md §5/§5.1`、`ra2opt\{__init__,pe,game,cli}.py`、`RE-N00\BASELINE.json`、`W7_load_baseline\load_baseline_probe.py` |
| `[静态推断]` | 「Import Descriptor 落在 `.detour` VA 内是 Microsoft Detours 1.x 追加描述符形态」——基于 PE/Detours 结构的解释，非运行期证据 |
| `[转引]` | `W38 VERSION_GUARD_CONTRACT.md:22` 的原生措辞（经 `W42 §2 P4 D4` 转引，本卡未直读）；其余账面哈希**均已本卡复算，不再转引** |
| `[待运行验证]` | 真机行为（本卡零真机，按纪律不执行）；`RETAIL_ORACLE` 若将来取得外部零售介质后的 D3/G1/G4/G6 复判 |

### 10.2 证据清单（本卡目录内）

| 工件 | 内容 |
|---|---|
| `STARTED.txt` | 首动作时间戳（20:41:08+08:00，先于任何读文件） |
| `BASELINE_ADJUDICATION_RESULT.md` | 本文 |
| `BASELINE_CANDIDATES.json` | 机器可读：114 份候选全实测字段 + 1589 份惰性件 + 6 组 + P0–P6 + 六门 + D1–D5 + 推荐 + overall（1,332,439 B，`ConvertFrom-Json` 校验 OK） |
| `UNKNOWNS.md` / `DISAGREE.md` | 未决项 / 分歧登记 |
| `EVIDENCE\w47_probe.py` | v1 脚本（保留为**辅助函数库**；两次独立运行因全仓 `os.walk` 被终止，未产出数据） |
| `EVIDENCE\w47_probe_v2.py` | **权威驱动**（无 `os.walk`、按 SHA 缓存 PE 解析、`EXIT=0`、3.0 s） |
| `EVIDENCE\build_candidates_json.py` | 由 `probe_data.json` 生成 `BASELINE_CANDIDATES.json`（`EXIT=0`） |
| `EVIDENCE\exit_codes.txt` | 全部命令 + stdout 去向 + exit code（含两次被终止的 v1 尝试，如实记录） |
| `EVIDENCE\w47_probe_v2.console.txt` / `w47_probe.stdout.txt` / `progress.log` / `build_candidates.stdout.txt` | stdout 留档 |
| `EVIDENCE\candidates.csv` | P0：1703 行（绝对路径、相对路径、大小、SHA-256、UTC/本地 mtime、is_pe、is_real_game_binary、is_symlink、st_dev、st_ino、st_nlink、是否仓库外）。注：W42 §2 P0 模板里的 `Volume` 列本卡以 `st_dev`（设备号）替代记录 |
| `EVIDENCE\CANDIDATE_ENUMERATION.md` | 1703 份逐行全表（路径/大小/SHA-256/mtime/字节身份组） |
| `EVIDENCE\pe_probe.stdout.txt` | P1：114 份逐副本 L1 五判据 + 完整节表 |
| `EVIDENCE\reconciliation.tsv` | P2：114 行三方精确对账布尔值 |
| `EVIDENCE\candidate_groups.json` | P3：6 组精确分组（含全部成员绝对路径） |
| `EVIDENCE\detour_classification.json` / `header_diff.txt` | P4：D1–D5 + 2 字节定位 |
| `EVIDENCE\ddraw_probe.json` / `components.json` / `media_paths.txt` | G3/G5/G1 原始实测 |
| `EVIDENCE\probe_data.json` | 全量机器可读原始数据（2,532,947 B） |

### 10.3 纪律复核

- ✅ 未启动 `gamemd.exe` / `ra2md.exe` / 任何游戏进程；未 attach；未读活进程内存。
- ✅ 未取 `.game_instance.lock`：只用 `-Filter` 列过它的元数据（169 B，mtime 2026-11-13 21:08:10，W45 持有）；**未打开、未写、未争夺**。观察到 `W45_b_line_equivalence\tools\w45_dual_track.py --phase run --arms A1,A2,B1` 正在运行，完全未碰。
- ✅ 未写 `ra2youli\` / `ra2bench\` / `D:\Red2\`（仅 `rb` 读取）；未改 `ra2forge/`；未动 `W21`–`W46` 任何文件；git 只读。
- ✅ 唯一写域 = `lead\next_re_20261112_r02\W47_baseline_adjudication\`（含 `EVIDENCE\`）。
- ⚠️ **执行瑕疵如实记录**：`w47_probe.py` v1 因在 582,702 文件仓库上做两次 `os.walk` + 逐份重解析 4.8 MB 文件而两次被终止（`EXIT=-1`/TERMINATED，**无输出**）；v2 覆写曾静默失败导致第二次跑的仍是 v1。已改用 `w47_probe_v2.py`（新文件名）+ PowerShell 文件系统级 `-Filter` 枚举，权威运行 `EXIT=0`。详见 `EVIDENCE\exit_codes.txt`。**这不构成任何数据造假**：所有交付数值均来自 v2 的 `EXIT=0` 运行。
- ⚠️ 枚举为时点快照（W45 并发活跃），见 §2.2。

---

> **最终声明**：本卡**没有**、也**不会**对任何一份候选作零售金标准声称（D4 明确禁止任何条目自称金标准）。`is_clean_retail_gold` 恒为 `false`；R-B `RETAIL_ORACLE` 判定 `UNDETERMINED`；R-A `TARGET_BASELINE` 仅为**推荐**，签发权在 Lead。
