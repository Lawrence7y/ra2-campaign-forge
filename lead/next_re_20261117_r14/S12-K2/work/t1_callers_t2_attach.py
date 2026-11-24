"""T1/T2: caller contexts for 0x47C620; 0x43F180 around the two can-place call
sites; full 0x47E8A0 / 0x47EA90 / 0x5683C0 / 0x5687F0 dumps.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, disasm_range, fmt_insn, load_atlas, sweep_calls, EVID

b = Bin()
out_lines = []

def dump(addr, nbytes, title):
    out_lines.append("=" * 90)
    out_lines.append(title)
    out_lines.append("=" * 90)
    insns = disasm_range(b, addr, addr + nbytes, skipdata=True)
    for ins in insns:
        out_lines.append(fmt_insn(ins))

# all direct callers of 0x47C620 via byte-channel sweep
calls, jmps, stat = sweep_calls(b)
cs = sorted(calls.get(0x47C620, []))
out_lines.append("CALLERS of 0x47C620 (byte sweep, direct call rel32): count=%d" % len(cs))
for s in cs:
    # find containing atlas function
    rows,_ = load_atlas()
    cont = None
    for r in rows:
        if r["_va"] <= s < r["_va"] + r["_size"]:
            cont = r; break
    out_lines.append("  %08X  in fn %s size=%d" % (s, ("%08X"%cont["_va"]) if cont else "OUTSIDE_ATLAS", cont["_size"] if cont else 0))

# 0x43F180 region around can-place call sites and the 0x47C620 call(s)
# dump 0x43F180..0x43F260 (start) and 0x43F600..0x43F6E0 (second site) and any call 47C620
rows,_ = load_atlas()
f43 = next(r for r in rows if r["_va"] == 0x43F180)
out_lines.append("")
out_lines.append("0x43F180 size=%d" % f43["_size"])
# find all call rel32 to 0x47C620 within 0x43F180
insns43 = disasm_range(b, 0x43F180, 0x43F180 + f43["_size"], skipdata=True)
for ins in insns43:
    if ins.id and ins.mnemonic in ("call","jmp") and ins.op_str.lower().endswith("0x47c620"):
        out_lines.append("  0x43F180: %s at %08X" % (ins.mnemonic, ins.address))

# Print contexts around 0x43F218 and 0x43F678 and any 0x47C620 call site
def context(center, before=0x60, after=0x90, title=""):
    dump(center - before, before + after, title or ("context @ %08X" % center))

context(0x43F218, 0x60, 0x90, "T1 call site A: 0x43F218 (can-place #1) +/- ")
context(0x43F678, 0x60, 0x90, "T1 call site B: 0x43F678 (can-place #2) +/- ")
# find call to 0x47C620 in 0x43F180
for ins in insns43:
    if ins.id and ins.mnemonic == "call" and ins.op_str.lower().endswith("0x47c620"):
        context(ins.address, 0x50, 0x60, "T1 call to 0x47C620 inside 0x43F180 @ %08X" % ins.address)

# also for each other caller, small context showing ecx source
for s in cs:
    context(s, 0x30, 0x20, "caller context %08X" % s)

# full attach/detach workers
dump(0x47E8A0, 489, "T2 0x47E8A0 full (atlas size 489)")
dump(0x47EA90, 263, "T2 0x47EA90 full (atlas size 263)")

out = os.path.join(EVID, "t1_callers_and_t2_attach.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines) + "\n")
print("wrote", out, "lines", len(out_lines))
print("callers of 0x47C620:", [hex(x) for x in cs])
