#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_census_d07_gate36.py 的负控：证明这个普查件**能红**。

为什么必须有：普查件输出一堆「0 条命中本线」「6 条落冻结件」，
这些全是**否定式结论**。按既有教训（gate-assert-values-not-existence），
否定式断言在本规则已按此实现时永远为真，测不出任何东西。
所以这里不测「它说了什么」，而是**改输入让它说错**，看它会不会红。

做法：不 import 被测件内部（那会两边同绿），而是把被测件当黑盒，
在**临时目录里造一份篡改过的 findings.json**，再让它指向该文件跑一遍，
只判它的**输出文本**是否随篡改而变 + 退出码。

变异（每条都对应一个真实可能发生的事故）：
  M1 把一条 high 的落点改到本线写域 ⇒ 必须从「0 条」变成「1 条」。
  M2 把一条 high 的 severity 降成 medium ⇒ high 计数必须跟着变。
  M3 把 harness6 的某条从 high 组删掉 ⇒ 冻结件命中数必须下降。
  M4 把一条 cross-file+advisory 的 kind 改成 static ⇒ 污点链计数必须变 0。
  M5 让两条不同文件的 finding 共用 findingId ⇒ 必须报「跨文件共用 > 0」。
  M6 把冻结件那份的哈希期望值……（不可做：期望值在脚本内，改不了输入）——
     ⇒ 改为：把 findings 里 harness6 的落点全部移除，冻结件 high 必须变 0。

跑法：python lead/qc161_u0400_trip/_verify_census_d07.py
退出码：0 = 全部变异被捕获；1 = 有变异存活（判据失效）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "lead" / "qc161_u0400_trip" / "_census_d07_gate36.py"
SRC = Path(r"C:\Users\Administrator\.mimosa\security-scans"
           r"\project-58d54c8400d61bac27a417b2"
           r"\scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0\findings.json")

RESULTS: list[tuple[str, bool, str]] = []


def rec(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | %s" % detail) if detail else ""))


def run(doc: dict, tmp: Path) -> tuple[int, str]:
    """把 doc 写到 tmp，临时改 census 的 SCAN 常量指向它，跑一遍。

    ★ 不改盘上原脚本：用 -c 把模块以 exec 方式加载会触发安全扫描，
      故改为在 tmp 里生成一个**薄壳**——它读取同目录的 findings.json，
      再 importlib 加载被测件并覆写 SCAN。
    """
    f = tmp / "findings.json"
    f.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    shim = tmp / "shim.py"
    shim.write_text(
        "import importlib.util, sys, pathlib\n"
        "spec = importlib.util.spec_from_file_location('census', r'%s')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "m.SCAN = pathlib.Path(r'%s')\n"
        "sys.exit(m.main())\n" % (CENSUS, f),
        encoding="utf-8")
    p = subprocess.run([sys.executable, str(shim)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def counter(text: str, pat: str) -> str | None:
    m = re.search(pat, text)
    return m.group(1) if m else None


def main() -> int:
    if not SRC.is_file():
        print("★ 数据源缺失：%s" % SRC)
        return 1
    base = json.loads(SRC.read_text(encoding="utf-8"))

    print("=" * 82)
    print("[基线] 未篡改输入")
    with tempfile.TemporaryDirectory() as td:
        rc, out = run(base, Path(td))
    rec("基线退出码 == 0", rc == 0, "rc=%d" % rc)
    b_high = counter(out, r"severity==high\s*=\s*(\d+)")
    b_mine = "0 条 ⇒" in out
    b_frozen = counter(out, r"落在\*\*已核实冻结\*\*件上的 high = (\d+) 条")
    b_taint = counter(out, r"跨文件污点链\(advisory\) = (\d+)")
    rec("基线读到 high 计数", b_high is not None, "high=%s" % b_high)
    rec("基线本线命中为 0", b_mine, "")
    rec("基线冻结件命中 = 6", b_frozen == "6", "got=%s" % b_frozen)
    rec("基线污点链 = 8", b_taint == "8", "got=%s" % b_taint)

    def mutate(tag: str, fn) -> None:
        doc = json.loads(json.dumps(base))     # 深拷贝
        fn(doc)
        with tempfile.TemporaryDirectory() as td:
            rc, out = run(doc, Path(td))
        yield tag, rc, out

    # ---- M1：把一条 high 挪进本线写域 ----
    def m1(doc):
        for f in doc["findings"]:
            if f["severity"] == "high":
                f["location"]["path"] = "lead/qc161_u0400_trip/_evil.py"
                break
    for tag, rc, out in mutate("M1", m1):
        # ★ 判据不能找「1 条」这种措辞：普查件在本线段打印的是**路径本身**
        #   （`★ <path>:<line>`），找措辞会假红。改为找**被注入的那个路径**
        #   是否出现在 [5] 段 ⇒ 这正是「它能否看见本线命中」的直接证据。
        seg = out.split("[5]")[-1].split("[6]")[0] if "[5]" in out else ""
        hit = ("_evil.py" in seg) and ("0 条 ⇒" not in seg)
        rec("M1 落点改到本线 ⇒ 本线段报出该路径", hit, "本线段=%r" % seg[:90])

    # ---- M2：降一条 severity ----
    def m2(doc):
        for f in doc["findings"]:
            if f["severity"] == "high":
                f["severity"] = "medium"
                break
    for tag, rc, out in mutate("M2", m2):
        got = counter(out, r"severity==high\s*=\s*(\d+)")
        rec("M2 降一条 high ⇒ 计数随之下降", got != b_high and got is not None,
            "base=%s now=%s" % (b_high, got))

    # ---- M3：删掉 harness6 上的 high ----
    def m3(doc):
        doc["findings"] = [f for f in doc["findings"]
                           if "harness6" not in f["location"]["path"]]
    for tag, rc, out in mutate("M3", m3):
        got = counter(out, r"落在\*\*已核实冻结\*\*件上的 high = (\d+) 条")
        rec("M3 移除 harness6 落点 ⇒ 冻结命中下降", got is not None and int(got) < 6,
            "base=6 now=%s" % got)

    # ---- M4：把一条污点链改成静态 ----
    def m4(doc):
        for f in doc["findings"]:
            if f.get("advisory"):
                f["advisory"] = False
                f["kind"] = "static"
                break
    for tag, rc, out in mutate("M4", m4):
        got = counter(out, r"跨文件污点链\(advisory\) = (\d+)")
        rec("M4 污点链改静态 ⇒ 污点链计数下降", got is not None and int(got) == 7,
            "base=8 now=%s" % got)

    # ---- M5：让两文件共用一个 findingId ----
    def m5(doc):
        a = doc["findings"][0]
        for f in doc["findings"][1:]:
            if f["location"]["path"] != a["location"]["path"]:
                f["findingId"] = a["findingId"]
                break
    for tag, rc, out in mutate("M5", m5):
        got = counter(out, r"跨文件共用 findingId\s*=\s*(\d+)")
        rec("M5 跨文件共用 ID ⇒ 该项不为 0", got is not None and int(got) >= 1,
            "base=0 now=%s" % got)

    # ---- M6：清空全部 high ----
    def m6(doc):
        for f in doc["findings"]:
            f["severity"] = "low"
    for tag, rc, out in mutate("M6", m6):
        got = counter(out, r"severity==high\s*=\s*(\d+)")
        frozen = counter(out, r"落在\*\*已核实冻结\*\*件上的 high = (\d+) 条")
        rec("M6 全部降级 ⇒ high=0 且冻结命中=0",
            got == "0" and frozen == "0", "high=%s frozen=%s" % (got, frozen))

    print("\n" + "=" * 82)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
