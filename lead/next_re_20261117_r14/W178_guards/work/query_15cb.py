"""CFG check for 0x6D15CB inside 0x6D14F0 (atlas-hole host)."""
import os
import sys
from collections import deque
sys.path.insert(0, os.path.dirname(__file__))
import analyze as a

ENTRY = 0x6D14F0
SITE = 0x6D15CB
END = 0x6D15E4

ins = a.disasm_range(a.Bin(a.EXE), ENTRY, END)
by = {i.address: k for k, i in enumerate(ins) if i.id}
print(f"idx={by.get(SITE)}")
for k, i in enumerate(ins):
    if not i.id:
        continue
    if 0x6D1570 <= i.address <= SITE + 8:
        print("  " + a.insn_text(i))

edges = {}
for k, i in enumerate(ins):
    if not i.id:
        continue
    nxt = ins[k + 1].address if k + 1 < len(ins) else None
    m = i.mnemonic
    if m == "ret" or m.startswith("retf"):
        succ = []
    elif m == "jmp":
        t = a.parse_target(i.op_str)
        succ = [t] if t is not None else []
    elif m.startswith("j"):
        t = a.parse_target(i.op_str)
        succ = [x for x in (t, nxt) if x is not None]
    else:
        succ = [nxt] if nxt is not None else []
    edges[i.address] = succ

seen = {ins[0].address}
q = deque([(ins[0].address,)])
path = None
while q:
    p = q.popleft()
    k = by.get(p[-1])
    if k is None:
        continue
    if p[-1] == SITE:
        path = p
        break
    for s in edges.get(p[-1], []):
        if s not in seen:
            seen.add(s)
            q.append(p + (s,))
print(f"reachable={path is not None} reachable_addrs={len(seen)}")
if path:
    for x in path:
        print("  PATH " + a.insn_text(ins[by[x]]))
else:
    first_unreach = next((i.address for i in ins if i.id and i.address not in seen), None)
    print(f"first_unreachable={first_unreach and hex(first_unreach)}")
