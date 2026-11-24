"""C4: FUN_004FC0B0 callers, and the shortest upward chain to a process entry.

Approach:
 1. find every direct call/jmp to 0x4FC0B0 in .text (byte level, E8/E9)
 2. also implicit references (dword slots) so "only 1 caller" is checked properly
 3. build a reverse call graph from ALL direct call/jmp sites in .text
 4. identify candidate process entries (window procs / WinMain / message pump)
 5. BFS upward from 0x4F8F82's enclosing function to those entries
"""
from base import BUF, IB, TEXT, u32, s32
from collections import deque, defaultdict

tlo = TEXT["va"]
thi = TEXT["va"] + TEXT["vsize"]

print("=== 1. direct call/jmp sites to 0x004FC0B0 ===")
TGT = 0x004FC0B0
sites = []
for va in range(tlo, thi - 5):
    i = va - IB
    if BUF[i] in (0xE8, 0xE9):
        if va + 5 + s32(va + 1) == TGT:
            sites.append((va, "call" if BUF[i] == 0xE8 else "jmp"))
print("  count=%d  %s" % (len(sites), [("%s@%08X" % (k, a)) for a, k in sites]))

print()
print("=== 2. dword slots holding 0x004FC0B0 (function pointer class) ===")
from base import SECTIONS
ptrs = []
for s in SECTIONS:
    for va in range(s["va"], s["va"] + s["rawsize"] - 3):
        if u32(va) == TGT:
            ptrs.append((s["name"], va))
print("  %s" % [("%s:%08X" % x) for x in ptrs])

print()
print("=== 3. build reverse call graph over .text (direct E8/E9 only) ===")
edges = []      # (src_site, dst)
for va in range(tlo, thi - 5):
    i = va - IB
    if BUF[i] in (0xE8, 0xE9):
        t = va + 5 + s32(va + 1)
        if tlo <= t < thi:
            edges.append((va, t))
print("  call/jmp edges within .text: %d" % len(edges))

# function-level: need function boundaries. Use a simple approach: the
# enclosing function of a call site is the nearest preceding alignment pad
# or a known entry. Instead build a site->target map and do BFS on SITES,
# treating a site's "owner" as the previous function start found by scanning.
# Robust alternative: BFS on code addresses directly, since we only need to
# show a chain of call instructions.
rev = defaultdict(list)     # dst -> list of (site)
for site, dst in edges:
    rev[dst].append(site)

def bfs_up(start_sites, goal_pred, maxdepth=12):
    """walk backwards: for address a, find call sites that directly call a
    (exact) or that call into the function containing a. Report chains."""
    seen = set()
    q = deque()
    for s in start_sites:
        q.append((s, [s]))
        seen.add(tuple([s]))
    results = []
    while q:
        addr, path = q.popleft()
        if len(path) > maxdepth:
            continue
        # who calls `addr`?
        for cs in rev.get(addr, []):
            if cs in path:
                continue
            newpath = path + [cs]
            if goal_pred(cs):
                results.append(newpath)
            q.append((cs, newpath))
    return results

print()
print("=== 4. find the function containing 0x4F8F82 ===")
cs = 0x004F8F82
print("  verify it really calls 0x4FC0B0: bytes=%s" %
      bytes(BUF[cs - IB: cs - IB + 5]).hex())
print("  decoded target = %08X" % (cs + 5 + s32(cs + 1)))

# walk back to find likely prologue
def find_func_start(site, limit=0x400):
    a = site
    while a > tlo and site - a < limit:
        # push ebp ; mov ebp,esp  or  sub esp,X
        if BUF[a - IB] == 0x55 and BUF[a + 1 - IB] == 0x8B and BUF[a + 2 - IB] == 0xEC:
            return a
        # ret immediately before a = previous function end
        if BUF[a - 1 - IB] == 0xC3 and BUF[a - IB] not in (0x00,):
            return a
        a -= 1
    return None

fs = find_func_start(cs)
print("  nearest preceding function-prologue candidate: %s" %
      ("%08X" % fs if fs else "not found"))
print("  bytes at that start: %s" % (bytes(BUF[fs - IB: fs - IB + 16]).hex() if fs else ""))

print()
print("=== 5. upward chains from 0x4F8F82 ===")
# goal: a site that is called by nothing, or is inside a known window-proc /
# WinMain / message pump. First try: chain to any site with no caller.
def no_caller(site):
    return site not in rev

chains = bfs_up([cs], no_caller, maxdepth=10)
print("  chains ending at an address with NO direct caller: %d" % len(chains))
for ch in sorted(chains, key=len)[:10]:
    print("    len=%d  %s" % (len(ch), " <- ".join("%08X" % x for x in ch)))

if not chains:
    print("  no chain terminates at an uncalled site within depth 10; showing depth-8 reach:")
    for depth in range(1, 9):
        pass
    # show all reachable call sites up to depth 6
    frontier = {cs}
    allpaths = []
    for d in range(6):
        nxt = set()
        for a in frontier:
            for p in rev.get(a, []):
                nxt.add(p)
                allpaths.append(p)
        frontier = nxt
    print("  reachable upward sites (depth<=5): %d" % len(allpaths))
    print("  %s" % sorted("%08X" % x for x in allpaths)[:40])
