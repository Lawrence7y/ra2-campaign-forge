"""
S11-K1: exact E8/E9 rel32 call-target scanner (decodes rel32, no heuristic).
Finds exact direct call sites to given targets; reports caller instruction addresses.
Also checks if site lies inside an atlas function interval for context (atlas used only for context,
not as the sole discovery channel).
"""
import struct
from pehelp import IMAGE_BASE, rd, u32, is_code, in_section

TARGETS = {
  0x41C250:'CoCreateInstance wrapper', 0x451890:'?', 0x6C6400:'register class obj',
  0x6C4010:'Drive IClassFactory::CreateInstance', 0x6C3F40:'Drive factory ctor',
  0x6BD130:'CLSID registration fn', 0x4AF540:'Drive ctor',
}

txt_lo = IMAGE_BASE + 0x1000
txt_size = 0x3DF38D
blob = rd(txt_lo, txt_size)

# exact rel32 call/jmp targets
calls={t:[] for t in TARGETS}
for i in range(txt_size-5):
    op=blob[i]
    if op in (0xE8,0xE9):
        rel=struct.unpack_from('<i',blob,i+1)[0]
        tgt=txt_lo+i+5+rel
        if tgt in calls:
            calls[tgt].append(txt_lo+i)

# atlas for context only
atlas={}
try:
    with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv') as f:
        next(f)
        for ln in f:
            p=ln.rstrip('\n').split('\t')
            a=int(p[0],16); sz=int(p[1])
            atlas[a]=sz
except Exception as e:
    print('atlas load failed',e)

def atlas_for(site):
    # find function whose interval contains site
    for a,sz in atlas.items():
        if a<=site<a+sz:
            return a,sz
    return None,None

for t,nm in TARGETS.items():
    print('%08X %-40s direct call sites: %d' % (t,nm,len(calls[t])))
    for s in calls[t]:
        a,sz=atlas_for(s)
        print('   site %08X in fn %s size %s' % (s, ('%08X'%a) if a else 'NOT-ATLAS', sz if sz else '-'))
