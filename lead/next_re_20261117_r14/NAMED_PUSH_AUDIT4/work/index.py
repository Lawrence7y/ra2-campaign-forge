"""One-pass index over .text: calls, imm32 data refs, function bounds.
Saved to index.json for per-row reuse.
"""
import sys, json, re, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

img = Img()
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
DATA_LO, DATA_HI = 0x7E038D, 0x840000

b = img.read(TEXT_LO, TEXT_HI - TEXT_LO)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = False

num = re.compile(r'0x[0-9a-f]+')
calls = []          # (addr, target) direct call
iatcalls = []       # (addr, iatva)
refs = {}           # value -> [addr]
insn_count = 0
for ins in md.disasm(b, TEXT_LO):
    insn_count += 1
    op = ins.op_str
    mn = ins.mnemonic
    if mn == 'call':
        if op.startswith('0x'):
            t = int(op, 16)
            calls.append((ins.address, t))
            continue
        m = re.search(r'\[(0x[0-9a-f]+)\]', op)
        if m:
            iatcalls.append((ins.address, int(m.group(1), 16)))
        continue
    for h in num.findall(op):
        v = int(h, 16)
        if DATA_LO <= v < DATA_HI:
            refs.setdefault(v, []).append(ins.address)

# function starts
starts = sorted({t for _, t in calls if TEXT_LO <= t < TEXT_HI})
import bisect
def func_start(addr):
    i = bisect.bisect_right(starts, addr) - 1
    return starts[i] if i >= 0 else None

out = dict(insn=insn_count, calls=calls, iat=iatcalls,
           refs={('%08X' % k): v for k, v in refs.items()}, starts=starts)
json.dump(out, open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json", 'w'))
print("insns", insn_count, "calls", len(calls), "iatcalls", len(iatcalls), "refs", len(refs), "starts", len(starts))
