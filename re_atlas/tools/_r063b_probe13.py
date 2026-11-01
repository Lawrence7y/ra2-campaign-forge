# -*- coding: utf-8 -*-
"""R-063b probe13 (continuation): method self-calibration + RTTI naming.

1) Same D-sim applied to the 5 FROZEN 'constructed' rows (R-062): check
   D(stamp) vs D(lea) -- if equal, the textual pairing was sound and the frozen
   verdict stands; if not, register erratum candidate.
2) RTTI names (R-058 recipe vtable-4 -> COL -> COL+0xC -> TD -> TD+8) for
   0x7E1B04, 0x7EA5F4, 0x7E1B0C, 0x7E1AFC.
3) 0x5d7590 head decode context (why the sim could not start there).
4) image-wide imm32 0x7EA5F4 store census (context count).
Read-only.
"""
import sys, os, re, bisect, struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r062_upward_trace_contract as R62
import r061_witness_this_contract as G61

R62.load()
stream = R62._ctx["stream"]
idx = R62._ctx["idx"]
callers = R62._ctx["callers"]
pred = R62._ctx["pred"]
addrs = [s[0] for s in stream]
TLO, THI = R62._ctx["TLO"], G61._ctx["THI"]

CONSTR = [(0x77884f, 0x7787c0), (0x77890c, 0x7787c0), (0x778956, 0x7787c0),
          (0x779c3d, 0x779bb3), (0x779ebd, 0x779e33)]
OVR = {0x5cef6b: (4, "same-disp-reload"), 0x5cef78: (4, "same-disp-reload"),
       0x778b47: (0, "zero-args"), 0x5d7c86: (0, "zero-args"),
       0x76c692: (0, "zero-args"), 0x5cefb7: (0, "census-ret0")}


def breach(site):
    seen = {site}
    work = [site]
    while work:
        a = work.pop()
        for p in pred.get(a, ()):
            if p not in seen:
                seen.add(p)
                work.append(p)
    seen.discard(site)
    return seen


E8T = set(callers)


def sim(head):
    states = {head: (0,)}
    order = [head]
    steps = 0
    while order:
        steps += 1
        if steps > 600000:
            break
        a = order.pop()
        dset = states[a]
        k = idx.get(a)
        if k is None:
            continue
        va, sz, bs, mn, op, t = stream[k]
        nxt = []
        if mn in ("ret", "retf", "hlt", "ud2"):
            continue
        if mn == "jmp":
            if t is not None and TLO <= t < THI and t in idx:
                nxt.append(t)
            continue
        if mn == "call":
            if a in OVR:
                imm = OVR[a][0]
            else:
                j = bisect.bisect_left(addrs, t) if (t is not None and TLO <= t < THI) else None
                imm = None
                if j is not None and j < len(stream) and stream[j][0] == t:
                    for _ in range(200000):
                        if j >= len(stream):
                            break
                        a3, sz3, bs3, mn3, op3, t3 = stream[j]
                        if mn3 == "ret":
                            imm = int(op3, 16) if op3 else 0
                            break
                        if mn3 == "jmp" and t3 is not None and TLO <= t3 < THI:
                            j2 = bisect.bisect_left(addrs, t3)
                            if j2 < len(stream) and stream[j2][0] == t3:
                                j = j2
                                continue
                            break
                        if mn3 in ("retf", "hlt", "ud2", "x87-boundary"):
                            break
                        j += 1
                if imm is None:
                    continue
            nd = tuple(d - imm for d in dset)
        elif mn == "push":
            nd = tuple(d + 4 for d in dset)
        elif mn == "pop":
            nd = tuple(d - 4 for d in dset)
        elif mn in ("sub", "add") and re.match(r"^esp, ", op):
            try:
                v = int(op.split(", ")[1], 0)
            except Exception:
                continue
            nd = tuple(d + v if mn == "sub" else d - v for d in dset)
        elif mn.startswith("j"):
            nf = va + sz
            if nf in idx:
                nxt.append(nf)
            if t is not None and TLO <= t < THI and t in idx:
                nxt.append(t)
            nd = dset
        elif mn == "leave" or op.endswith(", esp"):
            continue
        else:
            nd = dset
        nf = va + sz
        succs = nxt if nxt else ([nf] if nf in idx else [])
        for s in succs:
            merged = set(states.get(s, ())) | set(nd)
            if len(merged) > 8:
                continue
            if s not in states or set(states[s]) != merged:
                states[s] = tuple(sorted(merged))
                if s not in order:
                    order.append(s)
            else:
                states[s] = tuple(sorted(merged))
    return states


print("== 1) frozen constructed rows: D-normalized check")
for row, stamp in CONSTR:
    heads = sorted(breach(row) & E8T)
    H = heads[0]
    states = sim(H)
    krow = idx[row] - 1
    _, _, _, _, lop, _t = stream[krow]
    m = re.search(r"esp \+ (0x[0-9a-f]+|\d+)", lop)
    s = m.group(1)
    disp = int(s, 16) if s.startswith("0x") else int(s)
    dr = sorted(set(states.get(row, ())))
    ds = sorted(set(states.get(stamp, ())))
    _, _, _, smn, sop, _ = stream[idx[stamp]]
    ms = re.search(r"esp \+ (0x[0-9a-f]+|\d+)\]", sop)
    sdisp = int(ms.group(1), 16) if ms.group(1).startswith("0x") else int(ms.group(1))
    print("row %06x head=%08x stamp=%08x(%s)" % (row, H, stamp, sop))
    print("   D(row)=%s D(stamp)=%s" % ([hex(x) for x in dr], [hex(x) for x in ds]))
    for Dr in dr:
        print("   W(row lea)=0x%x" % (disp - Dr))
    for Ds in ds:
        print("   P(stamp)  =0x%x  -> %s" % (sdisp - Ds,
              "MATCH" if (dr and (sdisp - Ds) == (disp - dr[0])) else "no-match-vs-first-D"))
    if not dr or not ds:
        print("   (unresolved sides)")

print("\n== 2) RTTI names")
def rtti_name(vt):
    try:
        col = struct.unpack("<I", R62.rb(vt - 4, 4))[0]
        if not col:
            return "COL=0"
        td = struct.unpack("<I", R62.rb(col + 0xC, 4))[0]
        if not td:
            return "TD=0"
        raw = R62.rb(td + 8, 64)
        z = raw.find(b"\x00")
        return raw[:z].decode("latin1") if z > 0 else raw[:16].hex()
    except Exception as e:
        return "ERR:%s" % e

for vt in (0x7E1B04, 0x7EA5F4, 0x7E1B0C, 0x7E1AFC, 0x7E1668):
    print("  vtable %08x -> %s" % (vt, rtti_name(vt)))

print("\n== 3) 0x5d7590 decode context")
k = bisect.bisect_left(addrs, 0x5d7588)
while k < len(stream) and stream[k][0] < 0x5d75a8:
    va, sz, bs, mn, op, t = stream[k]
    print("   %08x: %-14s %-6s %s" % (va, bs, mn, op))
    k += 1

print("\n== 4) imm32 0x7EA5F4 image-wide store census")
n = 0
for a, sz, bs, mn, op, t in stream:
    if "f4a57e00" in bs:
        n += 1
        if n <= 40:
            print("   %08x %s %s %s" % (a, bs, mn, op))
print("  total:", n)
print("done.")
