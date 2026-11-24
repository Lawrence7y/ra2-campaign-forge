"""s10: boundary + reachability spot checks.

1. entry of the function that contains the 35-call chain: walk back from
   0x67DF0F to the first `ret` followed by padding.
2. does that entry (or any address in the chain function) get called by E8?
3. do any of the 35 slot VAs appear inside a vtable region / .rdata at all?
"""
import capstone

import pe

SLOTS = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
         "00680070", "006800F0", "00680170", "006801F0", "00680270",
         "006802F0", "00680370", "006803F0", "00680470", "006804F0",
         "00680570", "006805F0", "00680670", "006806F0", "00680770",
         "006807F0", "00680870", "006808F0", "00680970", "006809F0",
         "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
         "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0"]


def backward_entry(p, site, limit=0x2000):
    t = p.text()
    lo = max(t["vstart"], site - limit)
    win = p.raw(lo, site - lo)
    # find the LAST ret/ret-n whose successor bytes are padding
    for i in range(len(win) - 1, -1, -1):
        if win[i] == 0xC3:
            j = i + 1
            while j < len(win) and win[j] in (0x90, 0xCC):
                j += 1
            if j < len(win):
                return lo + j, lo + i
        if win[i] == 0xC2:
            j = i + 3
            while j < len(win) and win[j] in (0x90, 0xCC):
                j += 1
            if j < len(win):
                return lo + j, lo + i
    return None, None


def e8_callers(p, target):
    t = p.text()
    start = t["vstart"]
    data = p.raw(start, t["vsz"])
    out, i = [], 0
    while True:
        i = data.find(b"\xE8", i)
        if i < 0 or i + 5 > len(data):
            break
        rel = int.from_bytes(data[i + 1:i + 5], "little", signed=True)
        if start + i + 5 + rel == target:
            out.append(start + i)
        i += 1
    return out


def rdata_hits(p, targets):
    s = next(x for x in p.secs if x["name"] == ".rdata")
    data = p.raw(s["vstart"], s["rsz"])
    out = []
    for tt in targets:
        n = tt.to_bytes(4, "little")
        i = 0
        while True:
            i = data.find(n, i)
            if i < 0:
                break
            out.append((tt, s["vstart"] + i))
            i += 1
    return out


def main():
    p = pe.open_pe()
    ent, ret = backward_entry(p, 0x0067DF0F)
    print(f"walk back from 0x0067DF0F: nearest ret at 0x{ret:08X}, "
          f"candidate next entry 0x{ent:08X}")
    for cand in (0x0067D300, ent):
        c = e8_callers(p, cand)
        print(f"  E8 callers of 0x{cand:08X}: {len(c)} "
              + " ".join(f"0x{x:08X}" for x in c[:12]))
    print("\nslot VAs present in .rdata (vtable/literal):",
          rdata_hits(p, [int(s, 16) for s in SLOTS]) or "none")


if __name__ == "__main__":
    main()
