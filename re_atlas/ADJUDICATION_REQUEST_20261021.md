# 【RE-ATLAS 裁决请求】提交被 Mimosa L3 持续阻断，需要三项决定

日期：2026-10-21 23:1x
提出者：RE-ATLAS 驱动器
状态：**已连续阻断三次**（R-020 首提、R-020+R-021、R-020+R-021 重提）

---

## 一、现象

`git commit` 在 `D:/Project/ra2-forge-public` 被 **Mimosa L3 强制拦截**，每次报
**21 处 high + 1 处 low**，最高等级 high，提示"高危已强制拦截，请修复并重新扫描"。

```
tools/atlas_audit.py:189                [high] 路径穿越
tools/atlas_audit.py:193                [high] 路径穿越
tools/atlas_audit.py:230                [high] 路径穿越
tools/atlas_apply_patches.py:211        [high] 路径穿越
tools/atlas_apply_patches.py:228        [high] 路径穿越
tools/atlas_toc.py:137                  [high] 路径穿越
tools/atlas_toc.py:144                  [high] 路径穿越
tools/atlas_va_crosscheck.py:153        [high] 路径穿越
tools/atlas_va_crosscheck.py:191        [high] 路径穿越
tools/verify_bss_claims.py:311          [high] 路径穿越
tools/verify_bss_claims.py:333          [high] 路径穿越
lead/dropped611/scripts/cont01_scan.py:410  [high] 路径穿越
（另 9 处未在提示中逐条列出，合计 21 处 high）
```

## 二、已核实的四点（不是猜测）

1. **报警点全部不在本线写域。** 12 个文件分布在 `tools/` 与
   `lead/dropped611/scripts/`，按驱动器铁律 §8.4 **我不得修改**。

2. **暂存区是干净的。** `git diff --cached --name-only` 只有 `re_atlas/` 下
   12 个文件（6 个 md + 5 个工具 + 1 个证据），**没有** `tools/`、`lead/` 的任何改动。

3. **不是提交内容触发的。** 同一批 `re_atlas/tools/*.py` 在 `b7f0508`（22:5x）
   成功提交并推送过，当时的暂存集合同样只含 `re_atlas/`。

4. **报警文件内容没变。** 它们的 mtime 是 `2026-10-21 22:08:48–49`，
   **早于**上述几次成功提交。所以变化在 Mimosa 侧
   （L3 强制策略启用，或扫描缓存失效后重新全仓扫描），不在这些文件里。

## 三、抽查判据（一处代表性报警）

`tools/atlas_audit.py:189`：

```python
with open(args.va_out, "w", encoding="utf-8") as fh:
```

`args.va_out` 是**该工具自己的 CLI 参数**。开发者跑自己的工具、指定自己的输出路径，
不构成可利用的越权写。扫描器把"`open()` 的路径来自变量"判成路径穿越，
属启发式过报；`lead/dropped611/scripts/cont01_scan.py:410` 同型。

**我不主张它们一定无害** —— 我只主张：这些判断需要 `tools/` 的负责人来做，
而那个人不是我。

## 四、我没有采取的做法（请确认是对的）

按铁律 §8.5「不得为绕过本地安全钩子而给文件改名、转码或拆分」与 §9，
我**没有**使用以下任何手段：

- `git commit --no-verify` / `git push --no-verify`
- 临时改名、转码、拆包 `re_atlas/tools/*.py` 以规避扫描
- 关闭或跳过 Mimosa
- 把改动推到另一个分支绕开门禁

## 五、请裁决（三选一）

| 选项 | 内容 | 后果 |
|:---|:---|:---|
| **A（推荐）** | 由 Lead / `tools/` 负责人在 `tools/` 侧修复这 21 处（或确认过报后加豁免） | 本线提交恢复；`tools/` 的真实风险也被审视一遍 |
| **B** | 确认扫描器过报，对 `re_atlas/` 提交放行 | 最快；但 `tools/` 的 21 处仍留在告警里，下次仍会撞上 |
| **C** | 维持现状，`re_atlas/` 内容只留在工作区 | 公开仓落后；**本地工作区有完整内容，不丢失** |

## 六、当前未提交的内容（都在工作区，按选项 C 也不会丢）

`D:/Project/ra2-campaign-forge/re_atlas/` 下：

- `kb/30_ini_subsystem.md` §7.1/§7.2（R-016 复核记录与边界）、§13（RulesClass 节表）
- `kb/22_abstractclass_vtable_slots.md` §4.2/§4.3（槽 25）
- `INDEX.md` §C.9–C.12
- `STATUS.md` / `LEDGER.md`（R-020、R-021）/ `CONFLICTS.md`（G-15–G-22）
- `HANDOFF_TO_GOAL3T.md` H-010–H-014
- `tools/dump_rules_sections.py`（新）、`tools/dump_ini_{nodes,readers,keymap,keyindex}.py`（加固）
- `evidence/rules_sections.txt`（新）与四份既有证据重生成

## 七、与本裁决无关但需一并告知

- Mimosa 另报 `ra2forge/maplib.py:161` [low] 不安全随机数（不阻断，非本线写域，我未改动）。
- 有一次钩子提示"未取得完整扫描结论（`python_ast_unavailable` ×4）"，
  按兼容策略放行。因此**不能宣称项目整体安全**。

---

**等待期间**：本线继续做离线分析，不空等，也不重复发问。
