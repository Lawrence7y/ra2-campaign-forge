# -*- coding: utf-8 -*-
"""B2b 语义稿的构造+校验器（只操作内存文本，绝不写出候选 .py，不碰只读域）。

用法（两阶段）：
  python -I -X utf8 _draft_semantics_check.py build   -> 打印真实 unified diff hunk + 静态门禁
  python -I -X utf8 _draft_semantics_check.py verify  -> 校验 _draft_semantics.md 里的 hunk 可套用性

设计纪律：
  - 母本只读；patched 文本只在内存里存在，`ast.parse` 后即丢弃。
  - 不启动任何进程、不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
"""
from __future__ import annotations

import ast
import difflib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOTHER = Path(
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
    r"\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"
)
DRAFT = HERE / "_draft_semantics.md"

# ---------------------------------------------------------------------------
# 新增代码块（全部为纯只读 + 调用方指定 out_dir 的写盘，无任何进程/采样操作）
# ---------------------------------------------------------------------------

H1_CONSTANTS = '''

# ★★ B2b/N9：F（freshness）命名空间**单一真源**。
#   ★ E 恒用 "EXCEPT" group；整趟退出码唯一判据恒在 :5985-5990 的集合差，
#     F 字段与 F 代码**一律不得**进入该判据（静态门禁逐 token 核）。
#   ★ F 结论恒 usable_as_crash_evidence=False（:677 口径：sha 变化不判 crash）。
FRESHNESS_GROUP = "FRESHNESS"
FRESHNESS_KEY_PREFIX = "freshness_"
FRESHNESS_VERDICTS = ("unknown", "absent_both", "new_first_appearance",
                      "vanished", "leftover_unchanged", "new_write",
                      "rewritten_same_content", "error_pre_snapshot",
                      "post_read_error")
FRESHNESS_CONFIDENCES = ("high", "medium", "low", "none")
FRESHNESS_SNAPSHOT_STATES = ("unknown", "absent_confirmed", "present", "error")
'''

H2_BACKUP_MTIME = '''        rec.add("RESTORE", f"backup_mtime_pre:{name}",
                float(src.stat().st_mtime), f"{src}:file",
                note="★ B2b/N10：跑前 mtime 显式留痕（★ 不进 bak[name] 三键契约）")
'''

H3_HELPERS = '''def make_pre_freshness_snapshot(except_path: Path) -> dict:
    """★ B2b/F：跑前 `except.txt` **带状态标签**的基线快照（纯只读，不写载体）。

    ★★ N3 硬约束：`state` 是**唯一**判别口，`exists` 不得被用于反推状态。
      `None` / `{}` / 缺 `state` / 脏值 ⇒ 一律 unknown（未采集），
      **绝不等于**「跑前确认无件」。
    ★ N10：`captured_at_epoch` 与 `captured_at_iso` 双时刻必留，缺一即契约失败。
    ★ N1：采集抛异常 ⇒ state="error" 独立出口，不降级、不静默、不给 high。
    """
    snap = {"state": "unknown", "exists": None, "size": None,
            "sha256": None, "mtime_pre": None,
            "captured_at_epoch": None, "captured_at_iso": None,
            "error": None, "traceback": None,
            "source": "script:make_pre_freshness_snapshot"}
    try:
        p = Path(except_path)
        snap["captured_at_epoch"] = time.time()
        snap["captured_at_iso"] = now_iso()
        if not p.exists():
            snap["state"] = "absent_confirmed"
            snap["exists"] = False
            return snap
        st = p.stat()
        snap["state"] = "present"
        snap["exists"] = True
        snap["size"] = int(st.st_size)
        snap["mtime_pre"] = float(st.st_mtime)
        snap["sha256"] = sha256_file(p)
    except Exception as exc:
        import traceback
        snap["state"] = "error"
        snap["error"] = f"{type(exc).__name__}: {exc}"
        snap["traceback"] = "".join(traceback.format_exception(exc))
    return snap


def classify_except_freshness(pre_freshness_snapshot, post_observed: dict) -> dict:
    """★ B2b/F：只回答 **F（本趟窗口内是否被写/新出现）**。

    ★★ N9：本函数不得引用退出码判据（:5985-5990）、不得登记收尾失败、
      不得引用任何退出码常量；E（新异常）唯一口径恒为母本 :672-708。
      `usable_as_crash_evidence` 恒 False，任何 F verdict 都不得作为崩溃证据。
    ★★ N3：`state` 判别优先于一切；unknown ⇒ 不可判，**恒不给 high**。
    """
    out = {"verdict": None, "confidence": "none", "is_new": None,
           "note": "", "usable_as_crash_evidence": False,
           "pre_snapshot_state": "unknown"}

    def _finish(verdict: str, confidence: str, is_new, note: str) -> dict:
        out.update({"verdict": verdict, "confidence": confidence,
                    "is_new": is_new, "note": note,
                    "usable_as_crash_evidence": False})
        return out

    pre = (pre_freshness_snapshot
           if isinstance(pre_freshness_snapshot, dict) else {})
    st = pre.get("state")
    if st not in FRESHNESS_SNAPSHOT_STATES:
        st = "unknown"          # ★ None / {} / 缺 state / 脏值 ⇒ 一律「未采集」
    out["pre_snapshot_state"] = st

    post = post_observed if isinstance(post_observed, dict) else {}
    # ★ N1：错误独立出口，优先于一切状态折叠
    if post.get("read_error"):
        return _finish("post_read_error", "none", None,
                       "★ 跑后件读/复制失败（独立 error 出口，禁止静默）："
                       f"{post['read_error']}；pre_snapshot_state={st}")
    # ★★ N3/N2：unknown 与 absent_confirmed 在第一个分支就分道，禁止折叠
    if st == "unknown":
        return _finish("unknown", "none", None,
                       "★ 跑前快照未采集/传参丢失/采集未完成 ⇒ F 不可判；"
                       "未知 ≠ 不存在；不得据此输出「本趟新出现」或 high")
    if st == "error":
        return _finish("error_pre_snapshot", "none", None,
                       f"★ 跑前采集失败（独立 error 出口）：{pre.get('error')!r}")

    post_exists = bool(post.get("exists"))
    if not post_exists:
        if st == "absent_confirmed":
            return _finish("absent_both", "low", False,
                           "★ 跑前确认无件 + 跑后无件 ⇒ F=未见新出现；"
                           "但「文件未出现」不能证无崩溃（E 口径另算）")
        return _finish("vanished", "none", None,
                       "★ 跑前在、跑后失 ⇒ 异常态旗标（被删/改名/复制链中断），"
                       "须人工复核；不给 high、不判本趟新出现")

    if st == "absent_confirmed":
        return _finish("new_first_appearance", "high", True,
                       "★ 跑前确认无件 + 跑后在地 ⇒ F=本趟新出现（存在性）；"
                       "是否新崩溃仍只由 :672-708 集合差裁定")

    # ---- st == "present" ----
    pre_sha = pre.get("sha256")
    if not pre_sha:
        return _finish("error_pre_snapshot", "none", None,
                       "★ 跑前在场但缺 sha256 ⇒ B 主判据不可用"
                       "（独立 error 出口，不降级为 high、不静默）")
    post_sha = post.get("sha256")
    if not post_sha:
        return _finish("post_read_error", "none", None,
                       "★ 跑后缺 sha256 ⇒ 无法比对（error 出口）")
    if post_sha != pre_sha:
        return _finish("new_write", "high", True,
                       "★ 字节内容不同 ⇒ F=本趟被写；是否新异常归集合差（:677）")

    pre_mt, post_mt = pre.get("mtime_pre"), post.get("mtime_post")
    if pre_mt is None or post_mt is None:
        return _finish("leftover_unchanged", "medium", False,
                       "★ sha 同但 mtime 侧缺失 ⇒ A 旁证不可用，"
                       "同内容重写盲区此趟未覆盖（如实标注，不虚报 high）")
    if abs(float(post_mt) - float(pre_mt)) <= 0.0:
        return _finish("leftover_unchanged", "high", False,
                       "★ 跑前在 + sha 同 + mtime 未变 ⇒ 原样遗留（非本趟写入）")
    if float(post_mt) < float(pre_mt):
        return _finish("rewritten_same_content", "low", True,
                       "★ sha 同、mtime 变且回拨 ⇒ 疑似时钟回拨/utime 拉回，"
                       "置信降级为 low，须人工复核")
    return _finish("rewritten_same_content", "medium", True,
                   "★ sha 同而 mtime 变 ⇒ 同内容重写（F 旁证补 B 盲区）")

'''

H3_NEW_SIGNATURE = '''def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
                              out_dir: Path,
                              pre_freshness_snapshot: dict | None = None
                              ) -> dict | None:'''

H5_BODY = '''    src = carrier_dir / "except.txt"
    blob = None
    h = None
    dst = None
    post_observed = {"exists": None, "size": None, "sha256": None,
                     "mtime_post": None, "captured_at_iso": None,
                     "read_error": None}

    def _emit_f(fresh: dict, stage: str) -> None:
        """★ N4：正常与错误**每一条**出口都落盘 F 字段（不空转）。

        ★★ N9：全部写进 FRESHNESS_GROUP，键名一律带 FRESHNESS_KEY_PREFIX；
          本函数不读退出码判据、不登记收尾失败、不引用退出码常量。
        """
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "verdict",
                fresh["verdict"], "script:classify_except_freshness",
                note=f"stage={stage}；F 只答新鲜性，E 归 :672-708 集合差")
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "confidence",
                fresh["confidence"], "script:classify_except_freshness",
                note="★ none = 不可判；unknown 恒 none，禁止映射到 high")
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "is_new",
                fresh["is_new"], "script:classify_except_freshness",
                note="★ None = 未测写 null（Recorder :439-440 口径），"
                     "不得写 False 表示未知")
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "note",
                fresh["note"], "script:classify_except_freshness",
                note=fresh["note"])
        rec.add(FRESHNESS_GROUP, "pre_snapshot_state",
                fresh["pre_snapshot_state"],
                "script:make_pre_freshness_snapshot",
                note="★ unknown / absent_confirmed / present / error 三态可分")
        rec.add(FRESHNESS_GROUP, "usable_as_crash_evidence",
                fresh["usable_as_crash_evidence"],
                "script:classify_except_freshness",
                note="★★ 恒 False：F 结论不得作为本趟崩溃证据（:677）")
        rec.add(FRESHNESS_GROUP, "captured_at_iso",
                post_observed.get("captured_at_iso"), "script:now_iso",
                note="★ N10：跑后观测时刻（ISO-8601）；跑前同名键在快照内")

    try:
        if not src.exists():
            post_observed["exists"] = False
            post_observed["captured_at_iso"] = now_iso()
            rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
                    note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
            # ★ N4：早退分支同样落盘 F 字段（不可只算不写）
            _emit_f(classify_except_freshness(pre_freshness_snapshot,
                                              post_observed), "src_missing")
            return None
        post_observed["captured_at_iso"] = now_iso()
        blob = src.read_bytes()
        st = src.stat()
        h = hashlib.sha256(blob).hexdigest()
        post_observed.update({"exists": True, "size": len(blob),
                              "sha256": h, "mtime_post": float(st.st_mtime)})
        dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
        dst.write_bytes(blob)
    except Exception as exc:
        # ★★ N10：复制/读取失败 ⇒ 先 rec.add("ERROR", ...) 显式留痕，再**上抛**
        import traceback
        where = f"{src}:file"
        rec.add("ERROR", "freshness_copy_failed",
                f"{type(exc).__name__}: {exc}", where,
                note="★★ B2b/N10：复制失败显式留痕，不许静默降级")
        rec.add("ERROR", "freshness_copy_stage",
                "read_bytes/stat/write_bytes", where,
                note="captured_at_iso="
                     f"{post_observed.get('captured_at_iso')!r}")
        rec.add("ERROR", "freshness_copy_traceback",
                "".join(traceback.format_exception(exc)), "script:traceback")
        post_observed["read_error"] = f"{type(exc).__name__}: {exc}"
        # ★ N4/N1：错误分支同样落盘 F 字段，且走独立 error 出口
        _emit_f(classify_except_freshness(pre_freshness_snapshot,
                                          post_observed), "copy_failed")
        raise

    info = {"source": str(src), "evidence_path": str(dst),
            "size": len(blob), "sha256": h,
            "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
                    "（☆ 还原之后仍存在、可复核）",
            # ★★ N4/N6/N10：正常路径**必须**落盘的 F 字段（B2 在此空转）
            "mtime_post": post_observed["mtime_post"],
            "freshness_verdict": None,
            "freshness_confidence": None,
            "freshness_note": None,
            "captured_at_iso": None,
            "pre_snapshot_state": None,
            "pre_freshness_snapshot": None}
    fresh = classify_except_freshness(pre_freshness_snapshot, post_observed)
    info["freshness_verdict"] = fresh["verdict"]
    info["freshness_confidence"] = fresh["confidence"]
    info["freshness_note"] = fresh["note"]
    info["captured_at_iso"] = post_observed["captured_at_iso"]
    info["pre_snapshot_state"] = fresh["pre_snapshot_state"]
    info["pre_freshness_snapshot"] = (
        pre_freshness_snapshot
        if isinstance(pre_freshness_snapshot, dict) else None)
    rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",
            note="★★ 跑后 except.txt 原件副本（先于 restore_carrier）")
    _emit_f(fresh, "copied")   # ★ N4：正常路径同样落盘（非仅早退分支）
    # ★ 跑后载体件快照（★ 供"证据先于还原"复核：证明取的是跑后状态）
    files: dict = {}
    for name in CARRIER_FILES:
        p = carrier_dir / name
        files[name] = ({"path": str(p), "size": p.stat().st_size,
                        "sha256": sha256_file(p)} if p.exists() else None)
    (out_dir / "carrier_post_state.json").write_text(
        json.dumps(files, ensure_ascii=False, indent=1), encoding="utf-8")
    rec.add("EXCEPT", "carrier_post_state_path",
            str(out_dir / "carrier_post_state.json"), "script:copy_post_except_evidence")
    return info'''

H6_SIGNATURE_ADD = '''                  created_receipt: dict | None = None,
                  pre_freshness_snapshot: dict | None = None) -> int:'''

H7_CALL = '''        copy_post_except_evidence(rec, carrier_dir, out_dir,
                                 pre_freshness_snapshot=pre_freshness_snapshot)'''

H8_PREINIT = '''    # ★★ B2b/E1/N3：★ **try 之前**预初始化 ⇒ 五个早退 + 异常路径均不会
    #    未绑定；`None` 语义 = **未采集（unknown）**，绝不等于「跑前无件」。
    _pre_freshness_snapshot: dict | None = None'''

H9_SNAPSHOT = '''        # ★★ B2b/E1/N5/N10：载体定稿后、launch 前拍跑前 F 快照（纯只读，
        #    不写载体）；captured_at_iso 显式落盘，未知态不折叠成「无件」。
        _pre_freshness_snapshot = make_pre_freshness_snapshot(
            carrier_dir / "except.txt")
        rec.add(FRESHNESS_GROUP, "captured_at_iso_pre",
                _pre_freshness_snapshot["captured_at_iso"],
                "script:make_pre_freshness_snapshot",
                note="★ N10：跑前捕获时刻；state="
                     f"{_pre_freshness_snapshot['state']}")'''

H10_FINALLY = '''                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt),
                pre_freshness_snapshot=_pre_freshness_snapshot)'''


def _lines(s: str) -> list:
    return s.split("\n")


# (起始行, 结束行, 新行列表, 断言：原行必须含此子串)
# end = start-1 表示纯插入（插到原第 start 行之前）
EDITS = [
    (215, 214, _lines(H1_CONSTANTS), None),
    (4461, 4460, _lines(H2_BACKUP_MTIME), None),
    (4561, 4562, _lines(H3_HELPERS) + _lines(H3_NEW_SIGNATURE),
     "def copy_post_except_evidence"),
    (4574, 4599, _lines(H5_BODY), "src = carrier_dir / \"except.txt\""),
    (5909, 5909, _lines(H6_SIGNATURE_ADD), "created_receipt: dict | None = None) -> int:"),
    (5939, 5939, _lines(H7_CALL), "copy_post_except_evidence(rec, carrier_dir, out_dir)"),
    (6297, 6296, _lines(H8_PREINIT), None),
    (6389, 6388, _lines(H9_SNAPSHOT), None),
    (7125, 7125, _lines(H10_FINALLY), "created_receipt=(TRIP_CARRIER.get"),
]


def build_patched():
    text = io.open(MOTHER, encoding="utf-8").read()
    orig = text.split("\n")
    # 用 splitlines() 与 split("\n") 的差异无关：母本无 \r，逐行文本比对用 numpy 不需要
    work = list(orig)
    for start, end, new, marker in sorted(EDITS, key=lambda e: -e[0]):
        old_block = work[start - 1:end]
        if marker is not None:
            assert marker in "\n".join(old_block), (
                f"锚点失配 @{start}-{end}: 期望含 {marker!r}, "
                f"实为 {chr(10).join(old_block)[:200]!r}")
        work[start - 1:end] = new
    return orig, work


def f_region(patched_lines):
    """F 代码区：从 make_pre_freshness_snapshot 的 def 到 copy 函数的 return info。"""
    a = next(i for i, l in enumerate(patched_lines)
             if l.startswith("def make_pre_freshness_snapshot("))
    b = next(i for i, l in enumerate(patched_lines)
             if i > a and l.startswith("def _dump_json("))
    return "\n".join(patched_lines[a:b])


def do_build():
    orig, patched = build_patched()
    print("=" * 88)
    print("PHASE build · 母本只读，patched 文本仅存在于内存（未写出任何候选 .py）")
    print("=" * 88)
    print("母本行数:", len(orig), " patched 行数:", len(patched))
    try:
        ast.parse("\n".join(patched))
        print("ast.parse(patched) = PASS (exitcode 0)")
    except SyntaxError as e:
        print("ast.parse(patched) = FAIL", repr(e))
        raise
    # E 口径未被改的两条硬断言
    o = "\n".join(orig)
    p = "\n".join(patched)
    assert "def except_set_diff(rec: Recorder, pre_txt: str, post_txt: str) -> dict:" in p
    assert ('        if not setdiff.get("no_new_exception", True):\n'
            '            rec.add("EXCEPT", "finalize_new_exception_found", True,\n'
            '                    "script:finalize_trip",\n'
            '                    note="★★ 跑后出现新异常 ⇒ 非 0 退出码")\n'
            '            note_cleanup_failure(EXIT_INTERNAL_ERROR, "script:except_set_diff",\n'
            '                                 "★ 跑后 except.txt 出现新异常行", rec)') in p
    print("E 口径 unchanged: except_set_diff(:672-708) + :5985-5990 判据块 = PASS")
    fr = f_region(patched)
    for forbidden in ("note_cleanup_failure(", "no_new_exception", "EXIT_",
                      "except_set_diff(", "CLEANUP_FAILURES"):
        assert forbidden not in fr, f"F 区出现禁词 {forbidden!r}"
    print("F/E 静态门禁: F 区零 note_cleanup_failure/no_new_exception/EXIT_/except_set_diff(/CLEANUP_FAILURES = PASS")
    print("F 区 FRESHNESS_GROUP 写入次数:", fr.count("rec.add(FRESHNESS_GROUP"))
    # 关键 import 是否已在母本存在（无需新增）
    for tok in ("import hashlib", "import time", "from datetime import datetime, timezone",
                "from pathlib import Path", "import json"):
        assert tok in o, tok
    print("依赖 import 已在母本存在 = PASS（无需新增 import）")
    print()
    print("=" * 88)
    print("UNIFIED DIFF (difflib.unified_diff, n=3) —— 以下即设计稿要收录的 hunk")
    print("=" * 88)
    d = list(difflib.unified_diff(
        orig, patched, fromfile="a/qc151_trip.py", tofile="b/qc151_trip.py",
        n=3, lineterm=""))
    hunks = [l for l in d if l.startswith("@@ ")]
    print("HUNK_COUNT =", len(hunks))
    print("\n".join(d))
    print()
    print("HUNK_HEADERS =", json.dumps(hunks, ensure_ascii=False))
    return d


def parse_hunks_from_draft():
    """从 _draft_semantics.md 的 ```diff 代码块里抽出所有 hunk。"""
    txt = io.open(DRAFT, encoding="utf-8").read()
    blocks = re.findall(r"```diff\n(.*?)\n```", txt, flags=re.S)
    assert blocks, "设计稿里没有 ```diff 代码块"
    doc_hunks = []
    for b in blocks:
        lines = b.split("\n")
        cur = None
        for l in lines:
            if l.startswith("@@ "):
                if cur:
                    doc_hunks.append(cur)
                cur = [l]
            elif cur is not None:
                cur.append(l)
        if cur:
            doc_hunks.append(cur)
    return doc_hunks


def apply_hunks(orig, doc_hunks):
    """按标准 unified diff 语义把 hunk 套回母本，并逐行核上下文/-行原文。"""
    out = []
    idx = 0  # 0-based 指向 orig 下一待消费行
    for h in doc_hunks:
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", h[0])
        assert m, f"hunk 头无法解析: {h[0]!r}"
        a = int(m.group(1)) - 1
        assert idx <= a, f"hunk 起点倒退: idx={idx}, a={a}"
        out.extend(orig[idx:a])          # hunk 之间的未改动区
        idx = a
        for l in h[1:]:
            if l.startswith("+++") or l.startswith("---"):
                continue
            if l.startswith("+"):
                out.append(l[1:])
            elif l.startswith("-"):
                assert idx < len(orig), "hunk 越过母本末尾"
                assert orig[idx] == l[1:], (
                    f"删除行原文失配 @母本 {idx+1}: {orig[idx]!r} != {l[1:]!r}")
                idx += 1
            elif l.startswith(" "):
                assert idx < len(orig), "hunk 越过母本末尾"
                assert orig[idx] == l[1:], (
                    f"上下文原文失配 @母本 {idx+1}: {orig[idx]!r} != {l[1:]!r}")
                out.append(l[1:])
                idx += 1
            elif l == "":
                # difflib 的空行上下文是 " " 单空格；纯空行视为上下文兼容项
                assert idx < len(orig) and orig[idx] == "", (
                    f"空上下文行失配 @母本 {idx+1}")
                out.append("")
                idx += 1
            else:
                raise AssertionError(f"hunk 内出现非法行: {l[:60]!r}")
    out.extend(orig[idx:])
    return out


def do_matrix():
    """离线合成单测：把 H3_HELPERS 在隔离命名空间里 exec，喂合成字典，
    证明 None/{}/缺state/脏值一律 unknown，且历史遗留件不再被判 high。"""
    print("=" * 88)
    print("PHASE matrix · 离线合成单测（不启动真机、不读活进程内存、纯内存字典）")
    print("=" * 88)
    ns = {"time": __import__("time"),
          "Path": __import__("pathlib").Path,
          "now_iso": lambda: "2026-11-06T00:00:00+00:00",
          "sha256_file": lambda p: "DEADBEEF",
          "FRESHNESS_SNAPSHOT_STATES": ("unknown", "absent_confirmed",
                                        "present", "error")}
    exec(H3_HELPERS, ns)          # 只 exec 纯函数定义，无副作用
    cls = ns["classify_except_freshness"]
    cases = [
        ("pre=None (未采集) + 跑后有历史件", None,
         {"exists": True, "sha256": "X", "mtime_post": 1.0}),
        ("pre={} (空) + 跑后有历史件", {},
         {"exists": True, "sha256": "X", "mtime_post": 1.0}),
        ("pre={exists:False} 伪折叠 + 跑后有历史件", {"exists": False},
         {"exists": True, "sha256": "X", "mtime_post": 1.0}),
        ("pre 脏 state=zzz + 跑后有历史件", {"state": "zzz"},
         {"exists": True, "sha256": "X", "mtime_post": 1.0}),
        ("pre.state=unknown + 跑后无件", {"state": "unknown"},
         {"exists": False}),
        ("pre.state=error + 跑后有件", {"state": "error", "error": "OSError"},
         {"exists": True, "sha256": "X", "mtime_post": 1.0}),
        ("pre 确认无件 + 跑后有件", {"state": "absent_confirmed"},
         {"exists": True, "sha256": "X", "mtime_post": 1.0}),
        ("pre 确认无件 + 跑后无件", {"state": "absent_confirmed"},
         {"exists": False}),
        ("present + sha 不同", {"state": "present", "sha256": "A"},
         {"exists": True, "sha256": "B", "mtime_post": 2.0}),
        ("present + sha 同 + mtime 未变",
         {"state": "present", "sha256": "A", "mtime_pre": 1.0},
         {"exists": True, "sha256": "A", "mtime_post": 1.0}),
        ("present + sha 同 + mtime 变大",
         {"state": "present", "sha256": "A", "mtime_pre": 1.0},
         {"exists": True, "sha256": "A", "mtime_post": 2.0}),
        ("present + sha 同 + mtime 回拨",
         {"state": "present", "sha256": "A", "mtime_pre": 2.0},
         {"exists": True, "sha256": "A", "mtime_post": 1.0}),
        ("present + 缺 sha", {"state": "present"},
         {"exists": True, "sha256": "A", "mtime_post": 1.0}),
        ("present + 跑后无件 (vanished)",
         {"state": "present", "sha256": "A"}, {"exists": False}),
        ("跑后读/复制失败", {"state": "present", "sha256": "A"},
         {"exists": True, "read_error": "PermissionError"}),
    ]
    for label, pre, post in cases:
        r = cls(pre, post)
        print(f"  {label:38s} -> verdict={r['verdict']!r:24s} "
              f"conf={r['confidence']!r:8s} is_new={r['is_new']!r:5s} "
              f"crash_ev={r['usable_as_crash_evidence']}")
    # 硬断言：N2/N3 的核心回归
    for pre in (None, {}, {"exists": False}, {"state": "zzz"}):
        r = cls(pre, {"exists": True, "sha256": "X", "mtime_post": 1.0})
        assert r["verdict"] == "unknown", (pre, r)
        assert r["confidence"] != "high", (pre, r)
        assert r["usable_as_crash_evidence"] is False
    print("ASSERT 通过：None/{}/缺state/脏值 ⇒ verdict=unknown 且 conf!=high "
          "且 usable_as_crash_evidence=False（历史遗留件不再 new_first_appearance/high）")
    print("MATRIX_ALL = PASS")


def do_anchors():
    """把每个 hunk 用到的母本锚点行原文打印出来，并与探针已建立的结构锚点交叉核对。"""
    print("=" * 88)
    print("PHASE anchors · 逐锚点打印母本原文（1-based）")
    print("=" * 88)
    L = io.open(MOTHER, encoding="utf-8").read().splitlines()
    nums = [212, 213, 214, 215, 216,
            4458, 4459, 4460, 4461, 4462,
            4558, 4559, 4560, 4561, 4562,
            4572, 4573, 4574, 4583, 4587, 4599,
            5906, 5907, 5908, 5909,
            5936, 5937, 5938, 5939,
            6294, 6295, 6296,
            6386, 6387, 6388, 6389,
            7122, 7123, 7124, 7125]
    for n in nums:
        print(f"  {n}: {L[n-1][:110]}")
    print("--- 与探针 _b2b_probe_out.txt 已建立的结构锚点交叉核对 ---")
    probe = io.open(HERE / "_b2b_probe_out.txt", encoding="utf-8").read()
    canonical = [5900, 4561, 5939, 6185, 6387, 6313, 7030, 7038, 7117,
                 4447, 4460, 672, 677, 5985, 4583, 446]
    for n in canonical:
        hit = f"{n}:" in probe or f" {n}:" in probe or f"[{n}]" in probe
        print(f"  探针含 {n}: -> {hit}")
    print("ANCHORS_DONE")


def sections(txt):
    """按行首 `^## N` 切分章节，避免散文里的 `## 7` 式交叉引用误切。"""
    heads = list(re.finditer(r"(?m)^## (\d+)\b", txt))
    out = {}
    for k, m in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(txt)
        out[int(m.group(1))] = txt[m.start():end]
    return out


def do_verify():
    print("=" * 88)
    print("PHASE verify · 逐条核 _draft_semantics.md 的 hunk 可套用性")
    print("=" * 88)
    orig, patched = build_patched()
    doc_hunks = parse_hunks_from_draft()
    print("设计稿 hunk 数 =", len(doc_hunks))
    applied = apply_hunks(orig, doc_hunks)
    print("套用后文本行数 =", len(applied), "，build 阶段 patched 行数 =", len(patched))
    ok = applied == patched
    print("套用结果与 build patched 逐行一致 =", ok)
    assert ok, "设计稿的 hunk 不能无损套回母本"
    ast.parse("\n".join(applied))
    print("ast.parse(套用后文本) = PASS")
    txt = io.open(DRAFT, encoding="utf-8").read()
    S = sections(txt)
    print("识别到的章节编号 =", sorted(S))
    # 专项检查 A：清单条数 == hunk 条数
    sec7 = S[7]
    rows = [l for l in sec7.split("\n") if re.match(r"^\|\s*H\d+", l)]
    print("§7 清单数据行 =", len(rows), "；设计稿 hunk 数 =", len(doc_hunks))
    assert len(rows) == len(doc_hunks), "专项检查 A 失败：清单条数 != hunk 条数"
    print("专项检查 A (hunksMatchManifest) = PASS")
    # 专项检查 B：状态矩阵 unknown 不得 -> high
    m = re.search(r"```json\n(.*?)\n```", S[2], re.S)
    assert m, "§2 里没有机器可读 JSON 状态矩阵"
    mat = json.loads(m.group(1))
    assert len(mat) >= 8, "状态矩阵行数 < 8"
    bad = [r for r in mat if r.get("state") == "unknown"
           and r.get("confidence") == "high"]
    print("STATE_MATRIX.json 行数 =", len(mat), "；unknown->high 行数 =", len(bad))
    assert not bad, "专项检查 B 失败：unknown 映射到 high"
    print("专项检查 B (unknown 不映射 high) = PASS")
    # 专项检查 C：五个早退路径
    sec3 = S[3]
    found = [f":{n}" for n in (6340, 6349, 6361, 6374, 6377)
             if f":{n}" in sec3]
    print("earlyReturnsCovered =", f"{len(found)}/5", found)
    assert len(found) == 5, "专项检查 C 失败：早退路径覆盖不足"
    print("专项检查 C = PASS")
    # 十条根治小节
    sec1 = S[1]
    heads = re.findall(r"^####\s+(\S+)", sec1, flags=re.M)
    need = {"E1", "N5", "N4", "N6", "N3", "N1", "N2", "N7", "N10", "N9"}
    print("§1 小节编号 =", heads, "覆盖十条 =", need.issubset(set(heads)))
    assert need.issubset(set(heads)), "十条未全覆盖"
    print("VERIFY_ALL = PASS")
    print("=" * 88)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "build":
        do_build()
    elif mode == "verify":
        do_verify()
    elif mode == "matrix":
        do_matrix()
    elif mode == "anchors":
        do_anchors()
    else:
        raise SystemExit("usage: build | verify | matrix | anchors")
