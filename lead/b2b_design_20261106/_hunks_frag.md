```diff
@@ -212,6 +212,21 @@
 # ★ 载体内五个文件（`QC141:152-160`）
 CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
                  "ra2opt_play.bat", "except.txt")
+
+
+# ★★ B2b/N9：F（freshness）命名空间**单一真源**。
+#   ★ E 恒用 "EXCEPT" group；整趟退出码唯一判据恒在 :5985-5990 的集合差，
+#     F 字段与 F 代码**一律不得**进入该判据（静态门禁逐 token 核）。
+#   ★ F 结论恒 usable_as_crash_evidence=False（:677 口径：sha 变化不判 crash）。
+FRESHNESS_GROUP = "FRESHNESS"
+FRESHNESS_KEY_PREFIX = "freshness_"
+FRESHNESS_VERDICTS = ("unknown", "absent_both", "new_first_appearance",
+                      "vanished", "leftover_unchanged", "new_write",
+                      "rewritten_same_content", "error_pre_snapshot",
+                      "post_read_error")
+FRESHNESS_CONFIDENCES = ("high", "medium", "low", "none")
+FRESHNESS_SNAPSHOT_STATES = ("unknown", "absent_confirmed", "present", "error")
+
 
 # ===========================================================================
 # §1 · 两控常量（★ 逐字承自 `QC141:149`/`:150`/`:160`；★ 真值不写死为参数）
```

```diff
@@ -4458,6 +4473,10 @@
         dst.write_bytes(src.read_bytes())
         h = sha256_file(dst)
         bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}
+        rec.add("RESTORE", f"backup_mtime_pre:{name}",
+                float(src.stat().st_mtime), f"{src}:file",
+                note="★ B2b/N10：跑前 mtime 显式留痕（★ 不进 bak[name] 三键契约）")
+
         rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
     return bak
 
```

```diff
@@ -4558,8 +4577,131 @@
         encoding="utf-8")
 
 
+def make_pre_freshness_snapshot(except_path: Path) -> dict:
+    """★ B2b/F：跑前 `except.txt` **带状态标签**的基线快照（纯只读，不写载体）。
+
+    ★★ N3 硬约束：`state` 是**唯一**判别口，`exists` 不得被用于反推状态。
+      `None` / `{}` / 缺 `state` / 脏值 ⇒ 一律 unknown（未采集），
+      **绝不等于**「跑前确认无件」。
+    ★ N10：`captured_at_epoch` 与 `captured_at_iso` 双时刻必留，缺一即契约失败。
+    ★ N1：采集抛异常 ⇒ state="error" 独立出口，不降级、不静默、不给 high。
+    """
+    snap = {"state": "unknown", "exists": None, "size": None,
+            "sha256": None, "mtime_pre": None,
+            "captured_at_epoch": None, "captured_at_iso": None,
+            "error": None, "traceback": None,
+            "source": "script:make_pre_freshness_snapshot"}
+    try:
+        p = Path(except_path)
+        snap["captured_at_epoch"] = time.time()
+        snap["captured_at_iso"] = now_iso()
+        if not p.exists():
+            snap["state"] = "absent_confirmed"
+            snap["exists"] = False
+            return snap
+        st = p.stat()
+        snap["state"] = "present"
+        snap["exists"] = True
+        snap["size"] = int(st.st_size)
+        snap["mtime_pre"] = float(st.st_mtime)
+        snap["sha256"] = sha256_file(p)
+    except Exception as exc:
+        import traceback
+        snap["state"] = "error"
+        snap["error"] = f"{type(exc).__name__}: {exc}"
+        snap["traceback"] = "".join(traceback.format_exception(exc))
+    return snap
+
+
+def classify_except_freshness(pre_freshness_snapshot, post_observed: dict) -> dict:
+    """★ B2b/F：只回答 **F（本趟窗口内是否被写/新出现）**。
+
+    ★★ N9：本函数不得引用退出码判据（:5985-5990）、不得登记收尾失败、
+      不得引用任何退出码常量；E（新异常）唯一口径恒为母本 :672-708。
+      `usable_as_crash_evidence` 恒 False，任何 F verdict 都不得作为崩溃证据。
+    ★★ N3：`state` 判别优先于一切；unknown ⇒ 不可判，**恒不给 high**。
+    """
+    out = {"verdict": None, "confidence": "none", "is_new": None,
+           "note": "", "usable_as_crash_evidence": False,
+           "pre_snapshot_state": "unknown"}
+
+    def _finish(verdict: str, confidence: str, is_new, note: str) -> dict:
+        out.update({"verdict": verdict, "confidence": confidence,
+                    "is_new": is_new, "note": note,
+                    "usable_as_crash_evidence": False})
+        return out
+
+    pre = (pre_freshness_snapshot
+           if isinstance(pre_freshness_snapshot, dict) else {})
+    st = pre.get("state")
+    if st not in FRESHNESS_SNAPSHOT_STATES:
+        st = "unknown"          # ★ None / {} / 缺 state / 脏值 ⇒ 一律「未采集」
+    out["pre_snapshot_state"] = st
+
+    post = post_observed if isinstance(post_observed, dict) else {}
+    # ★ N1：错误独立出口，优先于一切状态折叠
+    if post.get("read_error"):
+        return _finish("post_read_error", "none", None,
+                       "★ 跑后件读/复制失败（独立 error 出口，禁止静默）："
+                       f"{post['read_error']}；pre_snapshot_state={st}")
+    # ★★ N3/N2：unknown 与 absent_confirmed 在第一个分支就分道，禁止折叠
+    if st == "unknown":
+        return _finish("unknown", "none", None,
+                       "★ 跑前快照未采集/传参丢失/采集未完成 ⇒ F 不可判；"
+                       "未知 ≠ 不存在；不得据此输出「本趟新出现」或 high")
+    if st == "error":
+        return _finish("error_pre_snapshot", "none", None,
+                       f"★ 跑前采集失败（独立 error 出口）：{pre.get('error')!r}")
+
+    post_exists = bool(post.get("exists"))
+    if not post_exists:
+        if st == "absent_confirmed":
+            return _finish("absent_both", "low", False,
+                           "★ 跑前确认无件 + 跑后无件 ⇒ F=未见新出现；"
+                           "但「文件未出现」不能证无崩溃（E 口径另算）")
+        return _finish("vanished", "none", None,
+                       "★ 跑前在、跑后失 ⇒ 异常态旗标（被删/改名/复制链中断），"
+                       "须人工复核；不给 high、不判本趟新出现")
+
+    if st == "absent_confirmed":
+        return _finish("new_first_appearance", "high", True,
+                       "★ 跑前确认无件 + 跑后在地 ⇒ F=本趟新出现（存在性）；"
+                       "是否新崩溃仍只由 :672-708 集合差裁定")
+
+    # ---- st == "present" ----
+    pre_sha = pre.get("sha256")
+    if not pre_sha:
+        return _finish("error_pre_snapshot", "none", None,
+                       "★ 跑前在场但缺 sha256 ⇒ B 主判据不可用"
+                       "（独立 error 出口，不降级为 high、不静默）")
+    post_sha = post.get("sha256")
+    if not post_sha:
+        return _finish("post_read_error", "none", None,
+                       "★ 跑后缺 sha256 ⇒ 无法比对（error 出口）")
+    if post_sha != pre_sha:
+        return _finish("new_write", "high", True,
+                       "★ 字节内容不同 ⇒ F=本趟被写；是否新异常归集合差（:677）")
+
+    pre_mt, post_mt = pre.get("mtime_pre"), post.get("mtime_post")
+    if pre_mt is None or post_mt is None:
+        return _finish("leftover_unchanged", "medium", False,
+                       "★ sha 同但 mtime 侧缺失 ⇒ A 旁证不可用，"
+                       "同内容重写盲区此趟未覆盖（如实标注，不虚报 high）")
+    if abs(float(post_mt) - float(pre_mt)) <= 0.0:
+        return _finish("leftover_unchanged", "high", False,
+                       "★ 跑前在 + sha 同 + mtime 未变 ⇒ 原样遗留（非本趟写入）")
+    if float(post_mt) < float(pre_mt):
+        return _finish("rewritten_same_content", "low", True,
+                       "★ sha 同、mtime 变且回拨 ⇒ 疑似时钟回拨/utime 拉回，"
+                       "置信降级为 low，须人工复核")
+    return _finish("rewritten_same_content", "medium", True,
+                   "★ sha 同而 mtime 变 ⇒ 同内容重写（F 旁证补 B 盲区）")
+
+
 def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
-                              out_dir: Path) -> dict | None:
+                              out_dir: Path,
+                              pre_freshness_snapshot: dict | None = None
+                              ) -> dict | None:
     """★★★ `QC162:W7`：★ 在**还原之前**把本趟跑后的 `except.txt` 原件
     （★ 与五个载体件的跑后状态）**另存一份证据副本**进 `--out-dir`。
 
```

```diff
@@ -4572,20 +4714,105 @@
     ★ 返回证据元信息（`None` = 载体 `except.txt` 不存在）。
     """
     src = carrier_dir / "except.txt"
-    if not src.exists():
-        rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
-                note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
-        return None
-    blob = src.read_bytes()
-    h = hashlib.sha256(blob).hexdigest()
-    dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
-    dst.write_bytes(blob)
+    blob = None
+    h = None
+    dst = None
+    post_observed = {"exists": None, "size": None, "sha256": None,
+                     "mtime_post": None, "captured_at_iso": None,
+                     "read_error": None}
+
+    def _emit_f(fresh: dict, stage: str) -> None:
+        """★ N4：正常与错误**每一条**出口都落盘 F 字段（不空转）。
+
+        ★★ N9：全部写进 FRESHNESS_GROUP，键名一律带 FRESHNESS_KEY_PREFIX；
+          本函数不读退出码判据、不登记收尾失败、不引用退出码常量。
+        """
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "verdict",
+                fresh["verdict"], "script:classify_except_freshness",
+                note=f"stage={stage}；F 只答新鲜性，E 归 :672-708 集合差")
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "confidence",
+                fresh["confidence"], "script:classify_except_freshness",
+                note="★ none = 不可判；unknown 恒 none，禁止映射到 high")
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "is_new",
+                fresh["is_new"], "script:classify_except_freshness",
+                note="★ None = 未测写 null（Recorder :439-440 口径），"
+                     "不得写 False 表示未知")
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "note",
+                fresh["note"], "script:classify_except_freshness",
+                note=fresh["note"])
+        rec.add(FRESHNESS_GROUP, "pre_snapshot_state",
+                fresh["pre_snapshot_state"],
+                "script:make_pre_freshness_snapshot",
+                note="★ unknown / absent_confirmed / present / error 三态可分")
+        rec.add(FRESHNESS_GROUP, "usable_as_crash_evidence",
+                fresh["usable_as_crash_evidence"],
+                "script:classify_except_freshness",
+                note="★★ 恒 False：F 结论不得作为本趟崩溃证据（:677）")
+        rec.add(FRESHNESS_GROUP, "captured_at_iso",
+                post_observed.get("captured_at_iso"), "script:now_iso",
+                note="★ N10：跑后观测时刻（ISO-8601）；跑前同名键在快照内")
+
+    try:
+        if not src.exists():
+            post_observed["exists"] = False
+            post_observed["captured_at_iso"] = now_iso()
+            rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
+                    note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
+            # ★ N4：早退分支同样落盘 F 字段（不可只算不写）
+            _emit_f(classify_except_freshness(pre_freshness_snapshot,
+                                              post_observed), "src_missing")
+            return None
+        post_observed["captured_at_iso"] = now_iso()
+        blob = src.read_bytes()
+        st = src.stat()
+        h = hashlib.sha256(blob).hexdigest()
+        post_observed.update({"exists": True, "size": len(blob),
+                              "sha256": h, "mtime_post": float(st.st_mtime)})
+        dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
+        dst.write_bytes(blob)
+    except Exception as exc:
+        # ★★ N10：复制/读取失败 ⇒ 先 rec.add("ERROR", ...) 显式留痕，再**上抛**
+        import traceback
+        where = f"{src}:file"
+        rec.add("ERROR", "freshness_copy_failed",
+                f"{type(exc).__name__}: {exc}", where,
+                note="★★ B2b/N10：复制失败显式留痕，不许静默降级")
+        rec.add("ERROR", "freshness_copy_stage",
+                "read_bytes/stat/write_bytes", where,
+                note="captured_at_iso="
+                     f"{post_observed.get('captured_at_iso')!r}")
+        rec.add("ERROR", "freshness_copy_traceback",
+                "".join(traceback.format_exception(exc)), "script:traceback")
+        post_observed["read_error"] = f"{type(exc).__name__}: {exc}"
+        # ★ N4/N1：错误分支同样落盘 F 字段，且走独立 error 出口
+        _emit_f(classify_except_freshness(pre_freshness_snapshot,
+                                          post_observed), "copy_failed")
+        raise
+
     info = {"source": str(src), "evidence_path": str(dst),
             "size": len(blob), "sha256": h,
             "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
-                    "（☆ 还原之后仍存在、可复核）"}
+                    "（☆ 还原之后仍存在、可复核）",
+            # ★★ N4/N6/N10：正常路径**必须**落盘的 F 字段（B2 在此空转）
+            "mtime_post": post_observed["mtime_post"],
+            "freshness_verdict": None,
+            "freshness_confidence": None,
+            "freshness_note": None,
+            "captured_at_iso": None,
+            "pre_snapshot_state": None,
+            "pre_freshness_snapshot": None}
+    fresh = classify_except_freshness(pre_freshness_snapshot, post_observed)
+    info["freshness_verdict"] = fresh["verdict"]
+    info["freshness_confidence"] = fresh["confidence"]
+    info["freshness_note"] = fresh["note"]
+    info["captured_at_iso"] = post_observed["captured_at_iso"]
+    info["pre_snapshot_state"] = fresh["pre_snapshot_state"]
+    info["pre_freshness_snapshot"] = (
+        pre_freshness_snapshot
+        if isinstance(pre_freshness_snapshot, dict) else None)
     rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",
             note="★★ 跑后 except.txt 原件副本（先于 restore_carrier）")
+    _emit_f(fresh, "copied")   # ★ N4：正常路径同样落盘（非仅早退分支）
     # ★ 跑后载体件快照（★ 供"证据先于还原"复核：证明取的是跑后状态）
     files: dict = {}
     for name in CARRIER_FILES:
```

```diff
@@ -5906,7 +6133,8 @@
                   mother_baseline: dict | None = None,
                   carrier_identity: dict | None = None,
                   handover: Path | None = None,
-                  created_receipt: dict | None = None) -> int:
+                  created_receipt: dict | None = None,
+                  pre_freshness_snapshot: dict | None = None) -> int:
     """★★★ `QC157:3`：★ 覆盖**全程**的收尾（★ `finally` 调用本函数）。
 
     ★★ `QC162:W7` —— ★★ **证据必须先于还原**（★ 本卡最重）：
```

```diff
@@ -5936,7 +6164,8 @@
     state: dict = {"evidence": None, "pre_manifest": None, "delete": None}
 
     def _except_evidence_copy() -> None:
-        copy_post_except_evidence(rec, carrier_dir, out_dir)
+        copy_post_except_evidence(rec, carrier_dir, out_dir,
+                                 pre_freshness_snapshot=pre_freshness_snapshot)
         # ★★ 第 1 项：★ 证据**先搬出**并**逐件验 SHA**
         ev = move_out_evidence_and_verify(rec, carrier_dir, out_dir)
         state["evidence"] = ev
```

```diff
@@ -6294,6 +6523,9 @@
     bak: dict = {}
     t0: list = []
     pre_except_txt = None
+    # ★★ B2b/E1/N3：★ **try 之前**预初始化 ⇒ 五个早退 + 异常路径均不会
+    #    未绑定；`None` 语义 = **未采集（unknown）**，绝不等于「跑前无件」。
+    _pre_freshness_snapshot: dict | None = None
     budget = TripBudget(rec)
     ACTIVE_REC[0] = rec       # ★ 第 3 项：★ 最外层最终落盘要用同一 rec
     # ★★ 进程身份跟踪（外部裁定：Popen 后须建立可清理所有权）
```

```diff
@@ -6386,6 +6618,15 @@
         budget.begin_stage("backup")
         bak = backup_carrier(rec, carrier_dir)
         budget.end_stage("backup")
+        # ★★ B2b/E1/N5/N10：载体定稿后、launch 前拍跑前 F 快照（纯只读，
+        #    不写载体）；captured_at_iso 显式落盘，未知态不折叠成「无件」。
+        _pre_freshness_snapshot = make_pre_freshness_snapshot(
+            carrier_dir / "except.txt")
+        rec.add(FRESHNESS_GROUP, "captured_at_iso_pre",
+                _pre_freshness_snapshot["captured_at_iso"],
+                "script:make_pre_freshness_snapshot",
+                note="★ N10：跑前捕获时刻；state="
+                     f"{_pre_freshness_snapshot['state']}")
 
         # ---- ④ `except.txt` 被动基线（★ U-5：★ 不再写载体 except.txt） ----
         #   ★ 外部裁定 V5 §6.1.1 U-5：★ 在既有禁写范围内移除 except_reset 对
```

```diff
@@ -7122,7 +7363,8 @@
                 carrier_identity=(TRIP_CARRIER.get("identity")),
                 handover=(Path(args.carrier_handover) if args.carrier_handover
                           else None),
-                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt))
+                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt),
+                pre_freshness_snapshot=_pre_freshness_snapshot)
         except Exception as exc:
             # ★★ 收尾项自身抛异常（★ `run_guarded_steps` 已把每个失败的
             #   文件:行·类型·repr 落盘 `finalize_errors.txt` 后**原样重抛**，
```
