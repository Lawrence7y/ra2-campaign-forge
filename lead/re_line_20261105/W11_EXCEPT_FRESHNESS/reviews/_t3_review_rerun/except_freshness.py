# -*- coding: utf-8 -*-
"""W11/T3 · `except_post` 新鲜性离线修复候选（D-22 裁决(A) nextSteps 第 3 条）。

定位：
  - ★ 纯离线候选模块：不启动游戏/loader、不写 hook、不注入、不读活进程内存；
  - ★ 只操作调用方给出的（临时）目录里的文件：`classify_except_post` 对
    `post_path` **只读**，全程不写任何文件；写盘仅发生在
    `copy_post_evidence_guarded` 里、且只写调用方指定的 out_dir；
  - ★ 判据 = T2 推荐组合：**B 跑前基线哈希（主）+ A 加固版 mtime 差分（旁证）**，
    方案 C 只以 `policy.hard_evidence_mode` 标注置信（启用需新裁定），
    方案 D 不进入判定链（与 qc151_trip.py:677 口径直接矛盾，已否决）。

与 harness 的关系（只引用、不修改）：
  - 生成点 `copy_post_except_evidence`（qc151_trip.py:4561-4599）只判 `exists()`
    （:4574-4578），`read_bytes` 原样复制（:4579），无任何新鲜性判断；
  - 跑前基线已有哈希：`backup_carrier`（:4447-4462，调用点 :6387）记
    `RESTORE.backup_sha256:{name}`（:4461），但**不记 mtime** ⇒ 历史趟 A 旁证
    退化；本模块的 `make_pre_snapshot` 是未来趟的补采口径（PATCH_SUGGESTION.md）；
  - 判定口径边界：`:677` 明令「不得用 sha 变化判 crash（游戏自身会重写该文件）」
    ⇒ 本模块回答 **F（freshness，本趟窗口内是否被写/新出现）**；
    **E（新异常）归 `except_set_diff` 集合差（:672-708）**，本模块不越界。
"""
from __future__ import annotations

import hashlib
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "VERDICT_DOC",
    "make_pre_snapshot",
    "classify_except_post",
    "copy_post_evidence_guarded",
]

# 各 verdict 的一句话语义（is_new 的语义 = F：本趟窗口内被写/新出现）
VERDICT_DOC = {
    "absent_both": "跑前缺、跑后缺：本趟未见新出现；但也**不能证无崩溃**（is_new=False 仅指 F）",
    "new_first_appearance": "跑前缺、跑后在场：本趟新出现（存在性证据，强；C 模式下为硬证）",
    "vanished": "跑前在、跑后失：异常态旗标（被删/改名/复制链中断），须人工复核",
    "new_write": "跑前在、跑后内容不同：本趟被写（F 高置信；是否新异常归集合差）",
    "rewritten_same_content": "跑前在、跑后 sha 同而 mtime 变：同内容重写（B 盲区被 A 旁证补住）",
    "leftover_unchanged": "跑前在、跑后内容与 mtime 均未变：原样遗留（l1b_20261021 实测态）",
    "post_read_error": "跑后件读失败：error 显式留痕（禁止静默）",
    "error_pre_snapshot": "跑前快照失败/缺 sha：error 显式留痕（禁止静默）",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_file(p: Path) -> str:
    """字节级 sha256（与 harness `:4580` 对 `read_bytes` 求 sha 的口径一致）。"""
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_pre_snapshot(except_path, *, sha: bool = True) -> dict:
    """跑前（载体定稿后、launch 前）对 `except.txt` 拍**基线快照**（只读）。

    对应 harness 侧 `backup_carrier`（qc151_trip.py:4447-4462，调用点 :6387）：
    该处只记 size+sha256（:4460-4461）；本函数额外补记 `mtime` 与捕获时刻
    （A 加固版旁证的最小采集面，见 PATCH_SUGGESTION.md 补丁 1）。
    快照过程失败 ⇒ 返回的 dict 带 `error`/`traceback`（不静默）。
    """
    p = Path(except_path)
    snap = {
        "path": str(p),
        "exists": False,
        "size": None,
        "sha256": None,
        "mtime": None,
        "captured_at_epoch": time.time(),
        "captured_at_iso": _now_iso(),
        "error": None,
        "traceback": None,
    }
    try:
        if not p.exists():
            return snap          # 源件缺失 ⇒ exists=False（分支 1 的跑前半边）
        snap["exists"] = True
        st = p.stat()
        snap["size"] = st.st_size
        snap["mtime"] = st.st_mtime
        if sha:
            snap["sha256"] = _sha256_file(p)
    except OSError as exc:
        snap["error"] = f"{type(exc).__name__}: {exc}"
        snap["traceback"] = traceback.format_exc()
    return snap


def classify_except_post(pre_snapshot, post_path, run_start_ts=None, policy=None) -> dict:
    """判定 `except.txt` 跑后新鲜性（F：本趟窗口内是否被写/新出现）。

    ★ 纯函数：只读 `pre_snapshot`（dict）与 `post_path` 指向的文件；
      不写盘、不启动进程、不读活进程内存。测试应在临时目录构造文件。

    参数：
      pre_snapshot  `make_pre_snapshot` 的返回值（或同构 dict）；
      post_path     跑后观察位（harness 语义 = 载体里的 except.txt，
                    先于 restore_carrier 观察，对应 :5938-5939 的调用序）；
      run_start_ts  可选的运行窗口锚点（建议用 `launch_pid_creation_time`
                    的 FILETIME 换算 epoch，qc151_trip.py:1107/:766-786）。
                    ★ 仅作旁证回显：T2 §3-A 已否决 naive「mtime>=跑开始」判据，
                    本函数**不**用它定判（test_10 专测此点）。
      policy        可省 dict：
                      hard_evidence_mode: bool —— 方案 C（跑前移走）已获新裁定
                        （默认 False；只影响 new_first_appearance 的置信标注）；
                      mtime_abs_tol: float —— mtime 相等比较容差（默认 0.0；
                        NTFS 直接比即可，FAT 系介质可调）。

    返回：至少含 `is_new` / `reason` / `evidence` 三键；另含
      `confidence`、`suspect_clock_rollback`、`f_vs_e_note`、`verdict_doc`。
      `is_new=None` 表示 F 无法判定（vanished / error 类）。
    """
    pol = dict(policy or {})
    tol = float(pol.get("mtime_abs_tol", 0.0))
    hard = bool(pol.get("hard_evidence_mode", False))

    ev = {
        "pre": dict(pre_snapshot or {}),
        "post": {"path": str(post_path), "exists": None, "size": None,
                 "sha256": None, "mtime": None,
                 "observed_at_epoch": time.time(),
                 "read_error": None, "traceback": None},
        "run_start_ts": run_start_ts,
        "corroboration": {
            "post_mtime_ge_run_start": None,
            "note": "旁证 only（T2 §3-A：naive mtime>=跑开始 判据已否决，不参与定判）",
        },
        "notes": [],
    }
    out = {
        "is_new": None, "reason": None, "evidence": ev,
        "confidence": None, "suspect_clock_rollback": False,
        "f_vs_e_note": "内容/写入变化只回答 freshness（F）；「是否新异常」归 "
                       "except_set_diff 集合差（qc151_trip.py:677 明令不得用 "
                       "sha 变化判 crash）",
        "verdict_doc": None,
    }

    def _finish(reason: str) -> dict:
        out["reason"] = reason
        out["verdict_doc"] = VERDICT_DOC[reason]
        return out

    pre = dict(pre_snapshot or {})
    if pre.get("error"):
        ev["notes"].append("跑前快照失败 ⇒ B/A 均不可用（显式留痕，不静默）")
        return _finish("error_pre_snapshot")

    # ---- 跑后观察（只读） ----
    post = Path(post_path)
    try:
        if post.exists():
            st = post.stat()
            ev["post"]["exists"] = True
            ev["post"]["size"] = st.st_size
            ev["post"]["mtime"] = st.st_mtime
            ev["post"]["sha256"] = _sha256_file(post)
        else:
            ev["post"]["exists"] = False
    except OSError as exc:
        ev["post"]["read_error"] = f"{type(exc).__name__}: {exc}"
        ev["post"]["traceback"] = traceback.format_exc()
        ev["notes"].append("跑后件读失败 ⇒ error 显式留痕（禁止静默）")
        return _finish("post_read_error")

    # ---- 旁证回显（不参与定判） ----
    if run_start_ts is not None and ev["post"]["mtime"] is not None:
        ev["corroboration"]["post_mtime_ge_run_start"] = (
            ev["post"]["mtime"] >= float(run_start_ts))

    pre_exists = bool(pre.get("exists"))
    pre_sha = pre.get("sha256")
    pre_mtime = pre.get("mtime")
    post_exists = bool(ev["post"]["exists"])

    # ---- 六分支决策表（T2 §6） ----
    if not pre_exists and not post_exists:
        out["is_new"] = False
        out["confidence"] = "low"
        ev["notes"].append("跑前缺、跑后缺：F=未写；但「文件未出现」不能证「本趟无崩溃」")
        return _finish("absent_both")

    if not pre_exists and post_exists:
        out["is_new"] = True
        out["confidence"] = "hard (C-mode 存在性硬证)" if hard else "high"
        if hard:
            ev["notes"].append("policy.hard_evidence_mode=True：方案 C 需新裁定（U-5）")
        return _finish("new_first_appearance")

    if pre_exists and not post_exists:
        ev["notes"].append("跑前在、跑后失：异常态旗标（被删/改名/复制链中断），须人工复核")
        return _finish("vanished")          # is_new=None：F 不可判

    # ---- pre 在场 且 post 在场：B 主判据（sha256 字节级） ----
    if pre_sha is None:
        ev["notes"].append("pre_snapshot 缺 sha256 ⇒ B 主判据不可用（显式留痕，不静默）")
        return _finish("error_pre_snapshot")

    if ev["post"]["sha256"] != pre_sha:
        out["is_new"] = True
        out["confidence"] = "high"
        ev["notes"].append("内容不同 ⇒ 本趟被写（F）；是否新异常归集合差（:677 口径不变）")
        return _finish("new_write")

    # ---- sha 相同：A 加固版 mtime 差分（旁证，补 B 的同内容重写盲区） ----
    if pre_mtime is None or ev["post"]["mtime"] is None:
        out["is_new"] = False
        out["confidence"] = "medium"
        ev["notes"].append("mtime 缺失 ⇒ A 旁证不可用，退化为纯 B 判定"
                           "（同内容重写盲区此趟未覆盖，如实标注）")
        return _finish("leftover_unchanged")

    if abs(ev["post"]["mtime"] - pre_mtime) <= tol:
        out["is_new"] = False
        out["confidence"] = "high"
        ev["notes"].append("内容与 mtime 均未变 ⇒ 原样遗留（l1b_20261021 实测态）")
        return _finish("leftover_unchanged")

    out["is_new"] = True
    ev["corroboration"]["mtime_pre"] = pre_mtime
    ev["corroboration"]["mtime_post"] = ev["post"]["mtime"]
    if ev["post"]["mtime"] < pre_mtime:
        out["suspect_clock_rollback"] = True
        out["confidence"] = "low"
        ev["notes"].append("mtime_post < mtime_pre 且 sha 同 ⇒ 疑似时钟回拨/utime 拉回"
                           "（T2 §3-A-2），置信降级；两侧 epoch 见 corroboration")
    else:
        out["confidence"] = "medium"
        ev["notes"].append("sha 同而 mtime 变 ⇒ 同内容重写（B 盲区被 A 补住；T2 探针[4]）")
    return _finish("rewritten_same_content")


def copy_post_evidence_guarded(src, out_dir, *, name_prefix: str = "except_post_") -> dict:
    """harness `copy_post_except_evidence` 复制语义（qc151_trip.py:4579-4582）的
    **防静默**包装：read_bytes → write_bytes → sha256 信息。

    harness 原实现里 `dst.write_bytes(blob)`（:4582）若抛 OSError 会沿调用链
    上抛（在 `run_guarded_steps` 之外无专用留痕）；本包装把任何一步的 OSError
    显式落为 `{"ok": False, "stage": …, "error": …, "traceback": …}`——
    **error 并留痕，不是静默**（TASK T3 分支 4）。只写调用方指定的 out_dir。
    """
    src = Path(src)
    out_dir = Path(out_dir)
    rec = {"ok": None, "src": str(src), "out_dir": str(out_dir), "dst": None,
           "size": None, "sha256": None, "stage": None, "error": None,
           "traceback": None, "captured_at_iso": _now_iso()}
    try:
        if not src.exists():
            rec["ok"] = False
            rec["stage"] = "src_missing"
            rec["error"] = f"src 不存在：{src}"
            return rec          # harness 对应返回 None（:4575-4578），这里显式记账
        rec["stage"] = "read_bytes"
        blob = src.read_bytes()                     # 对应 :4579
        dst = out_dir / f"{name_prefix}{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
        rec["dst"] = str(dst)
        rec["stage"] = "write_bytes"
        dst.write_bytes(blob)                       # 对应 :4582；失败 ⇒ 显式留痕
        rec["stage"] = "done"
        rec["ok"] = True
        rec["size"] = len(blob)
        rec["sha256"] = hashlib.sha256(blob).hexdigest()   # 对应 :4580
        return rec
    except OSError as exc:
        rec["ok"] = False
        rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["traceback"] = traceback.format_exc()
        return rec
