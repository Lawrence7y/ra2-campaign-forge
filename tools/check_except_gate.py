#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_except_gate.py — 对局后 `except.txt` 门禁（崩溃可观测性）

上游依据：
  - `docs/re/except_zc11_forensics.md` §[9]⑨：harness 在对局结束后应主动检查
    `except.txt` 存在性并写入段记录（ZC-11 靠收尾才发现崩溃）；
  - RESULT_ZC11 [7]「零崩溃」勘误：崩溃后 harness 未中断，不得记 PASS。

红线：
  - 对游戏目录 `except.txt` **只读**（fingerprint），不写游戏目录；
  - 不改 bench_replay 的 ESC 门禁 / bench_cam_reset 行为（薄集成）。

判定口径：
  - 基线 = 会话/段开始时 `except.txt` 的 (exists, mtime_ns, size, sha256)；
  - 「新生/变化」= exists 由 False→True，或 mtime_ns / size / sha256 任一变化；
  - 默认严格（expect_no_except=True）：新生 ⇒ 段 FAIL + 退出码非零（不得记 PASS）；
  - expect_no_except=False（`--no-expect-no-except`）：仍记入报告并标 fail-lane
    （verdict=FAIL_LANE），**不得记 PASS**，但不强制非零退出码。

用法（CLI 自检 / 独立复核）：
  python tools/check_except_gate.py --game-dir ra2bench --selftest
  python tools/check_except_gate.py --game-dir ra2bench --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

# 退出码约定（与 bench_replay.main 共用）
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_EXCEPT_GATE = 2
EXIT_SELFCHECK = 3

# 报告默认落点（写作用域：out/re_work/except_gate/**）
DEFAULT_REPORT_DIR = PROJECT / "out" / "re_work" / "except_gate"

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_FAIL_LANE = "FAIL_LANE"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(path: Path | str) -> dict:
    """except.txt 指纹：exists / mtime_ns / size / sha256（只读）。"""
    p = Path(path)
    if not p.is_file():
        return {"path": str(p), "exists": False, "mtime_ns": 0, "size": 0, "sha256": None}
    st = p.stat()
    return {
        "path": str(p),
        "exists": True,
        "mtime_ns": int(st.st_mtime_ns),
        "size": int(st.st_size),
        "sha256": _sha256_file(p),
    }


def diff_fingerprint(before: dict, after: dict) -> dict:
    """对比两份指纹：是否「新生/变化」及原因列表。"""
    reasons: list[str] = []
    if not before.get("exists") and after.get("exists"):
        reasons.append("appeared")
    elif before.get("exists") and not after.get("exists"):
        reasons.append("removed")
    else:
        if after.get("exists"):
            if int(before.get("mtime_ns") or 0) != int(after.get("mtime_ns") or 0):
                reasons.append("mtime_changed")
            if int(before.get("size") or 0) != int(after.get("size") or 0):
                reasons.append("size_changed")
            if (before.get("sha256") or None) != (after.get("sha256") or None):
                reasons.append("sha256_changed")
    fresh = bool(reasons) and not (reasons == ["removed"])
    return {
        "fresh": fresh,
        "changed": bool(reasons),
        "reasons": reasons,
        "before": before,
        "after": after,
    }


@dataclass
class ExceptGate:
    """对局/分段收尾的 except.txt 门禁。

    用法：
        gate = ExceptGate(game_dir, expect_no_except=True)
        gate.begin("U0200")          # 段/局开始（记基线）
        ...                          # 跑对局
        seg = gate.end("U0200")      # 段收尾主动检查
        summary = gate.summary()
        code = gate.exit_code()
    """

    game_dir: Path
    expect_no_except: bool = True
    session_baseline: dict = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    segments: list[dict] = field(default_factory=list)
    _seg_baseline: dict | None = None
    _seg_tag: str | None = None

    def __post_init__(self):
        self.game_dir = Path(self.game_dir)
        if not self.session_baseline:
            self.session_baseline = self.snapshot()

    @property
    def except_path(self) -> Path:
        return self.game_dir / "except.txt"

    def snapshot(self) -> dict:
        fp = fingerprint(self.except_path)
        fp["ts"] = datetime.now().isoformat(timespec="seconds")
        return fp

    def begin(self, tag: str) -> dict:
        """段/局开始：记基线（会话基线仅首次记）。"""
        self._seg_tag = tag
        self._seg_baseline = self.snapshot()
        self.events.append({"op": "begin", "tag": tag, "fp": self._seg_baseline})
        return self._seg_baseline

    def end(self, tag: str | None = None) -> dict:
        """段/局收尾：主动检查 except.txt 是否新生/变化。"""
        tag = tag or self._seg_tag or f"seg{len(self.segments)}"
        base = self._seg_baseline or self.session_baseline
        after = self.snapshot()
        d = diff_fingerprint(base, after)
        d_session = diff_fingerprint(self.session_baseline, after)
        verdict = VERDICT_PASS
        if d["fresh"]:
            verdict = VERDICT_FAIL if self.expect_no_except else VERDICT_FAIL_LANE
        rec = {
            "tag": tag,
            "ts": datetime.now().isoformat(timespec="seconds"),
            "verdict": verdict,
            "segment_diff": d,
            "session_diff": d_session,
            "expect_no_except": self.expect_no_except,
        }
        self.segments.append(rec)
        self.events.append({"op": "end", "tag": tag, "verdict": verdict,
                            "reasons": d["reasons"]})
        self._seg_baseline = None
        self._seg_tag = None
        return rec

    def check_session(self) -> dict:
        """会话级复查（整批收尾）：相对会话基线。"""
        after = self.snapshot()
        d = diff_fingerprint(self.session_baseline, after)
        verdict = VERDICT_PASS
        if d["fresh"]:
            verdict = VERDICT_FAIL if self.expect_no_except else VERDICT_FAIL_LANE
        rec = {"ts": datetime.now().isoformat(timespec="seconds"),
               "verdict": verdict, "session_diff": d,
               "expect_no_except": self.expect_no_except}
        self.events.append({"op": "session_check", "verdict": verdict,
                            "reasons": d["reasons"]})
        return rec

    def summary(self) -> dict:
        fresh_segs = [s for s in self.segments if s.get("segment_diff", {}).get("fresh")]
        any_fresh = bool(fresh_segs)
        # 会话级也再判一次（防「段间写入但段基线相同」漏检）
        session_now = diff_fingerprint(self.session_baseline, self.snapshot())
        if session_now["fresh"]:
            any_fresh = True
        if any_fresh:
            verdict = VERDICT_FAIL if self.expect_no_except else VERDICT_FAIL_LANE
        else:
            verdict = VERDICT_PASS
        return {
            "verdict": verdict,
            "fresh_segment_count": len(fresh_segs),
            "segment_count": len(self.segments),
            "segments": self.segments,
            "session_baseline": self.session_baseline,
            "session_now": self.snapshot(),
            "session_fresh": session_now["fresh"],
            "session_reasons": session_now["reasons"],
            "expect_no_except": self.expect_no_except,
            "except_path": str(self.except_path),
            "gate": "check_except_gate",
        }

    def exit_code(self) -> int:
        v = self.summary()["verdict"]
        if v == VERDICT_FAIL:
            return EXIT_EXCEPT_GATE
        if v == VERDICT_FAIL_LANE:
            return EXIT_OK  # fail-lane：标记不放行，但不强制非零退出
        return EXIT_OK

    def write_report(self, path: Path | None = None) -> Path:
        out = Path(path) if path else (
            DEFAULT_REPORT_DIR / f"except_gate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.summary(), ensure_ascii=False, indent=2),
                       encoding="utf-8")
        return out

    def as_run_field(self) -> dict:
        """嵌入 run JSON 的精简字段（供报告可复算）。"""
        last = self.segments[-1] if self.segments else None
        return {
            "verdict": (last or {}).get("verdict", VERDICT_PASS),
            "reasons": ((last or {}).get("segment_diff") or {}).get("reasons", []),
            "fresh": ((last or {}).get("segment_diff") or {}).get("fresh", False),
            "expect_no_except": self.expect_no_except,
            "except_path": str(self.except_path),
        }


# ---------------- 兼容旧接口 -------------------------------------------------

def _legacy_except_is_fresh(game_dir: Path) -> bool:
    """旧口径（仅 mtime 近期）：保留给历史调用方；新逻辑请用 ExceptGate。"""
    p = Path(game_dir) / "except.txt"
    if not p.is_file():
        return False
    import time
    mt = p.stat().st_mtime
    return (time.time() - mt) < 3600 * 6


# ---------------- 离线自检（不启动游戏） --------------------------------------

def selftest() -> int:
    """用临时目录模拟 except.txt 生命周期，验证门禁判定与退出码。"""
    import tempfile
    print("=== check_except_gate 离线自检（不启动游戏、不碰游戏目录）===")
    fails = 0

    def chk(name, cond, detail=""):
        nonlocal fails
        if cond:
            print(f"  [PASS] {name}" + (f"  ({detail})" if detail else ""))
        else:
            fails += 1
            print(f"  [FAIL] {name}" + (f"  ({detail})" if detail else ""))

    with tempfile.TemporaryDirectory(prefix="except_gate_") as td:
        gdir = Path(td)

        # 场景 1：无 except → 始终 PASS
        g1 = ExceptGate(gdir, expect_no_except=True)
        g1.begin("segA")
        r1 = g1.end("segA")
        chk("无 except.txt 段收尾 PASS", r1["verdict"] == VERDICT_PASS, r1["verdict"])
        chk("无 except.txt 退出码 0", g1.exit_code() == EXIT_OK, str(g1.exit_code()))

        # 场景 2：段中途新生 except → 严格模式 FAIL + 非零退出
        g2 = ExceptGate(gdir, expect_no_except=True)
        g2.begin("segB")
        (gdir / "except.txt").write_text("EXCEPTION_ACCESS_Violation test\n", encoding="utf-8")
        r2 = g2.end("segB")
        chk("新生 except 判 fresh", r2["segment_diff"]["fresh"] is True,
            str(r2["segment_diff"]["reasons"]))
        chk("严格模式 verdict=FAIL", r2["verdict"] == VERDICT_FAIL, r2["verdict"])
        chk("严格模式退出码=2", g2.exit_code() == EXIT_EXCEPT_GATE, str(g2.exit_code()))

        # 场景 3：已有 except（基线内）不变 → PASS（不是「新生」）
        g3 = ExceptGate(gdir, expect_no_except=True)
        g3.begin("segC")
        r3 = g3.end("segC")
        chk("既有 except 未变化 → 不算 fresh", r3["segment_diff"]["fresh"] is False,
            str(r3["segment_diff"]["reasons"]))
        chk("既有 except 未变化 → PASS", r3["verdict"] == VERDICT_PASS, r3["verdict"])

        # 场景 4：mtime/内容变化 → fresh（sha256 变化）
        g4 = ExceptGate(gdir, expect_no_except=True)
        g4.begin("segD")
        (gdir / "except.txt").write_text("EXCEPTION_ACCESS_Violation test\nMORE\n", encoding="utf-8")
        r4 = g4.end("segD")
        chk("内容变化 → sha256_changed", "sha256_changed" in r4["segment_diff"]["reasons"],
            str(r4["segment_diff"]["reasons"]))
        chk("内容变化 → FAIL", r4["verdict"] == VERDICT_FAIL, r4["verdict"])

        # 场景 5：宽松模式（expect_no_except=False）→ FAIL_LANE、退出码 0、不得 PASS
        g5 = ExceptGate(gdir, expect_no_except=False)
        g5.begin("segE")
        (gdir / "except.txt").write_text("another crash\n", encoding="utf-8")
        r5 = g5.end("segE")
        chk("宽松模式 verdict=FAIL_LANE", r5["verdict"] == VERDICT_FAIL_LANE, r5["verdict"])
        chk("宽松模式退出码 0（fail-lane 标记）", g5.exit_code() == EXIT_OK, str(g5.exit_code()))
        chk("宽松模式不得 PASS", r5["verdict"] != VERDICT_PASS, r5["verdict"])

        # 场景 6：会话级漏检兜底（段基线恰好相同但会话后变化）
        g6 = ExceptGate(gdir, expect_no_except=True)
        g6.begin("segF1")
        g6.end("segF1")
        # 段间写入后立刻再 begin（新基线含新内容）→ 段内无变化
        (gdir / "except.txt").write_text("between segments\n", encoding="utf-8")
        g6.begin("segF2")
        g6.end("segF2")
        s6 = g6.summary()
        chk("会话级仍检出 fresh（段间写入不漏）", s6["session_fresh"] is True,
            str(s6["session_reasons"]))
        chk("会话级 summary verdict=FAIL", s6["verdict"] == VERDICT_FAIL, s6["verdict"])

        # 场景 7：diff_fingerprint 语义
        b = {"exists": False, "mtime_ns": 0, "size": 0, "sha256": None}
        a = {"exists": True, "mtime_ns": 1, "size": 1, "sha256": "aa"}
        d = diff_fingerprint(b, a)
        chk("appeared → fresh", d["fresh"] and d["reasons"] == ["appeared"], str(d["reasons"]))
        d2 = diff_fingerprint(a, a)
        chk("相同指纹 → 不 fresh", d2["fresh"] is False and d2["reasons"] == [], str(d2["reasons"]))

        # 场景 8：write_report 落盘 + as_run_field
        rp = g2.write_report(DEFAULT_REPORT_DIR / "selftest_except_gate.json")
        chk("报告落盘", rp.is_file(), str(rp))
        fld = g2.as_run_field()
        chk("as_run_field 含 verdict/fresh", "verdict" in fld and "fresh" in fld, str(fld))

    print(f"=== check_except_gate 自检 {'PASS' if fails == 0 else f'FAIL ({fails})'} ===")
    return EXIT_OK if fails == 0 else EXIT_SELFCHECK


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="check_except_gate")
    ap.add_argument("--game-dir", default=str(PROJECT / "ra2youli"),
                    help="游戏目录（含 except.txt；默认 ra2youli）")
    ap.add_argument("--selftest", action="store_true", help="离线自检（临时目录，不启动游戏）")
    ap.add_argument("--check", action="store_true",
                    help="对游戏目录做一次单点指纹检查（打印 JSON；不写游戏目录）")
    ap.add_argument("--expect-no-except", action=argparse.BooleanOptionalAction, default=True,
                    help="严格模式（默认开）：新生 except ⇒ FAIL+非零退出；--no-expect-no-except = fail-lane")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    gdir = Path(args.game_dir)
    if args.check:
        g = ExceptGate(gdir, expect_no_except=args.expect_no_except)
        g.begin("cli_check")
        rec = g.end("cli_check")
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return g.exit_code()
    ap.print_help()
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
