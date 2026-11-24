# -*- coding: utf-8 -*-
# 逐输入独立跑 + AND_k + 坏针注入：真 exit code 捕获（无管道）
# 全部 python -I -X utf8 + 绝对路径；只读驱动，结果走 stdout
import subprocess, sys, hashlib, os

S = r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109\_sp_sandbox"
CFG = {
    "d27": (S, [("外推", "_w_d27_A.py"), ("卡顿不存在", "_w_d27_B.py"),
                ("SENTINEL", "_w_d27_S.py")]),
    "d29": (S + r"\d29", [("互斥", "_w_d29_A.py"), ("前提", "_w_d29_B.py"),
                          ("SENTINEL", "_w_d29_S.py")]),
    "d30": (S + r"\d30", [("93.98", "_w_d30_A.py"), ("误报率", "_w_d30_B.py"),
                          ("SENTINEL", "_w_d30_S.py")]),
    "d28": (S + r"\d28x\a\b", [("历史数字", "_w_d28_A.py"), ("1681", "_w_d28_B.py"),
                               ("SENTINEL", "_w_d28_S.py")]),
}

def run(cwd, script):
    p = os.path.join(cwd, script)
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", p],
                       cwd=cwd, capture_output=True)
    out = r.stdout.decode("utf-8", errors="replace").strip()
    return r.returncode, out, hashlib.sha256(open(p, "rb").read()).hexdigest()

for key, (cwd, items) in CFG.items():
    print("=== %s ===" % key)
    per = []
    for label, fn in items:
        rc, out, sha = run(cwd, fn)
        ok = (rc == 0) and ("PASS" in out) and ("FAIL" not in out)
        print("  input[%-12s] EXIT=%d PASS=%s sha256=%s" %
              (label, rc, ok, sha[:16]))
        print("      STDOUT = %r" % out)
        if label != "SENTINEL":
            per.append(ok)
    agg = all(per)
    print("  AND_k(over %d real per-word runs) = %s" % (len(per), agg))
    # 坏针必须被抓：SENTINEL 单跑须 FAIL
    rc_s, out_s, _ = run(cwd, items[-1][1])
    caught = (rc_s != 0) or ("FAIL" in out_s)
    print("  BAD_NEEDLE_CAUGHT = %s (sentinel EXIT=%d)" % (caught, rc_s))
    print("  DISTINGUISHABLE_PASS = %s" % (agg and caught))
    print()
