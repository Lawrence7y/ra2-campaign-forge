# PATCH_SUGGESTION · `except_post` 新鲜性建议性补丁文本（★ 未应用，仅文本）

```
被核对象 = qc151_trip.py + 相关 harness 文件
qc151_trip.py SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508，行数 = 7291
  （本人实算：sha256sum + wc -c + wc -l，2026-11-06T03:38+08:00，路径
   out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py）
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它）
回件时刻 = 2026-11-06T03:47+08:00
```

> ★★ **本文件只是建议性 diff 片段，未应用于任何文件**。
> `qc151_trip.py` 的实际修改属 D-22 nextSteps 第 5 条，**需用户新授权**；
> 本任务（D-22(A) 执行步）的写域仅 `W11_EXCEPT_FRESHNESS/`。
> 补丁语义 = `candidate/except_freshness.py` 的候选判据（T2：B 主 + A 旁证，
> C 备选需新裁定，D 否决），判据组合与六分支决策表见 `T2_CRITERIA.md` §6。

---

## 补丁 1 · `backup_carrier` 补采 `mtime_pre` + 捕获时刻（A 旁证的最小采集面）

**动机**：现行 `:4458-4461` 只记 `size + sha256`，**不记 mtime** ⇒ 跑后无法做
A 加固版差分，历史趟已不可补采（只能对未来趟生效）。
`import time` 已在 `:173`，无需新增导入；`Recorder.add(group, key, value, source,
note="")` 签名（`:446`）兼容。

```diff
--- a/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
+++ b/（建议性文本，未应用）
@@ def backup_carrier(rec: Recorder, carrier_dir: Path) -> dict:
         dst = BACKUP_DIR / name
         dst.write_bytes(src.read_bytes())
         h = sha256_file(dst)
-        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}
-        rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
+        _st_pre = src.stat()
+        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h,
+                     "mtime_pre": _st_pre.st_mtime,
+                     "captured_at_epoch": time.time(),
+                     "captured_at_iso": now_iso()}
+        rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
+        rec.add("RESTORE", f"backup_mtime_pre:{name}", _st_pre.st_mtime,
+                f"{src}:file",
+                note="★ W11/T3 建议：A 加固版旁证采集（跑前实测，不信任进场 mtime）")
```

## 补丁 2 · `copy_post_except_evidence` 加新鲜性判定 + 复制防静默

**动机**：`:4574-4582` 只判 `exists()`、原样复制、零新鲜性判断（TASK §0 前置事实 1，
本轮已亲读核对）；且 `:4582 write_bytes` 失败时无专用留痕。
判据 = `candidate/except_freshness.py::classify_except_post` 的语义（就地内联最小移植，
避免 harness 依赖候选件路径）；**只回答 F（freshness），不当 crash 归因**（`:677` 口径不变）。

```diff
--- a/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
+++ b/（建议性文本，未应用）
@@ def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
-                              out_dir: Path) -> dict | None:
+                              out_dir: Path,
+                              pre_snapshot: dict | None = None) -> dict | None:
@@ （docstring 增补一行）
     ★ 返回证据元信息（`None` = 载体 `except.txt` 不存在）。
+    ★ W11/T3：`pre_snapshot`（backup_carrier 时刻的基线）用于新鲜性判定（F），
+      判据 = sha256 主 + mtime_pre 差分旁证；**不做 crash 归因**（:677）。
@@
     blob = src.read_bytes()
     h = hashlib.sha256(blob).hexdigest()
+    _mtime_post = src.stat().st_mtime
+    # ★ W11/T3 候选语义（最小移植自 candidate/except_freshness.py）：
+    _pre = dict(pre_snapshot or {})
+    _pre_sha, _pre_mtime = _pre.get("sha256"), _pre.get("mtime")
+    if not _pre.get("exists"):
+        _fresh = ("new_first_appearance", "high")      # 跑前缺、跑后在：本趟新出现
+    elif _pre_sha is not None and _pre_sha != h:
+        _fresh = ("new_write", "high")                 # 内容不同：本趟被写（F）
+    elif _pre_mtime is not None and abs(_mtime_post - _pre_mtime) > 0.0:
+        _fresh = ("rewritten_same_content",
+                  "low" if _mtime_post < _pre_mtime else "medium")
+        # ★ 同内容重写（B 盲区被 A 补住）；mtime 倒挂 ⇒ 疑似回拨/utime，置信降级
+    else:
+        _fresh = ("leftover_unchanged", "high")        # 原样遗留（l1b 实测态）
     dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
-    dst.write_bytes(blob)
+    try:
+        dst.write_bytes(blob)
+    except OSError as _exc:
+        rec.add("ERROR", "evidence_copy_write_failed", repr(_exc), f"{dst}:file",
+                note="★ W11/T3 建议：复制失败显式留痕（禁止静默），随后按原语义上抛")
+        raise
     info = {"source": str(src), "evidence_path": str(dst),
             "size": len(blob), "sha256": h,
+            "mtime_post": _mtime_post,
+            "freshness_verdict": _fresh[0], "freshness_confidence": _fresh[1],
+            "freshness_note": "★ F=freshness only；新异常判定归 except_set_diff（:677）",
             "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
                     "（☆ 还原之后仍存在、可复核）"}
```

## 补丁 3 · 调用点接线（两处，保持证据先于还原的现行序）

`:5938-5939` 的 `_except_evidence_copy`（在 `run_guarded_steps` 序里排第 1，
先于 `restore_carrier` 第 6，`:6042-6052`——**该顺序正确，不动**）：

```diff
--- a/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
+++ b/（建议性文本，未应用）
@@ def _except_evidence_copy() -> None:          # qc151_trip.py:5938
-        copy_post_except_evidence(rec, carrier_dir, out_dir)
+        copy_post_except_evidence(rec, carrier_dir, out_dir,
+                                  pre_snapshot=_pre_freshness_snapshot)
```

基线采集点（`:6387` `backup_carrier` 之后、launch 之前——B 判据的基线时机要求，
见 `T2_CRITERIA.md` §3-B-3）：

```diff
@@ （main 内，except 被动基线段 :6390 附近）
         bak = backup_carrier(rec, carrier_dir)
+        _pre_freshness_snapshot = (bak or {}).get("except.txt") or \
+            {"exists": False}
```

## 补丁不做什么（★ 与既有裁定的边界）

1. **不改 `restore_carrier`**（`:4465-4499` 只比 sha+size 的核验语义保持原样）；
2. **不移走/不改名/不写载体 `except.txt`**——方案 C 触碰 U-5 裁定
   （`:6390-6408` 被动基线），需新裁定后另行评估；
3. **不加任何「sha 变化 ⇒ crash」判定**——`:677` 明令禁止；`freshness_verdict`
   只回答 F，`except_set_diff`（`:672-708`）仍是 E（新异常）唯一口径；
4. **不改 `carrier_post_state.json` 的既有字段**（只增不改，历史可比性不断）。

## 验收（若获授权应用后应跑的离线复核）

- `qc151_fields.json` 新增 `RESTORE.backup_mtime_pre:except.txt`；
- `evidence_copy` info 新增 `mtime_post / freshness_verdict / freshness_confidence`；
- 对 l1b_20261021 型「原样遗留」趟：`freshness_verdict == "leftover_unchanged"`；
- 四分支合成验证已由 `candidate/test_except_freshness.py` 离线先行覆盖
  （`PASS=14 FAIL=0 EXIT=0`，见 `_w11_t3_test_out.txt`）。
