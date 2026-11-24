# -*- coding: utf-8 -*-
"""独立复核员·Q4 —— 自写探针，不调用 _w9_q4.py，不采信其任何数字。

只读：gamemd.exe / EXCEPT 件 / 仓内 except* 文本 / harness 源码。
唯一写域 = W9_SINGLESTEP_7CFC9F/reviews/。
运行：python -I -X utf8 <this file>
"""
import sys
import os
import re
import hashlib
import subprocess
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = ROOT + (r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
                 r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\reviews\_Q4_review_probe_out.txt"
VA = 0x7CFC9F
TARGET = "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251"
FIND = r"D:\Git\usr\bin\find.exe"

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

L = []


def p(s=""):
    L.append(str(s))
    print(s, flush=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def all_files():
    r = subprocess.run([FIND, ".", "-path", "./.git", "-prune", "-o", "-type", "f", "-print"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    p("[find-all] rc=%d stderr=%r lines=%d" % (r.returncode, r.stderr[:100], len(r.stdout.splitlines())))
    return [os.path.normpath(os.path.join(ROOT, x)) for x in r.stdout.splitlines()
            if x.strip() and not x.replace("\\", "/").startswith("./.git/")]


def main():
    p("=" * 78)
    p("Q4 独立复核探针（自写 / 不调用 _w9_q4.py）")
    p("=" * 78)

    # --- 1. 两个 SHA256 + 字节数（hashlib 自算） ---
    eb = Path(EXE).read_bytes()
    xb = Path(EXCEPT).read_bytes()
    p("[R1] gamemd.exe sha=%s size=%d" % (sha(eb), len(eb)))
    p("[R1] EXCEPT     sha=%s size=%d" % (sha(xb), len(xb)))
    p("[R1] EXCEPT L1 = %r" % xb.splitlines()[0].decode("utf-8", "replace"))
    p("[R1] EXCEPT L3 = %r" % xb.splitlines()[2].decode("utf-8", "replace"))

    # --- 2. Engine 自证 + 真读字节 + 真反汇编 ---
    e = Engine()
    p("[R2] Engine.sha == 自算 : %s" % (e.sha == sha(eb)))
    p("[R2] IMAGEBASE = %s" % hex(e.IB))
    p("[R2] fo(0x7CFC9F) = %s (VA-0x400000=%s)" % (hex(e.fo(VA)), hex(VA - 0x400000)))
    cov, nins, nf = e.coverage
    p("[R2] COVERAGE = %.12f%% / %d insns / %d resync-fails" % (cov, nins, nf))
    raw = e.rd(VA, 32)
    p("[R2] e.rd(0x7CFC9F,32) = " + raw.hex(" ").upper())
    # 独立解析 EXCEPT 的 'Bytes at CS:EIP' 行
    ev = None
    for ln in Path(EXCEPT).read_text(encoding="utf-8", errors="replace").splitlines():
        if "Bytes at CS:EIP" in ln:
            tail = ln.rsplit(":", 1)[1]
            ev = bytes(int(x, 16) for x in re.findall(
                r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{2}(?![0-9A-Fa-f])", tail))
    p("[R2] EXCEPT L17 解析 = %s (len=%d)" % (ev.hex(" ").upper() if ev else "NONE", len(ev or b"")))
    p("[R2] rd[0:32] == EXCEPT L17 : %s ; diff idx = %s" % (
        raw == ev, [i for i in range(min(len(raw), len(ev or b""))) if raw[i] != ev[i]]))
    by = e.by()
    p("[R2] VA in e.by() = %s" % (VA in by))
    d = e.disasm(VA, 32)
    p("[R2] e.disasm(VA,32) 条数 = %d" % len(d))
    for j, (a, hx, mn, ops) in enumerate(d[:8]):
        p("     [%d] 0x%08X %-12s %-7s %s" % (j, a, hx.upper(), mn, ops))
    ins = by.get(VA)
    p("[R2] by()[VA] bytes=%s %s %s" % (bytes(ins.bytes).hex().upper(), ins.mnemonic, ins.op_str) if ins else "NONE")

    # --- 3. 整仓全量 except_post_*.txt 哈希逐一比对（独立于 Q4 的实现） ---
    fs = all_files()
    import fnmatch
    posts = sorted(f for f in fs if fnmatch.fnmatch(os.path.basename(f), "except_post_*.txt"))
    recs = [(sha(Path(f).read_bytes()), Path(f).stat().st_size, f) for f in posts]
    same = [r for r in recs if r[0] == TARGET]
    diff = [r for r in recs if r[0] != TARGET]
    byte_same = [r for r in recs if Path(r[2]).read_bytes() == xb]
    p("[R3] 整仓 except_post_*.txt 总数 = %d" % len(posts))
    p("[R3] 与 TARGET 同哈希 = %d ; 不同 = %d ; distinct = %d" % (
        len(same), len(diff), len({r[0] for r in recs})))
    p("[R3] 逐字节全文 == EXCEPT = %d / %d" % (len(byte_same), len(recs)))
    p("[R3] 尺寸集合 = %s" % sorted({r[1] for r in recs}))
    for r in diff:
        p("     DIFF %s %d %s" % (r[0], r[1], os.path.relpath(r[2], ROOT)))
    # 更宽口径：大小写不敏感 / 任意含 except_post 名
    wide = sorted(f for f in fs if "except_post" in os.path.basename(f).lower())
    wide_diff = [f for f in wide if f.lower().endswith(".txt") and sha(Path(f).read_bytes()) != TARGET]
    p("[R3] 宽口径 *except_post* 文件数 = %d ; 其中 .txt 且哈希不同 = %d" % (len(wide), len(wide_diff)))
    for f in wide:
        if not f.lower().endswith(".txt"):
            p("     非 txt: %s" % os.path.relpath(f, ROOT))

    # --- 4. 反例猎捕：所有含 007CFC9F 的 except*.txt，凡哈希 != TARGET 全部列出寄存器 ---
    hits = []
    for f in fs:
        bn = os.path.basename(f)
        if not (bn.lower().startswith("except") and bn.lower().endswith(".txt")):
            continue
        try:
            b = Path(f).read_bytes()
        except OSError:
            continue
        if b"007CFC9F" in b:
            hits.append((sha(b), len(b), f, b))
    p("[R4] 含 007CFC9F 的 except*.txt 总数 = %d" % len(hits))
    p("[R4] distinct 哈希 = %d" % len({h[0] for h in hits}))
    from collections import Counter
    for h, c in Counter(h[0] for h in hits).most_common():
        p("     %s x%d %s" % (h, c, "<== TARGET 基线" if h == TARGET else "<== 反例/不同哈希"))
    p("[R4] --- 不同哈希件逐件头部（L1/L3/L11/L13/L17） ---")
    for h, n, f, b in sorted((x for x in hits if x[0] != TARGET), key=lambda x: x[2]):
        lines = b.decode("utf-8", "replace").splitlines()
        p("     FILE %s" % os.path.relpath(f, ROOT))
        p("       sha=%s size=%d" % (h, n))
        for idx in (0, 2, 10, 12, 16):
            if idx < len(lines):
                p("       L%-2d %r" % (idx + 1, lines[idx][:160]))

    # --- 5. 上游 except.txt / odd-named / ra2bench 母本 ---
    srcs = sorted(f for f in fs if os.path.basename(f).lower() == "except.txt")
    srecs = [(sha(Path(f).read_bytes()), f) for f in srcs]
    p("[R5] except.txt 总数 = %d ; distinct 哈希 = %d ; == TARGET = %d" % (
        len(srcs), len({r[0] for r in srecs}), sum(1 for r in srecs if r[0] == TARGET)))
    odd = sorted(f for f in fs if fnmatch.fnmatch(os.path.basename(f), "except_*.txt")
                 and not os.path.basename(f).startswith("except_post_"))
    p("[R5] odd-named except_*.txt = %d ; == TARGET = %d" % (
        len(odd), sum(1 for f in odd if sha(Path(f).read_bytes()) == TARGET)))
    master = os.path.join(ROOT, "ra2bench", "except.txt")
    if os.path.exists(master):
        mb = Path(master).read_bytes()
        p("[R5] ra2bench/except.txt sha=%s size=%d L1=%r L3=%r" % (
            sha(mb), len(mb), mb.splitlines()[0].decode("utf-8", "replace"),
            mb.splitlines()[2].decode("utf-8", "replace")))

    # --- 6. 时间反证（独立 stat / cmp） ---
    import datetime
    def mt(f):
        return datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
    ear = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead",
                       "qc161_u0400_trip", "archive_T5", "except_post_20261017T081458810997.txt")
    p("[R6] EXCEPT mtime = %s ; size=%d" % (mt(EXCEPT), os.path.getmtime(EXCEPT) and len(xb)))
    p("[R6] EARLIEST mtime = %s ; exists=%s" % (mt(ear), os.path.exists(ear)))
    p("[R6] cmp(EXCEPT, EARLIEST) bytes equal = %s" % (xb == Path(ear).read_bytes()))
    stamps = []
    for f in posts:
        m = re.search(r"except_post_(\d{8}T\d{6})\d*\.txt", os.path.basename(f))
        if m:
            stamps.append(m.group(1)[:12])
    p("[R6] 文件名时间戳 < 20261019T1352 = %d ; >= = %d ; total=%d" % (
        sum(1 for s in stamps if s < "20261019T1352"),
        sum(1 for s in stamps if s >= "20261019T1352"), len(stamps)))
    mt_range = sorted(mt(f) for f in posts)
    p("[R6] mtime 范围 = %s .. %s" % (mt_range[0], mt_range[-1]))

    Path(OUT).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n[written] " + OUT, flush=True)


if __name__ == "__main__":
    main()
