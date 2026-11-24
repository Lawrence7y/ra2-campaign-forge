from common import Image, EV, BASE, ROOT
import bisect, struct
img=Image(); lines=[]
atlas=ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'
ents=[]
for ln in atlas.read_text(encoding='utf-8',errors='replace').splitlines()[1:]:
 c=ln.split('\t')
 if len(c)>=2:
  try: ents.append((int(c[0],16),int(c[1])))
  except: pass
ents.sort(); starts=[e[0] for e in ents]
def owner(va):
 i=bisect.bisect_right(starts,va)-1
 if i<0: return None
 e,sz=ents[i]
 return (e,sz) if va<e+sz else None
def callers(target):
 out=[]
 for e,sz in ents:
  for ins in img.cs.disasm(img.read(e,sz),e):
   if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
    try: t=int(ins.op_str,16)
    except: continue
    if t==target: out.append((e,ins.address))
 return out
lines.append('=== verified direct callers (capstone over atlas function ranges) ===')
for t in (0x006B6C90,0x006B6EA0,0x006B6FA0,0x004E0E80,0x006B7010):
 cs=callers(t)
 lines.append(f'{t:08X}: '+', '.join(f'call@{a:08X} in {e:08X}' for e,a in cs))
# dump relevant functions
def dump_func(va,label,stop_after=None):
 o=owner(va)
 if not o: lines.append(f'NO OWNER {va:08X}'); return
 e,sz=o
 lines.append(f'===== {label} entry {e:08X} size {sz:X} =====')
 for ins in img.cs.disasm(img.read(e,sz),e):
  lines.append(img.fmt(ins))
  if stop_after and ins.address>=stop_after: break
 lines.append('')
dump_func(0x006B6C90,'ctor candidate A')
dump_func(0x006B6EA0,'ctor candidate B')
for va in (0x006F3FF4,0x006C0A4C,0x004D32D6,0x006F4402):
 dump_func(va,'caller context '+f'{va:08X}',stop_after=va+0x60)
(EV/'caller_and_ctor_context.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines[:400]))
