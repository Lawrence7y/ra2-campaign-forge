"""Caller / dispatch evidence: direct E8/E9 callers, indirect call sites with a given disp,
atexit registration probe, and destructor-vs-ctor classification for a function."""
import sys
import struct
from pe import (TEXT_LO, TEXT_HI, BY, ORDER, u32, u8, read, fmt, dis, win, find_imm32,
                in_text, IMAGEBASE, MDD)

ATEXIT = 0x7C978A


def direct_callers(target, limit=200):
    """Every .text E8/E9 whose rel32 target == target, verified via linear map."""
    out = []
    for a in ORDER:
        i = BY[a]
        if i.mnemonic not in ("call", "jmp"):
            continue
        op = i.op_str
        if not op.startswith("0x"):
            continue
        try:
            t = int(op, 16)
        except ValueError:
            continue
        if t == target:
            out.append(i)
    return out


def indirect_calls(disp, sib_regs=("eax", "ecx", "edx", "esi", "edi", "ebx"), want_disp=None):
    """call dword ptr [reg + disp] sites."""
    out = []
    for a in ORDER:
        i = BY[a]
        if i.mnemonic != "call":
            continue
        if not i.op_str.startswith("dword ptr ["):
            continue
        out.append(i)
    return out


def call_reg_disp_all():
    res = []
    for a in ORDER:
        i = BY[a]
        if i.mnemonic not in ("call", "jmp"):
            continue
        if "dword ptr [" not in i.op_str:
            continue
        res.append(i)
    return res


def atexit_pushes():
    """(site, pushed_value) for every `push imm32` immediately followed by call 0x7C978A."""
    res = []
    for a in ORDER:
        i = BY[a]
        if i.mnemonic != "call":
            continue
        if i.op_str != "0x%x" % ATEXIT:
            continue
        # walk back a few instructions for the push
        prev = [x for x in ORDER if x < a][-6:]
        for p in reversed(prev):
            j = BY[p]
            if j.mnemonic == "push" and j.op_str.startswith("0x"):
                try:
                    v = int(j.op_str, 16)
                except ValueError:
                    continue
                res.append((a, p, v))
                break
    return res


def classify(entry, cap=4000):
    """Rough ctor/dtor verdict from the body."""
    body = []
    a = entry
    bad = 0
    while a < TEXT_HI and len(body) < cap:
        i = BY.get(a)
        if i is None:
            bad += 1
            a += 1
            if bad >= 8:
                break
            continue
        bad = 0
        body.append(i)
        a += i.size
    calls = [i for i in body if i.mnemonic == "call"]
    news = [i for i in calls if i.op_str in ("0x7c8e17", "0x7c8e05")]
    dels = [i for i in calls if i.op_str in ("0x7c8b3d", "0x7c8b1f", "0x7c8a37")]
    vt_w = [i for i in body if i.mnemonic == "mov" and "dword ptr [" in i.op_str
            and i.op_str.split(",")[-1].strip().startswith("0x7")]
    return dict(body=body, calls=calls, news=news, dels=dels, vt_writes=vt_w,
                size=body[-1].address + body[-1].size - entry if body else 0)


if __name__ == "__main__":
    t = int(sys.argv[1], 16)
    print("direct callers of %08X:" % t)
    for i in direct_callers(t):
        print("   " + fmt(i))
    c = classify(t)
    print("body size=%d calls=%d operator_new=%d free=%d" % (
        c["size"], len(c["calls"]), len(c["news"]), len(c["dels"])))
    print("vt writes:", [fmt(i) for i in c["vt_writes"]])
