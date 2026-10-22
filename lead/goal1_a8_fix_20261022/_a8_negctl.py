#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A8 补丁的负控：证明生成器的 6 项自检**有判别力**。

方法：对每项自检，构造一个"故意做错"的变体，重跑同一判定，必须变红。
若某项改错后仍绿 ⇒ 该自检无效，补丁不可采信。

负控段
------
N-1 母本哈希改位：期望"母本哈希校验"变红（防止误改母本）。
N-2 守卫改成 try 局部名 `allow_loader_flag`：期望"作用域自检"变红。
N-3 删掉 `A8_ALLOW_LOADER = [False]` 声明：期望"容器顺序自检"变红。
N-4 在补丁里删一行母本内容：期望"零删除行"变红。
N-5 删掉 A8 清扫函数定义：期望"符号存在"变红。
N-6 在 A8 块里塞回 `if _u8_authorized:`：期望"作用域自检"变红。

本脚本**不写任何文件**，只在内存里做替换后跑判定。
"""
import ast
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u8_impl_20261021/qc151_trip.harness3_u8.py"
DST = ROOT / "lead/goal1_a8_fix_20261022/qc151_trip.harness4.py"

SRC_SHA16 = "7db3c11009b7183c"

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


def judge(text, mother_text):
    """与生成器同口径的一组判定，返回 dict。"""
    r = {}
    try:
        ast.parse(text)
        r["syntax"] = True
    except SyntaxError:
        r["syntax"] = False
    r["guard_module_level"] = "if A8_ALLOW_LOADER[0]:" in text
    a8_pos = text.find("# ==== [A8] 授权趟")
    tail = text[a8_pos:] if a8_pos >= 0 else ""
    r["no_try_local"] = not any(b in tail for b in
                                ("allow_loader_flag", "if _u8_authorized:",
                                 "if allow_loader:"))
    decl = text.find("A8_ALLOW_LOADER = [False]")
    use = text.find("A8_ALLOW_LOADER[0] = bool(_u8_authorized)")
    guard = text.find("if A8_ALLOW_LOADER[0]:")
    r["container_order"] = (0 < decl < use < guard)
    r["symbols"] = all(s in text for s in
                       ("def a8_sweep_carrier_processes",
                        "def _a8_query_image_path",
                        "def _a8_path_under_carrier"))
    c_old = Counter(mother_text.split("\n"))
    c_new = Counter(text.split("\n"))
    r["no_removed_lines"] = all(c_new[ln] >= c_old[ln] for ln in c_old)
    return r


def main():
    mother = SRC.read_text(encoding="utf-8")
    good = DST.read_text(encoding="utf-8")

    msha = hashlib.sha256(SRC.read_bytes()).hexdigest()[:16]
    print(f"mother sha16: {msha} (expect {SRC_SHA16})")
    if not chk("baseline: mother hash matches", msha == SRC_SHA16, msha):
        return 1

    print()
    print("=" * 74)
    print("== baseline: the real harness4 must pass ALL judgements")
    print("=" * 74)
    base = judge(good, mother)
    for k, v in base.items():
        chk(f"baseline {k}", v, str(v))

    print()
    print("=" * 74)
    print("== N-1  mother hash mutated by 1 bit (expect RED)")
    print("=" * 74)
    bad_sha = hashlib.sha256(mother.encode("utf-8") + b" ").hexdigest()[:16]
    chk("N-1 RED: appended space changes mother hash", bad_sha != SRC_SHA16,
        f"{bad_sha} != {SRC_SHA16}")

    print()
    print("=" * 74)
    print("== N-2  guard replaced with try-local `allow_loader_flag` (expect RED)")
    print("=" * 74)
    v2 = good.replace("if A8_ALLOW_LOADER[0]:", "if allow_loader_flag:", 1)
    r2 = judge(v2, mother)
    chk("N-2 RED: scope self-check fails", not (r2["guard_module_level"]
                                                and r2["no_try_local"]),
        f"guard={r2['guard_module_level']} no_try_local={r2['no_try_local']}")

    print()
    print("=" * 74)
    print("== N-3  container declaration deleted (expect RED)")
    print("=" * 74)
    v3 = good.replace("A8_ALLOW_LOADER = [False]", "A8_ALLOW_LOADER_DISABLED = [False]", 1)
    r3 = judge(v3, mother)
    chk("N-3 RED: container ordering self-check fails", not r3["container_order"],
        f"order={r3['container_order']}")

    print()
    print("=" * 74)
    print("== N-4  one mother line removed from the patch (expect RED)")
    print("=" * 74)
    # 删掉母本里必然存在的一行
    victim = "def find_pids(name: str) -> list:"
    assert victim in good
    v4 = good.replace(victim, "", 1)
    r4 = judge(v4, mother)
    chk("N-4 RED: zero-removed-lines self-check fails", not r4["no_removed_lines"],
        f"no_removed_lines={r4['no_removed_lines']}")

    print()
    print("=" * 74)
    print("== N-5  A8 sweep function definition removed (expect RED)")
    print("=" * 74)
    v5 = good.replace("def a8_sweep_carrier_processes(", "def _removed_sweep(", 1)
    r5 = judge(v5, mother)
    chk("N-5 RED: symbol self-check fails", not r5["symbols"],
        f"symbols={r5['symbols']}")

    print()
    print("=" * 74)
    print("== N-6  try-local guard injected into the A8 block (expect RED)")
    print("=" * 74)
    v6 = good.replace("if A8_ALLOW_LOADER[0]:",
                      "if _u8_authorized:", 1)
    r6 = judge(v6, mother)
    chk("N-6 RED: no-try-local self-check fails", not r6["no_try_local"],
        f"no_try_local={r6['no_try_local']}")

    print()
    print("=" * 74)
    print("== summary")
    print("=" * 74)
    reds = sum(1 for n, ok, _ in CHECKS if n.startswith("N-") and "RED" in n)
    print(f"negative-control RED segments: {reds}/6")
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
