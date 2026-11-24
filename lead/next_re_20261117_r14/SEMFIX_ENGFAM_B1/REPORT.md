# SEMFIX-ENGFAM-B1 — 报告（完成：17/17 行）

批次 B1：34 行按 entry 数值升序排序后取前 17 行。输出目录 `SEMFIX_ENGFAM_B1\`。

## 目标与判定来源

- 目标二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
  SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（已校验一致）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`；capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26，Python 3.12.10
- 依据改写方向（已裁定，不重开）：③b④ 全族不成立；成立通道为 ③b②（4 处 call 派生 HRESULT 检查 `test eax,eax`+`jl`，失败落点不清零 eax 原样返回，成功 `xor eax,eax` 返回 0，被调用方以 `test/jge` 消费）。
- 只读线索目录 `TIEBREAK_ENGFAM\`、`S17_ENGFAM\`、`SEMFIX_ENGFAM\`：仅复用代码方法，不复用结论。

## 切片命令与 17 个 entry

过滤语义：`(?i)unproven|unverified|not proven`，且全 S17、全 `[已证]`、全在 atlas。取 `coverage.tsv` 第 4 列语义匹配者共 34 行，按 entry 数值升序排序后，`Select-Object -First 17` 为本批。

复现脚本：`work/s0_slice.py`（调用随附 `work/semfix_lib.py::load_target_rows`，语义过滤后断言 `len==34`、subsystem 集合 `=={'S17'}`、grade 集合 `=={'[已证]'}`）。等价 PowerShell 切片命令：

```powershell
$rows = Get-Content 'COVERAGE\coverage.tsv' | ForEach-Object { $_ -split "`t" } |
  Where-Object { $_.Count -ge 6 -and $_[3] -match '(?i)unproven|unverified|not proven' }
# 34 行；按 entry 数值升序
$sorted = $rows | Sort-Object { [Convert]::ToUInt32($_[0],16) }
$b1 = $sorted | Select-Object -First 17
$b1 | ForEach-Object { $_[0] }
```

B1 的 17 个 entry（升序）：

```
0067FDF0 0067FE70 0067FEF0 0067FF70 0067FFF0 00680070 006800F0 00680170 006801F0
00680270 006802F0 00680370 006803F0 00680470 006804F0 00680570 00680670
```

（序号 01–16 与 18；模板第 17 槽 `0x6805F0` 归 S05，故跳过。）

## 本批总表（17 行）

| entry | 类名取得 | ③b② 成立 | 是否改写 |
|---|---|---|---|
| 0067FDF0 | 是 | 是 | 是 |
| 0067FE70 | 是 | 是 | 是 |
| 0067FEF0 | 是 | 是 | 是 |
| 0067FF70 | 是 | 是 | 是 |
| 0067FFF0 | 是 | 是 | 是 |
| 00680070 | 是 | 是 | 是 |
| 006800F0 | 是 | 是 | 是 |
| 00680170 | 是 | 是 | 是 |
| 006801F0 | 是 | 是 | 是 |
| 00680270 | 是 | 是 | 是 |
| 006802F0 | 是 | 是 | 是 |
| 00680370 | 是 | 是 | 是 |
| 006803F0 | 是 | 是 | 是 |
| 00680470 | 是 | 是 | 是 |
| 006804F0 | 是 | 是 | 是 |
| 00680570 | 是 | 是 | 是 |
| 00680670 | 是 | 是 | 是 |


## 锚点与失败清单

- 类名 `未取得` 的行：无（17 行全部取得元素类类名）。
- ③b② 不成立的行：无（17 行全部成立）。
- 每行证据均含该行独立的向量地址 / 失败落点 / 成功 xor / Save_Core 调用点 / 调用方消费点；改写后的 17 条 one_line_semantics 互不相同。
- base_rate: rows=17, class_named=17, ring3b2_ok=17, rewritten=17, rate=1.0000
