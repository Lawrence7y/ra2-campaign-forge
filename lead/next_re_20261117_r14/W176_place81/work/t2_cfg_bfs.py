"""W176 Task 2: rigorous intra-function CFG / BFS for 0x43F180.

Tracks whether 0x43F241 (xor ebp,ebp) has executed on any path to 0x43F658.
Answers: (a) can 0x43F658 be reached with ebp == mode parameter? (b) are mode 1 / mode 3
reachable-instruction sets identical? (c) exact reachable sets of can-place sites,
0x47C620 call, hook call 0x5683C0, and all rets.

Uses capstone skipdata=True; linear decode of the whole atlas interval.
No function_atlas.tsv entry+size for the CFG itself (only used to know where to stop).
"""
import capstone, pefile, os, collections, json

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
START, END = 0x43F180, 0x43FB0C

pe = pefile.PE(EXE, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase

def read(va, n):
    for s in pe.sections:
        v = ib + s.VirtualAddress
        if v <= va and va+n <= v + s.SizeOfRawData:
            off = s.PointerToRawData + (va-v)
            return pe.__data__[off:off+n]
    raise ValueError(hex(va))

m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
m.detail = True
m.skipdata = True
insns = {}
for ins in m.disasm(read(START, END-START), START):
    if ins.id == 0 or ins.address >= END:
        continue
    insns[ins.address] = ins

# Build successor map (intra-function)
def succ(ins):
    s = []
    if ins.mnemonic.startswith('ret'):
        return []
    if ins.mnemonic == 'jmp':
        op = ins.op_str
        if op.startswith('0x'):
            t = int(op, 16)
            if t in insns:
                s.append(t)
        # indirect jmp (jump table) handled specially below
        return s
    # conditional jumps: fallthrough + target
    if ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp':
        if ins.op_str.startswith('0x'):
            t = int(ins.op_str, 16)
            if t in insns:
                s.append(t)
        s.append(ins.address + ins.size)
        return s
    # call: assume returns to next insn (we are only doing intra-function CFG)
    s.append(ins.address + ins.size)
    return s

# jump table at 0x43FB0C: 4 dwords
jt = [int.from_bytes(read(0x43FB0C+4*i,4),'little') for i in range(4)]
print('jump table', [hex(x) for x in jt])

def bfs(mode):
    # start at dispatch target
    entry = jt[mode]
    seen_ebp0 = set()   # (addr, xor_done)
    seen_ebp1 = set()
    q = collections.deque([(entry, False)])
    order = []
    while q:
        addr, xor_done = q.popleft()
        key = (addr, xor_done)
        seen = seen_ebp0 if not xor_done else seen_ebp1
        if key in seen:
            continue
        seen.add(key)
        order.append((addr, xor_done))
        ins = insns.get(addr)
        if ins is None:
            continue
        if addr == START+0xC1:  # 0x43F241 xor ebp,ebp
            xor_done = True
        # special: 0x43F1C3 jmp [ebp*4+0x43FB0C] -> already dispatched; if reached again, use mode
        if addr == 0x43F1C3:
            for t in [entry]:
                q.append((t, xor_done))
            continue
        for t in succ(ins):
            q.append((t, xor_done))
    return order, seen_ebp0, seen_ebp1

for mode in range(4):
    order, s0, s1 = bfs(mode)
    addrs = {a for a,_ in order}
    targets = [0x43F218,0x43F2AE,0x43F504,0x43F5D8,0x43F5E0,0x43F658,0x43F678,0x43F686,0x43F691]
    print('MODE',mode,'entry',hex(jt[mode]),'reachable insns',len(addrs))
    print('  targets:', {hex(t):(t in addrs) for t in targets})
    at658 = [ (hex(a),xd) for a,xd in order if a==0x43F658 ]
    print('  0x43F658 states (addr,xor_done):', at658)
    rets = [hex(a) for a in sorted(addrs) if insns[a].mnemonic.startswith('ret')]
    print('  rets:', rets)
    if mode in (1,3):
        with open(os.path.join(OUT,'T2_CFG_mode%d.txt'%mode),'w',encoding='utf-8') as f:
            f.write('MODE %d entry %08X reachable=%d\n'%(mode,jt[mode],len(addrs)))
            for a,xd in order:
                ins=insns[a]
                f.write('  %08X xor_done=%d %-9s %s\n'%(a,xd,ins.mnemonic,ins.op_str))
