> 卡号：R16-EVID9
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_EVID9\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-20（R16 第 1 轮）

# 任务：为 9 行歧义 `evidence_path` 定出唯一目标文件，产出待并表 delta

## 0. 绝对边界

1. **不写 `COVERAGE\coverage.tsv`**（单写者纪律：只有合并员能改，Lead 会在下一轮派合并员并表）。你只产出 delta 文件。
2. **不写** `COVERAGE\PANEL.md`、`R14_COMMON.md`、`STATUS_BOARD.md`、台账、`_drafts\`、`_cards\` 下任何文件。
3. **不做逆向**：不跑 capstone / Ghidra / pefile / 反汇编。
4. **产物只写** `lead\next_re_20261117_r14\R16_EVID9\` 下。
5. **不许编造**：一个 entry 若两个候选都无法判定，就如实写「未定」并说明你看过了什么。宁可 9 行只定 5 行，不可凑数。

## 1. 背景（照录，不要重算）

`EVID_RESOLVE` 全量解析 1,654 行 `[已证]` 的 `evidence_path` 后，`R_MISSING` 从 374 降到 9。这 9 行的根因是**同一个文件名存在于两个卡目录**，`M83` 的消歧规则（「目录名含该行 subsystem 编号」）对它们失效：

- **7 行 S10**：候选目录 `S10_K8` 与 `S10_K8F` **都含 "S10"**，按 subsystem 号无法二分。
- **2 行 S22**：候选目录（`S10_K8`/`S10_K8F`）**都不含 "S22"**，0 匹配。
- （另有 1 行同类，见下表实际 9 行。）

⇒ 这 9 行必须**逐行看候选文件内容**才能定。

## 2. 这 9 行（Lead 已从 `R16_BASE\evid\resolve.tsv` 逐行取出，class=`R_MISSING`）

| # | entry | subsystem | name | 现 evidence_path |
|---|---|---|---|---|
| 1 | `004DF320` | S10 | AircraftClass::QueueMissionId2ElseId1_OnFlags_behavior | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF320` |
| 2 | `004DF3A0` | S10 | AircraftClass::QueueMissionId1_AfterCellTargetCheck_behavior | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF3A0` |
| 3 | `004DFB70` | S10 | AircraftClass::QueueMissionId7_AfterNearbyFilter_behavior | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFB70` |
| 4 | `004DFCB0` | S10 | AircraftClass::QueueMissionId8_NearHouseFilter_behavior | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFCB0` |
| 5 | `004DFE00` | S10 | AircraftClass::QueueMissionId8_NearGlobalFilter_behavior | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFE00` |
| 6 | `004E0E80` | S10 | VectorClass<AbstractClass*>::VectorClass | `EVIDENCE/OWNERSHIP_004E0E80.txt#004E0E80` |
| 7 | `006B6EA0` | S22 | SpawnManagerClass::SpawnManagerClass | `EVIDENCE/SPAWNMANAGER_CTORS.txt#006B6EA0` |
| 8 | `006F4960` | S10 | AircraftClass::QueueMissionId15_OnMission14_behavior | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#006F4960` |
| 9 | `006B6FA0` | S22 | SpawnManagerClass::SpawnManagerClass_1arg | `EVIDENCE/SPAWNMANAGER_CTORS.txt#006B6FA0` |

## 3. 候选文件（Lead 已枚举，只此 2 处，别处没有同名文件）

| 文件名 | 候选 A | 候选 B |
|---|---|---|
| `QUEUE_DISPATCH_AND_FALSE_KILLS.txt` | `...\next_re_20261117_r14\S10_K8\EVIDENCE\` （42,375 B） | `...\S10_K8F\EVIDENCE\` （42,895 B） |
| `OWNERSHIP_004E0E80.txt` | `...\S10_K8\EVIDENCE\` （2,188 B） | `...\S10_K8F\EVIDENCE\` （2,188 B） |
| `SPAWNMANAGER_CTORS.txt` | `...\S10_K8\EVIDENCE\` （21,109 B） | `...\S10_K8F\EVIDENCE\` （21,109 B） |

（若你实测发现别处还有同名文件，**以你的实测为准**并写进报告；Lead 的枚举只作起点。）

## 4. 判定方法（照做，别自创）

对每一行：

1. 先算两个候选文件的 **sha256** 与字节数。
2. **若两候选 sha256 相同（字节完全一致）**：说明内容等价，任取其一即可。判定规则固定为 **取字典序较小的目录名**（即 `S10_K8`），并在 note 里写明「两候选字节一致（sha256=<值>，N B），取 S10_K8，另一候选内容相同」。**这种情况不构成歧义，可以定。**
3. **若两候选不同**：在**两个文件里都搜**该 entry 的 8 位十六进制串（大小写都搜），统计**出现次数**，并看它出现在什么上下文（例如是章节标题、地址列、还是顺带提及）。
   - 只有一个文件里出现 ⇒ 定该文件。
   - 两个都出现 ⇒ 看出现次数与上下文强度，给出你的判断与理由；**若无法给出明确优于另一方的理由，就写「未定」并附两个次数**，不要硬选。
4. 记下你搜的确切命令。

## 5. 产物

### 5.1 `R16_EVID9\decision.tsv`（TAB 分隔，9 行 + 表头）

列（严格按此顺序）：

```
entry	subsystem	name	old_evidence_path	decision	cand_A_sha256	cand_A_bytes	cand_A_hits	cand_B_sha256	cand_B_bytes	cand_B_hits	new_evidence_path	note
```

- `decision` 取值只允许：`BOTH_IDENTICAL`（两候选字节一致）/ `UNIQUE_HIT`（只有一个文件含该 entry）/ `BOTH_HIT_JUDGED`（都含、你判定了）/ `UNDECIDED`（未定）
- `new_evidence_path`：**相对 `lead\next_re_20261117_r14\` 的路径**，形如 `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF320`（保留 `#entry` 锚点原样）。`UNDECIDED` 行此列留空。
- `note`：逐行独立写，**不许复制上一行**。要写出你凭什么这么判。

### 5.2 `R16_EVID9\coverage_delta.tsv`（TAB 分隔，只含可定行 + 表头）

**8 列，与 `coverage.tsv` 完全同构**（表头与数据行都用 TAB）：
```
entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict
```
- 只放 `decision != UNDECIDED` 的行。
- 第 1–5、7、8 列**必须与盘上 `coverage.tsv` 逐字节相同**（你从盘上原行整行取出，只改第 6 列）。
- 第 6 列 = 新路径 + `;M84 指针修复：<一句话理由>`（理由按行写，不许复制）。

### 5.3 `R16_EVID9\REPORT.md`

必须含：
- 改前/改后 `coverage.tsv` 的 **mtime / 字节数 / sha256**（改前值必须实记；你**不该改**它，所以改后值应与改前相同 —— 若你只读它，就写「未改，sha256 前后一致」）
- 9 行逐行判定摘要表
- 你的确切命令清单（搜 entry 用的、算 sha 用的）
- **未定行清单与原因**
- 预估并表后 `R_OK` 会从 **843 / 1,654** 变成多少（843 + 可定行数），并注明这是**预估**、不是 Lead 复算
- 一句自检：你**没有**写 `coverage.tsv`（给 sha 证明）

## 6. 回复里给什么

只给：可定行数 / 未定行数、`R_OK` 预估、你判 `BOTH_IDENTICAL` 的有几行、三份产物的绝对路径。**不要贴全文**。
