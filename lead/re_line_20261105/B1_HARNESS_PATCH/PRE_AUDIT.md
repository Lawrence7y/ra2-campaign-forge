# B1 预审报告 · W11 新鲜性补丁合规性与可应用性预审

> **预审员定位**：默认怀疑。职责是**判断这个补丁该不该应用**，而不是帮它过关。
> **预审结论**：**shouldApply = NO（否决应用，全面阻断）**。
> **依据**：Leader 任务书及建议补丁存在**致命作用域断裂（运行时 NameError）**、**数据契约缺陷（缺失 exists 导致 100% 误报 new_first_appearance）**、**旁证键名不匹配（死代码）**与**改动面边界死锁**。强行应用将摧毁 harness 收尾链路。

---

## 0. 预审基本信息与改前指纹核验

| 检查项 | 预审员实测值（2026-11-06 09:31） | TASK.md §1 Leader 标称值 | 校验结果 |
|---|---|---|---|
| **被核对象** | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | 同左 | 一致 |
| **SHA256** | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | **逐位完全匹配** |
| **字节数** | `399,508` | `399,508` | **完全匹配** |
| **行数** | `7,291` | `7,291` | **完全匹配** |
| **mtime** | `2026-10-20 00:08:02.206731 +0800` (epoch `1792426082.206731`) | `2026-10-20 00:08:02.206731100 +0800` | **完全匹配** |

**实测核算命令**：
```bash
sha256sum D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
wc -c D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
wc -l D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
```
改前文件状态确认未变（`OBJECT_CHANGED = False`）。

---

## 1. 五项必查专项审计

### 1.1 改前指纹自算（必查项 1）
- **核验结论**：通过。实算 SHA256、字节数、行数与 TASK.md §1 逐位完全一致。目标文件自 2026-10-20 以来保持冻结，无脏改动。

### 1.2 三处改动点物理定位与原文比对（必查项 2）
预审员亲读 `qc151_trip.py` 并由探针 `_b1_preaudit.py` 提取原文：
- **改动点 1 (`backup_carrier`)**：
  - **实际行号**：`:4447-4462`（Leader 称“约 :4458-4461”对应备份生成与记录处）；
  - **当前源码原文**（`:4457-4462`）：
    ```python
    4457:         dst = BACKUP_DIR / name
    4458:         dst.write_bytes(src.read_bytes())
    4459:         h = sha256_file(dst)
    4460:         bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}
    4461:         rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
    4462:     return bak
    ```
- **改动点 2 (`copy_post_except_evidence`)**：
  - **实际行号**：`:4561-4599`（Leader 称“:4561，核心 :4574-4582”吻合）；
  - **当前源码原文**（`:4574-4587`）：
    ```python
    4574:     src = carrier_dir / "except.txt"
    4575:     if not src.exists():
    4576:         rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
    4577:                 note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
    4578:         return None
    4579:     blob = src.read_bytes()
    4580:     h = hashlib.sha256(blob).hexdigest()
    4581:     dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
    4582:     dst.write_bytes(blob)
    4583:     info = {"source": str(src), "evidence_path": str(dst),
    4584:             "size": len(blob), "sha256": h,
    4585:             "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
    4586:                     "（☆ 还原之后仍存在、可复核）"}
    4587:     rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",
    ```
- **改动点 3（调用点接线）**：
  - **实际行号**：
    - `:5938-5939`：`def _except_evidence_copy() -> None: copy_post_except_evidence(rec, carrier_dir, out_dir)`；
    - `:6387-6409`：`bak = backup_carrier(rec, carrier_dir)` 与 U-5 被动基线段；
    - `:7118`：`FINALIZE_CODE[0] = finalize_trip(rec, fin_carrier, bak, t0, pre_except_txt, ...)`；
  - **物理存在性**：三处代码段均真实存在，但 **Leader 对调用关系的理解存在重大架构性错误**（详见下文 2.1）。

### 1.3 :677 禁令与 except_set_diff 边界核查（必查项 3）
- **核验对象**：`qc151_trip.py:672-708`（`except_set_diff`）。
- **当前逻辑原文分析**：
  - `:676-677` 明确红线：「**不得**用 `sha` 变化判 crash（★ 游戏自身会重写该文件）」；
  - `:679` 规定唯一有效的新增异常判据：「集合差里含 `Exception occurred at` 的行」；
  - `:5985-5990` 展示了 harness 退出码的唯一触发逻辑：只有 `not setdiff.get("no_new_exception", True)` 才会调用 `note_cleanup_failure` 产生 `EXIT_INTERNAL_ERROR`。
- **误读与冲突判定**：
  - 形式上，补丁增加了注释 `"freshness_note": "★ F=freshness only；新异常判定归 except_set_diff（:677）"`；
  - **但实质上，由于 Leader 在补丁 2 中造成的字典契约错误（缺失 exists 导致恒走 new_first_appearance），任何历史遗留的 `except.txt`（哪怕哈希完全未变）在跑后都会被标记为 `freshness_verdict: "new_first_appearance", confidence: "high"`！**
  - 在 `qc151_fields.json` 的 `EXCEPT` 分组下，一个包含崩溃栈的历史遗留件被高置信标记为“本趟新出现（存在性证据，强）”，必然导致任何消费该字段的下游分析脚本、Nightwatch 或审查员**直接误判为“本趟发生了异常崩溃”**！
  - 这与 `:677` 明令禁止的“不得因文件变动/出现而草率判定崩溃”发生严重的**实质性冲突与误导**。
  - **结论**：在当前补丁实现下，`conflictsWith677 = true`（存在必然误读为 crash 的现实机制）。

### 1.4 U-5 边界核查（必查项 4）
- **核验对象**：`qc151_trip.py:6390-6408`。
- **原文确认**：
  - `:6394-6408` 实施了 V5 §6.1.1 U-5 裁决：“在既有禁写范围内移除 except_reset 对载体 except.txt 的覆盖写。改为被动读取现有内容作基线。”
  - `pre_except_txt = _except_pre_path.read_text(...)`，且记 `reset_verdict: "SKIPPED_U5"`。
- **补丁核验**：
  - 建议补丁未引入任何 `except_reset` 调用，未对载体 `except.txt` 进行写盘、重命名或移动；
  - 补丁遵守了 U-5 的只读约束。若仅看 U-5 自身边界未被越界，但无法挽救其他结构性致命伤。

### 1.5 候选语义与 harness 现有逻辑的结构性冲突（必查项 5）
- **核验对象**：`W11_EXCEPT_FRESHNESS/candidate/except_freshness.py` vs `PATCH_SUGGESTION.md`。
- **结构性冲突发现**：
  1. **截断假定冲突（丢失 absent_both 与 vanished）**：
     - `candidate/except_freshness.py:187-202` 的核心价值在于六分支完备决策表，尤其是分支 1（`absent_both`：跑前无、跑后无，代表绝大多数正常的无崩溃趟）与分支 3（`vanished`：跑前有、跑后失，代表异常删除）；
     - 然而 Leader 在 `PATCH_SUGGESTION.md` 中将新鲜性判定内联于 `copy_post_except_evidence` 的 `:4574` 之后。该函数在 `:4575-4578` 明确规定：
       ```python
       if not src.exists():
           rec.add("EXCEPT", "evidence_copy", None, ...)
           return None
       ```
     - 这意味着只要跑后没有 `except.txt`（干净运行），函数直接提前退出返回 `None`，根本不会执行内联判定代码！候选模块宣称的 `absent_both` 与 `vanished` 语义在 harness 内直接被截断丢失。
  2. **基线时机假定冲突**：
     - `candidate/except_freshness.py` 假定调用方传入规范的 `make_pre_snapshot` 结构；
     - 但 Leader 试图复用 `backup_carrier` 的 `bak` 字典，却没有保持字段同构，导致字段语义全面崩塌。

---

## 2. 发现的 Leader 严重错误清单（leaderErrors）

在本次预审中，预审员对 Leader 的任务书（`TASK.md`）及建议补丁（`PATCH_SUGGESTION.md`）进行了逐行静态分析与逻辑推演，发现了 **6 处致命或严重错误**：

### 错误 1：顶级函数作用域断裂，导致运行时必抛 `NameError`
- **出处**：`TASK.md` §3.3、`PATCH_SUGGESTION.md` §补丁 3。
- **事实**：
  Leader 建议在 `main()` 函数内部（`:6390` 附近）构造局部变量：
  `_pre_freshness_snapshot = (bak or {}).get("except.txt") or {"exists": False}`；
  然后在 `:5938-5939` 的 `_except_evidence_copy()` 中直接使用：
  `copy_post_except_evidence(rec, carrier_dir, out_dir, pre_snapshot=_pre_freshness_snapshot)`。
- **致命后果**：
  `_except_evidence_copy()` 是定义在顶级函数 `finalize_trip()`（`:5900`）内部的局部辅助函数！而 `main()`（`:6300+`）是另一个独立的顶级函数。
  在 Python 中，顶级函数 `finalize_trip` 绝不可能访问到 `main()` 内部的局部变量 `_pre_freshness_snapshot`！
  一旦按 Leader 补丁修改，执行收尾流程时调用 `_except_evidence_copy()` 必将立即抛出：
  `NameError: name '_pre_freshness_snapshot' is not defined`！
  收尾被致命异常中断，导致整个 harness 运行崩溃（`_b1_preaudit.py` 探针已 100% 证实该 NameError）。

### 错误 2：`backup_carrier` 缺失 `"exists"` 键，导致 100% 误判 `new_first_appearance`
- **出处**：`PATCH_SUGGESTION.md` §补丁 1 与 §补丁 2。
- **事实**：
  - 在补丁 1 中，Leader 在 `backup_carrier` 为 `bak[name]` 新增字段时写道：
    `bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h, "mtime_pre": _st_pre.st_mtime, "captured_at_epoch": time.time(), "captured_at_iso": now_iso()}`。**注意：Leader 完全漏掉了 `"exists": True`**！
  - 在补丁 3 中：`_pre_freshness_snapshot = (bak or {}).get("except.txt") or {"exists": False}`。当跑前 `except.txt` 存在时，返回 `bak["except.txt"]`（该字典不含 `"exists"` 键）。
  - 在补丁 2 中，Leader 的判定逻辑第一行就是：
    `if not _pre.get("exists"): _fresh = ("new_first_appearance", "high")`。
- **致命后果**：
  当跑前 `except.txt` 存在时，`_pre.get("exists")` 返回 `None`，`not None` 恒为 `True`！
  **所有跑前原样存在的历史文件，全部被无条件判定为 `new_first_appearance`（高置信新出现）！**
  后续的 `new_write`、`rewritten_same_content`、`leftover_unchanged` 分支变成了永远无法到达的废代码！整个补丁的核心功能彻底颠倒错乱。

### 错误 3：时间戳键名不匹配，导致 A 旁证（mtime 差分）逻辑沦为死代码
- **出处**：`PATCH_SUGGESTION.md` §补丁 1 与 §补丁 2。
- **事实**：
  - 补丁 1 中，Leader 存入字典的键名是 `"mtime_pre": _st_pre.st_mtime`；
  - 补丁 2 中，Leader 读取字典的键名却是 `_pre_sha, _pre_mtime = _pre.get("sha256"), _pre.get("mtime")`；
  - 由于存的是 `mtime_pre`，读的是 `mtime`，`_pre_mtime` 永远为 `None`。
- **致命后果**：
  `elif _pre_mtime is not None and abs(_mtime_post - _pre_mtime) > 0.0:` 分支由于前置条件不满足，永远不可能被触发！
  W11 耗费大量精力论证的“A 方案同内容重写旁证（`rewritten_same_content`）”在补丁中变成了纯粹的死代码。

### 错误 4：调用关系与改动面自相矛盾（“两处调用点”虚假表述与改动面死锁）
- **出处**：`TASK.md` §3.3、§6.2。
- **事实**：
  Leader 声称只需修改“两处调用点（:5938-5939 与 :6390 附近）”，并严令“证明只改了三处，不许扩大改动面”。
  但实际上，`copy_post_except_evidence` 在全局只有唯一一处调用点（`:5939`）；`:6390` 根本不是调用点。
  若要修复错误 1（作用域断裂），必须在中间传递参数：修改 `finalize_trip` 的函数签名（`:5900`）并在 `main()` 的 `finally` 块（`:7118`）中显式传入 `_pre_freshness_snapshot`；或者在 `finalize_trip` 内部直接从已有参数 `bak` 派生。
  但如果按 Leader“严格按建议补丁修改三处、不得扩大”的要求，任何修复方案都会因扩大改动面或偏离任务书而直接违规，陷入执行死锁。

### 错误 5：判定逻辑前置截断，导致 `absent_both` 语义无法产出
- **出处**：`PATCH_SUGGESTION.md` §补丁 2。
- **事实**：
  `copy_post_except_evidence` 的原始设计是在跑后文件缺失时立即 `:4578 return None`。
  Leader 将判定逻辑塞在该 early-return 之后，导致最普遍的正常态（跑前无、跑后无，即 `absent_both`）无法在此处输出新鲜性判定。

### 错误 6：在 `.gitignore:33` 忽略 `out/` 的前提下，仍要求 `git diff` 验证
- **出处**：`TASK.md` §5、§6.2。
- **事实**：
  `.gitignore:33` 明文配置了 `out/` 忽略规则。`git diff` 对 `out/` 下的文件输出永远为空。
  Leader 在 §5 称要求提供 `git diff 输出`，在 §6.2 称用 `git diff --stat 证明只改了三处`，属于未充分核实版本控制状态的错误要求。

---

## 3. 预审决策与阻断依据总结

| 决策字段 | 预审裁定 | 说明 |
|---|---|---|
| **shouldApply** | **NO** | **坚决否决应用，全面阻断**。硬着头皮打上会直接造成运行期 NameError 崩溃与业务逻辑 100% 误判。 |
| **conflictsWith677** | **true** | 补丁缺陷导致历史遗留 `except.txt` 100% 误标为 `new_first_appearance`（高置信新出现），必然引发下游对崩溃的严重误读，触发 :677 禁令风险。 |
| **threeSitesLocated** | **true** | 三处物理代码位置均在 `qc151_trip.py` 中准确查实并给出原文。 |
| **siteLines** | `backup_carrier: 4447-4462 (核心 4458-4461); copy_post_except_evidence: 4561-4599 (核心 4574-4586); finalize_trip / _except_evidence_copy: 5900, 5938-5939; main backup & baseline: 6387, 6390-6409; finalize_trip 调用点: 7118` | 详细标明各改动点及关联调用链行号。 |
| **preSha256** | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 改前实算 SHA256。 |
| **preBytes** | `399508` | 改前实算字节数。 |

### 阻断原因详述（blockReason）
1. **运行期崩溃阻断（NameError）**：`_except_evidence_copy`（位于 `finalize_trip` 内部）无法访问 `main` 中的局部变量 `_pre_freshness_snapshot`，直接应用必然抛出 `NameError`，导致 harness 收尾全面崩溃；
2. **判定逻辑倒错阻断（100% 伪造 new_first_appearance）**：`backup_carrier` 未存入 `"exists": True`，导致补丁 2 的 `if not _pre.get("exists")` 恒真，所有原样遗留文件全部被误判为新出现，严重破坏数据真实性；
3. **死代码阻断（键名不匹配）**：存入 `mtime_pre` 却读取 `mtime`，导致 A 旁证逻辑沦为摆设；
4. **规约死锁阻断**：Leader 限制的“严格只改三处”无法在语法正确的前提下完成作用域接线。

**预审员立场**：
在预审阶段勇于指出设计缺陷并予以阻断，不仅是对系统质量的最高负责，也是守住正式 harness 稳定性的关键防线。本补丁建议不可应用。
