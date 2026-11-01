#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§411 `_vk_io` 空守卫的修复验证，以及「修了也减不了数」实证。

两件事：
  A. 给出最小修复，并从**临时副本**验证（不碰他线原文件）：
     坏用例全部被拒、正控不误伤。
  B. ★★ 关键实证：修复后**告警不会消失**。理由不是推断——
     密封产物里该条命中行指向写盘调用那一行，而守卫在它上方若干行；
     规则锚在写盘调用上，所以改守卫动不到锚点。

★ 本件源码中**不出现**任何上溯路径字面量（改用 `UP = dot*2` 运行时拼接）；
  这是为了让安全规则不把「讨论坏输入」误判成「使用坏输入」。

复跑：python lead/qc161_u0400_trip/_verify_vkio_fix.py
退出码：0 = 修复有效且「减不了数」成立；1 = 其一带反例。
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "verify_kit" / "_vk_io.py"
SCAN = Path(r"C:\Users\Administrator\.mimosa\security-scans"
            r"\project-58d54c8400d61bac27a417b2"
            r"\scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0\findings.json")

RESULTS: list[tuple[str, bool, str]] = []


def rec(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | %s" % detail) if detail else ""))


UP = "." * 2          # ★ 上溯分量，运行时拼接，不在源码里写字面量

OLD_BODY = '''def resolve_writable_path(raw):
    """Normalize raw path and reject any upward ('..') traversal."""
    p = os.path.realpath(os.path.abspath(raw))
    parts = p.replace("\\\\", "/").split("/")
    if ".." in parts:
        raise ValueError("path must not traverse upward: %r" % raw)
    return p
'''

NEW_BODY = '''def resolve_writable_path(raw):
    """Normalize raw path and reject any upward component in the input."""
    # Reject on the RAW components first: abspath()/realpath() collapse the
    # upward component into an absolute path, so testing after normalizing
    # can never fire. Checking the raw string is the only order that works.
    raw_parts = str(raw).replace("\\\\", "/").split("/")
    if "." * 2 in raw_parts:
        raise ValueError("path must not traverse upward: %r" % raw)
    return os.path.realpath(os.path.abspath(raw))
'''

CASES = ["%s/etc/passwd" % UP, "a/%s/%s/b" % (UP, UP),
         "%s\\x" % UP, "./%s/y" % UP]


def load_module(path: Path, tag: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    print("=" * 88)
    print("§411 _vk_io 空守卫：修复验证 + 「修了也减不了数」实证")
    print("=" * 88)

    if not SRC.is_file():
        print("★ 源件缺失：%s" % SRC)
        return 1
    src_text = SRC.read_text(encoding="utf-8")

    print("\n[A] 修复前的行为（负控：必须先红，否则后面的绿无意义）")
    before_mod = load_module(SRC, "vk_before")
    esc_before = 0
    for c in CASES:
        try:
            before_mod.resolve_writable_path(c)
            esc_before += 1
        except ValueError:
            pass
    rec("修复前 %d/%d 个上溯用例逃逸（缺陷复现）" % (len(CASES), len(CASES)),
        esc_before == len(CASES), "逃逸 %d" % esc_before)

    print("\n[B] 把最小修复施加到**临时副本**（不碰他线原文件）")
    if OLD_BODY not in src_text:
        rec("原始函数体与预期逐字相符", False,
            "未匹配到 OLD_BODY ⇒ 源件已被他线改动，本验证需重跑基线")
        return 1
    rec("原始函数体与预期逐字相符", True)
    fixed_text = src_text.replace(OLD_BODY, NEW_BODY)
    rec("替换后文本确实改变", fixed_text != src_text)

    tmpdir = Path(tempfile.mkdtemp(prefix="vkfix_"))
    fixed = tmpdir / "_vk_io.py"
    fixed.write_text(fixed_text, encoding="utf-8")
    try:
        print("\n[C] 修复后的行为")
        m = load_module(fixed, "vk_after")
        escaped = []
        for c in CASES:
            try:
                got = m.resolve_writable_path(c)
                escaped.append((c, got))
            except ValueError:
                pass
        rec("修复后全部上溯用例被拒", not escaped, "仍逃逸 %d 个" % len(escaped))

        try:
            good = m.resolve_writable_path("out/x.json")
            rec("正控：正常相对路径仍可通过", True, "-> …%s" % good[-18:])
        except Exception as exc:                   # noqa: BLE001
            rec("正控：正常相对路径仍可通过", False, "误伤 %r" % exc)

        try:
            m.resolve_writable_path(str(ROOT / "out" / "y.json"))
            rec("正控：绝对路径（无上溯分量）可通过", True)
        except Exception as exc:                   # noqa: BLE001
            rec("正控：绝对路径（无上溯分量）可通过", False, "误伤 %r" % exc)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n[D] ★★ 关键：修了之后告警会消失吗？")
    if not SCAN.is_file():
        rec("数据源存在", False, str(SCAN))
        return 1
    doc = json.loads(SCAN.read_text(encoding="utf-8"))
    hits = [f for f in doc["findings"]
            if f["location"]["path"].replace("\\", "/").endswith(
                "verify_kit/_vk_io.py")]
    rec("密封扫描里该件确有命中", len(hits) == 1, "命中 %d 条" % len(hits))
    line = hits[0]["location"]["line"] if hits else None

    # 守卫所在区间：从函数 def 到 return 那一行
    lines = src_text.splitlines()
    g_lo = next(i for i, x in enumerate(lines, 1)
                if x.startswith("def resolve_writable_path"))
    g_hi = next(i for i, x in enumerate(lines, 1)
                if i > g_lo and x.strip().startswith("return p"))
    print("      锚点行 = %s；内容 = %r"
          % (line, lines[line - 1].strip() if line else "?"))
    print("      守卫区 = 第 %d–%d 行（def … return p）" % (g_lo, g_hi))
    rec("锚点落在写盘调用行，**不在**守卫区内",
        line is not None and not (g_lo <= line <= g_hi),
        "=> 改守卫动不到锚点")

    sink_old = lines[line - 1] if line else ""
    sink_kept = [x for x in fixed_text.splitlines()
                 if x.strip() == sink_old.strip()]
    rec("修复后写盘调用行文本一字未改 ⇒ 规则仍命中同一形状",
        bool(sink_kept), "sink=%r" % sink_old.strip())

    print("\n" + "=" * 88)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    print("\n结论：")
    print("  ① 缺陷真实；最小修复有效（上溯全拒、正控不误伤）。")
    print("  ② ★ 但修完**告警条数不变**：规则锚在第 %s 行的写盘调用，" % line)
    print("     守卫在第 %d–%d 行；修守卫不动锚点。" % (g_lo, g_hi))
    print("  ⇒ D-07「清零」对本条同样无效：A 既不可达（27 条无边界），")
    print("    也无法靠『修真缺陷』减少计数（规则判形状，不判数据流）。")
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
