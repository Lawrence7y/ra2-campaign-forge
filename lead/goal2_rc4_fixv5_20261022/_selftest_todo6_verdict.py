#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_todo6_verdict.py v2 的自检：正控 + 负控 + 方向性回归。

★ v2 相对 v1 的关键变化（§379 推翻 §374 §二 后）：
   归因必须用**崩溃瞬间**读数（singleton_at_hit），不能用关窗前读数
   （singleton_before_close）—— 因为 WM_CLOSE 经 DefWindowProcA 必然清零单例。

本自检专门验证这一点：构造「关窗前非 0、崩溃瞬间为 0」的趟，
v2 必须判「与因果链一致」，而不是因为"关窗前非 0"就判矛盾。
"""
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

CARD = Path(__file__).resolve().parent
sys.path.insert(0, str(CARD))
import _todo6_verdict as V  # noqa: E402

RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-52s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def trip(before, at_hit, hit=True, abort=None, drop_hit_field=False):
    r = {"closed_at_s": 1.0, "clean_exit": True,
         "guard": {"hits_total": 3 if hit else 0}}
    if before is not None or not drop_hit_field:
        r["singleton_before_close"] = before
    if hit:
        h = {"address": 0x00724737, "info": [0, 0x250]}
        if not drop_hit_field:
            h["singleton_at_hit"] = at_hit
        r["rc4_hit"] = h
    else:
        r["rc4_hit"] = None
    if abort:
        r["abort"] = abort
    return r


def run(fixture):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for name, (arm, trips) in fixture.items():
            (d / name).write_text(
                json.dumps({"arm": arm, "dll": None, "trips": trips},
                           ensure_ascii=False), encoding="utf-8")
        old = V.CARD
        V.CARD = d
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = V.main()
        finally:
            V.CARD = old
        return rc, buf.getvalue()


def main():
    print("=" * 96)
    print("_todo6_verdict v2 自检（方向性回归：归因只看崩溃瞬间）")
    print("=" * 96)

    # N1 无数据 ⇒ exit 2
    rc, out = run({})
    check("N1 无数据 ⇒ NO_DATA / exit 2", rc == 2 and "NO_DATA" in out, "rc=%d" % rc)

    # ★ P1 方向性核心：关窗前非 0，崩溃瞬间为 0 ⇒ 必须判「一致」
    rc, out = run({"AB_A_1.json": ("A", [
        trip(0x0F00BA00, 0), trip(0x0F00BA00, 0), trip(0x0F00BA00, 0)])})
    # ★ 断言要避开说明句里的"并不矛盾"字样，只看判据行的「✗ … 矛盾！」标记
    has_conflict_verdict = "✗" in out and "与因果链矛盾" in out
    check("P1 关窗前非0 + 瞬间为0 ⇒ 判一致（不判矛盾）",
          rc == 0 and "✓" in out and not has_conflict_verdict,
          "rc=%d" % rc)
    check("P1 输出里有「并不矛盾」的说明",
          "并不矛盾" in out, "")

    # P2 崩溃瞬间非 0 ⇒ 必须判矛盾，且退出码 4
    rc, out = run({"AB_A_1.json": ("A", [trip(0x0F00BA00, 0x0F00BA00)])})
    check("P2 瞬间非0 ⇒ 判矛盾 + exit 4",
          rc == 4 and "矛盾" in out, "rc=%d" % rc)

    # N2 命中但缺 singleton_at_hit ⇒ UNVERIFIABLE
    rc, out = run({"AB_A_1.json": ("A", [trip(0, None, drop_hit_field=True)])})
    check("N2 命中但缺瞬间字段 ⇒ UNVERIFIABLE / exit 2",
          rc == 2 and "UNVERIFIABLE" in out, "rc=%d" % rc)

    # N3 abort ⇒ 不参与
    rc, out = run({"AB_A_1.json": ("A", [trip(0, None, abort="x")])})
    check("N3 abort 趟不参与归因", "NO_HIT" in out or "UNVERIFIABLE" in out, "")

    # N4 未命中 ⇒ NO_HIT，不归因
    rc, out = run({"AB_A_1.json": ("A", [trip(0, 0, hit=False)])})
    check("N4 未命中 ⇒ NO_HIT / 无归因结论", rc == 2 and "NO_HIT" in out,
          "rc=%d" % rc)

    # P3 创建态表与瞬间态表分开
    rc, out = run({"AB_A_1.json": ("A", [trip(0x0F00BA00, 0)])})
    check("P3 表 A（创建态）与表 B（瞬间态）都存在",
          "表 A" in out and "表 B" in out, "")
    check("P3 创建态判为 CREATED（关窗前非 0）",
          "CREATED" in out and "NEVER_CREATED" not in out.split("表 B")[0], "")

    # N5 铁律：不得把 except.txt 当判据
    check("N5 输出不含 except.txt", "except.txt" not in out, "")

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    if npass != len(RESULTS):
        for t, c, e in RESULTS:
            if not c:
                print("  - %s  %s" % (t, e))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
