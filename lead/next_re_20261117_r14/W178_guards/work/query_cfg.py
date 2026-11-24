"""Focused CFG probe for 0x6CD8CD inside FUN_006CC390."""
import json
import os
import sys
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(__file__))
import analyze as a

ENTRY = 0x6CC390
SITE = 0x6CD8CD


def parse_t(op):
    return a.parse_target(op)


def main():
    b = a.Bin(a.EXE)
    instrs = a.disasm_range(b, ENTRY, ENTRY + 6835)
    by = {i.address: k for k, i in enumerate(instrs) if i.id}
    print(f"instrs={len(instrs)} site_idx={by.get(SITE)}")

    # Build CFG edges, mark direct/indirect transfers.
    edges = defaultdict(list)
    indirect = []
    for k, ins in enumerate(instrs):
        if not ins.id:
            continue
        nxt = instrs[k + 1].address if k + 1 < len(instrs) else None
        m = ins.mnemonic
        if m == "ret" or m.startswith("retf"):
            succ = []
        elif m == "jmp":
            t = parse_t(ins.op_str)
            if t is None:
                indirect.append((k, ins.address, a.insn_text(ins)))
                succ = []
            else:
                succ = [t]
        elif m.startswith("j"):
            t = parse_t(ins.op_str)
            succ = [x for x in (t, nxt) if x is not None]
        elif m == "call":
            succ = [nxt] if nxt is not None else []
        else:
            succ = [nxt] if nxt is not None else []
        edges[ins.address] = succ

    reachable = {instrs[0].address}
    q = deque([instrs[0].address])
    while q:
        x = q.popleft()
        for y in edges.get(x, []):
            if y not in reachable:
                reachable.add(y)
                q.append(y)
    print(f"reachable_addrs={len(reachable)} site_reachable={SITE in reachable}")

    # Locate statement block containing SITE: back up to previous ret/jmp/jcc target/fallthrough boundary.
    k = by[SITE]
    block_start_k = k
    while block_start_k > 0:
        prev = instrs[block_start_k - 1]
        if not prev.id:
            break
        pm = prev.mnemonic
        if pm == "ret" or pm.startswith("retf") or pm == "jmp" or pm.startswith("j"):
            break
        # also stop if the current instruction is a direct jump/call target
        if any(ins.address == instrs[block_start_k].address for ins in instrs if ins.id and ins.mnemonic in {"call", "jmp"} and parse_t(ins.op_str) == instrs[block_start_k].address):
            break
        block_start_k -= 1
    block_start = instrs[block_start_k].address
    print(f"block_start={block_start:#x} block_start_reachable={block_start in reachable}")

    # Find all predecessors of any address in the site's straight-line block.
    block_addrs = {i.address for i in instrs[block_start_k:k + 1] if i.id}
    preds = []
    for x, succs in edges.items():
        for y in succs:
            if y in block_addrs:
                preds.append((x, y))
    print("predecessors_of_block", [(f"{x:#x}", f"{y:#x}", x in reachable) for x, y in preds])

    # Show branches whose source or target is near the block/site.
    print("NEARBY_CONTROL_FLOW")
    for x, ins in enumerate(instrs):
        if not ins.id:
            continue
        if not (0x6CD780 <= ins.address <= SITE + 0x40):
            continue
        if ins.mnemonic == "jmp" or ins.mnemonic.startswith("j") or ins.mnemonic == "call" or ins.mnemonic.startswith("ret"):
            mark = "*" if ins.address in reachable else " "
            print(f" {mark} {a.insn_text(ins)}")

    print("INDIRECT_JMPS_IN_FUNCTION")
    for k2, addr, text in indirect:
        mark = "*" if addr in reachable else " "
        print(f" {mark} {text}")

    # Last reachable instruction before the target block in linear order, and first unreachable run.
    first_unreach = None
    last_reach_before = None
    for ins in instrs[: by[SITE] + 1]:
        if not ins.id:
            continue
        if ins.address not in reachable and first_unreach is None:
            first_unreach = ins.address
        if ins.address in reachable:
            last_reach_before = ins.address
    print(f"first_unreachable_in_linear_order={first_unreach and hex(first_unreach)}")
    print(f"last_reachable_before_site={last_reach_before and hex(last_reach_before)}")


if __name__ == "__main__":
    main()
