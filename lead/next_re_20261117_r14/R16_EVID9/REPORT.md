# R16-EVID9 执行报告

> 卡号：R16-EVID9（R16 第 1 轮）
> 执行角色：执行器（agent-2）
> 日期：2026-11-20
> 边界遵守：未写 `COVERAGE/coverage.tsv`（单写者纪律），未写任何卡面禁止文件，未做逆向，产物仅写 `lead/next_re_20261117_r14/R16_EVID9/`。

## 0. coverage.tsv 改前/改后状态（证明未写）

| 时点 | 路径 | mtime (ISO-8601) | 字节数 | sha256 |
|---|---|---|---|---|
| 改前 | `lead\next_re_20261117_r14\COVERAGE\coverage.tsv` | `2026-11-20T21:37:14.9932414+08:00` | 4016071 | `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2` |
| 改后 | 同上 | `2026-11-20T21:37:14.9932414+08:00` | 4016071 | `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2` |

**未改，sha256 前后一致，mtime 与字节数亦一致。** 本次执行对该文件只读（仅 `ReadAllLines` / `Get-Item` / `Get-FileHash`）。

## 1. 候选文件枚举核对（卡面第 3 节）

用 `glob` 在项目全树搜三个文件名，确认 Lead 的枚举完整——每个文件名**仅**存在两个候选，别处没有同名文件：

- `QUEUE_DISPATCH_AND_FALSE_KILLS.txt`：`S10_K8\EVIDENCE\`（42,375 B）、`S10_K8F\EVIDENCE\`（42,895 B）
- `OWNERSHIP_004E0E80.txt`：`S10_K8\EVIDENCE\`（2,188 B）、`S10_K8F\EVIDENCE\`（2,188 B）
- `SPAWNMANAGER_CTORS.txt`：`S10_K8\EVIDENCE\`（21,109 B）、`S10_K8F\EVIDENCE\`（21,109 B）

## 2. 候选文件 sha256 / 字节数（卡面第 4 节第 1 步）

| 文件 | 目录 | 字节数 | sha256 |
|---|---|---|---|
| QUEUE_DISPATCH_AND_FALSE_KILLS.txt | S10_K8 | 42375 | `CE05780549696FB90AE51A67D479B240466E227C0AEA8B65D3DF3D6611D0DEEE` |
| QUEUE_DISPATCH_AND_FALSE_KILLS.txt | S10_K8F | 42895 | `D11D812B5776439B7F9061912FB191356D509522921442B79B55F610DF7A86CC` |
| OWNERSHIP_004E0E80.txt | S10_K8 | 2188 | `86B4094123B55357665ABBBA6B2CE8B1BCA27806184E5B60D94B2E1E15C48ED9` |
| OWNERSHIP_004E0E80.txt | S10_K8F | 2188 | `86B4094123B55357665ABBBA6B2CE8B1BCA27806184E5B60D94B2E1E15C48ED9` |
| SPAWNMANAGER_CTORS.txt | S10_K8 | 21109 | `10A334CAB067836FB7F4AF5E3768AC1F3F72B1868BAF996637C7AC7951CF9349` |
| SPAWNMANAGER_CTORS.txt | S10_K8F | 21109 | `10A334CAB067836FB7F4AF5E3768AC1F3F72B1868BAF996637C7AC7951CF9349` |

- `OWNERSHIP_004E0E80.txt` 两候选字节全同（sha256 相同，2188 B）⇒ 按卡面第 4 节第 2 步，`BOTH_IDENTICAL`，取字典序较小的 `S10_K8`。
- `SPAWNMANAGER_CTORS.txt` 两候选字节全同（sha256 相同，21109 B）⇒ 同上，`BOTH_IDENTICAL`，取 `S10_K8`。
- `QUEUE_DISPATCH_AND_FALSE_KILLS.txt` 两候选**不同**（42375 vs 42895 B，sha256 不同）⇒ 走第 4 节第 3 步，逐 entry 搜出现次数与上下文。

## 3. QUEUE 两候选文件的差异定位

对两个 QUEUE 文件做逐行 diff：

- 行数：S10_K8 = 733 行，S10_K8F = 738 行（相差 5 行；字节相差 520 B）。
- 全部差异都在**头部/语义摘要区**，共 13 行差异（S10_K8F 独有 9 行，S10_K8 独有 4 行）：
  - S10_K8F 多出 `REVERIFY=work/reverify_semantics_k8f.py (independent byte assertions; corrected inner index 0 -> call)`；
  - S10_K8F 对 dispatch 语义做了校正展开（如 `Inner index 0 -> 41BAD3 (call 005B35E0)`，`queued==id OR queued==-1 suppresses the write; queued!=-1 alone is not sufficient`）；
  - S10_K8 对应位置是较旧的摘要（如 `inner index 0 -> 41BADE (pop esi; ret 8)`、`cur==id&&queued!=-1`）。
- **关键实测**：从第一个 `=== ROW 004DF320 ===` 起，两文件尾部**逐字节完全一致**：tail 长度均 34317 B，sha256 均 `8B4E7C8014481E5ED499853096765FFC03E9990FB3DCCC54FC7510058A32A09E`。9 行中 6 个 QUEUE entry（004DF320/004DF3A0/004DFB70/004DFCB0/004DFE00/006F4960）的 `=== ROW ... ===` 区块在两文件中各自逐字节一致。
- 即：6 个 QUEUE entry 的**出现次数与上下文强度在两候选中完全相同**，头部差异不提及这些 entry。

## 4. 9 行逐行判定摘要表

| # | entry | subsystem | decision | cand_A hits | cand_B hits | 新 evidence_path（或空） | 判定依据（摘要） |
|---|---|---|---|---|---|---|---|
| 1 | 004DF320 | S10 | UNDECIDED | 2 | 2 | 空 | 两文件各 2 次（章节标题+地址列），上下文逐字节同；无明确优于一方理由 |
| 2 | 004DF3A0 | S10 | UNDECIDED | 2 | 2 | 空 | 同上，各 2 次，上下文一致，头部差异不涉本行 |
| 3 | 004DFB70 | S10 | UNDECIDED | 2 | 2 | 空 | 同上，各 2 次，ROW 区字节一致 |
| 4 | 004DFCB0 | S10 | UNDECIDED | 2 | 2 | 空 | 同上，各 2 次，反汇编相同 |
| 5 | 004DFE00 | S10 | UNDECIDED | 2 | 2 | 空 | 同上，各 2 次，ROW 区字节一致 |
| 6 | 004E0E80 | S10 | BOTH_IDENTICAL | 3 | 3 | `S10_K8\EVIDENCE\OWNERSHIP_004E0E80.txt#004E0E80` | 两候选字节全同（86B409...，2188 B），取字典序较小 S10_K8 |
| 7 | 006B6EA0 | S22 | BOTH_IDENTICAL | 5 | 5 | `S10_K8\EVIDENCE\SPAWNMANAGER_CTORS.txt#006B6EA0` | 两候选字节全同（10A334...，21109 B），取 S10_K8 |
| 8 | 006F4960 | S10 | UNDECIDED | 2 | 2 | 空 | 两文件各 2 次（章节标题+地址列），上下文一致，头部差异不涉本行 |
| 9 | 006B6FA0 | S22 | BOTH_IDENTICAL | 6 | 6 | `S10_K8\EVIDENCE\SPAWNMANAGER_CTORS.txt#006B6FA0` | 两候选字节全同（10A334...，21109 B），取 S10_K8 |

统计：可定行 = 3（全为 `BOTH_IDENTICAL`），未定行 = 6，无 `UNIQUE_HIT`、无 `BOTH_HIT_JUDGED`。

## 5. 未定行清单与原因

**未定 6 行**：`004DF320`、`004DF3A0`、`004DFB70`、`004DFCB0`、`004DFE00`、`006F4960`（均为 S10 QUEUE entry）。

统一原因（逐行理由见 `decision.tsv` 的 `note` 列，各行独立撰写）：

- 两候选 `QUEUE_DISPATCH_AND_FALSE_KILLS.txt` 的 sha256/字节数不同（42375 vs 42895 B），故不能走"字节一致取 S10_K8"规则。
- 按卡面第 4 节第 3 步在两文件中分别大小写不敏感搜索各 entry 的 8 位十六进制串：**每个 entry 在两文件均恰好出现 2 次**；上下文均为（a）`=== ROW <entry> ===` 章节标题 +（b）反汇编地址列首行（如 `004DF320 53 push ebx`）。出现次数相同、上下文强度相同。
- 我从首个 `=== ROW` 起对两文件做了尾部字节比对：尾部 34317 B 逐字节一致（sha256 相同），差异全部落在头部 REVERIFY/语义摘要区，且这些差异**未提及**这 6 个 entry。

**关于 S10_K8F 头部 REVERIFY 校正的说明（我看了但据卡面规则未用作判定）**：

- 我确实观察到 S10_K8F 头部带 `REVERIFY=... (corrected inner index 0 -> call)`，并把 `queued!=-1` 校正为 `cur==id && queued in {id,-1}`；而盘上 `coverage.tsv` 的这些 QUEUE 行 `one_line_semantics` 恰使用 "queued in {id,-1}" 的校正措辞，与 S10_K8F 头部一致。
- 但卡面第 4 节第 3 步规定的判定依据是"该 entry 的出现次数与上下文强度"，而两候选在这两项上完全相同；REVERIFY 是头部摘要级差异、不绑定这些 entry，且卡面明确要求"照做，别自创"与"不要硬选"。据"宁可少定、不可凑数"的纪律，我把这 6 行判为 `UNDECIDED`，并把上述观察完整记录在此，供 Lead/合并员决策，不擅自硬选。

## 6. 预估并表后 R_OK

- 卡面给定基线：`R_OK = 843 / 1,654`。
- 本次可定行 = 3（`004E0E80`、`006B6EA0`、`006B6FA0`）。
- **预估**（非 Lead 复算）：并表后 `R_OK ≈ 843 + 3 = 846`，即 **846 / 1,654**。6 行 `UNDECIDED` 不计入。

## 7. 确切命令清单

> 均在 `D:\Project\ra2-campaign-forge` 下，经 pwsh 执行；路径段按卡面基准 `lead\next_re_20261117_r14\`。

计算 sha256 / 字节数：
```powershell
$base = "D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
Get-Item -LiteralPath $cov                          # .Length, .LastWriteTime
(Get-FileHash -LiteralPath $cov -Algorithm SHA256).Hash
Get-Item -LiteralPath <候选文件> | Select Length
(Get-FileHash -LiteralPath <候选文件> -Algorithm SHA256).Hash
```

枚举候选（glob 工具，全树）：
```
**/QUEUE_DISPATCH_AND_FALSE_KILLS.txt
**/OWNERSHIP_004E0E80.txt
**/SPAWNMANAGER_CTORS.txt
```

搜 entry 出现次数（大小写不敏感，全文正则匹配计数）——对每个 entry 与每个候选：
```powershell
$re = [regex]::new($e, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
$re.Matches($txt).Count      # $txt = [IO.File]::ReadAllText(<候选文件>)
```

看上下文（打印每个命中行及前后各一行）：
```powershell
$lines = [IO.File]::ReadAllLines(<候选文件>)
for ($i=0; $i -lt $lines.Length; $i++) {
  if ($lines[$i] -match $e) { /* 打印 line $i-1, $i, $i+1 */ }
}
```

diff 两 QUEUE 文件 + 尾部字节一致性校验：
```powershell
Compare-Object -ReferenceObject $a -DifferenceObject $b -IncludeEqual:$false
$idxA = $txtA.IndexOf("=== ROW 004DF320 ===")
$idxB = $txtB.IndexOf("=== ROW 004DF320 ===")
$tailA = $txtA.Substring($idxA); $tailB = $txtB.Substring($idxB)
($tailA -ceq $tailB)   # True；并对 tail 计算 sha256 比对
```

提取 coverage.tsv 原行（用于 delta 列保真）：
```powershell
$covLines = [IO.File]::ReadAllLines($cov)
$covLines[$i].StartsWith($entry + "`t")   # 定位原行
$cols = $line -split "`t"; $cols[5] = $newCol6; $cols -join "`t"
```

delta 列保真自检：对 3 行分别比对列 0,1,2,3,4,6,7 与盘上原行 `-cne`，全部 `True`（一致）。

## 8. 自检：未写 coverage.tsv

- 改前 sha256 = `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2`
- 改后 sha256 = `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2`
- 两者相等（mtime 与字节数亦相等）。**我没有写 `coverage.tsv`**，产物仅在 `R16_EVID9\` 下：`decision.tsv`、`coverage_delta.tsv`、`REPORT.md`。
