#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""`_census_x11_endtrigger.py` 的负控自检：每条「0 命中」判据必须抓得住诱饵。

M1 诱饵图=含 [Triggers] 的 .orig ⇒ T1 必红（装置真有看见触发器的能力）
M2 诱饵图=尾部插 TimeLimit 的 C 图 ⇒ T2 必红
M3 诱饵时钟=跳零行 units 清零 ⇒ T4 必红（'歼灭收场' 形态若真存在会被抓到）
另 M0：基线必须全绿 rc=0。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENSUS = HERE / "_census_x11_endtrigger.py"
OUT = HERE.parents[1] / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

RESULTS = []


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, str(CENSUS)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=600, env=env)
    states = {}
    for ln in p.stdout.splitlines():
        m = re.match(r"\s*\[(PASS|FAIL)\]\s+(\S+)(.*)$", ln)
        if m:
            key = m.group(2)
            states[key] = m.group(1)
    return p.returncode, states, p.stdout


def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


def main() -> int:
    print("=" * 78)
    print("X11 普查件负控：零命中判据 × 诱饵必红")
    print("=" * 78)

    rc, base, _ = run({})
    check("M0 基线全绿 rc=0", rc == 0 and all(v == "PASS" for v in base.values()),
          "checks=%d rc=%d" % (len(base), rc))

    tmp = Path(tempfile.mkdtemp())
    # M1: C 图换成带 [Triggers] 的 .orig ⇒ T1 红
    rc, got, out1 = run({"CENSUS_C_MAP": str(OUT / "_maps_fixed/XMP29U2.MAP.orig_93c2974b"),
                         "CENSUS_SKIP_SHA_ANCHOR": "1"})
    check("M1 诱饵图含 [Triggers] ⇒ T1 变红", got.get("T1d") == "FAIL",
          "T1=%s" % got.get("T1d"))

    # M2: 在 C 图副本尾部插 TimeLimit ⇒ T2 红（两图判据读 max(tl_c,tl_l3)）
    decoy2 = tmp / "XMP29U2_TL.MAP"
    decoy2.write_bytes((OUT / "_src_L1_sf8_20261020/XMP29U2.MAP").read_bytes()
                       + b"\r\nTimeLimit=99\r\n")
    rc, got, _ = run({"CENSUS_C_MAP": str(decoy2), "CENSUS_SKIP_SHA_ANCHOR": "1"})
    check("M2 诱饵图含 TimeLimit ⇒ T2 变红", got.get("T2b") == "FAIL",
          "T2=%s" % got.get("T2b"))

    # M3: 时钟里跳零行 units 置 0 ⇒ T4 红（歼灭形态可被看见）
    clock = json.loads((OUT / "l1_20261023c/_v11a_concurrent_clock.json").read_text(encoding="utf-8"))
    ser = clock["series"]
    zi = next(i for i in range(1, len(ser)) if ser[i][1] == 0 and ser[i - 1][1] > 0)
    ser[zi] = [ser[zi][0], 0, 0, 0, 0]  # units/inf/techno 清零 = 歼灭形态
    decoy3 = tmp / "clock_zeroed.json"
    decoy3.write_text(json.dumps(clock), encoding="utf-8")
    rc, got, _ = run({"CENSUS_CLOCK": str(decoy3)})
    check("M3 诱饵时钟跳零 units=0 ⇒ T4 变红", got.get("T4") == "FAIL",
          "T4=%s" % got.get("T4"))
    others_green = all(v == "PASS" for k, v in got.items() if not k.startswith("T4"))
    check("M3 非目标判据互不传染", others_green, "非 T4 全绿" if others_green else "有串红")

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
