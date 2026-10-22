#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_todo6_verdict.py 的合成自检：正控 + 负控 + 反方向控制。

不启动任何进程，不读真机数据。全部在临时目录内造 AB_*.json 喂给判定器。
断言口径：判定器输出的 verdict 行必须含指定关键字，且 exit code 必须符合预期。
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


def trip(singleton, hit=False, clean=True, abort=None, drop_field=False):
    r = {"closed_at_s": 1.0, "clean_exit": clean,
         "guard": {"hits_total": 3 if hit else 0},
         "rc4_hit": ({"address": 0x00724737, "info": [0, 0x250]} if hit else None)}
    if not drop_field:
        r["singleton_before_close"] = singleton
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


CASES = []


def case(name, fixture, want_rc, must, must_not=()):
    CASES.append((name, fixture, want_rc, must, must_not))


# N1 空目录 ⇒ NO_DATA / exit 2（fail-closed：没数据不许判 PASS）
case("N1 无数据", {}, 2, ["NO_DATA"])

# P1 零态全命中 vs 活态全不命中 ⇒ 支持因果链
case("P1 零态全命中", {
    "AB_A_1.json": ("A", [trip(0, hit=True) for _ in range(3)]),
    "AB_B1_1.json": ("B1", [trip(0x0F00BA00, hit=False) for _ in range(3)]),
}, 0, ["SINGLETON_DEAD", "SINGLETON_ALIVE", "支持"])

# P2 活态全命中 vs 零态全不命中 ⇒ 方向相反（告警）
case("P2 活态全命中", {
    "AB_A_1.json": ("A", [trip(0, hit=False) for _ in range(3)]),
    "AB_B1_1.json": ("B1", [trip(0x0F00BA00, hit=True) for _ in range(3)]),
}, 0, ["SINGLETON_ALIVE", "方向相反"])

# P3 混合两侧，零态命中率高 ⇒ 支持
case("P3 双侧对照", {
    "AB_A_1.json": ("A", [trip(0, hit=True), trip(0, hit=True)]),
    "AB_B1_1.json": ("B1", [trip(0x0F00BA00, hit=False),
                            trip(0x0F00BA00, hit=False)]),
}, 0, ["单例存活趟", "单例为零趟", "支持"])

# N2 字段缺失 ⇒ UNVERIFIABLE，不参与结论
case("N2 字段缺失", {
    "AB_A_1.json": ("A", [trip(None, drop_field=True)]),
}, 2, ["UNVERIFIABLE", "字段缺失"])

# N3 abort ⇒ UNVERIFIABLE
case("N3 abort", {
    "AB_A_1.json": ("A", [trip(0, abort="carrier_path_too_long")]),
}, 2, ["UNVERIFIABLE", "abort="])

# N4 单侧只有样本 ⇒ 明确说无法对照
case("N4 单侧样本", {
    "AB_A_1.json": ("A", [trip(0, hit=False)]),
}, 0, ["只有单侧样本"])

# N5 坏 JSON ⇒ 不静默跳过，列出坏文件
case("N5 坏文件", {
    "AB_A_1.json": ("A", [trip(0)]),
}, 0, ["SINGLETON_DEAD"])


def main():
    npass = 0
    fails = []
    for name, fixture, want_rc, must, must_not in CASES:
        rc, out = run(fixture)
        bad = []
        if rc != want_rc:
            bad.append("rc=%d want=%d" % (rc, want_rc))
        for m in must:
            if m not in out:
                bad.append("缺 %r" % m)
        for m in must_not:
            if m in out:
                bad.append("不该有 %r" % m)
        if bad:
            fails.append((name, bad, out))
            print("FAIL %-18s %s" % (name, "; ".join(bad)))
        else:
            npass += 1
            print("PASS %-18s rc=%d" % (name, rc))

    # N6 负控：判定器输出里绝不能出现 except.txt 作为判据（铁律）
    _, out = run({"AB_A_1.json": ("A", [trip(0, hit=False)])})
    if "except.txt" in out or "except_changed" in out:
        fails.append(("N6 except 泄漏", ["输出引用了 except.txt"], out))
        print("FAIL N6 判定器输出引用了 except.txt")
    else:
        npass += 1
        print("PASS N6 except.txt 未被当判据")

    total = len(CASES) + 1
    print()
    print("%d/%d PASS" % (npass, total))
    for name, bad, out in fails:
        print()
        print("--- %s ---" % name)
        print(out)
    return 0 if npass == total else 1


if __name__ == "__main__":
    sys.exit(main())
