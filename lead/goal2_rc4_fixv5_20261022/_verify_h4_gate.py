#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§405 H-4 门禁核验：`_todo7_creation_trigger.py` 新增的边界断言能杀掉哪些变异。

★ 判据纪律
  只看退出码不够 —— 任何一条 FAIL 都让 rc=1，区分不出「变异被目标断言抓到」
  还是「变异把别的断言弄红了」。所以每个变异都要断言：
    ① rc != 0
    ② **指定**的断言标签出现在 FAIL 行里
    ③ 未指定的关键断言仍然 PASS（证明不是全局崩坏）

★ 变异只改常量/窗口表达式，不改被测逻辑本身。
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET = Path(__file__).with_name("_todo7_creation_trigger.py")
PY = sys.executable

# (名字, 旧文本, 新文本, 必须变红的断言子串, 必须仍绿的断言子串)
MUTATIONS = [
    ("M1 窗口改回手选 0x400（函数体被截断）",
     "BODY_END = JT_DWORDS",
     "BODY_END = WNDPROC_HINT + 0x400",
     "函数体内 ret 数 = 11",
     "创建入口唯一"),

    ("M2 窗口越过函数体 0x80（捡到别的函数）",
     "BODY_END = JT_DWORDS",
     "BODY_END = JT_DWORDS + 0x80",
     "函数体内全部 ret 尺寸唯一",
     "创建入口唯一"),

    ("M3 分派表基址常量写错（+0xC）",
     "JT_DWORDS = 0x777A80",
     "JT_DWORDS = 0x777A8C",
     "间接跳转的基址 = JT_DWORDS",
     "函数体内全部 ret 尺寸唯一"),

    ("M4 字节索引表基址常量写错（+0x10）",
     "JT_BYTES = 0x777A98",
     "JT_BYTES = 0x777AA8",
     "字节索引表基址 = JT_BYTES",
     "间接跳转的基址 = JT_DWORDS"),

    ("M5 负控窗口缩回函数体内（负控失去杀伤力）",
     "beyond = dis(WNDPROC_HINT, (BODY_END - WNDPROC_HINT) + 0x80)",
     "beyond = dis(WNDPROC_HINT, (BODY_END - WNDPROC_HINT))",
     "负控 窗口越过函数体 0x80 字节",
     "函数体内全部 ret 尺寸唯一"),

    ("M6 函数入口错移 1 字节",
     "WNDPROC_HINT = 0x7775C0",
     "WNDPROC_HINT = 0x7775C1",
     "入口前 3 字节全是填充",
     "负控 旧值"),

    ("M7 帧对称修正为 3 条 pop（破坏配平断言）",
     'tail_pops == ["pop edi", "pop esi", "pop ebx", "pop ecx"]',
     'tail_pops == ["pop edi", "pop esi", "pop ebx"]',
     "末 ret 前 4 条 = pop",
     "函数体内 ret 数 = 11"),
]


def run(src_text: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "_t7_mut.py"
        p.write_text(src_text, encoding="utf-8")
        r = subprocess.run([PY, str(p)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        return r.returncode, (r.stdout or "") + (r.stderr or "")


def fails(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.startswith("[FAIL]")]


def passes(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.startswith("[PASS]")]


def main() -> int:
    base_src = TARGET.read_text(encoding="utf-8")
    print("=" * 92)
    print("§405 H-4 门禁核验：%s" % TARGET.name)
    print("=" * 92)

    # ---------- 基线 ----------
    rc, out = run(base_src)
    m = re.search(r"checks passed: (\d+)/(\d+)", out)
    base = (m.group(1), m.group(2)) if m else ("?", "?")
    print()
    print("--- 基线 ---")
    print("  rc=%d  checks %s/%s  FAIL=%d"
          % (rc, base[0], base[1], len(fails(out))))
    base_ok = rc == 0 and not fails(out)
    print("  [%s] 基线必须全绿（否则后面所有变异判定无意义）"
          % ("PASS" if base_ok else "FAIL"))
    if not base_ok:
        for ln in fails(out)[:10]:
            print("     " + ln)
        return 1

    # ---------- 变异 ----------
    rows = []
    print()
    print("--- 变异 ---")
    for name, old, new, must_red, must_green in MUTATIONS:
        n_old = base_src.count(old)
        if n_old != 1:
            print("  [%s] %s" % ("SKIP", name))
            print("     锚出现 %d 次（必须恰好 1 次）: %r" % (n_old, old))
            rows.append((name, "SKIP", n_old))
            continue
        mutated = base_src.replace(old, new)
        if mutated == base_src:
            print("  [%s] %s  变异未生效" % ("SKIP", name))
            rows.append((name, "SKIP", "no-op"))
            continue
        rc2, out2 = run(mutated)
        f = fails(out2)
        p = passes(out2)
        hit_red = any(must_red in ln for ln in f)
        hit_green = any(must_green in ln for ln in p)
        killed = rc2 != 0 and hit_red and hit_green
        print("  [%s] %s" % ("KILLED" if killed else "SURVIVED", name))
        print("     rc=%d  FAIL %d 条" % (rc2, len(f)))
        print("     目标断言变红: %s" % ("是" if hit_red else "否"))
        print("     对照断言仍绿: %s" % ("是" if hit_green else "否"))
        if not hit_red:
            print("     !! 目标 '{}' 未出现在 FAIL 里".format(must_red))
        if not hit_green:
            print("     !! 对照 '{}' 未出现在 PASS 里".format(must_green))
        if f and not killed:
            for ln in f[:5]:
                print("       " + ln)
        rows.append((name, "KILLED" if killed else "SURVIVED", rc2))

    # ---------- 汇总 ----------
    print()
    print("=" * 92)
    killed = sum(1 for _n, s, _v in rows if s == "KILLED")
    surv = [n for n, s, _v in rows if s == "SURVIVED"]
    skip = [n for n, s, _v in rows if s == "SKIP"]
    print("  变异总 %d：KILLED %d / SURVIVED %d / SKIP %d"
          % (len(rows), killed, len(surv), len(skip)))
    for n in surv:
        print("    SURVIVED: " + n)
    for n in skip:
        print("    SKIP    : " + n)
    ok = not surv and not skip
    print("  RESULT: %s" % ("ALL MUTATIONS KILLED" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
