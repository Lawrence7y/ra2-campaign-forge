"""Final: identify death->Destroy/Uninit/delist entry; confirm armor field +0x9C owner."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone
from safe_dis import real_insns

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"
out=[]
def p(s=""): out.append(str(s))

p("=== 1. All direct calls in ReceiveDamage whose target is in 0x70xxxx (death family) ===")
rd=R.disasm_fn(0x701900)
for insn in rd:
    t=R.call_target(insn)
    if t is not None and 0x700000<=t<0x712000:
        nm=R.KNOWN if hasattr(R,'KNOWN') else {}
        p(f"   {R.fmt_insn(insn)} -> 0x{t:08X} fn=0x{R.fn_at(t):08X}")

p("\n=== 2. death block 0x7027D0..0x702830 (call 0x708080 context + exit) ===")
p(R.dump_insns(R.disasm(0x7027D0,0x70)))

p("\n=== 3. 0x708080 deeper: scan its direct calls ===")
f=R.disasm(0x708080, 0x800)
for insn in f:
    t=R.call_target(insn)
    if t is not None:
        p(f"   {R.fmt_insn(insn)} -> 0x{t:08X} fn=0x{R.fn_at(t):08X}")

p("\n=== 4. Does ReceiveDamage call 0x70D4A0 (ClearRefs)? ===")
hits=[insn.address for insn in rd if R.call_target(insn)==0x70D4A0]
p("   hits in ReceiveDamage: "+str([hex(x) for x in hits]))

p("\n=== 5. Armor field TechnoTypeClass+0x9C: loader anchor (grep ini_fields) ===")
import re
for line in open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ini_fields.tsv",encoding="utf-8"):
    if "+0x9C" in line or "\t9C\t" in line or "\t0x9C\t" in line:
        p("   "+line.rstrip())

p("\n=== 6. Key death-family known symbols from atlas (what is 0x708080 / 0x70D4A0 / 0x5B3A00) ===")
for va in (0x708080,0x70D4A0,0x5B3A00,0x70D690,0x702D11,0x6FC0B0):
    fa=R.fn_at(va)
    p(f"   0x{va:08X}: atlas_fn=0x{fa:08X} size={R.ATLAS_FN.get(fa,{}).get('size')}")

txt="\n".join(out)
open(EV+r"\trace_death2.txt","w",encoding="utf-8").write(txt)
print(txt)
