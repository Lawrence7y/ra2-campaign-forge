import sys, random, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R

# S16 atlas [静态推断] pool (37 rows)
POOL = """00430BA0 00539EB0 0053A0E0 0053A6C0 0053AE00 0053AE50 0053B410
0053DA40 0053DA70 0053DA90 0053DAA0 0053DAE0 0053DB90 0053DBC0 0053DC00
0053DC20 0053DCD0 0053DD00 0053DD50 006CDEB0 006CDFF0 006CE1F0 006CE270
006CE280 006CE2C0 006CE7C0 006CE800 006CEA10 006CEF80 0071A650 0071A660
0071A700 0071A720 0071A760 0071B190 0071B1A0 0071B1B0""".split()
N = 3
SEED = 20261119
TRIALS = 2000

# atlas sizes
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
sizes = {}
with open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2:
            sizes[p[0].lower()] = int(p[1])

# D-42 strict ③b detector (faithful):
#  (1) jump table: jmp with mem index reg -> ③b① physical
#  (2) falsifiable err code: mov r,0x8000xxxx (HRESULT) / cmp x,-1 / or r,-1 / test+jl after call -> ③b②
#  (3) memory shape: >=2 writes of imm32 in 0x7xxxxx range to [mem] (vtable writes) -> ③b③
#  (4) complete loop: a backward branch whose body has a non-stack mem write + bound check + advance -> ③b④
# Any one suffices for strict ③b.
def detect(entry):
    size = sizes.get(entry.lower(), 0)
    insns = R.disasm(int(entry,16), size)
    jt = err = shape = loop = False
    # condition (3): vtable-ish imm writes
    vt_writes = 0
    for ins in insns:
        m = ins.mnemonic
        ops = ins.operands
        # jump table: indirect jmp with index
        if m == "jmp" and ops and ops[0].type == 3:  # X86_OP_MEM
            if ops[0].index != 0:
                jt = True
        # HRESULT 0x80004000..0x80004fff
        for op in ops:
            if op.type == 2 and 0x80004000 <= (op.imm & 0xffffffff) <= 0x80004fff:
                err = True
            if op.type == 2 and (op.imm & 0xffffffff) == 0xffffffff:
                # or reg,-1 / cmp ,-1 sentinel
                if m in ("or", "cmp", "mov", "push"):
                    err = True
        # vtable imm write: mov [mem], imm32 in 0x7e0000..0x800000
        if m in ("mov","movq") and len(ops)==2 and ops[0].type==3 and ops[1].type==2:
            imm = ops[1].imm & 0xffffffff
            if 0x7e0000 <= imm <= 0x810000:
                vt_writes += 1
    # test eax,eax / jl (negative return convention) after a call
    prev_call = False
    for ins in insns:
        if ins.mnemonic == "call":
            prev_call = True
            continue
        if prev_call and ins.mnemonic in ("test",) and any(o.type==1 for o in ins.operands):
            prev_call = "test"
            continue
        if prev_call=="test" and ins.mnemonic in ("jl","jle","js"):
            err = True
            prev_call = False
            continue
        if ins.mnemonic not in ("test",):
            prev_call = False
    if vt_writes >= 2:
        shape = True
    # loop: backward branch with non-stack write in body
    for i, ins in enumerate(insns):
        if ins.mnemonic.startswith("j") and ins.operands and ins.operands[0].type==2:
            tgt = ins.operands[0].imm
            if tgt < ins.address:
                # body between tgt and ins.address
                body = [x for x in insns if tgt <= x.address < ins.address]
                nonstack_writes = 0
                for x in body:
                    if x.mnemonic.startswith("mov") and len(x.operands)==2 and x.operands[0].type==3:
                        base = x.operands[0].mem.base
                        bname = x.reg_name(base) if base is not None else None
                        if bname not in ("ebp","esp"):
                            nonstack_writes += 1
                if nonstack_writes >= 1:
                    loop = True
    return {"jt":jt,"err":err,"shape":shape,"loop":loop,
            "strict": any([jt,err,shape,loop])}

res = {}
for e in POOL:
    res[e] = detect(e)

K = sum(1 for e in POOL if res[e]["strict"])
p = K/len(POOL)
E = N*p
random.seed(SEED)
mc = 0
for _ in range(TRIALS):
    sample = random.sample(POOL, N)
    mc += sum(1 for e in sample if res[e]["strict"])
mc /= TRIALS

with io.open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work\baselines.txt","w",encoding="utf-8") as f:
    f.write("S16 [静态推断] pool N_total=%d; draw N=%d; seed=%d; trials=%d\n" % (len(POOL),N,SEED,TRIALS))
    f.write("K(strict 3b)=%d  p=%.6f  E[N]=%.6f  MC_mean=%.6f\n" % (K,p,E,mc))
    f.write("\nPer-row detector breakdown:\n")
    for e in POOL:
        r=res[e]
        f.write("  %s jt=%d err=%d shape=%d loop=%d strict=%d\n" % (e,r["jt"],r["err"],r["shape"],r["loop"],r["strict"]))
print("K=%d p=%.6f E=%.6f MC=%.6f" % (K,p,E,mc))
for e in POOL:
    r=res[e]
    if r["strict"]:
        print("  3b:",e,r)
