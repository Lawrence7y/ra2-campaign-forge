import os,sys,json,collections,datetime,re
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work\callmap.json",encoding='utf-8') as f: cm={int(k,16):v for k,v in json.load(f).items()}
out=[]
w=out.append
w('S10-K15 EVIDENCE — generated '+datetime.datetime.now().astimezone().isoformat())
w('Target SHA-256 '+common.hashlib.sha256(open(common.EXE,'rb').read()).hexdigest().upper())
w('')
w('== BASELINE / COVERAGE SCHEMA ==')
w('coverage rows '+str(len(rows))+' atlas rows '+str(len(atl)))
w('grade is column index 4; entry normalized lower-case against atlas')
w('')
for entry,slot in [(0x6FB170,0x414),(0x6FB470,0x418)]:
 cr=cov[f'{entry:08X}']; size=int(atl[f'{entry:08x}'][1])
 w('== TARGET '+f'{entry:08X}'+' ==')
 w('coverage '+'\t'.join(cr))
 w('atlas size '+str(size))
 w('RTTI slots:')
 for vt in common.vtable_info():
  found=[]
  for k in range(vt['slots']):
   if common.u32(vt['vt']+4*k)==entry: found.append(k)
  if found:
   col=common.u32(vt['vt']-4); td=common.u32(col+0xC); nm=common.cstr(td+8,80)
   w('  class='+vt['class']+' vt='+hex(vt['vt'])+' COL='+hex(col)+' TD='+hex(td)+' TD+8='+repr(nm)+' slots='+str(found))
 w('direct proved callees in body:')
 ins=common.disasm(entry,size)
 ctr=collections.Counter()
 for i in ins:
  t=common.call_target(i)
  if t is not None: ctr[t]+=1
 for t,n in sorted(ctr.items()):
  rr=cov.get(f'{t:08X}')
  if rr and rr[4]=='[已证]':
   w('  '+f'{t:08X}'+' x'+str(n)+' '+rr[2]+' ['+rr[1]+']')
 w('external vcall sites at slot disp '+hex(slot)+':')
 pat=re.compile(r'\[\w+ \+ 0x'+f'{slot:x}'+r'\]')
 by=collections.defaultdict(list)
 for k,r in atl.items():
  if k=='entry': continue
  a=int(k,16); sz=int(r[1])
  for i in common.disasm(a,sz):
   if i.mnemonic=='call' and pat.search(i.op_str): by[a].append(i.address)
 for a,sites in sorted(by.items()):
  rr=cov.get(f'{a:08X}')
  w('  caller '+f'{a:08X}'+' sites='+','.join(hex(x) for x in sites)+' '+(('['+rr[1]+'] '+rr[2]+' '+rr[4]) if rr else '?'))
 w('body key bytes/instructions:')
 for i in ins:
  s=common.fmt(i)
  if any(x in i.bytes.hex() for x in ['c6866902000001','c6866902000000','c6866c020000']) or ('call' in i.mnemonic and common.call_target(i) in [0x5657A0,0x50B6F0,0x4F9A50,0x657CE0,0x4F42F0,0x6D20E0]):
   w('  '+s+(' ; '+cov[f'{common.call_target(i):08X}'][2] if common.call_target(i) in cov and cov[f'{common.call_target(i):08X}'][4]=='[已证]' else ''))
 w('body entry-to-ret disassembly:')
 for i in ins: w('  '+common.fmt(i))
 w('')
text='\n'.join(out)
p=os.path.join(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\EVIDENCE",'PROOF_006FB170_006FB470.txt')
with open(p,'w',encoding='utf-8') as f: f.write(text)
print('wrote',p,'chars',len(text),'lines',len(out))
