"""Port test for _cm_AUDIT.md §3(c) template (_cm_AUDIT.md:469-536).

I paste the template VERBATIM below (same function names, same bodies except the
three placeholders I must fill), point it at a DIFFERENT script (check_d29.py,
hard-coded OR keyword tuple, no CLI), and record what it takes to make it run and
what the four reported metrics come out as.

Changes relative to the published template (counted, not hidden):
  1. run_once body: replaced `raise NotImplementedError` with a temp-copy adapter
  2. parse body   : replaced `raise NotImplementedError` with a gate parser
  3. inputs       : `[...]` -> ["互斥", "前提"]
  4. tempfile.TemporaryDirectory() -> TemporaryDirectory(dir=<write domain>)
Everything else is copied line-for-line from _cm_AUDIT.md:473-535.
"""
import hashlib, shutil, subprocess, sys, tempfile
from pathlib import Path

SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"   # 保证零命中

REPO = Path("D:/Project/ra2-campaign-forge")
SRC = REPO / "lead/d29_ruling_20261106"
WD = REPO / "lead/check_masking_20261109"
SANDBOX_ROOT = WD / "_cmv_tmp" / "tpl"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)


def run_once(inputs, workdir):
    """(a) CLI 多输入 / (b) 硬编码词表：临时副本替换词表字面量，再跑副本。
    禁止写回源文件；所有写入限制在 workdir。"""
    sb = Path(workdir) / ("run_" + "_".join(str(i) for i in inputs).replace("/", "_"))
    sb.mkdir(parents=True, exist_ok=True)
    for name in ("check_d29.py", "RULING_D29.md", "FACTCHECK.md"):
        shutil.copy2(str(SRC / name), str(sb / name))
    sp = sb / "check_d29.py"
    text = sp.read_text(encoding="utf-8")
    # OR tuple is ('互斥', '前提') at check_d29.py:76. Replace with inputs.
    tuple_src = '"互斥", "前提"'
    tuple_dst = ", ".join('"%s"' % x for x in inputs)
    assert tuple_src in text, "OR tuple literal not found"
    sp.write_text(text.replace(tuple_src, tuple_dst, 1), encoding="utf-8")
    cmd = [sys.executable, "-I", "-X", "utf8", str(sp)]
    p = subprocess.run(cmd, cwd=str(sb), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).splitlines()


def parse(lines):
    """按脚本形态返回 (aggregate_pass, controls)：
       三 gate：aggregate = (exit == 0)  <- see NOTE below
               controls  = 目标检查项 [4] 未出现在 failures 中"""
    txt = "\n".join(lines)
    ok = ("PASS" in txt) and ("FAIL" not in txt)
    controls = ["[4]" not in txt]      # OR item [4] not reported as failure
    return ok, controls


def real_per_input_selftest(inputs, workdir):
    """甲' 核心：每根输入单独跑未修改被审脚本，AND_k 才给 PASS。"""
    per = []
    for i, x in enumerate(inputs):
        rc, lines = run_once([x], workdir)          # 单输入，不是并集
        ok, controls = parse(lines)
        per.append(ok and rc == 0 and all(controls))
        print(f"  input[{i}] = {x!r}: SELF_TEST={'PASS' if per[-1] else 'FAIL'}"
              f" controls={sum(controls)}/{len(controls)}")
    return all(per)                                  # AGGREGATE = AND_k


def bad_needle_injection(inputs, workdir):
    """坏针注入：依次把第 i 根换成哨兵，要求 AGGREGATE 变 FAIL。"""
    results = []
    for i in range(len(inputs)):
        broken = list(inputs)
        broken[i] = SENTINEL
        rc, lines = run_once(broken, workdir)
        ok, _ = parse(lines)
        caught = (rc != 0) or (not ok)
        results.append(caught)
        print(f"  broken[{i}] -> {SENTINEL}: caught={caught}  (rc={rc})")
    return all(results)                              # 每根坏针都必须被抓


def main():
    inputs = ["互斥", "前提"]       # 填：needles / OR 词表；k>=2
    with tempfile.TemporaryDirectory(dir=str(SANDBOX_ROOT)) as workdir:
        base_rc, base_lines = run_once(inputs, workdir)
        base_ok, _ = parse(base_lines)
        agg   = real_per_input_selftest(inputs, workdir)
        inj   = bad_needle_injection(inputs, workdir)
        print(f"BASE_PASS={base_ok}  AND_k={agg}  BAD_NEEDLE_CAUGHT={inj}")
        verdict = base_ok and agg and inj
        print("DISTINGUISHABLE_PASS =", verdict)
        return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
