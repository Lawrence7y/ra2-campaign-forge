# -*- coding: utf-8 -*-
"""P01 v1 主取证脚本 —— 帧冻结出口 0x55D877 + [GameLogic+0x62C] 定谳材料。
只读 gamemd.exe（SHA 校验在 Engine 内强制）。全部输出落盘本目录。"""
import os
import sys
import pickle
import re
import bisect
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(BASE, "..")))
from ra2tool import Engine


def out(name):
    """把输出文件名约束在本目录内。"""
    p = os.path.normpath(os.path.join(BASE, name))
    if not p.startswith(BASE):
        raise ValueError("refuse: %s" % p)
    return p


eng = Engine()
print("coverage = %.2f%% / %d insns / resync=%d" % eng.coverage, flush=True)

tup = [(i.address, i.size, i.bytes.hex(), i.mnemonic, i.op_str) for i in eng.stream]
pickle.dump(tup, open(out("stream_cache.pkl"), "wb"))
idx = {t[0]: k for k, t in enumerate(tup)}


def line(t):
    return "%08X  %-20s %-7s %s" % (t[0], t[2], t[3], t[4])


def dump_win(f, lo, hi):
    for t in tup:
        if lo <= t[0] < hi:
            f.write(line(t) + "\n")


# ---------- 函数头集合（ret 扫描 + E8 目标，G-83 口径） ----------
starts = {0x55D360, 0x55E160}
for (va, sz, b, mn, ops) in tup:
    if mn.startswith("ret"):
        starts.add(va + sz)
    elif mn == "call" and ops.startswith("0x"):
        try:
            starts.add(int(ops, 16))
        except ValueError:
            pass
sstarts = sorted(starts)


def fstart(va):
    k = bisect.bisect_right(sstarts, va) - 1
    return sstarts[k] if k >= 0 else None


# ---------- 向后来源追踪（启发式，标注 [推导]） ----------
def provenance(hit_va, base):
    k = idx.get(hit_va)
    if k is None:
        return ("?", "no-idx")
    reg = base
    for j in range(k - 1, max(k - 48, -1), -1):
        va, sz, b, mn, ops = tup[j]
        if mn == "call":
            return ("UNCERTAIN", "call@%08X-clobbers" % va)
        if mn.startswith("ret") or mn == "jmp":
            return ("FUNC", "reached-%s@%08X" % (mn, va))
        m = re.match(r"^(\w+), (.+)$", ops) if mn in ("mov", "lea") else None
        if m and m.group(1) == reg:
            src = m.group(2)
            if "a8b230" in src:
                return ("GLOBAL230", "mov %s,[0xA8B230]@%08X" % (reg, va))
            if re.match(r"^\w+$", src):
                reg = src
                continue
            mm = re.match(r"^\[(\w+)[^\]]*\]$", src)
            if mm:
                return ("LOADMEM", "%s<=[%s]@%08X" % (reg, mm.group(1), va))
            return ("IMM", "src=%s@%08X" % (src, va))
    return ("FUNC", "window-exhausted")


def base_reg(op_str):
    m = re.search(r"\[(\w+)", op_str)
    return m.group(1) if m else None


# ---------- 基线对账 ----------
for name, va in (("0xA8ED84 Frame", 0xA8ED84), ("0xA8ED80 Focus", 0xA8ED80),
                 ("0xA8B230 pGL", 0xA8B230), ("0xA8B238 Mode", 0xA8B238)):
    hs = eng.disp_hits(va)
    ws = [h for h in hs if h[1] == "W"]
    print("%s refs=%d writes=%d %s" % (name, len(hs), len(ws), [hex(w[0]) for w in ws]), flush=True)
    if va in (0xA8B230, 0xA8B238):
        with open(out("C_write_%06X.txt" % va), "w", encoding="utf-8") as f:
            f.write("# disp_hits(0x%06X) n=%d  W=%d\n" % (va, len(hs), len(ws)))
            for (hva, rw, mn, ops) in hs:
                f.write("%08X %s %s %s\n" % (hva, rw, mn, ops))
            for (hva, rw, mn, ops) in ws:
                f.write("\n==== WRITE %08X +-context ====\n" % hva)
                dump_win(f, hva - 0x80, hva + 0x50)

# ---------- CFG: MainLogicFrame 出口与可达性 ----------
rets, succ = eng.func_rets(0x55D360, 0x55DEE0)
reach = eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
be = eng.loop_backedges(0x55D360, 0x55DEE0)
ret_vas = [r.address for r in rets]
print("MLF rets = %s" % [hex(x) for x in ret_vas], flush=True)
print("MLF rets reachable without INC-block = %s" %
      [hex(x) for x in ret_vas if x in reach], flush=True)
print("MLF backedges = %s" % be, flush=True)

# ---------- A: MainLogicFrame 全文 ----------
with open(out("A_mlf_body.txt"), "w", encoding="utf-8") as f:
    f.write("# MainLogicFrame 0x55D360..0x55DEE0  resync-stream slice\n")
    f.write("# rets=%s  reach_without_inc_ret=%s  backedges=%s\n" %
            ([hex(x) for x in ret_vas], [hex(x) for x in ret_vas if x in reach], be))
    dump_win(f, 0x55D360, 0x55DEE0)

# ---------- B: [reg+0x62C] 全家族 ----------
hits62c = eng.disp_hits_field(0x62C)
print("field 0x62C hits=%d rw=%s" % (len(hits62c), dict(Counter(h[1] for h in hits62c))), flush=True)
with open(out("B_field62c.txt"), "w", encoding="utf-8") as f:
    f.write("# disp_hits_field(0x62C) n=%d\n" % len(hits62c)
            + "\n")
    for (va, rw, mn, ops) in hits62c:
        fs = fstart(va)
        br = base_reg(ops)
        tag, note = provenance(va, br) if br else ("?", "no-base")
        f.write("\n==== %08X %s %s %s | fstart~%08X | prov=%s(%s)\n" %
                (va, rw, mn, ops, fs or 0, tag, note))
        k = idx[va]
        for j in range(max(0, k - 16), min(len(tup), k + 3)):
            f.write("  " + line(tup[j]) + "\n")

# ---------- E: 被调函数头 + 调用点交叉 ----------
def call_sites(target):
    out_sites = []
    for (va, sz, b, mn, ops) in tup:
        if mn in ("call", "jmp") and ops.startswith("0x"):
            try:
                if int(ops, 16) == target:
                    out_sites.append((va, mn))
            except ValueError:
                pass
    return out_sites


CALLEES = [0x5D4D50, 0x48D080, 0x53B560, 0x4F4480, 0x55E160]
with open(out("E_callees.txt"), "w", encoding="utf-8") as f:
    for va in CALLEES:
        cs = call_sites(va)
        print("calls->%08X: %d %s" % (va, len(cs), [hex(x) for x, _ in cs][:24]), flush=True)
        f.write("\n==== callee %08X  call/jmp sites(%d): %s ====\n" %
                (va, len(cs), [("%08X" % x) + ":" + m for x, m in cs]))
        dump_win(f, va, va + 0xC0)
    f.write("\n==== LogicUpdate 0x55E160 extended 0x400 ====\n")
    dump_win(f, 0x55E160, 0x55E160 + 0x400)

# ---------- S: 字符串面 ----------
def cstr(va, n=96):
    raw = eng.rd(va, n)
    z = raw.find(b"\0")
    if z < 0:
        z = n
    s = raw[:z]
    if len(s) >= 4 and all(32 <= c < 127 for c in s):
        return s.decode("ascii")
    return None


DATA = [(nm, sva, sva + vsz) for (nm, sva, vsz, rp, rsz) in eng.SEC]
print("sections:", [(nm, hex(a), hex(b)) for nm, a, b in DATA], flush=True)


def strings_in(lo, hi, acc):
    for (va, sz, b, mn, ops) in tup:
        if lo <= va < hi and ops.startswith("0x"):
            try:
                imm = int(ops, 16)
            except ValueError:
                continue
            for nm, a, bb in DATA:
                if nm != ".text" and a <= imm < bb:
                    s = cstr(imm)
                    if s:
                        acc.append((va, imm, s))
                    break


STR_WINDOWS = [("MainLogicFrame", 0x55D360, 0x55DEE0), ("LogicUpdate", 0x55E160, 0x55E560),
               ("pump5D4D50", 0x5D4D50, 0x5D5150), ("48D080", 0x48D080, 0x48D480),
               ("53B560", 0x53B560, 0x53B960), ("4F4480", 0x4F4480, 0x4F4880)]
with open(out("S_strings.txt"), "w", encoding="utf-8") as f:
    for nm, lo, hi in STR_WINDOWS:
        found = []
        strings_in(lo, hi, found)
        f.write("\n==== %s [%08X,%08X) strings=%d ====\n" % (nm, lo, hi, len(found)))
        for (va, imm, s) in found:
            f.write("%08X -> %08X \"%s\"\n" % (va, imm, s))
        print("strings %s: %d" % (nm, len(found)), flush=True)

# ---------- W: 主循环 caller ----------
print("callers of MainLogicFrame 0x55D360: %s" %
      [("%08X" % x) + ":" + m for x, m in call_sites(0x55D360)], flush=True)
print("DONE v1", flush=True)
