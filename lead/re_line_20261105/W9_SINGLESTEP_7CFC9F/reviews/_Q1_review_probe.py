# -*- coding: utf-8 -*-
"""Q1 独立复核探针（只读；唯一写域 = reviews/ 下本探针输出）。
不调用 Q1 的 _w9_q1.py，独立重算哈希/字节、独立反汇编、独立普查直接分支落点。
"""
import sys
import re
import hashlib
import datetime
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = ROOT + (
    r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
    r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
TASK = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\TASK.md"
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\reviews\_Q1_review_probe_out.txt"
VA = 0x7CFC9F

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []


def p(s=""):
    _lines.append(str(s))
    print(s, flush=True)


def sha_of(path):
    b = Path(path).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b), b


def hex_tokens(line):
    tail = line.rsplit(":", 1)[1]
    return bytes(int(x, 16) for x in re.findall(
        r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{2}(?![0-9A-Fa-f])", tail))


def find_bytes_line(path):
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if "Bytes at CS:EIP" in ln:
            return ln
    return None


def main():
    p("=" * 78)
    p("Q1 INDEPENDENT REVIEW PROBE -- 0x7CFC9F")
    p("run: python -I -X utf8 <this file>   at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    p("=" * 78)

    # --- R1: 两个 SHA256 + 字节数，独立实算 ---
    p("")
    p("[R1] SHA256 / size (independently computed)")
    exe_sha, exe_n, _ = sha_of(EXE)
    exc_sha, exc_n, _ = sha_of(EXCEPT)
    p("gamemd.exe SHA256 = " + exe_sha + "  bytes = " + str(exe_n))
    p("EXCEPT      SHA256 = " + exc_sha + "  bytes = " + str(exc_n))

    # --- R2: Engine 自证 ---
    p("")
    p("[R2] Engine self-attestation")
    e = Engine()
    p("Engine.sha = " + e.sha + "  (== self SHA: " + str(e.sha == exe_sha) + ")")
    p("IMAGEBASE = " + hex(e.IB))
    p("fo(VA) = " + hex(e.fo(VA)) + " ; VA-0x400000 = " + hex(VA - 0x400000))
    by = e.by()
    cov, nins, nfails = e.coverage
    p("COVERAGE = %.12f%% / %d insns / %d resync-fails" % (cov, nins, nfails))
    p("TLO/THI/TSZ = %s / %s / %s" % (hex(e.TLO), hex(e.THI), hex(e.TSZ)))

    # --- R3: 原始字节 32 + 0x30，三源逐字节比对 ---
    p("")
    p("[R3] raw bytes + 3-source byte comparison")
    raw32 = e.rd(VA, 32)
    raw48 = e.rd(VA, 0x30)
    p("rd(VA,32)  = " + raw32.hex(" ").upper())
    p("rd(VA,0x30)= " + raw48.hex(" ").upper())
    ev = hex_tokens(find_bytes_line(EXCEPT))
    tv = hex_tokens(find_bytes_line(TASK))
    p("EXCEPT L17 bytes (%d) = %s" % (len(ev), ev.hex(" ").upper()))
    p("TASK.md:40  bytes (%d) = %s" % (len(tv), tv.hex(" ").upper()))
    p("rd32 == EXCEPT : " + str(raw32 == ev) + " ; diff idx = " +
      repr([i for i in range(min(len(raw32), len(ev))) if raw32[i] != ev[i]]))
    p("EXCEPT == TASK : " + str(ev == tv))
    p("len(raw32)=%d len(EXCEPT)=%d len(TASK)=%d" % (len(raw32), len(ev), len(tv)))

    # --- R4: 两条独立反汇编口径 ---
    p("")
    p("[R4] E1 linear disasm(VA,0x30) / E2 resync by() walk; addr+bytes+mnemonic+op_str")
    d48 = e.disasm(VA, 0x30)
    p("E1 count = %d, bytes covered = %d" % (len(d48), sum(len(x[1]) // 2 for x in d48)))
    for j, (a, hx, mn, ops) in enumerate(d48):
        p("  E1[%2d] 0x%08X  %-14s %-7s %s" % (j, a, hx.upper(), mn, ops))
    walk = []
    cur = VA
    while cur < VA + 0x30:
        ins = by.get(cur)
        if ins is None:
            p("  !! 0x%08X not in by(), stop" % cur)
            break
        blob = e.rd(ins.address, ins.size)
        walk.append((ins.address, bytes(ins.bytes).hex().upper(),
                     ins.mnemonic, ins.op_str, bytes(ins.bytes) == blob))
        cur = ins.address + ins.size
    p("E2 count = %d, bytes covered = %d, end VA = 0x%08X"
      % (len(walk), sum(len(x[1]) // 2 for x in walk), cur))
    for j, (a, hx, mn, ops, okb) in enumerate(walk):
        p("  E2[%2d] 0x%08X  %-14s %-7s %-24s bytes_ok=%s" % (j, a, hx, mn, ops, okb))
    p("E1==E2 first %d (addr,mnem,op_str) : %s"
      % (min(len(d48), len(walk)),
         [(a, mn, ops) for a, _, mn, ops in d48[:len(walk)]] ==
         [(a, mn, ops) for a, _, mn, ops, _ in walk]))

    # --- R5: 前 8 条 + ±32B 窗口 CC/F1/F0 ---
    p("")
    p("[R5] first 8 instructions + ±32B window CC/F1/F0 byte positions")
    for j, (a, hx, mn, ops, _ok) in enumerate(walk[:8]):
        p("  %d. 0x%08X  %-14s %-7s %s" % (j + 1, a, hx, mn, ops))
    win_lo, win_hi = VA - 32, VA + 32
    win = e.rd(win_lo, win_hi - win_lo)
    p("rd(0x%08X,64) = %s" % (win_lo, win.hex(" ").upper()))
    for byte in (0xCC, 0xF1, 0xF0):
        pos = [win_lo + i for i, v in enumerate(win) if v == byte]
        p("  0x%02X positions = %s" % (byte, [hex(x) for x in pos] or "NONE"))
    starts = []
    c = win_lo
    while c < win_hi:
        ins = by.get(c)
        if ins is None:
            c += 1
            continue
        starts.append((ins.address, bytes(ins.bytes)[0]))
        c = ins.address + ins.size
    p("  ±32 window instruction starts with opcode0 in CC/F1/F0 = %s"
      % ([(hex(a), "%02X" % op0) for a, op0 in starts if op0 in (0xCC, 0xF1, 0xF0)] or "NONE"))

    # --- R6: in by() + 前序上下文 ---
    p("")
    p("[R6] in by() + preceding sequential context")
    p("VA in by() = " + str(VA in by))
    ins0 = by.get(VA)
    p("by()[VA] = size=%d bytes=%s %s %s"
      % (ins0.size, bytes(ins0.bytes).hex().upper(), ins0.mnemonic, ins0.op_str)
      if ins0 else "NONE")
    ctx = []
    c = VA - 0x20
    while c < VA:
        ins = by.get(c)
        if ins is None:
            c += 1
            continue
        ctx.append((ins.address, bytes(ins.bytes).hex().upper(), ins.mnemonic, ins.op_str))
        c = ins.address + ins.size
    for a, hx, mn, ops in ctx:
        p("  ctx 0x%08X  %-14s %-7s %s" % (a, hx, mn, ops))
    prev = by.get(ctx[-1][0])
    p("  prev insn end = 0x%08X ; adjacent to VA = %s"
      % (prev.address + prev.size, prev.address + prev.size == VA))

    # --- R7: 直接分支落点普查（局部 + 全 .text）；含 debug 计数 ---
    p("")
    p("[R7] direct-branch targets to VA (local window + full .text)")
    lo, hi = 0x7CF000, 0x7D1000
    local_refs, all_refs = [], []
    scanned_local = 0
    jcc_local = 0
    imm_local = 0
    for ins in e.stream:
        mn = ins.mnemonic
        if lo <= ins.address < hi:
            scanned_local += 1
            if mn.startswith("j") or mn == "call":
                jcc_local += 1
                try:
                    if ins.operands and ins.operands[0].type == 2:
                        imm_local += 1
                except Exception:
                    pass
        if not (mn.startswith("j") or mn == "call"):
            continue
        try:
            if not ins.operands or ins.operands[0].type != 2:
                continue
            t = ins.operands[0].imm
        except Exception:
            continue
        if t == VA:
            all_refs.append((ins.address, mn, ins.op_str))
            if lo <= ins.address < hi:
                local_refs.append((ins.address, mn, ins.op_str))
    p("local window [0x%08X,0x%08X): scanned=%d insns, j/call=%d, imm-typed=%d"
      % (lo, hi, scanned_local, jcc_local, imm_local))
    p("local direct refs to VA = %d %s" % (len(local_refs), repr(local_refs)))
    p("full .text (%d insns) direct refs to VA = %d %s" % (nins, len(all_refs), repr(all_refs)))
    p("indirect branch / jump-table landing: NOT EXAMINED (未验)")
    p("rd(0x7CFC9B,4) = " + e.rd(0x7CFC9B, 4).hex(" ").upper())

    # --- R8: 探针 EXIT / 输出一致性 ---
    p("")
    p("[R8] note: reviewer reruns _w9_q1.py separately; this probe is independent.")
    p("PROBE DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        p("!! EXCEPTION !!")
        p(traceback.format_exc())
    finally:
        Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
        print("wrote " + OUT, flush=True)
