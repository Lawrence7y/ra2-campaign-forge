"""C4 part 3: function starts = only addresses that follow a ret + nop padding.
This removes internal branch targets (verified: 0x4F8F79 is only reached by
`jmp 0x4f8f79` at 0x4F8F1F, i.e. it is a basic block, not a function).
"""
from base import BUF, IB, TEXT, SECTIONS, u32, s32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from collections import defaultdict, deque
import bisect, json

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
tlo, thi = TEXT["va"], TEXT["va"] + TEXT["vsize"]
insns = {i.address: (i.size, i.mnemonic, i.op_str)
         for i in md.disasm(bytes(BUF[tlo - IB: thi - IB]), tlo)}
print("decoded %d instructions" % len(insns))

starts = set()
for a, (sz, mn, op) in insns.items():
    if mn.startswith("ret"):
        n = a + sz
        while n in insns and insns[n][1] == "nop":
            n += insns[n][0]
        if n in insns:
            starts.add(n)
# the very first code byte is a function start too
starts.add(tlo)
starts = sorted(starts)
print("function starts: %d" % len(starts))

def owner(addr):
    i = bisect.bisect_right(starts, addr) - 1
    return starts[i] if i >= 0 else None

print("owner(0x4F8F82) = %08X" % owner(0x004F8F82))
print("owner(0x4FC0B0) = %08X" % owner(0x004FC0B0))
print("owner(0x006922E0) = %08X" % owner(0x006922E0))
print("owner(0x6922F4)  = %08X" % owner(0x006922F4))

# ---- caller map at function granularity ----
callers = defaultdict(set)
sites = defaultdict(list)
for a, (sz, mn, op) in insns.items():
    if mn in ("call", "jmp") and op.startswith("0x"):
        try:
            t = int(op, 16)
        except ValueError:
            continue
        if tlo <= t < thi:
            cf, tf = owner(a), owner(t)
            if cf and tf and cf != tf:
                callers[tf].add(cf)
                sites[tf].append((a, mn))
print("functions with >=1 caller: %d" % len(callers))

ptr_refs = defaultdict(list)
for s in SECTIONS:
    lo, hi = s["va"], s["va"] + s["rawsize"]
    for va in range(lo, hi - 3):
        v = u32(va)
        if tlo <= v < thi:
            ptr_refs[owner(v)].append("%s:%08X" % (s["name"], va))

TARGET = 0x004FC0B0
print()
print("=== direct callers of 0x%08X ===" % TARGET)
print("   sites:", [(("%08X" % a), mn) for a, mn in sites.get(TARGET, [])])
print("   caller funcs:", ["%08X" % c for c in callers.get(TARGET, ())])
print("   pointer slots:", ptr_refs.get(TARGET, []))

START = owner(0x004F8F82)
print()
print("=== BFS upward from 0x%08X (encloses the only call to 0x4FC0B0) ===" % START)
seen = {START: None}
depth = {START: 0}
q = deque([START])
order = []
while q:
    f = q.popleft()
    order.append(f)
    if depth[f] >= 14:
        continue
    for c in sorted(callers.get(f, ())):
        if c not in seen:
            seen[c] = f
            depth[c] = depth[f] + 1
            q.append(c)
print("   reachable upward functions: %d" % len(seen))

roots = [f for f in seen if f != START and f not in callers and not ptr_refs.get(f)]
print("   root candidates (no caller, no pointer slot): %s" %
      ["%08X" % r for r in sorted(roots, key=lambda x: depth[x])])

def path(f):
    out = []
    while f is not None:
        out.append(f)
        f = seen[f]
    return out

print()
for r in sorted(roots, key=lambda x: depth[x])[:8]:
    p = path(r)
    print("  ROOT %08X depth=%d" % (r, depth[r]))
    print("    %s" % "  <-  ".join("%08X" % x for x in p))
    for i in range(len(p) - 1):
        callee, caller = p[i], p[i + 1]
        st = [x for x in sites.get(callee, []) if owner(x[0]) == caller]
        print("       %08X --%s@%08X--> %08X" %
              (caller, st[0][1] if st else "?", st[0][0] if st else 0, callee))

print()
print("=== full upward closure (for audit) ===")
for f in sorted(seen, key=lambda x: depth[x]):
    print("  depth %-2d %08X  callers=%d ptr=%d" %
          (depth[f], f, len(callers.get(f, ())), len(ptr_refs.get(f, []))))

json.dump({"start": "%08X" % START,
           "roots": ["%08X" % r for r in roots],
           "closure": {("%08X" % k): {"depth": v, "parent": ("%08X" % seen[k]) if seen[k] else None}
                       for k, v in seen.items()}},
          open("c4_closure.json", "w"), indent=1)
print()
print("wrote c4_closure.json")
