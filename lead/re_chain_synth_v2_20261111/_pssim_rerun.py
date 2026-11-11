# -*- coding: utf-8 -*-
"""_pssim_rerun.py — STEP 2（质疑二）：_ps_disasm 探针的 stdout 口径实测。
做法（不修改任何既有件、不触碰只读目录的写路径）：
  1) 把 lead/playerctrl_semantics_20261111/_ps_disasm.py 逐字节复制到本写域（副本 sha256 必须与原件一致，
     证明脚本未被改动；原件本身只读）；
  2) 在写域内以 `python -I -X utf8 <副本>` 重跑，stdout/stderr 分别重定向到本写域文件（文件句柄，非管道）；
     副本因 HERE=写域，其 _ps_disasm_out.txt/.json 也落在本写域，原件目录零写入；
  3) 实算各产物 sha256/字节数，并对拍：重跑 out.txt vs 既有原件 out.txt（文件级对拍）；
  4) 判定 stdout 级复现门能否建立。
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LEAD = os.path.join(REPO, "lead")
SRC = os.path.join(LEAD, "playerctrl_semantics_20261111", "_ps_disasm.py")
COPY = os.path.join(HERE, "_ps_disasm_rerun_copy.py")
OUT_STDOUT = os.path.join(HERE, "_pssim_rerun_stdout.txt")
OUT_STDERR = os.path.join(HERE, "_pssim_rerun_stderr.txt")
NEW_TXT = os.path.join(HERE, "_ps_disasm_out.txt")
NEW_JSON = os.path.join(HERE, "_ps_disasm_out.json")
OLD_TXT = os.path.join(LEAD, "playerctrl_semantics_20261111", "_ps_disasm_out.txt")
OLD_JSON = os.path.join(LEAD, "playerctrl_semantics_20261111", "_ps_disasm_out.json")
EMPTY_SHA = hashlib.sha256(b"").hexdigest()


def fp(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
            h.update(b)
    return h.hexdigest(), n


def main():
    print("== STEP2 复跑：_ps_disasm stdout 口径实测 ==")

    # 1) 字节级复制 + 指纹一致性
    shutil.copyfile(SRC, COPY)
    s1, n1 = fp(SRC)
    s2, n2 = fp(COPY)
    print("[1] 原件 %s (%d B)" % (s1, n1))
    print("    副本 %s (%d B)  一致=%s" % (s2, n2, s1 == s2))
    if s1 != s2:
        print("    !! 副本指纹不一致，终止")
        sys.exit(2)

    # 2) 写域内重跑，stdout/stderr 落文件
    with open(OUT_STDOUT, "wb") as so, open(OUT_STDERR, "wb") as se:
        rc = subprocess.call([sys.executable, "-I", "-X", "utf8", COPY],
                             stdout=so, stderr=se, cwd=HERE)
    print("[2] 重跑退出码=%d (命令=python -I -X utf8 <写域副本>)" % rc)

    # 3) 指纹与对拍
    rows = []
    for tag, p in (("重跑 stdout", OUT_STDOUT), ("重跑 stderr", OUT_STDERR),
                   ("重跑 out.txt(写域)", NEW_TXT), ("重跑 out.json(写域)", NEW_JSON),
                   ("既有 out.txt(只读原件)", OLD_TXT), ("既有 out.json(只读原件)", OLD_JSON)):
        if os.path.isfile(p):
            s, n = fp(p)
            rows.append((tag, s, n))
            print("[3] %-22s sha256=%s  %d B%s" % (tag, s, n, "  (== 空串 sha)" if s == EMPTY_SHA else ""))
        else:
            print("[3] %-22s 不存在" % tag)

    print("[4] 文件级对拍（重跑 out.txt vs 既有 out.txt）: %s" %
          ("MATCH" if fp(NEW_TXT)[0] == fp(OLD_TXT)[0] else "MISMATCH"))
    print("    文件级对拍（重跑 out.json vs 既有 out.json）: %s" %
          ("MATCH" if fp(NEW_JSON)[0] == fp(OLD_JSON)[0] else "MISMATCH"))

    so_n = os.path.getsize(OUT_STDOUT)
    se_n = os.path.getsize(OUT_STDERR)
    print("[5] 判定: stdout=%d B, stderr=%d B" % (so_n, se_n))
    if so_n == 0:
        print("    stdout 复现门不可建立：探针 stdout 恒为空 —— 脚本把 print 重定向为内部缓冲")
        print("    并只写自己目录的 _ps_disasm_out.txt/_ps_disasm_out.json（原件 L19/L22-23/L113/L456-457/L471-472），")
        print("    唯一控制台输出为 stderr '(done)'（原件 L474）。复现口径只能是文件级对拍。")
    else:
        print("    stdout 非空，可建立 stdout 级复现门（与上轮 _repro_ps_disasm.txt=0B 矛盾，需复查）。")


if __name__ == "__main__":
    main()
