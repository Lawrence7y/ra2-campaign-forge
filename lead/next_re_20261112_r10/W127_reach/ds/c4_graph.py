"""C4 part 2: proper reverse call graph at FUNCTION granularity.

Function starts are recovered from the capstone decode stream:
 a function starts at an address that is
   (a) the instruction after a ret + nop padding, or
   (b) a direct call/jmp target that is not inside a known function.

Then BFS upward from the function containing 0x4F8F82 to any function that is
never called and never appears in a pointer slot == root candidate.
"""
from base import BUF, IB, TEXT, RDATA, DATA, SECTIONS, u32, s32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from collections import defaultdict, deque
import bisect, json

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
tlo, thi = TEXT["va"], TEXT["va"] + TEXT["vsize"]
code = bytes(BUF[tlo - IB: thi - IB])

insns = {}
for ins in md.disasm(code, tlo):
    insns[ins.address] = (ins.size, ins.mnemonic, ins.op_str)
print("decoded %d instructions" % len(insns))

ordered = sorted(insns)

# --- function starts ---
starts = set()
# after ret (+ nops)
for a, (sz, mn, op) in insns.items():
    if mn.startswith("ret"):
        n = a + sz
        while n in insns and insns[n][1] == "nop":
            n += insns[n][0]
        if n in insns:
            starts.add(n)
# direct call/jmp targets
call_edges = defaultdict(list)     # target_func -> [(site, caller_func)]
direct_targets = set()
for a, (sz, mn, op) in insns.items():
    if mn in ("call", "jmp") and op.startswith("0x"):
        try:
            t = int(op, 16)
        except ValueError:
            continue
        if tlo <= t < thi:
            direct_targets.add(t)
starts |= direct_targets
starts.discard(tlo)
starts_list = sorted(starts)
print("function start candidates: %d" % len(starts_list))

def owner(addr):
    i = bisect.bisect_right(starts_list, addr) - 1
    if i < 0:
        return None
    return starts_list[i]

# sanity: is 0x4F8F82's owner plausible?
own = owner(0x004F8F82)
print("owner(0x4F8F82) = %08X   (expect 0x4F8440)" % own)

# --- build caller map ---
callers = defaultdict(set)      # callee_func -> set(caller_func)
sites = defaultdict(list)       # callee_func -> list(site)
for a, (sz, mn, op) in insns.items():
    if mn in ("call", "jmp") and op.startswith("0x"):
        try:
            t = int(op, 16)
        except ValueError:
            continue
        if tlo <= t < thi:
            cf = owner(a)
            tf = owner(t)
            if cf and tf and cf != tf:
                callers[tf].add(cf)
                sites[tf].append(a)
print("functions with >=1 caller: %d" % len(callers))

# --- pointer-referenced functions (vtable slot etc) ---
ptr_refs = defaultdict(list)
for s in SECTIONS:
    lo, hi = s["va"], s["va"] + s["rawsize"]
    for va in range(lo, hi - 3):
        v = u32(va)
        if tlo <= v < thi:
            ptr_refs[v].append("%s:%08X" % (s["name"], va))
print("addresses appearing as dwords: %d" % len(ptr_refs))

# --- BFS upward from target ---
TARGET_FUNC = 0x004FC0B0
START_FUNC = owner(0x004F8F82)
print()
print("=== BFS upward from function %08X (contains 0x4F8F82) ===" % START_FUNC)
print("    looking for a function that is never called and never pointer-referenced")

seen = {START_FUNC: None}
q = deque([START_FUNC])
roots = []
depth = {START_FUNC: 0}
while q:
    f = q.popleft()
    if depth[f] > 0 and f not in callers and not ptr_refs.get(f):
        roots.append(f)
    if depth[f] >= 12:
        continue
    for c in callers.get(f, ()):
        if c not in seen:
            seen[c] = f
            depth[c] = depth[f] + 1
            q.append(c)

print("    reachable functions: %d" % len(seen))

def path_of(f):
    out = []
    while f is not None:
        out.append(f)
        f = seen[f]
    return out

print()
print("=== root candidates (never called, never in a pointer slot) ===")
for r in sorted(roots, key=lambda x: depth[x]):
    p = path_of(r)
    print("  root %08X  depth=%d" % (r, depth[r]))
    print("     chain: %s" % " -> ".join("%08X" % x for x in reversed(p)))
    # show the call instruction that realises each hop
    for i in range(len(p) - 1):
        callee = p[i]
        caller = p[i + 1]
        st = [x for x in sites[callee] if owner(x) == caller]
        print("        %08X calls %08X at %s" % (caller, callee, ["%08X" % x for x in st][:4]))

print()
print("=== shortest path to TARGET_FUNC 0x%08X ===" % TARGET_FUNC)
# Also show chain from each root down to the function calling 0x4FC0B0
tf_owner = owner(TARGET_FUNC)
print("  owner(0x4FC0B0) = %08X" % tf_owner)
print("  callers of 0x4FC0B0 (function level): %s" %
      ["%08X" % c for c in callers.get(tf_owner, ())])

json.dump({"start_func": START_FUNC, "roots": roots,
           "depth": {("%08X" % k): v for k, v in depth.items()}},
          open("c4_graph.json", "w"), indent=1)
