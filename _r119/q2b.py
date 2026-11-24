import sys, json, string
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
TI = 0x7f9594
PR = set(string.printable[:94].encode())   # 0x20..0x7e + tabs etc; we require 0x20<=c<=0x7e strictly below

def is_pr(c): return 0x20 <= c <= 0x7e

def maximal_strings(lo, hi, name):
    """NUL-terminated printable-ASCII runs whose START is >= lo and END (NUL) <= hi"""
    res = []
    o0, o1 = PE_.va2off(lo), PE_.va2off(hi)
    for p in range(o0, o1):
        if is_pr(BUF[p]) and (p == 0 or not is_pr(BUF[p-1])):
            e = BUF.find(b"\0", p, o1)
            if e > 0 and all(is_pr(c) for c in BUF[p:e]):
                res.append({"va": hex(PE_.off2va(p)), "len": e-p, "text": BUF[p:e].decode("latin1")})
    return res

out = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json"))
for va_s in ("0x817bb0", "0x817bc0", "0x819088"):
    va = int(va_s, 16)
    rec = out["q2"][va_s]
    rec["strings_strict"] = {
      "before_va-0x20..va (start and NUL both inside)": maximal_strings(va-0x20, va, "before"),
      "after_va+0x20..va+0x20+0x20? (card: 'after 0x20') = va..va+0x20 window": maximal_strings(va, va+0x20, "after_from_addr"),
      "after_va+0x10..va+0x30": maximal_strings(va+0x10, va+0x30, "after_from_plus10"),
      "before_va..va+0x20(window 0x20 bytes)": maximal_strings(va, va+0x20, "w"),
    }
    # also: any string overlapping the window (start may be before lo)
    rec["strings_overlapping"] = {
      "before_32_back": maximal_strings(va-0x40, va, "overlap_before"),
      "after_32_fwd": maximal_strings(va, va+0x40, "overlap_after"),
    }
json.dump(out, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json","w"), indent=1)
for k, rec in out["q2"].items():
    print("====", k)
    print("  strict:", json.dumps(rec["strings_strict"], ensure_ascii=False))
