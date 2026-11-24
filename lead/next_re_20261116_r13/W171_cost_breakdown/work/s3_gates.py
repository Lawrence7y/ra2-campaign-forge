"""S3: mechanical gate analysis by edge-removal reachability.

For a function F with entry E and a "target of interest" T (e.g. the `call 0x4CBBA0`
site), a conditional branch site B "can skip T" iff T is unreachable from E once the
edge B->taken_target is removed from the CFG.  Symmetrically "is required for T" iff T
is unreachable once the fallthrough edge B->B+size is removed.

This is the byte/CFG channel only: bodies are discovered by control flow from the entry,
never by function_atlas entry+size.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L
from capstone.x86 import X86_OP_IMM

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


def cfg_edges(entry, maxspan=0x4000):
    """Build (insns, edges, calls) by recursive descent, no branch pruning."""
    B = L.body(entry, maxspan=maxspan)
    edges = {}
    for a, ins in B.insns.items():
        nxt = a + ins.size
        succ = []
        mn = ins.mnemonic
        if mn == 'call':
            succ.append(('call_ret', nxt))
        elif mn == 'jmp':
            op = ins.operands[0] if ins.operands else None
            if op is not None and op.type == X86_OP_IMM:
                succ.append(('jmp', op.imm & 0xFFFFFFFF))
            else:
                for t in L._resolve_jmptable(ins):
                    succ.append(('jmp_tbl', t))
        elif mn.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
            succ.append(('jcc_t', ins.operands[0].imm & 0xFFFFFFFF))
            succ.append(('jcc_f', nxt))
        elif mn in ('ret', 'retf', 'iret', 'iretd', 'hlt'):
            pass
        else:
            succ.append(('seq', nxt))
        edges[a] = succ
    return B, edges


def reach(entry, edges, banned):
    """BFS from entry, skipping any edge (site, kind) in banned."""
    seen = {entry}
    work = [entry]
    while work:
        a = work.pop()
        for kind, t in edges.get(a, ()):
            if (a, kind) in banned:
                continue
            if t in edges and t not in seen:
                seen.add(t)
                work.append(t)
    return seen


def analyse(entry, targets, label, maxspan=0x4000):
    B, edges = cfg_edges(entry, maxspan)
    p()
    p('### %s  entry=%08X  cfg_insns=%d' % (label, entry, len(B.insns)))
    base = reach(entry, edges, set())
    for t in targets:
        p('  target %08X reachable-dflt: %s' % (t, t in base))
    rows = []
    for a in sorted(B.insns):
        ins = B.insns[a]
        if not (ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp'):
            continue
        if not (ins.operands and ins.operands[0].type == X86_OP_IMM):
            continue
        for t in targets:
            if t not in base:
                continue
            no_t = reach(entry, edges, {(a, 'jcc_t')})
            no_f = reach(entry, edges, {(a, 'jcc_f')})
            skips = t not in no_t
            required = t not in no_f
            if skips or required:
                rows.append((a, t, ins, skips, required))
    for a, t, ins, skips, required in rows:
        tag = []
        if skips:
            tag.append('SKIPS-TARGET')
        if required:
            tag.append('REQUIRED-FOR-TARGET')
        p('  %08X  %-16s %-40s %s' % (a, ins.mnemonic, ins.op_str, '+'.join(tag)))
        # backward context
        addrs = sorted(B.insns)
        i = addrs.index(a)
        for c in addrs[max(0, i - 7):i]:
            p('        ctx ' + L.fmt(B.insns[c]))
    return B, edges, rows


# ---------- 1. does every Drive-wrapper invocation reach the big Process? ----------
p('=' * 78)
p('PART 1  Drive wrapper 0x4B0500 -> big Process 0x4B2630 call sites')
p('=' * 78)
B1, E1 = cfg_edges(0x4B0500)
base1 = reach(0x4B0500, E1, set())
for s in (0x4B0647, 0x4B0A79):
    p('  call-site %08X reachable from entry: %s' % (s, s in base1))
rows = []
for a in sorted(B1.insns):
    ins = B1.insns[a]
    if ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp' and ins.operands and \
            ins.operands[0].type == X86_OP_IMM:
        for t in (0x4B0647, 0x4B0A79):
            no_t = reach(0x4B0500, E1, {(a, 'jcc_t')})
            no_f = reach(0x4B0500, E1, {(a, 'jcc_f')})
            if (t not in no_t) or (t not in no_f):
                rows.append((a, t, ins, t not in no_t, t not in no_f))
p()
p('  branches that gate the big-Process call (SKIPS = taking the jump bypasses it):')
for a, t, ins, skips, req in rows:
    p('    %08X -> %08X  %s   %s' % (a, t, L.fmt(ins),
                                     'SKIPS' if skips else '') + (' REQUIRED' if req else ''))

# ---------- 2. reachable-instruction counts for the two macro paths ----------
p()
p('  --- path A: gates at 0x4B0564/0x4B056D TAKEN (= no target / not moving) ---')
A = reach(0x4B0500, E1, {(0x4B0564, 'jcc_f'), (0x4B056D, 'jcc_f')})
p('      reachable insns = %d' % len(A))
p('      contains 0x4B2630 call site? %s' % any(s in A for s in (0x4B0647, 0x4B0A79)))
p('      contains 0x4D3920 chain? (via 4B2630 calls) n/a at this level')
p('  --- path B: gates NOT taken (= has target and is moving) ---')
Bset = reach(0x4B0500, E1, {(0x4B0564, 'jcc_t'), (0x4B056D, 'jcc_t')})
p('      reachable insns = %d' % len(Bset))
p('      contains 0x4B2630 call site 4B0647? %s  4B0A79? %s'
  % (0x4B0647 in Bset, 0x4B0A79 in Bset))

# ---------- 3. UpdatePathfinding gates ----------
p()
p('=' * 78)
p('PART 2  UpdatePathfinding 0x4D3920: which branches gate `call 0x4CBBA0` @0x4D3E4B')
p('=' * 78)
B2, E2, rows2 = analyse(0x4D3920, [0x4D3E4B], 'FootClass::UpdatePathfinding')

# ---------- 4. big Process: does it reach UpdatePathfinding, and how many sites? ----
p()
p('=' * 78)
p('PART 3  Drive big Process 0x4B2630 -> UpdatePathfinding 0x4D3920')
p('=' * 78)
B3, E3 = cfg_edges(0x4B2630, maxspan=0x9000)
base3 = reach(0x4B2630, E3, set())
sites = [a for a in base3 if a in B3.calls and B3.calls[a] == 0x4D3920]
p('  direct call sites of 0x4D3920 inside 0x4B2630: %s' % [hex(x) for x in sites])
rows3 = []
for a in sorted(B3.insns):
    ins = B3.insns[a]
    if ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp' and ins.operands and \
            ins.operands[0].type == X86_OP_IMM:
        for t in sites:
            no_t = reach(0x4B2630, E3, {(a, 'jcc_t')})
            no_f = reach(0x4B2630, E3, {(a, 'jcc_f')})
            if (t not in no_t) or (t not in no_f):
                rows3.append((a, t, ins, t not in no_t, t not in no_f))
p()
p('  branches gating those call sites:')
for a, t, ins, skips, req in rows3:
    p('    %08X -> %08X  %s  %s' % (a, t, L.fmt(ins), 'SKIPS' if skips else '') + (' REQUIRED' if req else ''))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S3_gates.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
