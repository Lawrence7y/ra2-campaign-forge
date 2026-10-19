# verify_annotate 跨环境补跑方案（PowerShell 5.1 / Python 复刻）

> 任务=R-VERIFY-RUN · 依据 `out/re_work/re_sprint/R_err_pack/verify_annotate.ps1` + `R_err_exec/exec_report.md`
> 背景：部分环境 shell 权限拦截 `powershell -File verify_annotate.ps1`；本方案提供 **PS 5.1 原版** 与 **Python 复刻** 双轨，任一可执行 shell 的环境均可关卡。
> 禁写面：已加注文档内容 / 台账 / 看板（本方案与配套脚本只读校验，不改冻结源）。

## 1. 产物与分工

| 产物 | 路径 | 用途 |
|:---|:---|:---|
| Python 复刻脚本 | `out/re_work/re_sprint/R_verify_run/verify_annotate.py` | 跨环境主执行体（无三方依赖，Py3.7+） |
| 20 处试跑记录 | `out/re_work/re_sprint/R_verify_run/trial_run_20sites.md` | 对 R-ERR-EXEC 已加注 20 处的试跑取证 |
| 本方案 | `docs/re/verify_annotate_portable.md` | 双轨操作说明 + 等价性说明 |
| PS 原版（只读） | `out/re_work/re_sprint/R_err_pack/verify_annotate.ps1` | 权威脚本，不改 |

## 2. 检查语义（两轨共用，Step 0–7）

| Step | 检查 | 判据 |
|:---:|:---|:---|
| 0 | baseline 快照 | 加注前/后可重建；写 `R_err_pack/baseline/*.md` + `MANIFEST_FORBIDDEN.sha256` |
| 1 | 原文锚点仍在 | `0x568297`×3 文件、`5B`、`s_origCase11Bytes[5]` 均命中 |
> 【W3 勘误 · W3-A6/ISSUE-VA-0X568297-OFFSET】改前：0x568297；改后：0x0056829A (7B: 83 89 2C 01 00 00 10 | or dword ptr [ecx+0x12c], 0x10)；依据：ra2youli/gamemd.exe:0x168295-0x1682A1; errata_sync_master_table.md:16 (R-E01); ra2render.h:96；分级：P0
| 2 | 勘误块已加 | `R-E01`×4 文件、`R-E03`×1 文件 |
| 3 | 只增不删 | baseline 对比 removed=0；added 行含【勘误】 |
| 4 | 禁写面哈希 | `REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md` 哈希不变 |
| 5 | W1 机器码回归 | `0F B6 C0`@net_fix、`56829A`@ra2render.h/.ini |
| 6 | W2 语义红线 | G6/OccuredEvents@trigger_save_pollution、12/12/dead@sw_radius_deadkey |
| 7 | 20 处加注抽检 | E01×5 + E03×3 + E-1×2 + E-2×8 + E-7×2：原文仍在 + 勘误可定位 |

**硬约束**：原文保留不删字；勘误只追加；禁写台账/看板/未授权文档。

## 3. 轨道 A · PowerShell 5.1（原版）

在**可执行 PowerShell** 的环境、仓库根目录：

```powershell
# Step 0 先建 baseline（加注前快照；若已有 baseline 可跳过）
# 见 verify_annotate.ps1 注释 / errata_w1w2_annotate_pack.md §4.2 Step 0
# 手工快照：把 7 份已加注 md 拷到 out/re_work/re_sprint/R_err_pack/baseline/
# 并记录禁写面 SHA256 到 baseline/MANIFEST_FORBIDDEN.sha256

powershell -NoProfile -ExecutionPolicy Bypass -File out/re_work/re_sprint/R_err_pack/verify_annotate.ps1
echo $LASTEXITCODE   # 0 = ALL CHECKS PASS
```

PS 5.1 注意事项（已在原脚本处理）：

1. 脚本必须**纯 ASCII**（无 BOM UTF-8 中文注释会破坏 PS 5.1 解析）。
2. 勘误标记 `【勘误` 用码点拼接：`[char]0x3010 + [char]0x52D8 + [char]0x8BEF`，勿写字面中文。
3. `Select-String -SimpleMatch` = 原文锚点；`-Pattern` = 正则（W2 用 `bit order|G6|OccuredEvents` 等）。
4. `Compare-Object` 按行集合比对；空行不计入 removed。

## 4. 轨道 B · Python 复刻（推荐，跨平台）

```bash
# 任意有 python3 的环境（Windows / WSL / Linux / CI）
cd /d D:/Project/ra2-campaign-forge   # 或你的仓库根

# Step 0 建 baseline（幂等）
python out/re_work/re_sprint/R_verify_run/verify_annotate.py --snapshot

# 主校验
python out/re_work/re_sprint/R_verify_run/verify_annotate.py

# 可选：指定根目录 / 输出 JSON / 指定 baseline 路径
python out/re_work/re_sprint/R_verify_run/verify_annotate.py --root D:/Project/ra2-campaign-forge
python out/re_work/re_sprint/R_verify_run/verify_annotate.py --json out/re_work/re_sprint/R_verify_run/verify_result.json
python out/re_work/re_sprint/R_verify_run/verify_annotate.py --baseline D:/Project/ra2-campaign-forge/out/re_work/re_sprint/R_err_pack/baseline
```

退出码：`0` 全绿 · `1` 有 FAIL · `2` root/用法错误。

### 4.1 与 PS 的等价性

| 点 | PS 5.1 | Python 复刻 | 说明 |
|:---|:---|:---|:---|
| 原文锚点 | `Select-String -SimpleMatch` | `str.count` | 等价 |
| 正则回归 | `Select-String -Pattern` | `re.findall(I\|M)` | 等价（忽略大小写） |
| 只增不删 | `Compare-Object` | `collections.Counter` 行多重集差 | 等价（PS 也不计空行） |
| 勘误标记 | U+3010 U+52D8 U+8BEF | `"\u3010\u52d8\u8bef"` | 等价，且 Python 不受编码破坏 |
| 哈希 | `Get-FileHash SHA256` | `hashlib.sha256` | 等价（大写 hex） |
| Step 2 范围 | 仅 R-E01/R-E03 | 同左 + Step 7 覆盖 E-1/E-2/E-7 | 复刻版更严 |
| baseline 缺失 | WARN | WARN（同） | 可用 `--snapshot` 补建 |

### 4.2 相对 PS 的增强（Step 7）

R-ERR-EXEC 实际加注 20 处（含 E-1/E-2/E-7），PS 原版 Step 1–2 只盯 E01/E03。
Python 版 Step 7 逐处抽检 **原文仍在 + 勘误可定位**，避免「E01/E03 全绿但 E-2 被误删」漏检。

## 5. 补跑操作顺序（建议）

1. **冻结面确认**：只读确认 `REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/RE_COORDINATION.md`、`S15/**`、`S18/**` 未被本轮触碰。
2. **Step 0**：`python verify_annotate.py --snapshot`（或 PS 手工快照）。
3. **主校验**：任一轨道跑 Step 1–7，期望 `FAILURES: 0`。
4. **落盘证据**：把 stdout / JSON 归档到 `out/re_work/re_sprint/R_verify_run/`。
5. **偏差处理**：
   - 原文锚点 GONE → **阻断**（违反「原文保留不删字」），回滚加注。
   - 勘误块 MISSING → 补粘贴模板（`errata_w1w2_annotate_pack.md` / `errata_patch_blocks_E1E2.md`）。
   - removed≠0 → **阻断**，定位删除行并恢复。
   - 禁写面哈希变 → **阻断**，报告 Lead。
   - W1/W2 回归 FAIL → 按 `errata_sync_master_table.md` 新文回写，禁止抄旧值。

## 6. 无 shell 权限环境的降级（检索复刻）

若 Bash/PowerShell 均被权限拦截（如 R-ERR-EXEC 所遇）：

1. 用文件检索工具（Grep/Read）按 Step 1–2、5–7 的 needle 逐条取证；
2. Step 3 构造性保证（仅插入新行、未改原行）+ 原文锚点全在 → 近似 only-add；
3. Step 4 本轮零写入禁写面；
4. 证据落盘 `trial_run_20sites.md`，并在报告注明「检索复刻，非机械执行」。

**降级不等于关卡**：最终仍须在可执行 shell 的环境补跑 `verify_annotate.py`（或 PS 原版）取得 `FAILURES: 0` 机械回执。

## 7. 预期结果与已知残留

| 项 | 预期 |
|:---|:---|
| Step 1/2/5/6/7 | PASS |
| Step 3 | baseline 存在时 PASS（removed=0）；缺失时 WARN |
| Step 4 | 哈希与 `dryrun_preannotate.md` 记录一致（`DFD22783…` / `C81782EC…`）；无 manifest 时 INFO |
| 总判 | `FAILURES: 0` |

残留：

- 本环境 shell 被拦 → 机械回执待补跑；本包给出可直接跑的 `verify_annotate.py` 与取证记录。
- `ra2render.ini:93` 注释「探测半径」改「瞄准圈显示半径（UI-only）」为 E04 待办，不在本验收范围（见 `exec_checklist.md` W2）。
- E-3/E-4（总表 P-2/P-6.2）未执行，不在本任务范围。

*依据：verify_annotate.ps1 六步语义 · R-ERR-EXEC 20 处加注清单 · 本方案只读校验、禁写台账/看板。*
