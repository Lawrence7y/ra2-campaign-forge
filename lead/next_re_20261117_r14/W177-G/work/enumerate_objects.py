#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""枚举 AbstractClass::Array 全部对象：RTTI、type 短名、cell、owner。只读。"""
import sys, os, json, time
import w177_core as W
import wb_probe as P
import dsnap as D

EVID = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "EVIDENCE")

def s32(u):
    if u is None: return None
    u &= 0xFFFFFFFF
    return u - 0x100000000 if u & 0x80000000 else u

def main():
    pid = W.pid_of()
    m = W.Mem(pid)
    ph = P.player_house(m)
    items = m.u32(P.A_ABSTRACT_ITEMS)
    count = m.u32(P.A_ABSTRACT)
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": pid,
           "frame": m.u32(W.A_FRAME), "playerHouse": hex(ph) if ph else None,
           "items": items, "count": count, "objects": []}
    if items and 0 < count < 20000:
        for i in range(count):
            p = m.u32(items + 4*i)
            if not p or (p & 3): continue
            vptr = m.u32(p)
            name, _ = D.rtti_name(m, p)
            tpp = m.u32(p + 0x520)
            tp = tpp if tpp else None
            tname = P.ascii_at(m, tp+0x24, 12) if tp else ""
            locx = s32(m.u32(p + 0x9C)); locy = s32(m.u32(p + 0xA0))
            cx = (locx >> 8) if locx is not None else None
            cy = (locy >> 8) if locy is not None else None
            owner = m.u32(p + 0x21C)
            out["objects"].append({
                "i": i, "this": hex(p), "vptr": hex(vptr) if vptr else None,
                "rtti": name, "type": tname, "cell": [cx,cy] if cx is not None else None,
                "owner": hex(owner) if owner else None, "is_player": (owner==ph),
                "o1_81": m.u8(p+0x81), "o2_74": m.u8(p+0x74),
            })
    path = os.path.join(EVID, "objects_" + str(out["frame"]) + ".jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({k:v for k,v in out.items() if k!="objects"}, ensure_ascii=False)+"\n")
        for o in out["objects"]:
            f.write(json.dumps(o, ensure_ascii=False)+"\n")
    print("frame=%s count=%s objects=%d -> %s" % (out["frame"], count, len(out["objects"]), path))
    from collections import Counter
    print("RTTI:", Counter(o["rtti"] for o in out["objects"]).most_common())
    print("player objs:", Counter((o["rtti"],o["type"]) for o in out["objects"] if o["is_player"]).most_common(30))
    print("MCV candidates:", [o for o in out["objects"] if o["type"] and "MCV" in o["type"].upper()])
    return 0

if __name__ == "__main__":
    sys.exit(main())
