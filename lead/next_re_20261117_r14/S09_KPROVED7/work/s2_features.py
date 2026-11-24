"""S09-KPROVED7 step 2: ③b feature detection over each candidate's CFG extent.
Detects jump tables, loops with NON-STACK writes, error sentinels/returns,
multi-guard chains. M7: loop 'write' must be non-stack mem write (or falsifiable
return code); stack-only accumulator / register-only advance does NOT count."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED7\work')
import s09lib as L
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_GRP_JUMP
import capstone.x86 as cx

BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = json.load(open(OUT + r'\pool.json', encoding='utf-8'))

JCCS = {'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jecxz','jcxz'}

def is_stack_mem(op):
    if op.type != X86_OP_MEM: return False
    m = op.mem
    return m.base in (cx.X86_REG_ESP, cx.X86_REG_EBP) and m.index == 0

for rec in pool:
    e = int(rec['entry'], 16)
    lo, hi, ordered, byaddr = L.cfg_extent(e, cap=8000)
    rset = set(byaddr)
    jt = []; loops = []; sentinel = []; distinct_jcc_t = set(); calls = set(); writes = []
    disasm = []
    for ins in sorted(ordered, key=lambda i: i.address):
        a = ins.address; rel = a - e; mn = ins.mnemonic; ops = ins.operands
        txt = ('%s %s' % (mn, ins.op_str)).strip()
        disasm.append('%04X: %-08s %s' % (rel, ins.bytes.hex(), txt))
        if mn == 'jmp' and ops and ops[0].type == X86_OP_MEM:
            m = ops[0].mem
            if m.index != 0 and m.scale in (2,4,8):
                jt.append((rel, txt))
        if mn in ('cmp','test'):
            for op in ops:
                if op.type == X86_OP_IMM and (int(op.imm) & 0xffffffff) == 0xffffffff:
                    sentinel.append((rel, txt))
        if mn in JCCS and ops and ops[0].type == X86_OP_IMM:
            t = int(ops[0].imm) & 0xffffffff
            if t in rset: distinct_jcc_t.add(t - e)
        if mn == 'call' and ops and ops[0].type == X86_OP_IMM:
            calls.add(int(ops[0].imm) & 0xffffffff)
        if ops and ops[0].type == X86_OP_MEM and mn in ('mov','add','sub','inc','dec','and','or','xor','movzx','movsx'):
            if not is_stack_mem(ops[0]):
                writes.append((rel, txt))
        if mn == 'jmp' or mn in JCCS:
            if ops and ops[0].type == X86_OP_IMM:
                t = int(ops[0].imm) & 0xffffffff
                if lo <= t <= a:
                    loops.append((rel, t - e, txt))
    rec['_det'] = dict(jt=jt, loops=loops, sentinel=sentinel,
        jcc_distinct=len(distinct_jcc_t), calls_distinct=len(calls),
        writes=writes, nwrites=len(writes), size=hi-lo, nins=len(ordered))
    rec['_disasm'] = disasm

json.dump(pool, open(OUT + r'\features.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('%-10s %-24s %4s %4s %3s %3s %3s %3s %3s  %s' % ('entry','name','size','ins','jt','lp','sen','jT','call','W'))
for rec in sorted(pool, key=lambda r: (-(len(r['_det']['jt'])*4 + len(r['_det']['loops'])*3 + (2 if r['_det']['sentinel'] else 0) + (1 if r['_det']['jcc_distinct']>=3 else 0)), r['entry'])):
    d = rec['_det']
    print('%-10s %-24s %4d %4d %3d %3d %3d %3d %3d  %d' % (
        rec['entry'], rec['name'][:24], d['size'], d['nins'], len(d['jt']), len(d['loops']),
        len(d['sentinel']), d['jcc_distinct'], d['calls_distinct'], d['nwrites']))
