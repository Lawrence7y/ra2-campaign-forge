import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
def pr(c): return 0x20 <= c <= 0x7e
def strings_overlapping(lo_va, hi_va):
    """all maximal NUL-terminated printable-ASCII runs whose byte span intersects [lo,hi)"""
    o0, o1 = PE_.va2off(lo_va), PE_.va2off(hi_va)
    res = []
    for p in range(o0, o1):
        if pr(BUF[p]) and (p == 0 or not pr(BUF[p-1])):
            e = BUF.find(b"\0", p, o1 + 4096)
            if e > p and all(pr(c) for c in BUF[p:e]):
                sva, eva = PE_.off2va(p), PE_.off2va(e)
                if eva > lo_va and sva < hi_va:
                    res.append({"start_va": hex(sva), "nul_va": hex(eva), "len": e-p,
                                "text": BUF[p:e].decode("latin1"),
                                "relation": ("fully_inside" if sva >= lo_va and eva <= hi_va else
                                             "starts_before" if sva < lo_va else "ends_after")})
    return res
out = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json"))
for va_s in ("0x817bb0", "0x817bc0", "0x819088"):
    va = int(va_s, 16)
    out["q2"][va_s]["strings_overlap_before_0x20"] = strings_overlapping(va-0x20, va)
    out["q2"][va_s]["strings_overlap_after_0x20"] = strings_overlapping(va, va+0x20)
    out["q2"][va_s]["string_method"] = ("maximal NUL-terminated runs of bytes in 0x20..0x7e; a run is reported if its byte span "
        "intersects the window. 'before' window = [addr-0x20, addr), 'after' window = [addr, addr+0x20).")
json.dump(out, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json","w"), indent=1)
for k, v in out["q2"].items():
    if k == "explicit_verdicts": continue
    print("====", k)
    print("  before:", v["strings_overlap_before_0x20"])
    print("  after :", v["strings_overlap_after_0x20"])
