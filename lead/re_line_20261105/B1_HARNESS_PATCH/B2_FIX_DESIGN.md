# B2 · 新鲜性补丁修复版（按 B1 预审六条否决逐条修正）

> **来源**：B1 预审（`dwfrun-eb5587ba`，`magpie/antigravity/gemini-3.8-flash$high`）判
> `shouldApply = NO`，列出六条 leaderErrors（`B1_HARNESS_PATCH/PRE_AUDIT.md` 15,209 B）。
> **我（Leader）已逐条亲验六条全部成立**（见锚点 §六 轮次 59）。
> **本文件 = 修复版设计，不是应用。零真机、不改 harness。**
>
> **★ 重要**：本文件由我手写，不经工作流派发 —— 六条错误都非常具体，
> 我直接改比让子代理再推一遍更可靠。

---

## 0 六条错误的根本原因（我的自省）

B1 预审的六条里，**五条源自 W11 的 `PATCH_SUGGESTION.md` 本身**，不是转述失真：

| # | 错误 | 根因归属 |
|---|---|---|
| 1 | 作用域断裂（`main` 局部变量在 `finalize_trip` 里引用） | **W11 补丁** |
| 2 | `exists` 键缺失 ⇒ 100% 误判 | **W11 补丁** |
| 3 | `mtime_pre` vs `mtime` 键名不匹配 | **W11 补丁** |
| 4 | 规约死锁（不许改 `finalize_trip` 签名，但合法接线必须改） | **我的 TASK** |
| 5 | 早退截断（判定内联在 `return None` 之后） | **W11 补丁** |
| 6 | `git diff` 要求与 `.gitignore:33` 矛盾 | **我的 TASK** |

**★ 我的失误**：我把 `PATCH_SUGGESTION.md` 当「可直接起点」传给 B1，**没先自己静态审一遍**。
如果当时花十分钟读那个 diff，第 2、3 条（两个傻瓜错误）我自己就能发现。

---

## 1 六条修正方案

### 修正 1 · 作用域：改传参，不跨函数引用

**错误**：`_pre_freshness_snapshot` 建在 `main`（`:6387` 附近），却要在
`finalize_trip`（`:5900`）的子函数 `_except_evidence_copy`（`:5938`）里用。

**修法**：给 `finalize_trip` 加一个可选形参，由 `main` 的调用点（`:7117-7125`）传进去。

```diff
--- a/qc151_trip.py
+++ b/qc151_trip.py
@@ def finalize_trip(rec: Recorder, carrier_dir: Path, bak: dict,
                   carrier_identity: dict | None = None,
                   handover: Path | None = None,
-                  created_receipt: dict | None = None) -> int:
+                  created_receipt: dict | None = None,
+                  pre_freshness_snapshot: dict | None = None) -> int:
```

```diff
@@ main，:7117-7125 调用点
             FINALIZE_CODE[0] = finalize_trip(
                 rec, fin_carrier, bak, t0, pre_except_txt, out_dir=WORKDIR,
                 ownership=fin_ownership, terminated_ok=(term_ok is not False),
                 main_return_code=_main_return_code,
                 mother_baseline=_mother_bl,
                 carrier_identity=(TRIP_CARRIER.get("identity")),
                 handover=(Path(args.carrier_handover) if args.carrier_handover
                           else None),
-                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt))
+                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt),
+                pre_freshness_snapshot=_pre_freshness_snapshot)
```

★ 形参用**默认值 None** ⇒ 任何其他调用方（若有）不受影响，向后兼容。

### 修正 2 · `exists` 键必须显式写入

**错误**：`bak[name]` 没有 `exists` 键，`_pre.get("exists")` 返回 `None`，`not None` 恒真。

**修法**：`backup_carrier` 里显式写 `"exists": True`（能进到那一行的件必然存在）。

```diff
@@ def backup_carrier(rec: Recorder, carrier_dir: Path) -> dict:
         dst = BACKUP_DIR / name
         dst.write_bytes(src.read_bytes())
         h = sha256_file(dst)
-        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}
+        _st_pre = src.stat()
+        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h,
+                     "exists": True,
+                     "mtime_pre": _st_pre.st_mtime,
+                     "captured_at_epoch": time.time()}
         rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
```

★ 注意：`exists: True` 只在**成功备份**的分支写。前面 `:4455-4456` 那个
`note="★ 未测（源不存在）"` + `continue` 的分支**不写 `bak[name]`**（它跳过了），
所以 `bak` 里要么没有该键（源不存在），要么 `exists: True` —— 语义自洽。

### 修正 3 · 键名统一为 `mtime_pre`

**错误**：存 `mtime_pre`、读 `mtime`。

**修法**：判定侧统一读 `mtime_pre`。

```diff
-    _pre_sha, _pre_mtime = _pre.get("sha256"), _pre.get("mtime")
+    _pre_sha, _pre_mtime = _pre.get("sha256"), _pre.get("mtime_pre")
```

### 修正 4 · 放开 `finalize_trip` 签名 + 调用点（我的 TASK 错误，不是补丁的）

**错误**：我 TASK §3.3 只列了「两处调用点」，§6.2 又要求「证明只改了三处」——
但合法接线必须改 `finalize_trip` 签名（`:5900`）和它在 `main` 的调用点（`:7117-7125`）。
**这是我自己写的死锁。**

**修法**：改动面从「三处」正式扩为**四处**，并明确列出：

| # | 位置 | 改什么 |
|---|---|---|
| **A** | `backup_carrier`（`:4457-4461`） | 补 `exists` / `mtime_pre` / `captured_at_epoch` |
| **B** | `copy_post_except_evidence`（`:4561-4562` 签名 + `:4573` 前插判定 + `:4583-4586` info） | 加 `pre_snapshot` 形参 + 判定 + info 字段 |
| **C** | `finalize_trip` 签名（`:5900-5909`） | 加 `pre_freshness_snapshot=None` 形参 |
| **D** | `_except_evidence_copy`（`:5939`）+ `finalize_trip` 调用点（`:7117-7125`）+ `main` 基线（`:6387` 后） | 接线 + 快照构造 |

★ **四处改动是可论证的最小集**，不再是「三处」。

### 修正 5 · 判定插到早退之前

**错误**：判定写在 `if not src.exists(): return None`（`:4575-4578`）之后 ⇒
`absent_both` 与 `vanished` 两个分支永远输出不了。

**修法**：把判定**提到早退之前**，让早退也能带新鲜性结论。

```diff
@@ def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
                               out_dir: Path,
+                              pre_snapshot: dict | None = None) -> dict | None:
     src = carrier_dir / "except.txt"
+    # ★ 修正 5：新鲜性判定必须在早退**之前**算，否则 absent_both / vanished 永远输出不了
+    _pre = dict(pre_snapshot or {})
+    _pre_exists = bool(_pre.get("exists"))
+    _now_exists = src.exists()
+    if not _now_exists:
+        _fresh = ("vanished" if _pre_exists else "absent_both",
+                  "high" if _pre_exists else "n/a")
+    else:
+        _mtime_post = src.stat().st_mtime
+        if not _pre_exists:
+            _fresh = ("new_first_appearance", "high")
+        else:
+            _blob_probe = src.read_bytes()
+            _sha_probe = hashlib.sha256(_blob_probe).hexdigest()
+            _pre_sha = _pre.get("sha256")
+            _pre_mtime = _pre.get("mtime_pre")
+            if _pre_sha is not None and _pre_sha != _sha_probe:
+                _fresh = ("new_write", "high")
+            elif _pre_mtime is not None and _mtime_post != _pre_mtime:
+                _fresh = ("rewritten_same_content",
+                          "low" if _mtime_post < _pre_mtime else "medium")
+            else:
+                _fresh = ("leftover_unchanged", "high")
+    if not _now_exists:
         rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
-                note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
+                note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）"
+                     f"；★ 新鲜性判定 = {_fresh[0]}")
+        rec.add("EXCEPT", "evidence_freshness", _fresh[0], f"{src}:path",
+                note=f"★ 新鲜性（F）置信={_fresh[1]}；★ 不做 crash 归因（:677）")
         return None
     blob = src.read_bytes()
     h = hashlib.sha256(blob).hexdigest()
```

★ 注意 `_blob_probe` 是个小冗余（早退分支外又读一次）——为保持原代码 `blob` 不动，
接受这点冗余；也可把它提到判定前，但那会改动 `:4579` 的原有结构，**改动面更大**，
所以我选「多读一次」而不是「动原行」。

### 修正 6 · 删掉 `git diff` 要求

**错误**：`out/` 被 `.gitignore:33` 忽略，`git diff` 对该文件永远为空。

**修法**：**只用文件级 `diff -u` 备份对比 + SHA256**。TASK 里彻底删掉 `git diff` 字样。

---

## 2 修复后的完整改动面（四处）

| 位置 | 行号 | 改动 | 是否新增行 |
|---|---|---|---|
| **A** `backup_carrier` | `:4460` | `bak[name]` 加 3 个键 | 改 1 行 → 4 行 |
| **B** `copy_post_except_evidence` 签名 | `:4561-4562` | 加 `pre_snapshot` 形参 | +1 行 |
| **B** 判定块 | `:4574` 之后 | 插 ~22 行判定 | +22 行 |
| **B** info 字段 | `:4583-4586` | 加 4 个键 | +4 行 |
| **C** `finalize_trip` 签名 | `:5909` | 加形参 | +1 行 |
| **D** `_except_evidence_copy` | `:5939` | 传参 | 改 1 行 |
| **D** `finalize_trip` 调用点 | `:7125` | 传参 | +1 行 |
| **D** `main` 基线 | `:6388` 后 | 构造快照 | +2 行 |

**预计净增 ≈ 31 行，删除 0 行，无既有逻辑改动。**

---

## 3 修复版必须重新过预审（不能直接用）

★ **本文件只是设计。** 应用前必须重新走一遍 B1 的预审硬门，重点验：

1. **作用域链闭合**：`_pre_freshness_snapshot` → `finalize_trip(pre_freshness_snapshot=...)` → `_except_evidence_copy` 能否真的传到
2. **`exists` 键语义**：`bak` 里「有键且 True」vs「无键」两种情况的判定是否符合预期
   （用合成字典单测：`{}` / `{"exists": True, "sha256": X, "mtime_pre": T}`）
3. **早退分支**：`pre={"exists": False}` + 跑后无件 → 应得 `absent_both`；
   `pre={"exists": True}` + 跑后无件 → 应得 `vanished`
4. **`:677` 不侵犯**：`freshness_verdict` 只回答 F，`except_set_diff` 仍是 E 唯一口径
5. **`backup_carrier` 的 10 个件**：`CARRIER_FILES`（`:213-217`）里 `except.txt` 是否在其中，
   若不在则 `bak` 里根本没这个键，快照会走 `{"exists": False}` 分支 —— **这条必须核**

★ **第 5 条是我新想到的风险点，已当场验证：不成立，但结论需要写进设计。**

`backup_carrier` 循环的是 `CARRIER_FILES`。我实读 `:213-214`：

```
213 CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
214                  "ra2opt_play.bat", "except.txt")
```

⇒ **`except.txt` 确实在列表末位（`:214`）**，所以 `bak["except.txt"]` 会正常存在。
⇒ 该风险点**不成立**，无需改设计。

★ 但由此得到一条**必须守住的约束**（写进预审清单）：
快照必须从 `bak.get("except.txt")` 取，**且必须处理「件不存在」时的两种情况**：
- `bak` 里**没有** `except.txt` 键（跑前该件不存在）⇒ 快照 = `{"exists": False}`
- `bak` 里**有** `except.txt` 键（跑前存在）⇒ 快照 = 该 dict（含 `exists: True`）

这两种情况的区分**完全依赖修正 2 显式写入的 `exists` 键** —— 这就是为什么修正 2 不能省。

---

## 4 铁律

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存。
- **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。**D-13 维持暂停**。
- **本文件不改任何文件**，只做设计。
- Python 一律 `python -I -X utf8`，绝对路径。**不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；拿不到写「未验」。
