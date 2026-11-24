# W47 · DISAGREE.md · 分歧 / 与既有工件的差异 / 未更正的旧口径

> 本卡**不替 Lead 选边、不翻案、不改他人文档**（纪律：不动 `W21`–`W46`、git 只读、唯一写域为本卡目录）。以下逐条登记「本卡实测与既有口径不一致 / 既有口径内部冲突」之处，并标明是**证据升级**、**闭合未验项**、**新增定性**，还是**仍待 Lead 裁决**。
> 总判定不变：`overall = UNDETERMINED`、`is_clean_retail_gold = false`（D4 const false）；无任何条目自称零售金标准。

---

## A · 与 W43/W46 `TRACK_B_gates.json` 的差异（证据升级，非翻案）

### D-W47-1 · 六门由「全 UNKNOWN」细化为「2 FAIL + 4 UNKNOWN」
- **既有口径**：`W43_b_line_s3\TRACK_B_gates.json:74-111`（及逐字相同的 `W46_resolve_integration\TRACK_B_gates.json`）记 G1–G6 **全部 `UNKNOWN`**，并自述 `status: "[转引] -- this card computed NO hashes of any real game binary"`、P0–P5 全 `[待运行验证]`。
- **本卡 `[本次实测]`**：
  - **G3 = FAIL**：在 111 个父目录实跑 `ra2opt\game.components()`；真实游戏目录 `cnc_ddraw=true, ddraw_ini=true, ipxwrapper=true, xwis=true`（`EVIDENCE\components.json`）。
  - **G5 = FAIL**：C07 `85e0f7d5…` 定性为 **cnc-ddraw 7.1.0.0**（字面串 `cnc-ddraw`/`CnCNet`/`cnc_ddraw`/`ddraw.ini`、`FileDescription="DirectDraw replacement"`、`FileVersion="7.1.0.0 (git~541b5de, master)"`），不是官方 wrapper（`EVIDENCE\ddraw_probe.json`）。
  - G1/G2/G4/G6 仍 `UNKNOWN`（见 `UNKNOWNS.md` U-W47-1/2/3/4）。
- **性质**：W43/W46 明说未实算，所以「全 UNKNOWN」是**证据不足**而非「判过 PASS/FAIL」。本卡把可算的算掉 ⇒ **证据升级**。总判定仍 `UNDETERMINED`、`retail_oracle_eligible=false`，**不翻案**、不把 `FINAL_RULING.md §5.1:113` 的裁定改掉。
- **需 Lead 注意**：若后续工件继续引用 W43/W46 的「六门全 UNKNOWN」，应连带注明本卡已把 G3/G5 定成 FAIL。

### D-W47-2 · 账面哈希由「未复算」升级为「本卡独立复算」
- **既有口径**：`W43...TRACK_B_gates.json:15-23` `physical_copy.book_values_not_recomputed` 明确写「this card computed NO hashes of any real game binary; all book values above are quoted for reconciliation only」。W42 `§1.2` 也全部标 `[转引]`。
- **本卡 `[本次实测]`**：C01/C02/C08/C03/C04/C07 **全部重算**，1703/1703 哈希成功；`db264305…`（15 份）与 `73201cc0…`（95 份）均命中；`c0368a17…` 114/114；`SizeOfImage=7,954,432`；C07 38/49 份命中。
- **性质**：闭合「未复算」，不产生新冲突。

### D-W47-3 · `FINAL_RULING.md §5.1:115` 的「未验」项闭合
- **既有口径**：`lead\patch_capability_audit_20261112\FINAL_RULING.md:115`：「`D:\Red2\ra2youli\gamemd.exe` 也等于 `db264305…` ⇒ … **该路径我未亲自复算**，标未验」；`:131` 亦列「`D:\Red2\ra2youli\gamemd.exe` 未由我复算」。
- **本卡 `[本次实测]`**：该路径存在，4,825,360 B，`SHA-256 = db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa`，mtime `2020-11-30 15:56:40 +08:00`，PE32 全字段与 G3 组一致。**ZCode 报告成立**。
- **性质**：**闭合未验项**，不是分歧。但须并列：它仍是**同一条本地字节身份的又一个副本**，**不能**充当 G1/G6 的独立零售介质（见 U-W47-4）。

### D-W47-4 · `.detour` 字节事实由 `[本次实测/转引]` 升级为纯 `[本次实测]`
- **既有口径**：`W43...TRACK_B_gates.json:122` `byte_fact: "[本次实测/转引] .detour Characteristics=0xC0000040 … (Lead W42 signoff §4)"`。
- **本卡 `[本次实测]`**：用**与 `ra2opt.pe` 无关**的独立 `struct.unpack_from` 解析器，在 114/114 份 PE 上读到 `0xC0000040`，解码 `CNT_INITIALIZED_DATA|MEM_READ|MEM_WRITE`，`MEM_EXECUTE` 位**缺失**；首 32 字节与 `baseline_integrity_note.md:127-131` 逐字节一致。
- **性质**：独立复核 **CONFIRMED**，去掉「/转引」。

### D-W47-5 · 任务书 L85 / W42 G5「未定性」→ 本卡定性（**新增定性，需 Lead 知悉**）
- **既有口径**：`W42 §2 P6` 表 G5 写「任务书 L85 只给一个哈希，**未定性**」；`W43...TRACK_B_gates.json:104` 因此留 `UNKNOWN`。
- **本卡 `[本次实测]`**：`85e0f7d5…` = **第三方 cnc-ddraw v7.1.0.0**（`read_version_resource()` = `7.1.0.0`；原始字节含 `cnc-ddraw`/`CnCNet`/`cnc_ddraw`/`ddraw.ini`；`VS_VERSIONINFO` `FileDescription="DirectDraw replacement"`、`FileVersion="7.1.0.0 (git~541b5de, master)"`；`ra2opt\__init__.py:34-41` 的 `CNCDDRAW_RA2_FIXES` 正是 v4.4.7→v7.1.0；`ra2opt\cddraw.py` 为 cnc-ddraw 升级模块）。第二字节身份 `1fd305a9…` = `4.4.7.0`，同属 cnc-ddraw。
- **性质**：把「未定性」变成「已定性」，据此 **G5 = FAIL**。这是对 W42 判据的**正向执行**，但改变了 W43/W46 的门状态，登记备查。

---

## B · `.detour` 措辞分歧（W42 §2 P4 D4/D5 要求并列，本卡不选边）

### D-W47-6 · 「原生」 vs 「第三方」三处以上措辞冲突，至今未统一
| 出处 | 措辞 | 侧 | 分级 |
|---|---|---|---|
| `docs\re\baseline_integrity_note.md:136` | 2001 工程管道**原生集成** Microsoft Research Detours 1.x | 原生 | `[本次读码]` |
| `REVIEW\LEAD_DECISIONS_W42.md:28-38`（D2） | 裁决 `westwood_native`；「第三方 Detours」属**未更正旧口径，应改** | 原生 | `[本次读码]` |
| `W38 VERSION_GUARD_CONTRACT.md:22` | 「Westwood Detours，原生」 | 原生 | `[转引]`（经 W42 P4 D4，本卡未直读） |
| `ra2opt\__init__.py:25` | 「含**第三方** Detours 段（`.detour`）」 | 第三方 | `[本次读码]` |
| `ra2opt\pe.py:128` | 「是否带**第三方** Detours 补丁段…说明 exe 已被改过」 | 第三方 | `[本次读码]` |
| `ra2opt\game.py:121` | 「exe 被**第三方** Detours 补丁改过」 | 第三方 | `[本次读码]` |
| `FINAL_RULING.md:111`（§5.1） | 「已被**第三方追加过** `.detour` 段」 | 第三方 | `[本次读码]` |
| `W42 §2 P4 D5 / DISAGREE.md D-W42-13` | 本卡不选边 | 弃权 | `[本次读码]` |

- **本卡处置**：`detour_classification = westwood_native`（**D2 默认裁决保留**），D1–D5 字节判据照留，D3 明确 `undetermined`。**不以文档措辞替代字节证据**。
- **未更正的文档债（登记，不修）**：D2 说上述「第三方」措辞「应改」，但本卡纪律禁止改 `ra2opt/` 与 `W21`–`W46`，故 4 处旧口径**仍留在仓库里**。这是**已知且未闭合**的文档不一致，需 Lead/后续卡处理。
- **两派一致点（不翻案）**：无论「原生」还是「第三方」，**都不能当干净零售金标准**；`is_clean_retail_gold` 恒 `false`。

### D-W47-7 · `ra2opt\game.py:120-124` 会把推荐基线标成 `patched_by_ra2opt=true`
- `[本次读码]` `identity()` 中 `patched = bool(entry and sha != entry["full_sha256"])`；对 `73201cc0…`，`known` 命中 `KNOWN_GAMEMD`（因 C02 匹配），但 `sha != db264305…` ⇒ `patched=True`。
- **性质**：**不矛盾**，反而与本卡 §5.1 的「2 字节 ra2opt perf 留痕」一致。登记以免后续把 `patched=True` 误读成「第三方污染」。

---

## C · 数值 / 计数口径的既有不一致

### D-W47-8 · `docs\re\baseline_integrity_note.md:52-55` 的十进制换算错误（既有文档内部不一致）
- 该处写：`Misc_VirtualSize = 0x003DF38D（2,487,181 字节）`、`SizeOfRawData = 0x003E0000（2,490,368 字节，按 FileAlignment=0x1000 对齐）`。
- `[本次实测]` 本卡独立解析：`0x3DF38D = 4,060,045`、`0x3E0000 = 4,063,232`；差值 `0xC73 = 3,187` 字节（**该差值与文档 §2 的 3,187 一致**）。文档给的 2,487,181 / 2,490,368 实际对应 `0x25F38D / 0x260000`，是**十进制换算写错**，十六进制本身正确。
- **性质**：**既有文档笔误，本卡未修改**（纪律）。`W42 §1.2` 的 C02「raw `0x1000` / size 4,063,232」、§3 的 `baseline_integrity_note.md:127-131` 首 32 字节、`:122-126` 的 VA/offset/vsize/rawsize 都与本卡实测吻合。登记以免有人拿错误十进制反推段大小。

### D-W47-9 · W42 §1.1「两个 `73201cc0…` + 至少两个 `db264305…`」→ 本卡实测规模大得多
- `[本次读码]` `W42 §1.1:36` 写「两个 `73201cc0…` 留痕态 + 至少两个 `db264305…` 原始态」，`FINAL_RULING §5.1:115` 同口径。
- `[本次实测]` 本卡枚举到 **95 份 `73201cc0…` + 15 份 `db264305…`**，另有 **4 个未登记字节身份**（对抗 fixture）共享 `.text`/节表/`SizeOfImage`。
- **性质**：**规模更新，非矛盾**（那些卡只列了它们当时点名的路径，未做全树枚举）。但「多副本歧义」的规模远超原描述，登记以免按「只有 4 份」去设计歧义消解。

### D-W47-10 · W43/W46 `adjudicated:true` 与 P5 签发语义需区分
- `[本次读码]` `W43...TRACK_B_gates.json:5` 写 `adjudicated: true`，同时 `:12-13` 明确 `baseline_json_entry_added:false`、`:8` `baseline_json_schema_extended:false`。
- **本卡口径**：`BASELINE_CANDIDATES.json` 里用两个不同字段避免歧义：`track_b_gates_evaluated=true`（六门确实判过）、`adjudicated_target_baseline_signed=false`（**R-A `BASELINE.json` 条目未签**，因 P3 `MULTI_COPY_AMBIGUOUS`）。
- **性质**：**语义澄清，不是冲突**。W43 的 `adjudicated` 指「第二轨独立工件已裁决」，不指「Track A 已签 `BASELINE.json`」。按 W42 §2 P5 / W38-S1 R6，未签时 `guard_state` 仍应 `UNKNOWN` + `NO_ADJUDICATED_BASELINE`。

### D-W47-11 · 推荐 `TARGET_BASELINE` 取 `73201cc0…` 而非 `db264305…`（需 Lead 确认语义）
- `[本次读码]` W43/W46 的 `physical_copy.book_values_not_recomputed` 用 `db264305…` 作为 **R-B 观察候选**；`FINAL_RULING §5.1:113` 裁「`orig/` 快照不能充当干净零售 oracle」。
- **本卡 `[本次实测]` 推荐** `ra2youli\gamemd.exe` = `73201cc0…` 作为 **R-A `TARGET_BASELINE`**，理由是「写靶绝对路径 + 本轮 `RE-N00\BASELINE.json:63-71` / `W7_load_baseline\load_baseline_probe.py:74` 均登记此值 + 95 份互证」。
- **性质**：**两轨角色不同，不构成冲突**（R-A 是「写靶路径上那份字节」，R-B 是「干净零售 oracle」）。但若 Lead 的本意是「基线应取盘上改动最少的 pre-ra2opt 态」，则应改推 `db264305…` 并接受写靶目录 C01 会 `MISMATCH`。此项**留给 Lead 裁决**，见 `UNKNOWNS.md U-W47-8`。

---

## D · 与既有裁定一致（登记为「无分歧」，避免误读）

| 项 | 既有 | 本卡 |
|---|---|---|
| `RE-N00\BASELINE.json:59`「来源/『官方未修改原版』身份未证」 | 未证 | `[本次实测]` G1 仍 UNKNOWN，**未**推翻 |
| `FINAL_RULING.md §5.1:113`「干净零售 1.001 oracle 至今未被满足」 | 未满足 | `[本次实测]` 六门后 `overall=UNDETERMINED`，**未**翻案 |
| `W42 §1.2` C02 = `c0368a17…` / raw `0x1000` / `4,063,232` | 账面 `[转引]` | `[本次实测]` 114/114 命中 |
| `W42 §1.2` C04 = 5 段含 `.detour` | 账面 `[转引]` | `[本次实测]` 114/114 命中 |
| `LEAD_DECISIONS_W42.md D2`「`0xC0000040` 无执行位」 | `[本次实测]`（Lead） | `[本次实测]` 独立解析器 114/114 复核通过 |
| `LEAD_DECISIONS_W42.md D4` `is_clean_retail_gold: const false` | 裁决 | `[本次实测]` 全文/JSON/stdout 均为 `false`，无金标准声称 |
| `W42 §2 P3`「≥2 组 ⇒ MULTI_COPY_AMBIGUOUS，不自动挑最像的」 | 程序 | `[本次实测]` 6 组，本卡**只推荐不签发** |

---

## E · 本卡执行过程自身的分歧/瑕疵（如实登记）

### D-W47-12 · v1 两次被终止、v2 覆写静默失败
- `EVIDENCE\exit_codes.txt` 完整记录：`w47_probe.py` v1 在 582,702 文件仓库上做两次 `os.walk` + 逐份重解析 4.8 MB 文件，两次被终止（`EXIT=-1`/TERMINATED，**无任何输出**）；一次 v2 覆写静默失败，导致第二次运行的仍是 v1。
- **处置**：改用新文件名 `w47_probe_v2.py`（新文件，不覆写）+ PowerShell 文件系统级 `-Filter` 枚举 + 按 SHA 缓存 PE 解析，权威运行 `EXIT=0`、3.0 s。
- **性质**：**过程瑕疵，非数据分歧**。所有交付数值只来自 `w47_probe_v2.py` 的 `EXIT=0` 运行；`w47_probe.py` 保留为辅助函数库。原先 `exit_codes.txt` 中「`w47_probe.py v2 EXIT=-1`」是**误标**（实为 v1），已更正。

### D-W47-13 · `-Filter` 枚举 1702 份 vs 早前 `Where-Object` 枚举 1624 份
- `[本次实测]` 20:41 用 `Get-ChildItem -Recurse -File | Where-Object Name -match 'gamemd.*\.exe$'` 得 1624；21:01 用 `-Filter '*gamemd*.exe'` 得 1702。
- **归因**：W45 真机卡**并发活跃并持续创建 sandbox 副本**（`w45_dual_track.py --phase run`），两次枚举相隔 20 分钟，仓库在变化；另外 `-Filter` 由文件系统层匹配，不遗漏长路径/权限受限目录中的条目。
- **性质**：**时点差异，不是数据冲突**。本卡以 21:01 的 1702 + 1 份外部 = 1703 为准，并在 `UNKNOWNS.md U-W47-9` 声明快照性。

---

> **未替 Lead 选边的清单**：D-W47-6（`.detour` 原生/第三方措辞）、D-W47-11（R-A 基线取哪条字节身份）、U-W47-8（基线语义）三项**明确留给 Lead**；本卡只给实测证据与推荐，不改他人文档、不改 `BASELINE.json` schema、不签 `adjudicated=true`。
