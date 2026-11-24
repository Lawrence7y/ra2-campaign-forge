"""Focused final verification: 006CF430 full rings + 004A2990 atexit check."""
import re_lib as R
import struct

TAB = chr(9)
atlas = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
funcs = []
for ln in open(atlas, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if len(c) >= 2:
        try: funcs.append((int(c[0],16), int(c[1])))
        except ValueError: pass
funcs.sort()
def enclosing(va):
    for e,sz in funcs:
        if e<=va<e+sz: return e,sz
    return None

# --- 006CF430 full body ---
print("="*100)
print("006CF430 SwizzleManagerClass::slot0 - FULL BODY")
for a,mn,op,sz,bh in R.disasm(0x6CF430, 0x90):
    print("  %08X %-20s %-8s %s" % (a,bh,mn,op))
print("-- holders --")
for h in R.holder_scan(0x6CF430):
    print("  dword @ 0x%08X" % h)
    for k in range(0,16):
        vt=h-k*4; col=R.read_u32(vt-4)
        if col is None: continue
        td=R.read_u32(col+0xC)
        if td is None: continue
        nm=R.read_cstr(td+8)
        if nm and ".?AV" in nm:
            print("    vt=0x%08X slot=%d COL=0x%08X TD=0x%08X %r verify=0x%08X" % (vt,k,col,td,nm,R.read_u32(vt+k*4) or 0))

# vtable 0x7F4108 install sites
print("-- installs of vt 0x7F4108 --")
needle=struct.pack("<I",0x7F4108)
tv,ts,_=R.TEXT; blob=R.DATA[R.va_to_off(tv):R.va_to_off(tv)+ts]
pos=0
while True:
    pos=blob.find(needle,pos)
    if pos<0: break
    site=tv+pos
    print("  raw @ 0x%08X enclosing=%s" % (site, enclosing(site)))
    for a,mn,op,sz,bh in R.disasm(site-8,14):
        print("     %08X %-16s %-7s %s" % (a,bh,mn,op))
    pos+=1

# atexit registrations for candidate ctors/destructors
print("="*100)
print("atexit (call 0x7C978A) sites - count and pushed args")
cnt=0
for site,target in R.sweep_e8_boundary(tv,tv+ts):
    if target==0x7C978A:
        cnt+=1
        if cnt<=6:
            for a,mn,op,sz,bh in R.disasm(site-10,10):
                print("   @%08X %-8s %s" % (a,mn,op))
print("  total atexit sites:",cnt)
