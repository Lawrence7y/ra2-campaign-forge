# S08-K1 · S08（Shroud/Radar/FoggedObject）**整子系统收口**：差 1 个名字 + 10 行 proved

## 盘上现态（Lead 实测 2026-11-18 16:5x，atlas∩coverage；与你自己复算不符就停下报告）
`S08` **只有 22 行**：n = 22、named = **19**（门槛 20 ⇒ **差 1**）、proved = **1**（门槛 11 ⇒ **差 10**）、`[静态推断]` **20**、`[未证]` **1**。
⇒ **这是全项目最容易成为第 4 个达标子系统的目标**：只要 1 个真名 + 10 行升 `[已证]`。

## 22 行全貌（Lead 已列，供你对齐）
| entry | 现 grade | 现 name |
|---|---|---|
| `0040D250` | `[静态推断]` | `MouseClass::vslot43` |
| `004309D0` | `[静态推断]` | **`sub_004309D0`** ← **命名候选（差的就是它）** |
| `0045A070` `0045A0A0` `0045A0C0` `0045A640` `0045A680` `0045A730` `0045AB00` `0045AB50` `0045AC00` `0045AC30` `0045AC70` `0045AC90` | `[静态推断]` | `…FoggedObjectClass…::slotN/vslotN`（13 行）|
| `0047EFE0` | **`[已证]`** | `sub_0047EFE0`（引用 `FOG.SHP`）|
| `0047F250` | **`[未证]`** | `sub_0047F250`（引用 `FOG.SHP`）|
| `004D24A0` `004D2510` `004D27B0` `004D27D0` `004D2810` `004D2910` | `[静态推断]` | `FoggedObjectClass::slotN`（6 行）|

## 两个目标（都要做）
### 目标 A：补 **1 个真名**（把 named 从 19 抬到 20 = 达标）
优先给 **`004309D0`**（`sub_004309D0`，语义栏写「Shroud/Radar member (string/import)」）。
- 若它证不出真名 ⇒ 改攻 `0047F250`（引用 `FOG.SHP`，字符串线索最强）或 `0047EFE0`（已 `[已证]`，可复用其证据链命名）。
- **任一条成功即可**（named 19→20）。
- 合格条件（两条通道，各自提供对方给不出的信息）：①二进制（体内串/调用/字段/全局）②异源（`YRpp\` 的 `CALL(0x…)`/`JMP_THIS(0x…)` 原文行，或 `docs\re\`+台账的既有独立记录，须给行号）。
- **禁** `Class::sub_XXXX` 占位名；**禁编名**；查不到就交 0 条并列出已试通道（照实交差算合格）。

### 目标 B：把 **10 行**升 `[已证]`（proved 1→11 = 达标）
**只走 direct call 通道**（这是本项目唯一稳定的环④）：
`E8 rel32` 必须 ① 在**指令边界**上 ② `site+5+rel32==entry`（逐字节）③ **调用者 ≠ 本行体内**。

⚠️ **严禁**（本项目已因此 FAIL 4 次）：
- `atexit` 析构器装的虚表（`push <dtor>; call 0x7C978A`）—— 那不是活 vptr；
- 「entry 在自己虚表里是第 K 槽」式**槽号匹配**；`exact` 派发除非满足「静态 global + 构造器活 vptr + `vt[slot]==entry` + site 不共用」，否则不用；
- slot-baseline；用「恰命中 N / P=R=100%」当证据。

⚠️ 这 22 行里有 **19 行是虚表槽语义**（`FoggedObjectClass::slotN` / `…::vslotN`），**大概率 direct call = 0**。
⇒ **若 22 行里 direct call 行不足 10 条，如实报告「最多只能升 N 行」**，并列出 `DIRECT_ONLY.tsv`。**不要为凑数放宽判据。**

## 强制自证
- **扫描覆盖 `.text` 100%**（全扫基准 **1,392,592 条指令 / 68,253 个 `E8`@边界**），报告你的实测值；交付站点必须落在自报范围内。
- **⑲ 自检**：capstone 5.0.7 无 `op.index`（index 在 `op.mem.index`，无 index 返 **0 非 None**）。
- **基线 + 差分**：随机抽样基线要给；⚠️ 新错源 B：**随机基线对同源系统性错误零鉴别力**，须补**差分检验**（同一批行 × 弱/强判据取差集）。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）—— 只报不改名。
- **⑨ 停机核验**：盘上 S08 = 22 行 / named 19 / proved 1，自己重算。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_K1\`
`PROGRESS.md`（≤50 行，**第一行写两个目标各自达成没达成**）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S08), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`（命名行 + direct 升格行都放这里）
`DIRECT_ONLY.tsv`：direct 通道实证清单（entry + caller 站点地址）
**每完成 2–3 项就增量落盘 PROGRESS.md。严禁建 venv / pip install / import 其他卡 work 代码。**

## 核心数字
① 新增真名条数（目标 1）② direct 升 `[已证]` 行数（目标 10）③ 扫描规模（指令数/E8 数/覆盖率）④ 基线+差分 ⑤ 并入后 S08 的 named 与 proved 实测值