"""
S06-K2 T1c: comprehensive CellClass field table.
Combines:
  (a) local this-tracked accesses (t1_fields.py) 
  (b) global GetCellAt-return read points (t1b_global_reads.py)
  (c) rep stosd zero-fill write ranges from ctor (explicitly parsed)
Write-coverage: a W at O width w covers all byte offsets [O, O+w).
Outputs EVIDENCE/t1_field_table.txt (full, untruncated) and a TSV summary.
"""
from pehelp import *
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_INVALID
import struct, collections

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_field_table.txt"
_lines=[]
def p(s=''):
    print(s); _lines.append(str(s))

# 63 field offsets (from t1_fields.py, authoritative)
OFFSETS=[0x24,0x26,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,
0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0xac,0xdc,0xe0,0xe4,0xe8,0xec,0xf0,0xf4,0xf8,0xfc,
0x100,0x104,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,0x116,0x118,0x119,0x11a,0x11b,0x11c,
0x11d,0x11e,0x11f,0x120,0x121,0x122,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x140]
assert len(OFFSETS)==63

# ---- parse local accesses from evidence file ----
local=collections.defaultdict(lambda:{'W':[],'R':[]})
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_cell_fields.txt") as f:
    for ln in f:
        if ln.startswith('#') or ln.startswith('offset') or not ln.strip(): continue
        parts=ln.rstrip('\n').split('\t')
        if len(parts)<7: continue
        try: off=int(parts[0],16)
        except: continue
        w,k,mn,site,func,insn=parts[1],parts[2],parts[3],parts[4],parts[5],parts[6]
        try: site_i=int(site,16)
        except: site_i=site
        local[off][k].append((site_i,func,mn,insn))

# ---- parse global reads from evidence file ----
glob=collections.defaultdict(lambda:{'W':set(),'R':set()})
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t1_global_reads.txt") as f:
    for ln in f:
        if ln.startswith('#') or ln.startswith('offset') or not ln.strip(): continue
        parts=ln.rstrip('\n').split('\t')
        if len(parts)<5: continue
        try: off=int(parts[0],16)
        except: continue
        site,k,mn,insn=parts[1],parts[2],parts[3],parts[4]
        try: site_i=int(site,16)
        except: site_i=site
        glob[off][k].add((site_i,mn,insn))

# ---- rep stosd zero-fill ranges from ctor ----
# Parse ctor: lea edi,[esi+disp] ; mov ecx,N ; rep stosd => writes N dwords from disp
repfills=[]
ctor_insns=list(disasm(0x47bbf0,0x260))
pending_edi=None; pending_ecx=None
for i,ins in enumerate(ctor_insns):
    if ins.id==0: continue
    if ins.mnemonic=='lea' and 'edi' in ins.op_str and 'esi' in ins.op_str:
        # extract disp
        import re
        m=re.search(r'\[esi\s*\+\s*(0x[0-9a-f]+)\]',ins.op_str)
        if m: pending_edi=int(m.group(1),16)
    elif ins.mnemonic=='mov' and ins.op_str.startswith('ecx, 0x'):
        pending_ecx=int(ins.op_str.split('0x')[1],16)
    elif ins.mnemonic=='rep stosd' or (ins.mnemonic=='rep' and 'stosd' in ins.op_str):
        if pending_edi is not None and pending_ecx is not None:
            repfills.append((pending_edi, pending_ecx*4, ins.address))
        pending_edi=pending_ecx=None
p(f"rep stosd zero-fill ranges in ctor: {[(hex(a),hex(n),hex(s)) for a,n,s in repfills]}")

# ---- build combined per-offset write coverage ----
# Each W site: (start_off, width, site, func, mn, insn)
wall=[]  # direct writes
for off in local:
    for site,func,mn,insn in local[off]['W']:
        # infer width from insn (dword/word/byte) - check dword FIRST before word substring
        w=4
        if 'dword ptr' in insn or insn.startswith('mov ') and '[esi' not in insn and '[' not in insn:
            w=4
        if 'byte ptr' in insn: w=1
        elif 'word ptr' in insn and 'dword ptr' not in insn: w=2
        wall.append((off,w,site,func,mn,insn))
# rep fills as writes
for start,nbytes,site in repfills:
    wall.append((start,nbytes,site,'ctor','rep stosd',f'rep stosd [esi+{start:#x}] .. +{start+nbytes:#x}'))

def covers(off, writes):
    """return list of W that cover byte at `off`."""
    out=[]
    for ws,ww,site,func,mn,insn in writes:
        if ws<=off<ws+ww:
            out.append((site,func,mn,insn,ws,ww))
    return out

# ---- final table ----
p("\n"+"="*72)
p("S06-K2 CellClass 63-field table (W=write sites全集, R=read sites)")
p("="*72)
hdr=f"{'off':>6} {'width':>5} {'#W':>3} {'#R':>3} {'double?':>8}  semantics(derived)"
p(hdr)
rows_out=[]
for off in OFFSETS:
    wcov=covers(off,wall)
    rs=set()
    for site,func,mn,insn in local[off]['R']: rs.add((site,func,mn,insn))
    for site,mn,insn in glob[off]['R']: rs.add((site,'(global:cell*)',mn,insn))
    rlist=sorted(rs)
    dbl = 'YES' if (wcov and rlist) else ('Wonly' if wcov else ('Ronly' if rlist else 'NONE'))
    # width guess: from ctor insn covering this off
    width='?'
    if wcov:
        ww=wcov[0][5]
        width={1:'byte',2:'word',4:'dword'}.get(ww,f'{ww}B')
    p(f"{off:#06x} {width:>5} {len(wcov):3d} {len(rlist):3d} {dbl:>8}")
    rows_out.append((off,width,wcov,rlist,dbl))

# write full detail
with open(OUT,'w') as f:
    f.write("S06-K2 CellClass field table — full write-site catalogue + read samples\n")
    f.write(f"method set from .rdata RTTI (4 vtables + 9 known); rep stosd fills included; virtual [mem] calls excluded\n")
    f.write(f"63 offsets; repfills={repfills}\n\n")
    for off,width,wcov,rlist,dbl in rows_out:
        f.write(f"\n### {off:#06x} ({width})  W={len(wcov)} R={len(rlist)} support={dbl}\n")
        f.write("  WRITE sites (full):\n")
        for site,func,mn,insn,ws,ww in sorted(wcov):
            f.write(f"    {site:#08x} {func:12} {mn:12} {insn}   [covers +{ws:#x}..+{ws+ww:#x})\n")
        f.write("  READ sites (dedup):\n")
        for site,func,mn,insn in rlist:
            f.write(f"    {site:#08x} {func:20} {mn:10} {insn}\n")
p(f"\n[saved] {OUT}")

# double support count
dbl_count=sum(1 for _,_,_,_,d in rows_out if d=='YES')
p(f"\nDOUBLE-SUPPORT (W>=1 and R>=1) fields = {dbl_count}/63")
